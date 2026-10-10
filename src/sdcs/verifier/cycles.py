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
    advisory: bool = False


CODE_EXTENSIONS = {
    ".py",
    ".pyi",
    ".ts",
    ".tsx",
    ".js",
    ".jsx",
    ".mjs",
    ".cjs",
    ".c",
    ".cpp",
    ".cc",
    ".cxx",
    ".h",
    ".hpp",
    ".hxx",
    ".go",
    ".rs",
    ".java",
    ".kt",
    ".kts",
    ".scala",
    ".rb",
    ".php",
    ".cs",
    ".swift",
    ".sh",
    ".bash",
    ".zsh",
    ".ps1",
    ".lua",
    ".r",
    ".dart",
    ".zig",
    ".nim",
}

IGNORED_DIRECTORIES = {
    "docs",
    "doc",
    "documentation",
    "traces",
    "trace",
    "logs",
    "log",
    "cache",
    ".cache",
    ".scratch",
    ".tmp",
    "tmp",
    ".agent",
    ".gemini",
    ".vscode",
    ".idea",
    ".git",
    "sessions",
    "assets",
    "debug_rejections",
}


def _is_code_file(filepath: str) -> bool:
    """Return True if filepath represents source code, excluding docs, traces, and blackboards."""
    normalized = filepath.replace("\\", "/").strip().lower()
    p = Path(normalized)
    if any(part in IGNORED_DIRECTORIES for part in p.parts):
        return False
    if p.name in ("state.md", "roadmap.md", "decisions.md", "evals.md", "spine.md", "app_map.md"):
        return False
    return p.suffix in CODE_EXTENSIONS


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


def get_git_commit_diff_history(repo_root: Path, limit: int = 8) -> list[GitCommitDiff]:
    """Retrieve commits with modified source code files, subject, and line diffs for the last `limit` git commits."""
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
        active_is_code = False

        def push_current():
            nonlocal curr_hash, curr_msg, curr_files, curr_added, curr_removed, active_is_code
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
                active_is_code = False

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
                    if _is_code_file(filepath):
                        curr_files.add(filepath)
                        active_is_code = True
                    else:
                        active_is_code = False
            elif line.startswith("+") and not line.startswith("+++"):
                if active_is_code:
                    cleaned = line[1:].strip()
                    if cleaned:
                        curr_added.add(cleaned)
            elif line.startswith("-") and not line.startswith("---"):
                if active_is_code:
                    cleaned = line[1:].strip()
                    if cleaned:
                        curr_removed.add(cleaned)

        push_current()
        return commits
    except Exception:
        return []


