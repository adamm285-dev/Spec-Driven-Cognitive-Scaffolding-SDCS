"""SDCS Circuit Breaker Engine: File Oscillation and Semantic Thrashing Detection."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass
class CycleViolation:
    files: list[str]
    cycle_count: int
    message: str


def _jaccard_similarity(s1: set[str], s2: set[str]) -> float:
    if not s1 and not s2:
        return 1.0
    union = s1 | s2
    if not union:
        return 1.0
    return len(s1 & s2) / len(union)


def get_git_commit_file_history(repo_root: Path, limit: int = 8) -> list[set[str]]:
    """Retrieve the set of modified files for the last `limit` git commits."""
    try:
        cmd = ["git", "log", f"-n{limit}", "--name-only", "--format=COMMIT:%h"]
        res = subprocess.run(
            cmd,
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            check=False,
        )
        if res.returncode != 0 or not res.stdout.strip():
            return []

        commits: list[set[str]] = []
        current_files: set[str] = set()

        for line in res.stdout.splitlines():
            line = line.strip()
            if not line:
                continue
            if line.startswith("COMMIT:"):
                if current_files:
                    commits.append(current_files)
                    current_files = set()
            else:
                # normalize path separators
                current_files.add(line.replace("\\", "/"))

        if current_files:
            commits.append(current_files)

        return commits
    except Exception:
        return []


def detect_oscillations(
    repo_root: Path = Path("."),
    window: int = 6,
    threshold: int = 3,
    history: list[set[str]] | None = None,
) -> tuple[bool, list[CycleViolation]]:
    """Detect alternating file oscillations (e.g. A -> B -> A -> B) across recent commits.

    Parameters:
    - repo_root: Path to repository root.
    - window: Number of recent commits to analyze.
    - threshold: Minimum repetition count to trip the circuit breaker.
    - history: Optional pre-computed commit file sets (for testing or external telemetry).

    Returns:
    - (passed, list_of_violations)
    """
    if history is None:
        history = get_git_commit_file_history(repo_root, limit=window)

    if len(history) < threshold:
        # Not enough history to definitively identify a multi-cycle loop
        return True, []

    violations: list[CycleViolation] = []

    # 1. Check for Period-2 Oscillation (A -> B -> A -> B -> ...)
    # That is, history[0] ~ history[2] ~ history[4] and history[1] ~ history[3]
    if len(history) >= 4:
        period_2_matches = 0
        common_a = history[0]
        common_b = history[1]

        for i in range(2, len(history)):
            target = common_a if (i % 2 == 0) else common_b
            sim = _jaccard_similarity(history[i], target)
            cross_sim = _jaccard_similarity(history[i], common_b if (i % 2 == 0) else common_a)
            # High similarity to target, low similarity to the opposite phase
            if sim >= 0.7 and cross_sim < 0.7:
                period_2_matches += 1

        if period_2_matches + 2 >= threshold * 2 - 1:  # e.g., A B A B (2 matches, total 4 items)
            oscillating_files = sorted(common_a | common_b)
            violations.append(
                CycleViolation(
                    files=oscillating_files,
                    cycle_count=period_2_matches + 2,
                    message=(
                        f"Period-2 oscillation detected across {period_2_matches + 2} consecutive commits. "
                        f"Agent is ping-ponging between {oscillating_files}. "
                        "Halted to prevent token exhaustion. Require human architectural decision."
                    ),
                )
            )

    # 2. Check for Single-File Repeated Thrashing
    # If the exact same 1 or 2 files are the ONLY files modified in >= threshold consecutive commits
    consecutive_isolated_thrash = 0
    pinned_files: set[str] | None = None

    for commit_files in history[:window]:
        if 0 < len(commit_files) <= 2:
            if pinned_files is None:
                pinned_files = commit_files
                consecutive_isolated_thrash = 1
            elif commit_files == pinned_files:
                consecutive_isolated_thrash += 1
            else:
                break
        else:
            break

    if consecutive_isolated_thrash >= threshold:
        thrash_list = sorted(pinned_files or set())
        # Only add if not already flagged in period-2
        if not any(set(v.files) == set(thrash_list) for v in violations):
            violations.append(
                CycleViolation(
                    files=thrash_list,
                    cycle_count=consecutive_isolated_thrash,
                    message=(
                        f"Repeated isolated modification detected on {thrash_list} across "
                        f"{consecutive_isolated_thrash} consecutive commits without architectural progression. "
                        "Circuit breaker tripped."
                    ),
                )
            )

    passed = len(violations) == 0
    return passed, violations


def run_cycle_audit(
    repo_root: Path = Path("."),
    window: int = 6,
    threshold: int = 3,
) -> int:
    """CLI entrypoint for circuit breaker cycle detection."""
    passed, violations = detect_oscillations(
        repo_root=repo_root,
        window=window,
        threshold=threshold,
    )
    if passed:
        print("[SDCS::GATE_CYCLES] OK: No cyclic thrashing or file oscillations detected.")
        return 0

    print("[SDCS::GATE_CYCLES::REJECT] CIRCUIT BREAKER TRIPPED:")
    for v in violations:
        print(f"  - {v.message}")
    return 1
