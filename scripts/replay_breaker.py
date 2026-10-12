"""Replay the circuit breaker over a repository's WHOLE history.

    python scripts/replay_breaker.py <repo> [--window 6] [--limit 600]

`sdcs verify --cycles` looks at the last `window` commits only, so a clean run at HEAD says
nothing about the other five hundred. This slides the same window across every position in
history and counts the trips. It prints the SDCS commit and the replayed repo's HEAD beside
the numbers: a measurement without the code version that produced it is not a measurement.

Reviewer's figures, production reference repository at 437cc0a (544 commits, window 6):
    v1.8.0  file-touch rule       24 of 538 windows tripped
    v1.8.1  diff-reversal rule    71 of 538 windows tripped, 18 distinct commit pairs

What a mature production repo can and cannot measure. Every reversal in its history is a measured
withdrawal or a correct restore -- see KNOWN_CHAINS. It contains no example of thrashing,
so it measures false trips only. A catch rate needs a second corpus with real ping-pong in
it; until one exists the breaker has no band, and a gate with no band should not block.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

SDCS_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SDCS_ROOT / "src"))

from sdcs.verifier import cycles  # noqa: E402

# Reversal chains in production reference repository, oldest first. Every link carried a reason.
KNOWN_CHAINS = {
    "stated-wall envelope": [
        ("c410d7a", "shipped: the extent the drawing states"),
        ("7429698", "withdrawn: validated on a details sheet, not a plan (measured)"),
        ("cd3eabb", "restored, guarded by the resolved plan page -- the correct fix"),
    ],
    "leaf rule": [
        ("19f0ac2", "shipped: a face is cut where the drawing says the wall ends"),
        ("e406648", "withdrawn: it was deleting real walls"),
        ("4d10d4c", "half restored: the part that protects walls with doors in them"),
    ],
    "tab8 dimension network": [
        ("ee9f58a", "shipped: drawn into the calibration PNG"),
        ("b0ae632", "moved into Tab 8's viewer; the PNG layer was never displayed"),
    ],
}


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=str(repo), capture_output=True, text=True, encoding="utf-8"
    ).stdout.strip()


def _stamp(repo: Path) -> str:
    dirty = "dirty" if _git(repo, "status", "--porcelain", "--untracked-files=no") else "clean"
    return f"{_git(repo, 'rev-parse', '--short', 'HEAD')} ({dirty})"


def _load(repo: Path, limit: int):
    """History newest-first, in whichever form this version of cycles.py consumes."""
    if hasattr(cycles, "get_git_commit_diff_history"):
        return "diff", cycles.get_git_commit_diff_history(repo, limit=limit)
    return "files", cycles.get_git_commit_file_history(repo, limit=limit)


def _detect(kind: str, window_history):
    if kind == "diff":
        return cycles.detect_oscillations(diff_history=window_history)
    return cycles.detect_oscillations(history=window_history)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("repo", type=Path)
    ap.add_argument("--window", type=int, default=6)
    ap.add_argument("--limit", type=int, default=600)
    args = ap.parse_args()
    repo = args.repo.resolve()

    kind, history = _load(repo, args.limit)
    expected = min(args.limit, int(_git(repo, "rev-list", "--count", "HEAD") or 0))
    # The loaders swallow every exception and return []. An empty history replays clean.
    if not history:
        raise SystemExit(
            "REFUSED: no history parsed. The loader hides its errors; not reporting a clean replay."
        )
    if len(history) != expected:
        raise SystemExit(
            f"REFUSED: parsed {len(history)} commits, git has {expected}. Some were dropped."
        )

    print(f"sdcs      {_stamp(SDCS_ROOT)}")
    print(f"replayed  {repo.name} {_stamp(repo)}")
    print(
        f"rule      {'diff-reversal' if kind == 'diff' else 'file-touch'}, window {args.window}\n"
    )

    positions = len(history) - args.window
    tripped = 0
    distinct: dict[str, object] = {}
    for i in range(positions):
        ok, violations = _detect(kind, history[i : i + args.window])
        tripped += not ok
        for v in violations:
            distinct.setdefault(v.message, v)

    print(f"windows tripped: {tripped} of {positions}")
    print(f"distinct trips:  {len(distinct)}")
    for message in distinct:
        print(f"  - {message[:180]}")

    if kind != "diff":
        return 0

    print("\nKnown reversal chains (every link carried a reason):")
    index = {c.commit_hash: k for k, c in enumerate(history)}
    for name, chain in KNOWN_CHAINS.items():
        if not all(h in index for h, _ in chain):
            continue
        print(f"  {name}")
        for (old, old_why), (new, new_why) in zip(chain, chain[1:]):
            distance = index[old] - index[new]
            seen = (
                distance < args.window
            )  # detect_oscillations compares each commit across the window
            fires = cycles.is_diff_reversal(history[index[new]], history[index[old]])
            print(
                f"    {old} -> {new}  {distance} commit(s) apart, "
                f"{'compared' if seen else f'NEVER COMPARED (outside the {args.window}-commit reach)'}, "
                f"is_diff_reversal={fires}"
            )
            print(f"        {new_why}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
