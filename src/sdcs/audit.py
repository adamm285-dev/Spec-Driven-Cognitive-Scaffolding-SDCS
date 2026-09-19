#!/usr/bin/env python3
"""
sdcs.audit — Positive Ground Truth & Corpus Diversity Auditor
Conforming to SPEC-001 v1.2.0 (Pillars 7 & Failure Mitigation 7.4)

Verifies:
  1. Asset Reachability: Fixtures referenced in evals.md exist on disk.
  2. Cryptographic Integrity: Computes normalized SHA-256 digests.
  3. Anti-Evasion Normalization: Strips comments, line-end padding, and
     whitespace variance before digest calculation.
  4. Corpus Diversity Guard: Flags duplicate/near-duplicate fixtures
     masquerading as independent tests (Phantom Corpus Trap).
"""

import argparse
import hashlib
import re
import sys
from pathlib import Path
from typing import NamedTuple


class FixtureEntry(NamedTuple):
    fixture_id: str
    path_str: str
    recorded_hash: str
    status: str
    line_number: int


def calculate_sha256(filepath: Path) -> str:
    """Calculates standard raw SHA-256 digest over file bytes."""
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def strip_comments_and_whitespace(content: str, extension: str) -> str:
    """
    Normalizes text fixtures to defeat trivial hashing evasion (SPEC-001 §7.4).
    Strips comments, removes leading/trailing line padding, and drops empty lines.
    """
    lines = content.splitlines()
    normalized_lines: list[str] = []

    ext = extension.lower()
    is_hash_comment = ext in {".py", ".sh", ".bash", ".yaml", ".yml", ".toml", ".ini"}
    is_c_comment = ext in {".js", ".ts", ".c", ".cpp", ".h", ".java", ".go", ".rs"}
    is_markup_comment = ext in {".html", ".xml", ".md"}

    for raw_line in lines:
        line = raw_line.strip()
        if not line:
            continue

        # Strip full-line and inline '#' comments
        if is_hash_comment:
            if line.startswith("#"):
                continue
            if " #" in line:
                line = line.split(" #", 1)[0].rstrip()

        # Strip full-line and inline '//' comments
        elif is_c_comment:
            if line.startswith("//"):
                continue
            if " //" in line:
                line = line.split(" //", 1)[0].rstrip()

        # Strip single-line HTML/Markdown comments
        elif is_markup_comment:
            if line.startswith("<!--") and line.endswith("-->"):
                continue

        if line:
            normalized_lines.append(line)

    return "\n".join(normalized_lines)


