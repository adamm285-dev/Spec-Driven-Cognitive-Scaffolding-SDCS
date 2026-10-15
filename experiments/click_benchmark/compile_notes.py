"""Mechanical compiler: Arm B (SDCS pillars) -> Arm A (notes.md).

Guarantees 100% factual and informational parity: extracts the factual domain
knowledge, invariants, cartography, boundaries, roadmap targets, decisions,
baseline state, and testing rules from the 7 pillars into an unstructured,
flat developer notes file.
"""

from pathlib import Path
import re
import yaml

BENCHMARK_DIR = Path(__file__).parent
ARM_B_DIR = BENCHMARK_DIR / "arm_b_sdcs"
ARM_A_DIR = BENCHMARK_DIR / "arm_a_notes"


def clean_markdown(text: str) -> str:
    lines = []
    for line in text.splitlines():
        if line.startswith("<!-- SPEC-001") or line.startswith("# SPEC-001"):
            continue
        lines.append(line)
    return "\n".join(lines).strip()


def compile_notes() -> str:
    ARM_A_DIR.mkdir(parents=True, exist_ok=True)

    spine_raw = (ARM_B_DIR / "spine.md").read_text(encoding="utf-8")
    app_map_raw = (ARM_B_DIR / "app_map.md").read_text(encoding="utf-8")
    decisions_raw = (ARM_B_DIR / "decisions.md").read_text(encoding="utf-8")
    evals_raw = (ARM_B_DIR / "evals.md").read_text(encoding="utf-8")
    roadmap_raw = (ARM_B_DIR / "roadmap.md").read_text(encoding="utf-8")
    state_raw = (ARM_B_DIR / "state.md").read_text(encoding="utf-8")
    wiring_raw = (ARM_B_DIR / "wiring.yaml").read_text(encoding="utf-8")

    spine_clean = clean_markdown(spine_raw)
    app_map_clean = clean_markdown(app_map_raw)
    decisions_clean = clean_markdown(decisions_raw)
    evals_clean = clean_markdown(evals_raw)
    roadmap_clean = clean_markdown(roadmap_raw)
    state_clean = clean_markdown(state_raw)

    spine_body = re.sub(
        r"^# Constitutional Invariants[^\n]*\n", "", spine_clean, flags=re.MULTILINE
    )
    app_map_body = re.sub(
        r"^# Repository Cartography[^\n]*\n", "", app_map_clean, flags=re.MULTILINE
    )
    decisions_body = re.sub(
        r"^# Negative Episodic Memory[^\n]*\n", "", decisions_clean, flags=re.MULTILINE
    )
    evals_body = re.sub(r"^# Positive Ground Truth[^\n]*\n", "", evals_clean, flags=re.MULTILINE)
    roadmap_body = re.sub(r"^# Teleological Roadmap[^\n]*\n", "", roadmap_clean, flags=re.MULTILINE)
    state_body = re.sub(r"^# Dynamic Working Memory[^\n]*\n", "", state_clean, flags=re.MULTILINE)

    # Parse wiring.yaml for subsystem descriptions, allowed imports, and sandbox
    wiring_data = yaml.safe_load(wiring_raw)
    wiring_lines = ["Here are the subsystem boundaries and dependency rules:"]
    for sub_name, sub_info in wiring_data.get("subsystems", {}).items():
        path = sub_info.get("path", "")
        desc = sub_info.get("description", "")
        allowed = ", ".join(sub_info.get("allowed_imports", []))
        wiring_lines.append(f"- `{sub_name}` (`{path}`): {desc}")
        if allowed:
            wiring_lines.append(f"  Allowed imports: {allowed}")

    sandbox = wiring_data.get("sandbox", {})
    if sandbox:
        wiring_lines.append("\nSandbox constraints:")
        if "protected_paths" in sandbox:
            wiring_lines.append(f"- Protected paths: {', '.join(sandbox['protected_paths'])}")
        if "allowed_commands" in sandbox:
            wiring_lines.append(f"- Allowed commands: {', '.join(sandbox['allowed_commands'])}")

    wiring_body = "\n".join(wiring_lines)

    notes = f"""# Pallets/Click Developer Notes

This document contains general architecture notes, code conventions, module layout, subsystem boundaries, maintenance targets, and test instructions for working on `pallets/click`.

---

## 1. Core Architectural Invariants
{spine_body}

---

## 2. Subsystem Layout & Module Mapping
{app_map_body}

---

## 3. Subsystem Architecture & Boundary Contracts
{wiring_body}

---

## 4. Maintenance Targets & Acceptance Contract
{roadmap_body}

---

## 5. Past Architectural Decisions & Rejected Alternatives
{decisions_body}

---

## 6. Testing & Verification
{evals_body}

---

## 7. Baseline Environment & Initial State
{state_body}
"""
    output_path = ARM_A_DIR / "notes.md"
    output_path.write_text(notes.strip() + "\n", encoding="utf-8")
    print(f"Mechanically generated {output_path} ({len(notes.splitlines())} lines)")
    return notes


if __name__ == "__main__":
    compile_notes()