def is_diff_reversal(c_newer: GitCommitDiff, c_older: GitCommitDiff) -> bool:
    """Check if c_newer semantically reverses or undoes code changes made in c_older.

    Note: Matching is strictly diff-based on source code files. Commit message keywords
    are not used to avoid false positives on documentation or analytical commits.
    """
    # Check if commits share at least one common source code file
    common_code_files = c_newer.files & c_older.files
    if not common_code_files:
        return False

    # If neither commit has any tracked code lines, no diff reversal possible
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
        # Check for direct commit reversals across the entire window
        raw_reversals: list[tuple[int, int, GitCommitDiff, GitCommitDiff, list[str], set[str]]] = []
        for i in range(len(diff_history)):
            for j in range(i + 1, len(diff_history)):
                newer = diff_history[i]
                older = diff_history[j]
                if is_diff_reversal(newer, older):
                    common_files = sorted(newer.files & older.files) or sorted(
                        newer.files | older.files
                    )
                    inverted_lines = (newer.added_lines & older.removed_lines) | (
                        newer.removed_lines & older.added_lines
                    )
                    raw_reversals.append((i, j, newer, older, common_files, inverted_lines))

        # Identify which reversals are repeated identical reversals (cluster size >= 3) vs isolated/workflow reversals (cluster size <= 2)
        # Land -> Revert -> Reland has 2 reversals and is a legitimate engineering workflow.
        # True cyclic thrashing requires >= 3 repeated identical reversals of the same diff.
        adj: dict[int, set[int]] = {r: {r} for r in range(len(raw_reversals))}
        for r1 in range(len(raw_reversals)):
            for r2 in range(r1 + 1, len(raw_reversals)):
                i1, j1, _, _, _, inv1 = raw_reversals[r1]
                i2, j2, _, _, _, inv2 = raw_reversals[r2]
                if len(inv1) >= 3 and len(inv2) >= 3:
                    sim = len(inv1 & inv2) / len(inv1 | inv2)
                    if sim >= 0.7:
                        adj[r1].add(r2)
                        adj[r2].add(r1)

        visited = set()
        blocking_indices: set[int] = set()
        for r in range(len(raw_reversals)):
            if r not in visited:
                component = set()
                queue = [r]
                visited.add(r)
                while queue:
                    curr = queue.pop(0)
                    component.add(curr)
                    for neighbor in adj[curr]:
                        if neighbor not in visited:
                            visited.add(neighbor)
                            queue.append(neighbor)
                if len(component) >= 3:
                    blocking_indices.update(component)

        for idx, (i, j, newer, older, common_files, inv) in enumerate(raw_reversals):
            is_repeated = idx in blocking_indices
            if is_repeated:
                violations.append(
                    CycleViolation(
                        files=common_files,
                        cycle_count=len(blocking_indices),
                        message=(
                            f"Repeated identical commit reversal detected across commits "
                            f"{newer.commit_hash} ('{newer.message}') and {older.commit_hash} ('{older.message}'). "
                            f"Identical code diff ({len(inv)} lines) repeatedly inverted without architectural progression. "
                            "Circuit breaker tripped."
                        ),
                        advisory=False,
                    )
                )
            else:
                violations.append(
                    CycleViolation(
                        files=common_files,
                        cycle_count=2,
                        message=(
                            f"Commit reversal detected (advisory): commit {newer.commit_hash} ('{newer.message}') "
                            f"reverses diff from commit {older.commit_hash} ('{older.message}'). "
                            "If withdrawing or restoring an architectural approach, ensure rationale is recorded in decisions.md."
                        ),
                        advisory=True,
                    )
                )

        # Convert to file set history for oscillation check
        if history is None:
            history = [c.files for c in diff_history]

    if history is None:
        history = get_git_commit_file_history(repo_root, limit=window)

    blocking_violations = [v for v in violations if not v.advisory]
    if len(history) < threshold:
        return (len(blocking_violations) == 0), violations

    # 2. Check for Period-2 Oscillation (A -> B -> A -> B -> ...) ONLY if diff_history was not available
    # When diff_history is present, file-set alternation with forward diffs is normal TDD rhythm.
    if diff_history is None and len(history) >= 4:
        common_a = history[0]
        common_b = history[1]

        # A period-2 oscillation requires two distinct, non-empty file sets
        if common_a and common_b and _jaccard_similarity(common_a, common_b) < 0.5:
            period_2_matches = 0
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
                            advisory=False,
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

    # Determine whether any blocking (non-advisory) violations exist
    blocking_violations = [v for v in violations if not v.advisory]
    passed = len(blocking_violations) == 0
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
        advisory_violations = [v for v in violations if v.advisory]
        if advisory_violations:
            print("[SDCS::GATE_CYCLES::ADVISORY] Reversal detected (advisory, non-blocking):")
            for v in advisory_violations:
                print(f"  - {v.message}")
        print("[SDCS::GATE_CYCLES] OK: No cyclic thrashing or blocking oscillations detected.")
        return 0

    print("[SDCS::GATE_CYCLES::REJECT] CIRCUIT BREAKER TRIPPED:")
    for v in violations:
        if not v.advisory:
            print(f"  - {v.message}")
    return 1
