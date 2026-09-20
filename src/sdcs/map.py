"""
sdcs.map - Automated Cartography Drift Detection and Synchronization (SPEC-001 v1.4.0 Pillar 5)
"""

import re
from pathlib import Path

from sdcs.init import generate_flat_app_map, scan_repository_tree


def locate_map_file(repo_root: Path, custom_path: str | Path | None = None) -> Path:
    """Locates app_map.md in repo root, .agent/, or custom path."""
    if custom_path:
        p = Path(custom_path)
        if not p.is_absolute():
            p = repo_root / p
        return p

    candidates = [
        repo_root / "app_map.md",
        repo_root / ".agent" / "app_map.md",
        repo_root / "APP_MAP.md",
        repo_root / ".agent" / "APP_MAP.md",
    ]
    for c in candidates:
        if c.is_file():
            return c
    return repo_root / "app_map.md"


def get_actual_repo_files(repo_root: Path) -> set[str]:
    """
    Scans the repository tree ignoring runtime/cache directories.
    Returns a set of relative file paths using forward slashes.
    """
    tree = scan_repository_tree(repo_root)
    files: set[str] = set()
    for dir_name, filenames in tree.items():
        for fname in filenames:
            if dir_name == "root":
                rel = fname
            else:
                rel = f"{dir_name}/{fname}"
            files.add(rel.replace("\\", "/"))
    return files


def parse_mapped_files(map_content: str, repo_root: Path | None = None) -> set[str]:
    """
    Parses app_map.md content to extract all mapped file paths.
    Supports directory section headers (### `dir/`), bulleted items, and table rows.
    """
    mapped: set[str] = set()
    current_dir: str | None = None

    for line in map_content.splitlines():
        trimmed = line.strip()

        # Check for directory header: ### `dir/` or ### dir/ or ## `dir/`
        header_match = re.match(r"^#{2,4}\s+`?([^`\s:]+?)/?`?\s*$", trimmed)
        if header_match:
            d = header_match.group(1).rstrip("/")
            if d.lower() == "root":
                current_dir = ""
            else:
                current_dir = d
            continue

        # Check for markdown table row: | `path` | or | path |
        if trimmed.startswith("|") and not re.match(r"^\|(\s*:?-+:?\s*\|)+$", trimmed):
            cols = [c.strip().strip("`") for c in trimmed.split("|")[1:-1]]
            if cols:
                col_path = cols[0].replace("\\", "/").rstrip("/")
                if col_path and not col_path.lower().startswith(("file", "path", "asset", "-")):
                    mapped.add(col_path)
            continue

        # Check for bullet list item: - `filename` or * `filename`
        bullet_match = re.match(r"^[-*]\s+`?([^`\s]+)`?", trimmed)
        if bullet_match:
            raw_path = bullet_match.group(1).replace("\\", "/")
            if "/" in raw_path:
                mapped.add(raw_path)
            elif current_dir is not None:
                if current_dir == "":
                    mapped.add(raw_path)
                else:
                    mapped.add(f"{current_dir}/{raw_path}")
            else:
                mapped.add(raw_path)

    # If repo_root is provided, also verify relative bare paths that match real files
    if repo_root is not None:
        normalized: set[str] = set()
        for p in mapped:
            clean = p.replace("\\", "/")
            if (repo_root / clean).is_file():
                normalized.add(clean)
            else:
                normalized.add(p)
        return normalized

    return mapped


def check_cartography(
    repo_root: Path,
    map_file: Path | None = None,
) -> tuple[set[str], set[str]]:
    """
    Audits app_map.md against disk.
    Returns (unmapped_files, orphaned_files).
    """
    if map_file is None:
        map_file = locate_map_file(repo_root)

    actual_files = get_actual_repo_files(repo_root)

    # Exclude app_map.md itself and scaffolding sessions from check
    ignored_patterns = {"app_map.md", ".agent/app_map.md", "sessions/manifest.jsonl"}
    actual_files = {f for f in actual_files if f not in ignored_patterns}

    if not map_file.is_file():
        return actual_files, set()

    content = map_file.read_text(encoding="utf-8", errors="ignore")
    mapped_files = parse_mapped_files(content, repo_root)

    # Filter out directory entries that might have been captured
    mapped_files = {f for f in mapped_files if not f.endswith("/") and f not in ignored_patterns}

    unmapped = actual_files - mapped_files
    orphaned = {f for f in mapped_files if not (repo_root / f).exists()}

    return unmapped, orphaned


