"""
sdcs.verifier.state - Deterministic Token Budget Linter for Working Memory (SPEC-001 v1.4.0 Pillar 4)
"""

import re
from pathlib import Path


def locate_state_file(repo_root: Path, custom_path: str | Path | None = None) -> Path | None:
    """Locates state.md in repository root, .agent/, or custom path."""
    if custom_path:
        p = Path(custom_path)
        if not p.is_absolute():
            p = repo_root / p
        return p if p.is_file() else None

    candidates = [
        repo_root / "state.md",
        repo_root / ".agent" / "state.md",
        repo_root / "STATE.md",
        repo_root / ".agent" / "STATE.md",
    ]
    for c in candidates:
        if c.is_file():
            return c
    return None


def count_tokens(text: str) -> int:
    """
    Deterministically computes token count.
    Uses tiktoken if installed; otherwise falls back to a deterministic heuristic:
    max(word_count, ceil(char_count / 4)).
    """
    clean_text = text.strip()
    if not clean_text:
        return 0

    try:
        import tiktoken

        # Use standard OpenAI cl100k_base or gpt-4 tokenization
        enc = tiktoken.get_encoding("cl100k_base")
        return len(enc.encode(clean_text))
    except (ImportError, AttributeError, ValueError):
        # High-fidelity fallback heuristic for autonomous LLM token budgeting
        words = len(clean_text.split())
        chars = len(clean_text)
        return max(words, (chars + 3) // 4)


def parse_state_sections(content: str) -> dict[str, str]:
    """
    Parses state.md into sections delineated by markdown level-2 headers (##).
    Header-less preamble is keyed under '__preamble__'.
    """
    sections: dict[str, str] = {}
    current_header = "__preamble__"
    current_lines: list[str] = []

    for line in content.splitlines():
        header_match = re.match(r"^##\s+(.+)$", line.strip())
        if header_match:
            if current_lines:
                sections[current_header] = "\n".join(current_lines).strip()
                current_lines = []
            current_header = header_match.group(1).strip()
        else:
            current_lines.append(line)

    if current_lines:
        sections[current_header] = "\n".join(current_lines).strip()

    return sections


def audit_state_tokens(
    state_file: Path,
    max_tokens: int = 350,
) -> tuple[bool, int, dict[str, int], list[str]]:
    """
    Audits state.md against the specified token budget and verifies canonical schema.
    Returns: (passed, total_tokens, section_tokens, warnings)
    """
    if not state_file.is_file():
        return False, 0, {}, [f"State file not found: {state_file}"]

    content = state_file.read_text(encoding="utf-8", errors="ignore")
    total_tokens = count_tokens(content)

    sections = parse_state_sections(content)
    section_tokens: dict[str, int] = {}
    for header, sec_content in sections.items():
        if sec_content:
            section_tokens[header] = count_tokens(sec_content)

    warnings: list[str] = []

    # Check canonical schema sections
    headers_lower = [h.lower() for h in sections]
    has_objective = any("objective" in h for h in headers_lower)
    has_status = any("status" in h or "gate" in h for h in headers_lower)
    has_next_action = any("next" in h or "action" in h for h in headers_lower)

    if not has_objective:
        warnings.append("Missing recommended canonical section: '## Current Objective'")
    if not has_status:
        warnings.append("Missing recommended canonical section: '## Status & Gate Verification'")
    if not has_next_action:
        warnings.append(
            "Missing recommended canonical section: '## Immediate Next Action (Post-Compact)'"
        )

    passed = total_tokens <= max_tokens
    if not passed:
        warnings.append(
            f"Token budget exceeded: {total_tokens} tokens > {max_tokens} token threshold."
        )

    return passed, total_tokens, section_tokens, warnings


def run_state_audit(
    repo_root: Path,
    state_path: str | Path | None = None,
    max_tokens: int = 350,
) -> int:
    """CLI execution entrypoint for state working memory audit."""
    target_state = locate_state_file(repo_root, state_path)

    print("====================================================================")
    print(" SDCS :: Working Memory Token Budget Linter (SPEC-001 v1.4.0 Pillar 4)")
    print(f" Target State: {target_state}")
    print(f" Token Budget: <= {max_tokens} tokens")
    print("====================================================================\n")

    if target_state is None:
        print(f"[ERROR] No state.md found in {repo_root} or .agent/")
        return 1

    passed, total_tokens, section_tokens, warnings = audit_state_tokens(
        target_state, max_tokens=max_tokens
    )

    print(f"Total Working Memory Tokens: {total_tokens} / {max_tokens}")
    print("Section Breakdown:")
    for header, count in section_tokens.items():
        if header == "__preamble__":
            print(f"  · [Preamble]                    {count:>4} tokens")
        else:
            print(f"  · ## {header:<26} {count:>4} tokens")
    print()

    for w in warnings:
        prefix = "❌ [BUDGET EXCEEDED]" if "budget exceeded" in w.lower() else "⚠️ [SCHEMA WARNING]"
        print(f"{prefix} {w}")

    if passed:
        print("\n✓ [STATUS: PASSED] state.md working memory is disciplined and within budget.")
        return 0
    else:
        print(
            "\n🛑 [STATUS: FAILED] Working memory bloat detected. Prune state.md before compacting."
        )
        return 1
