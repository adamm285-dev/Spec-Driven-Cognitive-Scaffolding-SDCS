"""SDCS Circuit Breaker Engine: File Oscillation and Semantic Thrashing Detection."""

from __future__ import annotations

import re
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


@dataclass
class GitCommitDiff:
    commit_hash: str
    message: str
    files: set[str]
    added_lines: set[str]
    removed_lines: set[str]


def _is_ephemeral_blackboard(filepath: str) -> bool:
    """Return True if filepath is an ephemeral working memory file (e.g. state.md or sessions/)."""
    normalized = filepath.replace("\\", "/").strip().lower()
    if normalized.endswith("state.md"):
        return True
    if "/sessions/" in normalized or normalized.startswith("sessions/"):
        return True
    return False


def get_git_commit_diff_history(repo_root: Path, limit: int = 8) -> list[GitCommitDiff]:
    """Retrieve commits with modified files, subject, and line diffs for the last `limit` git commits."""
    try:
        cmd = ["git", "log", f"-n{limit}", "-p", "--format=COMMIT:%h%x1f%s"]
        res = subprocess.run(
            cmd,
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            check=False,
        )
        if res.returncode != 0 or not res.stdout.strip():
            return []

        commits: list[GitCommitDiff] = []
        curr_hash = ""
        curr_msg = ""
        curr_files: set[str] = set()
        curr_added: set[str] = set()
        curr_removed: set[str] = set()
        active_is_ephemeral = False

        def push_current():
            nonlocal curr_hash, curr_msg, curr_files, curr_added, curr_removed, active_is_ephemeral
            if curr_hash:
                commits.append(
                    GitCommitDiff(
                        commit_hash=curr_hash,
                        message=curr_msg,
                        files=set(curr_files),
                        added_lines=set(curr_added),
                        removed_lines=set(curr_removed),
                    )
                )
                curr_hash = ""
                curr_msg = ""
                curr_files = set()
                curr_added = set()
                curr_removed = set()
                active_is_ephemeral = False

        for line in res.stdout.splitlines():
            if line.startswith("COMMIT:"):
                push_current()
                header = line[len("COMMIT:") :].split("\x1f", 1)
                curr_hash = header[0]
                curr_msg = header[1] if len(header) > 1 else ""
            elif line.startswith("diff --git a/"):
                parts = line.split(" b/")
                if len(parts) == 2:
                    filepath = parts[1].strip().replace("\\", "/")
                    curr_files.add(filepath)
                    active_is_ephemeral = _is_ephemeral_blackboard(filepath)
            elif line.startswith("+") and not line.startswith("+++"):
                if not active_is_ephemeral:
                    cleaned = line[1:].strip()
                    if cleaned:
                        curr_added.add(cleaned)
            elif line.startswith("-") and not line.startswith("---"):
                if not active_is_ephemeral:
                    cleaned = line[1:].strip()
                    if cleaned:
                        curr_removed.add(cleaned)

        push_current()
        return commits
    except Exception:
        return []