def sync_cartography(
    repo_root: Path,
    map_file: Path | None = None,
) -> bool:
    """
    Synchronizes app_map.md by scanning disk and updating the cartography.
    Preserves annotations on existing files while appending new unmapped files
    under their directory sections and removing orphaned entries.
    """
    if map_file is None:
        map_file = locate_map_file(repo_root)

    actual_tree = scan_repository_tree(repo_root)
    # Ignore app_map.md itself from listing
    if "root" in actual_tree:
        actual_tree["root"] = [
            f for f in actual_tree["root"] if f not in {"app_map.md", "APP_MAP.md"}
        ]

    if not map_file.is_file():
        map_file.parent.mkdir(parents=True, exist_ok=True)
        content = generate_flat_app_map(repo_root)
        map_file.write_text(content.strip() + "\n", encoding="utf-8")
        print(f"  + Generated new cartography index: {map_file}")
        return True

    # Parse existing file annotations
    existing_content = map_file.read_text(encoding="utf-8", errors="ignore")
    existing_lines = existing_content.splitlines()
    annotations: dict[str, str] = {}  # rel_path -> annotation line
    current_dir: str | None = None

    for line in existing_lines:
        trimmed = line.strip()
        header_match = re.match(r"^#{2,4}\s+`?([^`\s:]+?)/?`?\s*$", trimmed)
        if header_match:
            d = header_match.group(1).rstrip("/")
            current_dir = "" if d.lower() == "root" else d
            continue

        bullet_match = re.match(r"^[-*]\s+`?([^`\s]+)`?(.*)$", trimmed)
        if bullet_match:
            fname = bullet_match.group(1)
            extra = bullet_match.group(2)
            if "/" in fname:
                rel = fname
            elif current_dir is not None:
                rel = fname if current_dir == "" else f"{current_dir}/{fname}"
            else:
                rel = fname
            annotations[rel] = extra

    # Build updated cartography content
    lines = [
        "# Repository Cartography (The Compass)",
        "<!-- SPEC-001 v1.4.0 Pillar 5 | Flat Cartography -->",
        "<!-- Golden Rule: Consult this map FIRST. Read ONLY necessary target files. -->\n",
    ]

    for directory, files in sorted(actual_tree.items()):
        if not files:
            continue
        lines.append(f"### `{directory}/`")
        for f in sorted(files):
            rel = f if directory == "root" else f"{directory}/{f}"
            extra = annotations.get(rel, "")
            lines.append(f"- `{f}`{extra}")
        lines.append("")

    new_content = "\n".join(lines).strip() + "\n"
    map_file.write_text(new_content, encoding="utf-8")
    print(f"  ✓ [SYNCED] Cartography synchronized with disk: {map_file}")
    return True


def run_map_command(
    repo_root: Path,
    map_path: str | Path | None = None,
    check: bool = False,
    sync: bool = False,
) -> int:
    """Entrypoint for sdcs map CLI."""
    map_file = locate_map_file(repo_root, map_path)
    print("====================================================================")
    print(" SDCS :: Cartography Drift Auditor & Synchronizer (SPEC-001 v1.4.0)")
    print(f" Map Target:  {map_file}")
    print(f" Repository:  {repo_root}")
    print("====================================================================\n")

    if sync:
        sync_cartography(repo_root, map_file)
        return 0

    unmapped, orphaned = check_cartography(repo_root, map_file)

    if not unmapped and not orphaned:
        print("✓ [STATUS: CLEAN] Cartography is 100% in sync with disk.")
        return 0

    if unmapped:
        print(
            f"❌ [DRIFT: UNMAPPED FILES] {len(unmapped)} tracked file(s) missing from {map_file.name}:"
        )
        for u in sorted(unmapped):
            print(f"   - {u}")
        print()

    if orphaned:
        print(
            f"⚠️ [DRIFT: ORPHANED FILES] {len(orphaned)} file(s) in {map_file.name} not found on disk:"
        )
        for o in sorted(orphaned):
            print(f"   - {o}")
        print()

    print("Recommendation: Run 'sdcs map --sync' to update app_map.md in-stride.")
    return 1 if check else 0
