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
        repo_root / "docs" / "state.md",
        repo_root / "docs" / "map" / "state.md",
        repo_root / "STATE.md",
        repo_root / ".agent" / "STATE.md",
        repo_root / "docs" / "STATE.md",
        repo_root / "docs" / "map" / "STATE.md",
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


def get_tokenizer_info() -> str:
    """Returns the name and encoding of the active tokenizer implementation."""
    try:
        import tiktoken

        tiktoken.get_encoding("cl100k_base")
        return "tiktoken (`cl100k_base`)"
    except (ImportError, AttributeError, ValueError):
        return "character heuristic (`max(words, ceil(chars/4))`)"


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


def compute_elastic_state_budget(
    content: str,
    repo_root: Path | None = None,
    base_budget: int = 350,
    max_ceiling: int = 1200,
) -> tuple[int, int, int, list[str]]:
    """
    Computes a dynamic, scope-elastic working memory token budget for `state.md`:
      - Starts at `base_budget` (default 350 tokens) for standard 1-package tasks (`<= 4` active bullets).
      - Automatically expands by +28 tokens for each active requirement bullet beyond 4,
        and +25 tokens per detected package beyond 1 in multi-package monorepos (capped at `max_ceiling`).
      - Enforces the core `state.md` discipline via per-bullet density auditing (`<= 55` tokens per bullet)
        and completed-item (`- [x]`) compaction advisories.
    Returns `(effective_budget, active_bullet_count, completed_bullet_count, density_advisories)`.
    """
    active_bullets = 0
    completed_bullets = 0
    density_advisories: list[str] = []

    for raw_line in content.splitlines():
        s = raw_line.strip()
        if not (s.startswith("- ") or s.startswith("* ")):
            continue
        b_tokens = count_tokens(s)
        if re.match(r"^[-*]\s*\[[xX]\]", s) or "[DONE]" in s or "[COMPLETED]" in s:
            completed_bullets += 1
        else:
            active_bullets += 1
            if b_tokens > 55:
                preview = s[:60] + ("..." if len(s) > 60 else "")
                density_advisories.append(
                    f"Verbose bullet ({b_tokens}t > 55t density target): '{preview}'"
                )

    if completed_bullets > 5:
        density_advisories.append(
            f"{completed_bullets} completed (`- [x]`) bullets present; consider collapsing finished items into a 1-line summary."
        )

    pkg_count = 1
    if repo_root and repo_root.is_dir():
        try:
            pkg_dirs = [
                d
                for d in repo_root.iterdir()
                if d.is_dir()
                and not d.name.startswith(".")
                and d.name not in ("tests", "docs", "scripts", "build", "dist", "__pycache__")
                and (d / "__init__.py").is_file()
            ]
            pkg_count = max(1, len(pkg_dirs))
        except OSError:
            pkg_count = 1

    extra_bullet_allowance = max(0, active_bullets - 4) * 28
    extra_pkg_allowance = max(0, pkg_count - 1) * 25
    elastic_budget = min(
        max_ceiling,
        base_budget + extra_bullet_allowance + extra_pkg_allowance,
    )
    return elastic_budget, active_bullets, completed_bullets, density_advisories


def audit_state_tokens(
    state_file: Path,
    max_tokens: int = 350,
    elastic: bool = True,
) -> tuple[bool, int, dict[str, int], list[str]]:
    """
    Audits state.md against the specified (or scope-elastic) token budget and verifies canonical schema.
    Returns: (passed, total_tokens, section_tokens, warnings)
    """
    if not state_file.is_file():
        return False, 0, {}, [f"State file not found: {state_file}"]

    content = state_file.read_text(encoding="utf-8", errors="ignore")
    total_tokens = count_tokens(content)

    effective_max = max_tokens
    density_notes: list[str] = []
    if elastic:
        elastic_max, _act, _comp, density_notes = compute_elastic_state_budget(
            content, repo_root=state_file.parent, base_budget=max_tokens
        )
        effective_max = max(max_tokens, elastic_max)

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

    for note in density_notes:
        warnings.append(f"[DENSITY ADVISORY] {note}")

    passed = total_tokens <= effective_max
    if not passed:
        warnings.append(
            f"Token budget exceeded: {total_tokens} tokens > {effective_max} token threshold (base={max_tokens})."
        )

    return passed, total_tokens, section_tokens, warnings


