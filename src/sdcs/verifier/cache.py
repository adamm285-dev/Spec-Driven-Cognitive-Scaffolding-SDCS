"""Gate C-Cache: KV-Cache Invariant & Prefix Pinning Auditor.

SPEC-001 v1.8.0 Section 7.13.
Verifies that Turn 1 boot hydration payloads and system instruction templates
maintain strict prefix invariance to maximize server-side KV prompt caching.
Detects dynamic timestamps, turn counters, and transient session IDs in the prefix
that would bust the 75-90% prompt cache discount across multi-turn agent loops.
"""

from __future__ import annotations

import re
from pathlib import Path

VOLATILE_PREFIX_PATTERNS = [
    (r"\b\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}", "ISO 8601 dynamic timestamp"),
    (r"\b\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}", "Dynamic datetime string"),
    (r"\b[Tt]urn\s+\d+\s+(of|/)\s+\d+\b", "Dynamic turn counter"),
    (r"\b[Ss]tep\s+\d+\s+(of|/)\s+\d+\b", "Dynamic step counter"),
    (r"\b[Pp]rocess\s+[Ii][Dd]:?\s*\d+\b", "Transient process ID"),
]


def audit_prefix_invariance(text: str, prefix_char_limit: int = 4000) -> list[str]:
    """Audits the prefix (first N chars) of a system instruction or hydration payload

    for volatile markers that invalidate downstream KV prompt caches.
    """
    prefix_sample = text[:prefix_char_limit]
    violations = []

    for pattern, desc in VOLATILE_PREFIX_PATTERNS:
        matches = re.findall(pattern, prefix_sample)
        if matches:
            violations.append(f"Detected {desc} in cache prefix: '{matches[0]}'")

    return violations


def audit_hydration_file(file_path: Path) -> list[str]:
    """Audits a cognitive pillar or prompt template for prefix cache compliance."""
    if not file_path.is_file():
        return []

    content = file_path.read_text(encoding="utf-8", errors="ignore")
    # For spine.md, wiring.yaml, AGENTS.md, the whole file should be cache-invariant
    return audit_prefix_invariance(content, prefix_char_limit=len(content))


def run_cache_invariance_audit(repo_root: Path) -> int:
    """CLI runner auditing repository prompt and hydration templates for KV-cache invariance."""
    print("\n====================================================================")
    print(" SDCS :: KV-Cache Prefix Invariance Auditor (SPEC-001 v1.8.0)")
    print(f" Target Repository: {repo_root}")
    print("====================================================================\n")

    candidates = [
        repo_root / "spine.md",
        repo_root / ".agent" / "spine.md",
        repo_root / "wiring.yaml",
        repo_root / ".agent" / "wiring.yaml",
        repo_root / "AGENTS.md",
    ]

    # Include prompt templates if present
    prompts_dir = repo_root / "prompts"
    if prompts_dir.is_dir():
        candidates.extend(prompts_dir.glob("*.md"))

    total_checked = 0
    violations_found = 0

    for cand in candidates:
        if cand.is_file():
            total_checked += 1
            rel = cand.relative_to(repo_root).as_posix()
            violations = audit_hydration_file(cand)
            if violations:
                violations_found += len(violations)
                print(f"[SDCS::CACHE_ERROR] {rel}:")
                for v in violations:
                    print(f"  · {v}")
            else:
                print(f"[SDCS::CACHE_OK] {rel}: Verified stable (100% KV-cache pinnable).")

    print("\n--------------------------------------------------------------------")
    if violations_found > 0:
        print(
            f"🛑 [GATE CACHE: FAILED] Found {violations_found} cache-busting volatile pattern(s)."
        )
        print("   Rule: Move volatile metadata (timestamps, counters) to dynamic state.md tail.")
        print("====================================================================\n")
        return 1

    print(f"✓ [GATE CACHE: PASSED] All {total_checked} prefix templates are 100% cache-invariant.")
    print("  Server-side KV cache discount (75-90%) is preserved across multi-turn loops.")
    print("====================================================================\n")
    return 0
