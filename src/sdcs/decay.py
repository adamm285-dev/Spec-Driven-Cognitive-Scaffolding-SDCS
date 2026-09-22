"""
sdcs.decay - Automated Temporal Staleness & Rejection Pruning Engine (SPEC-001 v1.5.0)

Detects stale empirical telemetry (>50 commits behind HEAD) in roadmap.md
and prunes decisions.md to prevent graveyard bloat (>15 active entries).
"""

import datetime
import re
import subprocess
from pathlib import Path


def locate_roadmap_file(repo_root: Path) -> Path | None:
    for c in [repo_root / "roadmap.md", repo_root / ".agent" / "roadmap.md"]:
        if c.is_file():
            return c
    return None


def locate_decisions_file(repo_root: Path) -> Path | None:
    for c in [repo_root / "decisions.md", repo_root / ".agent" / "decisions.md"]:
        if c.is_file():
            return c
    return None


def get_commit_distance(repo_root: Path, commit_hash: str) -> int | None:
    """Computes git commit distance between commit_hash and HEAD."""
    try:
        res = subprocess.run(
            ["git", "rev-list", "--count", f"{commit_hash}..HEAD"],
            cwd=str(repo_root),
            capture_output=True,
            text=True,
        )
        if res.returncode == 0:
            return int(res.stdout.strip())
    except (subprocess.SubprocessError, ValueError, OSError):
        pass
    return None


def audit_roadmap_staleness(
    roadmap_file: Path,
    repo_root: Path,
    threshold: int = 50,
    tag_stale: bool = False,
) -> tuple[int, list[dict]]:
    """
    Scans [MEASURED] entries in roadmap.md for commit hashes and checks distance from HEAD.
    Returns: (stale_count, list_of_audit_records)
    """
    content = roadmap_file.read_text(encoding="utf-8", errors="ignore")
    lines = content.splitlines()
    modified_lines = []
    records = []
    stale_count = 0

    # Pattern to match commit references in [MEASURED] lines:
    # e.g. (Commit `a9f4c21`), Commit a9f4c21, commit: 1234567
    commit_pattern = re.compile(
        r"(?:commit|hash)[:\s]+[`\"']?([0-9a-f]{7,40})[`\"']?", re.IGNORECASE
    )

    for line in lines:
        curr_line = line
        if "[MEASURED]" in line:
            match = commit_pattern.search(line)
            if match:
                chash = match.group(1)
                dist = get_commit_distance(repo_root, chash)
                is_stale = dist is not None and dist > threshold
                record = {
                    "line": line.strip(),
                    "commit": chash,
                    "distance": dist,
                    "stale": is_stale,
                }
                records.append(record)

                if is_stale:
                    stale_count += 1
                    if tag_stale and "[STALE" not in line:
                        curr_line = f"{line.rstrip()} [STALE: {dist} commits behind HEAD]"
        modified_lines.append(curr_line)

    if tag_stale and stale_count > 0:
        roadmap_file.write_text("\n".join(modified_lines) + "\n", encoding="utf-8")

    return stale_count, records


def parse_rejection_entries(content: str) -> list[dict]:
    """Parses decisions.md into discrete REJ- / ADR- blocks."""
    entries = []
    current_entry = None

    for line in content.splitlines():
        header_match = re.match(r"^##\s+((?:REJ|ADR)-[^\s:]+)(?::\s*(.+))?$", line.strip())
        if header_match:
            if current_entry:
                entries.append(current_entry)
            current_entry = {
                "id": header_match.group(1),
                "title": (header_match.group(2) or "").strip(),
                "header": line.strip(),
                "lines": [line],
            }
        elif current_entry:
            current_entry["lines"].append(line)

    if current_entry:
        entries.append(current_entry)

    return entries