def run_state_audit(
    repo_root: Path,
    state_path: str | Path | None = None,
    max_tokens: int = 350,
    elastic: bool = True,
) -> int:
    """CLI execution entrypoint for state working memory audit."""
    target_state = locate_state_file(repo_root, state_path)

    effective_budget = max_tokens
    active_b = 0
    done_b = 0
    if target_state and target_state.is_file() and elastic:
        raw_txt = target_state.read_text(encoding="utf-8", errors="ignore")
        elastic_b, active_b, done_b, _ = compute_elastic_state_budget(
            raw_txt, repo_root=repo_root, base_budget=max_tokens
        )
        effective_budget = max(max_tokens, elastic_b)

    print("====================================================================")
    print(" SDCS :: Working Memory Token Budget Linter (SPEC-001 v1.4.0 Pillar 4)")
    print(f" Target State: {target_state}")
    if effective_budget > max_tokens:
        print(
            f" Token Budget: <= {effective_budget} tokens (Elastic Scale from {max_tokens}t base; {active_b} active bullets, {done_b} done)"
        )
    else:
        print(f" Token Budget: <= {effective_budget} tokens")
    print(f" Tokenizer:    {get_tokenizer_info()}")
    print("====================================================================\n")

    if target_state is None:
        print(f"[ERROR] No state.md found in {repo_root} or .agent/")
        return 1

    passed, total_tokens, section_tokens, warnings = audit_state_tokens(
        target_state, max_tokens=max_tokens, elastic=elastic
    )

    print(
        f"Total Working Memory Tokens: {total_tokens} / {effective_budget} ({get_tokenizer_info()})"
    )
    print("Section Breakdown:")
    for header, count in section_tokens.items():
        if header == "__preamble__":
            print(f"  · [Preamble]                    {count:>4} tokens")
        else:
            print(f"  · ## {header:<26} {count:>4} tokens")
    print()

    for w in warnings:
        if "budget exceeded" in w.lower():
            prefix = "❌ [BUDGET EXCEEDED]"
        elif "density advisory" in w.lower():
            prefix = "💡 [DENSITY ADVISORY]"
            w = w.replace("[DENSITY ADVISORY] ", "")
        else:
            prefix = "⚠️ [SCHEMA WARNING]"
        print(f"{prefix} {w}")

    if passed:
        print("\n✓ [STATUS: PASSED] state.md working memory is disciplined and within budget.")
        return 0
    else:
        print(
            "\n🛑 [STATUS: FAILED] Working memory bloat detected. Prune state.md before compacting."
        )
        return 1


def locate_subagent_state_file(repo_root: Path, worker_id: str) -> Path:
    """Returns the expected path for a subagent blackboard."""
    agent_dir = repo_root / ".agent"
    if agent_dir.is_dir():
        return agent_dir / f"state.{worker_id}.md"
    return repo_root / f"state.{worker_id}.md"


