"""
sdcs.session - Structured Flight Recorder Indexing (SPEC-001 v1.4.0 Pillar 4 / Invariant 2)
"""

import json
import re
import sys
from pathlib import Path
from typing import Any


def locate_sessions_dir(repo_root: Path, custom_path: str | Path | None = None) -> Path:
    """Locates the sessions directory in root or .agent/."""
    if custom_path:
        p = Path(custom_path)
        if not p.is_absolute():
            p = repo_root / p
        return p

    candidates = [
        repo_root / "sessions",
        repo_root / ".agent" / "sessions",
    ]
    for c in candidates:
        if c.is_dir():
            return c
    return repo_root / "sessions"


def parse_session_file(session_file: Path) -> dict[str, Any]:
    """
    Parses a single flight recorder session markdown file into structured metadata.
    Extracts timestamp, topic, verdict, and high-level summary.
    """
    content = session_file.read_text(encoding="utf-8", errors="ignore")
    filename = session_file.name

    # Default fallback values from filename
    date_match = re.match(r"^(\d{4}-\d{2}-\d{2})", filename)
    timestamp = date_match.group(1) if date_match else "UNKNOWN"
    topic = filename.replace(".md", "")
    if date_match and len(topic) > 11:
        topic = topic[11:].replace("_", " ").replace("-", " ").title()
    verdict = "COMPLETED"
    summary_items: list[str] = []

    current_section = ""
    for line in content.splitlines():
        trimmed = line.strip()

        # Check section headers
        sec_match = re.match(r"^##\s+(.+)$", trimmed)
        if sec_match:
            current_section = sec_match.group(1).lower()
            continue

        # Check metadata bullets
        ts_match = re.match(r"^[-*]\s*Timestamp:\s*(.+)$", trimmed, re.IGNORECASE)
        if ts_match:
            timestamp = ts_match.group(1).strip()
            continue

        topic_match = re.match(
            r"^[-*]\s*(?:Shift Focus|Topic|Objective):\s*(.+)$", trimmed, re.IGNORECASE
        )
        if topic_match:
            topic = topic_match.group(1).strip()
            continue

        verdict_match = re.match(
            r"^[-*]\s*(?:Verdict|Status|Gate):\s*(.+)$", trimmed, re.IGNORECASE
        )
        if verdict_match:
            verdict = verdict_match.group(1).strip()
            continue

        # Extract summary from completed actions or summary section
        if (
            any(kw in current_section for kw in ("completed", "summary", "actions", "verification"))
            and trimmed.startswith(("-", "*"))
            and len(summary_items) < 3
        ):
            clean_item = trimmed.lstrip("-* ").strip()
            if clean_item:
                summary_items.append(clean_item)

    summary = "; ".join(summary_items) if summary_items else "Flight recorder checkpoint."

    return {
        "file": f"sessions/{filename}",
        "timestamp": timestamp,
        "topic": topic,
        "verdict": verdict,
        "summary": summary,
    }


def build_manifest(sessions_dir: Path) -> Path:
    """
    Scans sessions directory and builds/updates manifest.jsonl.
    Excludes template.md, README.md, and manifest.jsonl.
    """
    if not sessions_dir.exists():
        sessions_dir.mkdir(parents=True, exist_ok=True)

    manifest_path = sessions_dir / "manifest.jsonl"
    session_files = sorted(
        [f for f in sessions_dir.glob("*.md") if f.name.lower() not in {"template.md", "readme.md"}]
    )

    records: list[dict[str, Any]] = []
    for sf in session_files:
        try:
            records.append(parse_session_file(sf))
        except (OSError, UnicodeDecodeError, ValueError) as e:
            print(f"[WARN] Failed to parse {sf}: {e}", file=sys.stderr)

    with open(manifest_path, "w", encoding="utf-8") as f:
        f.writelines(json.dumps(rec) + "\n" for rec in records)

    return manifest_path


def query_manifest(
    sessions_dir: Path,
    query_str: str | None = None,
) -> list[dict[str, Any]]:
    """
    Queries manifest.jsonl, generating it if absent.
    Filters records matching query_str across all metadata fields.
    """
    manifest_path = sessions_dir / "manifest.jsonl"
    if not manifest_path.is_file():
        build_manifest(sessions_dir)

    if not manifest_path.is_file():
        return []

    records: list[dict[str, Any]] = []
    with open(manifest_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                try:
                    records.append(json.loads(line.strip()))
                except json.JSONDecodeError:
                    continue

    if not query_str:
        return records

    q = query_str.lower()
    return [
        r
        for r in records
        if q in r.get("topic", "").lower()
        or q in r.get("summary", "").lower()
        or q in r.get("timestamp", "").lower()
        or q in r.get("file", "").lower()
        or q in r.get("verdict", "").lower()
    ]


def run_session_command(
    repo_root: Path,
    action: str = "list",
    query_str: str | None = None,
    sessions_dir: str | Path | None = None,
    as_json: bool = False,
) -> int:
    """CLI handler for sdcs session subcommands."""
    s_dir = locate_sessions_dir(repo_root, sessions_dir)

    if action == "index":
        manifest = build_manifest(s_dir)
        with open(manifest, encoding="utf-8") as f:
            count = sum(1 for _ in f)
        print(f"✓ [INDEXED] Indexed {count} session log(s) into {manifest}")
        return 0

    records = query_manifest(s_dir, query_str)

    if as_json:
        print(json.dumps(records, indent=2))
        return 0

    print("====================================================================")
    print(" SDCS :: Structured Flight Recorder Index (SPEC-001 v1.4.0)")
    print(f" Sessions Dir: {s_dir}")
    print(f" Total Logs:   {len(records)}")
    print("====================================================================\n")

    if not records:
        print("No flight recorder sessions found matching criteria.")
        return 0

    print(f"{'TIMESTAMP':<20} | {'TOPIC':<26} | {'VERDICT':<10} | {'SUMMARY'}")
    print("-" * 85)
    for r in records:
        ts = r.get("timestamp", "")[:19]
        topic = r.get("topic", "")[:26]
        verd = r.get("verdict", "")[:10]
        summary = r.get("summary", "")
        if len(summary) > 40:
            summary = summary[:37] + "..."
        print(f"{ts:<20} | {topic:<26} | {verd:<10} | {summary}")

    return 0
