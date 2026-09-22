"""
sdcs.hydrate - Deterministic Context Compiler (SPEC-001 v1.5.0)

Compiles and streams a pre-budgeted, single-pass markdown payload directly to stdout,
reducing Turn 1 boot hydration from 5-7 individual tool calls down to 1 atomic command.
"""

import sys
from pathlib import Path

from sdcs.map import locate_map_file, slice_cartography
from sdcs.verifier.state import count_tokens, locate_state_file


def locate_pillar_file(repo_root: Path, filename: str) -> Path | None:
    """Locates a pillar file in repo root or .agent/."""
    candidates = [
        repo_root / filename,
        repo_root / ".agent" / filename,
        repo_root / filename.upper(),
        repo_root / ".agent" / filename.upper(),
    ]
    for c in candidates:
        if c.is_file():
            return c
    return None


def extract_active_milestone(roadmap_content: str, subsystem: str | None = None) -> str:
    """
    Extracts the active/unverified milestone from roadmap.md.
    If none is unverified, returns the first milestone.
    """
    lines = roadmap_content.splitlines()
    milestones: list[list[str]] = []
    current_ms: list[str] = []

    for line in lines:
        if line.startswith("## Milestone"):
            if current_ms:
                milestones.append(current_ms)
            current_ms = [line]
        elif current_ms:
            current_ms.append(line)

    if current_ms:
        milestones.append(current_ms)

    if not milestones:
        return roadmap_content.strip()

    # Look for a milestone with pending/unverified status or matching subsystem
    for ms in milestones:
        text = "\n".join(ms)
        if subsystem and subsystem.lower() in text.lower():
            return text.strip()
        if "VERIFIED" not in text.upper() or "PENDING" in text.upper():
            return text.strip()

    # Default to the first milestone if all are verified
    return "\n".join(milestones[0]).strip()


def extract_active_rejections(
    decisions_content: str, max_entries: int = 10, subsystem: str | None = None
) -> str:
    """
    Extracts up to max_entries active REJ- records from decisions.md,
    optionally prioritizing those referencing a subsystem.
    """
    lines = decisions_content.splitlines()
    entries: list[list[str]] = []
    current_entry: list[str] = []

    for line in lines:
        if line.startswith(("## REJ-", "## ADR-")):
            if current_entry:
                entries.append(current_entry)
            current_entry = [line]
        elif current_entry:
            current_entry.append(line)

    if current_entry:
        entries.append(current_entry)

    if not entries:
        return decisions_content.strip()

    if subsystem:
        filtered = [e for e in entries if subsystem.lower() in "\n".join(e).lower()]
        if filtered:
            entries = filtered

    selected = entries[-max_entries:]  # Latest active
    output = []
    for e in selected:
        output.append("\n".join(e).strip())
    return "\n\n".join(output)