def fork_subagent_state(
    repo_root: Path,
    worker_id: str,
    subtask_objective: str | None = None,
    state_path: str | Path | None = None,
) -> Path:
    """
    Forks a lightweight scoped working memory blackboard for a parallel worker/subagent.
    Inherits context from root state.md and creates state.<worker_id>.md.
    """
    locate_state_file(repo_root, state_path)
    subagent_file = locate_subagent_state_file(repo_root, worker_id)

    objective = subtask_objective or f"Autonomous execution slice assigned to worker [{worker_id}]"

    content = f"""# Dynamic Working Memory: Subagent [{worker_id}]
<!-- Ephemeral Subagent Blackboard | Conforming to SPEC-001 v1.5.0 Pillar 4 -->
<!-- Forked from root state.md. Rollup via 'sdcs state rollup {worker_id}' -->

## Current Objective
- {objective}

## Status & Gate Verification
- [PENDING] Worker [{worker_id}] initialized. Awaiting execution.

## Immediate Blockers
- None.

## Immediate Next Action (Post-Compact)
- Execute assigned objective and update status before rollup.
"""
    subagent_file.write_text(content.strip() + "\n", encoding="utf-8")
    return subagent_file


def rollup_subagent_state(
    repo_root: Path,
    worker_id: str,
    state_path: str | Path | None = None,
    delete_after_rollup: bool = True,
) -> tuple[bool, str]:
    """
    Rolls up a subagent blackboard (state.<worker_id>.md) into the primary state.md.
    Synthesizes the worker's status and blockers into root state.md, audits token budget,
    and removes the ephemeral slice.
    """
    subagent_file = locate_subagent_state_file(repo_root, worker_id)
    if not subagent_file.is_file():
        alt_path = repo_root / f"state.{worker_id}.md"
        if alt_path.is_file():
            subagent_file = alt_path
        else:
            return False, f"Subagent blackboard not found: {subagent_file}"

    root_state = locate_state_file(repo_root, state_path)
    if not root_state or not root_state.is_file():
        return False, f"Root state.md not found in {repo_root}"

    worker_content = subagent_file.read_text(encoding="utf-8")
    worker_sections = parse_state_sections(worker_content)

    worker_status = worker_sections.get("Status & Gate Verification", "").strip()
    if not worker_status:
        worker_status = worker_sections.get("Status", "Execution completed.")

    worker_blockers = worker_sections.get("Immediate Blockers", "None.").strip()

    root_content = root_state.read_text(encoding="utf-8")
    root_sections = parse_state_sections(root_content)

    status_summary = worker_status.replace("\n", " ")
    if len(status_summary) > 120:
        status_summary = status_summary[:117] + "..."

    curr_status = root_sections.get("Status & Gate Verification", "").strip()
    new_status_line = f"- Subagent [{worker_id}]: {status_summary}"
    if curr_status:
        updated_status = f"{curr_status}\n{new_status_line}"
    else:
        updated_status = new_status_line
    root_sections["Status & Gate Verification"] = updated_status

    if worker_blockers and worker_blockers.lower() not in ("none", "none."):
        curr_blockers = root_sections.get("Immediate Blockers", "").strip()
        blocker_line = f"- Subagent [{worker_id}] Blocker: {worker_blockers}"
        if curr_blockers and curr_blockers.lower() not in ("none", "none."):
            root_sections["Immediate Blockers"] = f"{curr_blockers}\n{blocker_line}"
        else:
            root_sections["Immediate Blockers"] = blocker_line

    output_lines = [
        "# Dynamic Working Memory (The Blackboard)",
        "<!-- SPEC-001 Pillar 4 | Mutability: HIGH VOLATILITY | Budget: ~300 Tokens -->\n",
    ]
    for h, sec_text in root_sections.items():
        if h == "__preamble__":
            continue
        output_lines.append(f"## {h}")
        output_lines.append(sec_text)
        output_lines.append("")

    root_state.write_text("\n".join(output_lines).strip() + "\n", encoding="utf-8")

    if delete_after_rollup:
        try:
            subagent_file.unlink()
        except OSError:
            pass

    passed, tokens, _, _warnings = audit_state_tokens(root_state, max_tokens=350)
    msg = f"Rollup completed for worker [{worker_id}]. Root state.md: {tokens} tokens."
    if not passed:
        msg += " ⚠️ WARNING: Root state exceeds 350 tokens. Pruning recommended."
    return True, msg