def prune_decisions_archive(
    decisions_file: Path,
    repo_root: Path,
    max_entries: int = 15,
) -> tuple[int, Path | None]:
    """
    Archives older rejections when active entries exceed max_entries.
    Moves superseded entries to decisions/archive/YYYY-QX.md and inserts an index table.
    Returns: (pruned_count, archive_path)
    """
    content = decisions_file.read_text(encoding="utf-8", errors="ignore")
    entries = parse_rejection_entries(content)

    if len(entries) <= max_entries:
        return 0, None

    # Keep latest max_entries, archive the rest
    excess_count = len(entries) - max_entries
    to_archive = entries[:excess_count]
    to_keep = entries[excess_count:]

    # Determine quarter for archive filename
    now = datetime.datetime.now(datetime.timezone.utc)
    quarter = (now.month - 1) // 3 + 1
    archive_dir = decisions_file.parent / "decisions" / "archive"
    archive_dir.mkdir(parents=True, exist_ok=True)
    archive_file = archive_dir / f"{now.year}-Q{quarter}.md"

    # Write or append to archive
    archive_lines = []
    if not archive_file.exists():
        archive_lines.append(f"# SDCS Decisions Archive — {now.year} Q{quarter}")
        archive_lines.append(f"<!-- Archived from {decisions_file.name} -->\n")

    for entry in to_archive:
        archive_lines.extend(entry["lines"])
        archive_lines.append("")

    with open(archive_file, "a", encoding="utf-8") as af:
        af.write("\n".join(archive_lines).strip() + "\n\n")

    # Reconstruct decisions.md with an archival index table
    new_decisions_lines = [
        "# Negative Episodic Memory (The Graveyard)",
        "<!-- SPEC-001 Pillar 6 | Mutability: APPEND-ONLY | Working Set: <= 15 Entries -->\n",
        "## Archived Rejections Index",
        "| Rejection ID | Title | Archive Target |",
        "| :--- | :--- | :--- |",
    ]
    for entry in to_archive:
        new_decisions_lines.append(
            f"| `{entry['id']}` | {entry['title'] or 'Superseded rejection'} | `{archive_file.name}` |"
        )
    new_decisions_lines.append("")

    for entry in to_keep:
        new_decisions_lines.extend(entry["lines"])
        new_decisions_lines.append("")

    decisions_file.write_text("\n".join(new_decisions_lines).strip() + "\n", encoding="utf-8")
    return excess_count, archive_file


def run_decay_command(
    repo_root: Path,
    commit_threshold: int = 50,
    max_entries: int = 15,
    prune: bool = False,
    tag_stale: bool = False,
) -> int:
    """CLI entrypoint for sdcs decay."""
    print("====================================================================")
    print(" SDCS :: Automated Staleness Decay & Rejection Pruning Engine")
    print(f" Target Repository: {repo_root}")
    print(f" Telemetry Staleness Threshold: > {commit_threshold} commits behind HEAD")
    print(f" Decisions Active Ceiling:       <= {max_entries} entries")
    print("====================================================================\n")

    exit_code = 0

    # 1. Audit Roadmap Telemetry Staleness
    roadmap_file = locate_roadmap_file(repo_root)
    if roadmap_file:
        stale_count, records = audit_roadmap_staleness(
            roadmap_file=roadmap_file,
            repo_root=repo_root,
            threshold=commit_threshold,
            tag_stale=tag_stale,
        )
        print(
            f"[ROADMAP TELEMETRY AUDIT] Audited {len(records)} [MEASURED] entries in {roadmap_file.name}"
        )
        for r in records:
            status_str = (
                f"STALE ({r['distance']} commits behind)"
                if r["stale"]
                else f"FRESH ({r['distance']} commits behind)"
            )
            flag = "⚠️" if r["stale"] else "✓"
            print(f"  {flag} Commit `{r['commit']}`: {status_str}")

        if stale_count > 0:
            print(
                f"\n⚠️  [DECAY WARNING] {stale_count} telemetry points exceed freshness window (>{commit_threshold} commits)."
            )
            if not tag_stale:
                print("   Run with '--tag-stale' to update roadmap.md markers.")
        else:
            print("  ✓ All telemetry records are within the freshness window.")
    else:
        print("  · No roadmap.md found. Skipping telemetry decay audit.")

    print()

    # 2. Audit & Prune Decisions Graveyard
    decisions_file = locate_decisions_file(repo_root)
    if decisions_file:
        content = decisions_file.read_text(encoding="utf-8", errors="ignore")
        entries = parse_rejection_entries(content)
        print(
            f"[DECISIONS GRAVEYARD AUDIT] Found {len(entries)} active entries in {decisions_file.name}"
        )

        if len(entries) > max_entries:
            print(f"⚠️  [BLOAT DETECTED] {len(entries)} entries exceed ceiling of {max_entries}.")
            if prune:
                pruned_count, arch_file = prune_decisions_archive(
                    decisions_file=decisions_file,
                    repo_root=repo_root,
                    max_entries=max_entries,
                )
                print(f"  ✓ [PRUNED] Moved {pruned_count} superseded rejections to {arch_file}")
            else:
                print("   Run with '--prune' to automatically archive oldest entries.")
                exit_code = 1
        else:
            print(
                f"  ✓ Active rejection count ({len(entries)}) is within disciplined threshold (<= {max_entries})."
            )
    else:
        print("  · No decisions.md found. Skipping graveyard audit.")

    return exit_code
