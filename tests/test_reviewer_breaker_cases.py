"""Two synthetic histories the circuit breaker has to tell apart.

Written by the reviewing agent, 2026-09-22, against the uncommitted working copy after
v1.8.1. Its hard block is a period-2 test on WHICH FILES each commit touches, and a
reversal of content is only ever advisory. So it blocked five commits of forward progress
that alternated code and test, and waved through one block of code added and removed five
times. Both are measured below; the second is the thing a circuit breaker exists for.

Floorsmith's history contains no thrashing at all -- every reversal in it carried a
measurement -- so it can only show false blocks. These two cases are the smallest
population that shows both directions.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from sdcs.verifier.cycles import detect_oscillations


def _git(repo: Path, *args: str) -> None:
    subprocess.run(
        [
            "git",
            "-c",
            "user.email=reviewer@example.com",
            "-c",
            "user.name=reviewer",
            "-c",
            "core.autocrlf=false",
            *args,
        ],
        cwd=str(repo),
        check=True,
        capture_output=True,
    )


def _commit(repo: Path, name: str, text: str, message: str) -> None:
    (repo / name).write_text(text, encoding="utf-8")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", message)


def _blocking(violations) -> list[str]:
    return [v.message for v in violations if not getattr(v, "advisory", False)]


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    _git(tmp_path, "init", "-q")
    return tmp_path


def test_alternating_code_and_test_commits_are_progress_not_thrash(repo):
    """Every commit adds new lines; nothing is undone. A TDD rhythm must not block."""
    code, tests = "", ""
    for k in range(1, 6):
        new = "".join(f"def f_{k}_{n}(): return {k}{n}\n" for n in range(4))
        if k % 2:
            code += new
            _commit(repo, "area.py", code, f"step {k}: extend area.py")
        else:
            tests += new
            _commit(repo, "test_area.py", tests, f"step {k}: extend test_area.py")

    _, violations = detect_oscillations(repo_root=repo)
    assert _blocking(violations) == []


def test_the_same_block_added_and_removed_five_times_blocks(repo):
    """Identical content reversed four times in a row carries no new information."""
    base = "def base():\n    return 0\n"
    block = (
        "def not_the_door(run):\n"
        "    if run.length < 3.0:\n"
        "        return False\n"
        "    if run.has_swing:\n"
        "        return False\n"
        "    return True\n"
    )
    _commit(repo, "walls.py", base, "base")
    for k in range(1, 6):
        added = k % 2 == 1
        _commit(
            repo,
            "walls.py",
            base + block if added else base,
            f"{'add' if added else 'drop'} not_the_door ({k})",
        )

    _, violations = detect_oscillations(repo_root=repo)
    assert _blocking(
        violations
    ), "the same block was added and removed five times and nothing blocked"


BLOCK = (
    "def split_lobby(area):\n"
    "    if area.width < 3.0:\n"
    "        return [area]\n"
    "    left, right = area.cut()\n"
    "    return [left, right]\n"
)


def test_land_revert_reland_is_a_workflow_not_thrash(repo):
    """Added second pass, 2026-09-22. Two identical reversals, ending where it started.

    This is how teams back a change out and put it back: `git revert`, then a reland once
    the unrelated failure is fixed. Floorsmith never uses git revert, so its history cannot
    show this. The thrash case above reverses the same lines four times; this one twice.
    """
    base = "def base():\n    return 0\n"
    _commit(repo, "walls.py", base, "base")
    _commit(repo, "walls.py", base + BLOCK, "feat: split the office out of the lobby")
    _commit(
        repo,
        "walls.py",
        base,
        'Revert "feat: split the office out of the lobby" (CI red on an unrelated flake)',
    )
    _commit(repo, "walls.py", base + BLOCK, 'Reland "feat: split the office out of the lobby"')

    _, violations = detect_oscillations(repo_root=repo)
    assert _blocking(violations) == []