def compile_hydration_payload(
    repo_root: Path,
    profile: str = "standard",
    subsystem: str | None = None,
) -> tuple[str, int]:
    """
    Compiles a structured, single-pass markdown payload based on the requested scale profile.
    Returns: (compiled_markdown, estimated_tokens)
    """
    profile = profile.lower().strip()
    sections: list[str] = []

    spine_file = locate_pillar_file(repo_root, "spine.md")
    state_file = locate_state_file(repo_root)
    roadmap_file = locate_pillar_file(repo_root, "roadmap.md")
    map_file = locate_map_file(repo_root)
    decisions_file = locate_pillar_file(repo_root, "decisions.md")
    evals_file = locate_pillar_file(repo_root, "evals.md")
    wiring_file = locate_pillar_file(repo_root, "wiring.yaml")

    header_banner = f"""<!-- ===================================================================== -->
<!-- SDCS DETERMINISTIC CONTEXT COMPILER (SPEC-001 v1.5.0)                  -->
<!-- Scale Profile: {profile.upper():<10} | Subsystem Focus: {subsystem or 'ALL'!s:<20} -->
<!-- Single-pass Turn 1 boot hydration payload. Do not re-request pillars. -->
<!-- ===================================================================== -->
"""
    sections.append(header_banner)

    if profile == "lite":
        # Profile Lite: spine.md + state.md (~400 tokens)
        if spine_file and spine_file.is_file():
            sections.append(
                f"# [PILLAR 1: THE LAW] Constitutional Invariants\n\n{spine_file.read_text(encoding='utf-8', errors='ignore').strip()}"
            )
        if state_file and state_file.is_file():
            sections.append(
                f"# [PILLAR 4: THE BLACKBOARD] Working Memory\n\n{state_file.read_text(encoding='utf-8', errors='ignore').strip()}"
            )

    elif profile == "standard":
        # Profile Standard: spine + roadmap (active) + cartography (sliced) + decisions (rejections) + state (~1,500 tokens)
        if spine_file and spine_file.is_file():
            sections.append(
                f"# [PILLAR 1: THE LAW] Constitutional Invariants\n\n{spine_file.read_text(encoding='utf-8', errors='ignore').strip()}"
            )

        if roadmap_file and roadmap_file.is_file():
            active_ms = extract_active_milestone(
                roadmap_file.read_text(encoding="utf-8", errors="ignore"), subsystem
            )
            sections.append(
                f"# [PILLAR 3: THE NORTH STAR] Active Macro Acceptance Contract\n\n{active_ms}"
            )

        if map_file and map_file.is_file():
            if subsystem:
                cartography = slice_cartography(repo_root, subsystem, map_file)
            else:
                cartography = map_file.read_text(encoding="utf-8", errors="ignore").strip()
            sections.append(f"# [PILLAR 5: THE COMPASS] Repository Cartography\n\n{cartography}")

        if decisions_file and decisions_file.is_file():
            rejections = extract_active_rejections(
                decisions_file.read_text(encoding="utf-8", errors="ignore"),
                max_entries=8,
                subsystem=subsystem,
            )
            sections.append(f"# [PILLAR 6: THE GRAVEYARD] Active Rejections\n\n{rejections}")

        if state_file and state_file.is_file():
            sections.append(
                f"# [PILLAR 4: THE BLACKBOARD] Working Memory\n\n{state_file.read_text(encoding='utf-8', errors='ignore').strip()}"
            )

    else:
        # Profile Full: All 7 Pillars in strict boot sequence (~2,500-3,500 tokens)
        if spine_file and spine_file.is_file():
            sections.append(
                f"# [PILLAR 1: THE LAW] Constitutional Invariants\n\n{spine_file.read_text(encoding='utf-8', errors='ignore').strip()}"
            )
        if roadmap_file and roadmap_file.is_file():
            sections.append(
                f"# [PILLAR 3: THE NORTH STAR] Macro Acceptance Contract\n\n{roadmap_file.read_text(encoding='utf-8', errors='ignore').strip()}"
            )
        if map_file and map_file.is_file():
            cartography = (
                slice_cartography(repo_root, subsystem, map_file)
                if subsystem
                else map_file.read_text(encoding="utf-8", errors="ignore").strip()
            )
            sections.append(f"# [PILLAR 5: THE COMPASS] Repository Cartography\n\n{cartography}")
        if decisions_file and decisions_file.is_file():
            sections.append(
                f"# [PILLAR 6: THE GRAVEYARD] Negative Episodic Memory\n\n{decisions_file.read_text(encoding='utf-8', errors='ignore').strip()}"
            )
        if evals_file and evals_file.is_file():
            sections.append(
                f"# [PILLAR 7: GROUND TRUTH] Positive Episodic Memory\n\n{evals_file.read_text(encoding='utf-8', errors='ignore').strip()}"
            )
        if state_file and state_file.is_file():
            sections.append(
                f"# [PILLAR 4: THE BLACKBOARD] Working Memory\n\n{state_file.read_text(encoding='utf-8', errors='ignore').strip()}"
            )
        if wiring_file and wiring_file.is_file():
            sections.append(
                f"# [PILLAR 2: THE MESH] Declarative Topology\n\n```yaml\n{wiring_file.read_text(encoding='utf-8', errors='ignore').strip()}\n```"
            )

    # Central Cognitive Warehouse Integration (SPEC-001 v1.6.0)
    # Appends Tier-1 index table if warehouse subscriptions are active and cached records exist
    if profile in ("standard", "full"):
        from sdcs.warehouse import (
            compile_tier1_index,
            filter_records,
            load_cached_records,
            locate_warehouse_cache,
            locate_warehouse_config,
        )

        wh_cfg = locate_warehouse_config(repo_root)
        if wh_cfg:
            wh_cache = locate_warehouse_cache(repo_root, wh_cfg)
            cached = load_cached_records(wh_cache)
            if cached:
                subs = wh_cfg.get("subscriptions", {})
                p_ctx = {}
                if subsystem:
                    p_ctx["domain"] = subsystem
                matched = filter_records(cached, subscriptions=subs, project_context=p_ctx)
                if matched:
                    tier1_table, _ = compile_tier1_index(matched, max_tokens=250)
                    if tier1_table:
                        sections.append(
                            f"# [CENTRAL WAREHOUSE: FLEET FEDERATION] Subscribed Vendor Traps (Tier-1 Index)\n\n{tier1_table}"
                        )

    full_payload = "\n\n---\n\n".join(sections)
    total_tokens = count_tokens(full_payload)
    return full_payload, total_tokens


def run_hydrate_command(
    repo_root: Path,
    profile: str = "standard",
    subsystem: str | None = None,
) -> int:
    """CLI execution entrypoint for sdcs hydrate."""
    payload, total_tokens = compile_hydration_payload(
        repo_root=repo_root,
        profile=profile,
        subsystem=subsystem,
    )

    # Stream to stdout
    print(payload)

    # Telemetry report to stderr
    sys.stderr.write(
        f"\n[SDCS::HYDRATE] Compiled single-pass context: ~{total_tokens} tokens "
        f"(Profile: {profile}, Subsystem: {subsystem or 'ALL'}).\n"
    )
    return 0