def is_diff_reversal(c_newer: GitCommitDiff, c_older: GitCommitDiff) -> bool:
    """Check if c_newer semantically reverses or undoes changes made in c_older."""
    # Check commit message for explicit revert
    msg_lower = c_newer.message.lower()
    if msg_lower.startswith("revert") or "revert" in msg_lower or "undo" in msg_lower:
        if c_older.commit_hash in c_newer.message or c_older.message in c_newer.message:
            return True
        # If commit explicitly states revert and shares specific topic terms with older commit
        stop_words = {
            "revert",
            "reverted",
            "shipped",
            "docs",
            "feat",
            "fix",
            "the",
            "and",
            "for",
            "with",
            "this",
            "that",
            "from",
        }
        words_newer = set(re.findall(r"\w{3,}", msg_lower)) - stop_words
        words_older = set(re.findall(r"\w{3,}", c_older.message.lower())) - stop_words
        if len(words_newer & words_older) >= 2:
            return True

    # Check if commits share at least one common non-ephemeral file
    common_code_files = {
        f for f in (c_newer.files & c_older.files) if not _is_ephemeral_blackboard(f)
    }
    if not common_code_files:
        return False

    # If neither commit has any tracked non-ephemeral lines, no diff reversal possible
    if not c_newer.added_lines and not c_newer.removed_lines:
        return False
    if not c_older.added_lines and not c_older.removed_lines:
        return False

    # Check line diff inversion (added in newer was removed in older, removed in newer was added in older)
    overlap_fwd = len(c_newer.added_lines & c_older.removed_lines)
    overlap_rev = len(c_newer.removed_lines & c_older.added_lines)
    total_reversed = overlap_fwd + overlap_rev

    if total_reversed >= 3:
        older_total = len(c_older.added_lines) + len(c_older.removed_lines)
        newer_total = len(c_newer.added_lines) + len(c_newer.removed_lines)
        if older_total > 0 and (total_reversed / older_total) >= 0.4:
            return True
        if newer_total > 0 and (total_reversed / newer_total) >= 0.4:
            return True

    return False


def detect_oscillations(
    repo_root: Path = Path("."),
    window: int = 6,
    threshold: int = 3,
    history: list[set[str]] | None = None,
    diff_history: list[GitCommitDiff] | None = None,
) -> tuple[bool, list[CycleViolation]]:
    """Detect alternating file oscillations (e.g. A -> B -> A -> B) and commit reversals across recent commits.

    Parameters:
    - repo_root: Path to repository root.
    - window: Number of recent commits to analyze.
    - threshold: Minimum repetition count to trip the circuit breaker.
    - history: Optional pre-computed commit file sets (for testing or external telemetry).
    - diff_history: Optional pre-computed commit diff objects.

    Returns:
    - (passed, list_of_violations)
    """
    violations: list[CycleViolation] = []

    # 1. If diff_history or live git repo available, perform semantic diff reversal audit
    if diff_history is None and history is None:
        diff_history = get_git_commit_diff_history(repo_root, limit=window)

    if diff_history:
        # Check for direct commit reversals across the window
        for i in range(len(diff_history)):
            for j in range(i + 1, min(len(diff_history), i + 3)):
                newer = diff_history[i]
                older = diff_history[j]
                if is_diff_reversal(newer, older):
                    common_files = sorted(newer.files & older.files) or sorted(
                        newer.files | older.files
                    )
                    violations.append(
                        CycleViolation(
                            files=common_files,
                            cycle_count=2,
                            message=(
                                f"Commit reversal detected: commit {newer.commit_hash} ('{newer.message}') "
                                f"reverses diff from commit {older.commit_hash} ('{older.message}'). "
                                "Semantic thrashing halted to prevent token exhaustion."
                            ),
                        )
                    )

        # Convert to file set history for oscillation check
        if history is None:
            history = [c.files for c in diff_history]

    if history is None:
        history = get_git_commit_file_history(repo_root, limit=window)

    if len(history) < threshold:
        return (len(violations) == 0), violations

    # 2. Check for Period-2 Oscillation (A -> B -> A -> B -> ...)
    if len(history) >= 4:
        period_2_matches = 0
        common_a = history[0]
        common_b = history[1]

        for i in range(2, len(history)):
            target = common_a if (i % 2 == 0) else common_b
            sim = _jaccard_similarity(history[i], target)
            cross_sim = _jaccard_similarity(history[i], common_b if (i % 2 == 0) else common_a)
            if sim >= 0.7 and cross_sim < 0.7:
                period_2_matches += 1

        if period_2_matches + 2 >= threshold * 2 - 1:
            oscillating_files = sorted(common_a | common_b)
            if not any(set(v.files) == set(oscillating_files) for v in violations):
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

    # 3. Check for Single-File Repeated Thrashing ONLY if diff_history was not available
    # When diff_history is present, forward progressive edits to the same file are welcomed.
    # When only raw file sets are given (e.g. synthetic test), maintain fallback check.
    if diff_history is None:
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