def calculate_normalized_sha256(file_path: Path) -> str:
    """
    Calculates SHA-256 digest on normalized text for supported extensions.
    Falls back to raw byte hashing for binary or non-UTF-8 assets.
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        normalized = strip_comments_and_whitespace(content, file_path.suffix)
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()
    except (UnicodeDecodeError, PermissionError, OSError):
        # Binary fixture fallback (PDF, PNG, etc.): hash raw bytes directly
        return calculate_sha256(file_path)


def locate_evals_file(base_dir: Path, explicit_path: str | None = None) -> Path:
    """Finds evals.md in the root, .agent/, or at an explicit user path."""
    if explicit_path:
        p = Path(explicit_path)
        if not p.is_absolute():
            p = base_dir / p
        return p

    candidates = [
        base_dir / "evals.md",
        base_dir / ".agent" / "evals.md",
        base_dir / "EVALS.md",
        base_dir / ".agent" / "EVALS.md",
        base_dir / "docs" / "evals.md",
    ]
    for c in candidates:
        if c.is_file():
            return c

    return base_dir / "evals.md"


find_evals_file = locate_evals_file


def parse_evals_table(evals_input: str | Path) -> list[FixtureEntry]:
    """Parses markdown table entries from evals.md content or file path."""
    if isinstance(evals_input, Path):
        evals_content = evals_input.read_text(encoding="utf-8", errors="ignore")
    elif isinstance(evals_input, str):
        if "\n" not in evals_input and Path(evals_input).is_file():
            evals_content = Path(evals_input).read_text(encoding="utf-8", errors="ignore")
        else:
            evals_content = evals_input
    else:
        evals_content = str(evals_input)

    entries: list[FixtureEntry] = []
    lines = evals_content.splitlines()
    table_started = False

    for idx, line in enumerate(lines, start=1):
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue

        lower = stripped.lower()
        # Detect table headers (supports both "Fixture ID" and "Asset ID")
        if ("fixture id" in lower or "asset id" in lower) and "path" in lower:
            table_started = True
            continue

        # Skip divider rows
        if table_started and re.match(r"^\|(\s*:?-+:?\s*\|)+$", stripped):
            continue

        if table_started:
            cols = [c.strip().strip("`") for c in stripped.split("|")[1:-1]]
            if len(cols) >= 3:
                fixture_id = cols[0]
                path_str = cols[1]
                recorded_hash = cols[2]
                status = cols[3] if len(cols) > 3 else "active"

                # Skip repeated header, divider, or empty rows
                if (
                    fixture_id.lower() in {"fixture id", "asset id", ":---", "---"}
                    or not fixture_id
                    or not path_str
                ):
                    continue

                entries.append(
                    FixtureEntry(
                        fixture_id=fixture_id,
                        path_str=path_str,
                        recorded_hash=recorded_hash,
                        status=status,
                        line_number=idx,
                    )
                )

    return entries


def run_audit(
    evals_file: Path | None = None,
    repo_root: Path | None = None,
    update_pending: bool = False,
) -> bool:
    """
    Audits ground truth references in evals.md against repository fixtures.
    Returns True if audit passes with zero violations, False otherwise.
    """
    # Normalize argument routing: supports run_audit(repo_root) or run_audit(evals_file, repo_root)
    if evals_file is not None and evals_file.is_dir():
        repo_root = evals_file
        evals_file = locate_evals_file(repo_root)
    elif repo_root is None:
        if evals_file is not None and evals_file.is_file():
            repo_root = evals_file.parent
        else:
            repo_root = Path.cwd()
            evals_file = locate_evals_file(repo_root)
    elif evals_file is None:
        evals_file = locate_evals_file(repo_root)

    print("====================================================================")
    print(" SDCS :: Corpus Integrity & Diversity Audit (SPEC-001 v1.2.0)")
    print(f" Spec Target: {evals_file}")
    print(f" Working Dir: {repo_root}")
    print(" Normalizer:  Whitespace & Comment Invariant Filter (Active)")
    print("====================================================================\n")

    if not evals_file.is_file():
        print(f"[FATAL] evals.md file not found at: {evals_file}", file=sys.stderr)
        return False

    entries = parse_evals_table(evals_file.read_text(encoding="utf-8", errors="ignore"))
    if not entries:
        print("[WARN] No fixture rows found in evals.md table.")
        return True

    seen_hashes: dict[str, list[str]] = {}
    pending_entries: list[tuple[FixtureEntry, str]] = []
    failures = 0

    print(f"Found {len(entries)} fixture entries. Executing verification...\n")

    for entry in entries:
        fixture_path = repo_root / entry.path_str

        # 1. Asset Reachability Gate
        if not fixture_path.exists():
            print(f"  [REACHABILITY FAIL] Fixture '{entry.fixture_id}' not found on disk:")
            print(f"                      Path: {fixture_path}")
            failures += 1
            continue

        computed_hash = calculate_normalized_sha256(fixture_path)

        # Register for diversity verification
        seen_hashes.setdefault(computed_hash, []).append(f"{entry.fixture_id} ({entry.path_str})")

        # 2. Cryptographic Integrity Gate
        if entry.recorded_hash.lower() in {"pending", "tbd", "todo", ""}:
            pending_entries.append((entry, computed_hash))
            print(f"  · [PENDING] {entry.fixture_id:<12} => Computed: {computed_hash[:16]}...")
        else:
            rec_clean = entry.recorded_hash.strip().lower()
            matches = computed_hash == rec_clean or (
                len(rec_clean) in (8, 12, 16) and computed_hash.startswith(rec_clean)
            )
            if not matches:
                print(f"  [HASH DRIFT FAIL]  {entry.fixture_id:<12} (line {entry.line_number})")
                print(f"                     Expected: {entry.recorded_hash}")
                print(f"                     Computed: {computed_hash}")
                failures += 1
            else:
                print(f"  ✓ [VERIFIED]        {entry.fixture_id:<12} => {computed_hash[:16]}...")

    # 3. Corpus Diversity Guard (Phantom Corpus Trap Detection)
    print("\n--------------------------------------------------------------------")
    print(" Evaluating Corpus Diversity Invariant (SHA-256 Collision Check)...")
    diversity_violations = 0
    for h, fixtures in seen_hashes.items():
        if len(fixtures) > 1:
            diversity_violations += 1
            print("\n[PHANTOM CORPUS ERROR] Duplicate or trivially padded fixtures detected:")
            print(f"  Digest: {h}")
            for f in fixtures:
                print(f"    - {f}")

    if diversity_violations > 0:
        print("\nSPEC-001 Violation: Golden fixtures must represent distinct test cases.")
        failures += diversity_violations

    # 4. Handle Pending Records
    if pending_entries:
        print(f"\nDiscovered {len(pending_entries)} 'pending' fixtures.")
        if update_pending:
            print("Writing computed hashes to evals.md...")
            content = evals_file.read_text(encoding="utf-8")
            for entry, computed in pending_entries:
                pattern = rf"(\|\s*`?{re.escape(entry.fixture_id)}`?\s*\|\s*`?{re.escape(entry.path_str)}`?\s*\|\s*)`?pending`?(\s*\|)"
                content = re.sub(pattern, rf"\g<1>{computed}\g<2>", content, flags=re.IGNORECASE)
            evals_file.write_text(content, encoding="utf-8")
            print("Successfully updated evals.md with computed SHA-256 digests.")
        else:
            print("Run with '--update-pending' to populate these hashes automatically.")

    print("\n====================================================================")
    if failures == 0:
        print(" [STATUS: PASSED] All fixtures reachable, verified, and diversified.")
        print("====================================================================")
        return True
    else:
        print(f" [STATUS: FAILED] Audit halted with {failures} error(s).")
        print("====================================================================")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Audit evals.md fixture integrity, anti-evasion normalization, and corpus diversity."
    )
    parser.add_argument("--evals-path", default=None, help="Path to evals.md file")
    parser.add_argument(
        "--repo-root",
        default=".",
        help="Root repository directory (default: current directory)",
    )
    parser.add_argument(
        "--update-pending",
        action="store_true",
        help="Automatically replace 'pending' entries in evals.md with computed hashes",
    )

    args = parser.parse_args()
    repo_root = Path(args.repo_root).resolve()
    evals_file = locate_evals_file(repo_root, args.evals_path)

    success = run_audit(
        evals_file=evals_file, repo_root=repo_root, update_pending=args.update_pending
    )
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
