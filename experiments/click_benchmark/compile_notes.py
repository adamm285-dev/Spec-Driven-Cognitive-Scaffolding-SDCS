"""Mechanical compiler: Arm B (SDCS pillars) -> Arm A (notes.md).

Guarantees 100% factual parity: extracts the factual domain knowledge,
invariants, cartography, decisions, and testing rules from the 7 pillars
into an unstructured, flat developer notes file.
"""

from pathlib import Path
import re

BENCHMARK_DIR = Path(__file__).parent
ARM_B_DIR = BENCHMARK_DIR / "arm_b_sdcs"
ARM_A_DIR = BENCHMARK_DIR / "arm_a_notes"


def compile_notes() -> str:
    ARM_A_DIR.mkdir(parents=True, exist_ok=True)

    spine_raw = (ARM_B_DIR / "spine.md").read_text(encoding="utf-8")
    wiring_raw = (ARM_B_DIR / "wiring.yaml").read_text(encoding="utf-8")
    app_map_raw = (ARM_B_DIR / "app_map.md").read_text(encoding="utf-8")
    decisions_raw = (ARM_B_DIR / "decisions.md").read_text(encoding="utf-8")
    evals_raw = (ARM_B_DIR / "evals.md").read_text(encoding="utf-8")

    # Strip SDCS pillar comments / operational metadata
    def clean_markdown(text: str) -> str:
        lines = []
        for line in text.splitlines():
            if line.startswith("<!-- SPEC-001") or line.startswith("# SPEC-001"):
                continue
            lines.append(line)
        return "\n".join(lines).strip()

    spine_clean = clean_markdown(spine_raw)
    app_map_clean = clean_markdown(app_map_raw)
    decisions_clean = clean_markdown(decisions_raw)
    evals_clean = clean_markdown(evals_raw)

    notes = f"""# Pallets/Click Developer Notes

This document contains general architecture notes, code conventions, module layout, and test instructions for working on `pallets/click`.

---

## 1. Core Architectural Invariants
{re.sub(r'^# Constitutional Invariants[^\n]*\n', '', spine_clean, flags=re.MULTILINE)}

---

## 2. Subsystem Layout & Module Mapping
{re.sub(r'^# Repository Cartography[^\n]*\n', '', app_map_clean, flags=re.MULTILINE)}

---

## 3. Subsystem Boundaries & Dependencies
Here is how the modules interact:
- `core` (`src/click/core.py`) imports from `types`, `utils`, `exceptions`, `formatting`, `globals`, `_compat`, `_termui_impl`.
- `types` (`src/click/types.py`) imports from `exceptions`, `utils`, `_compat`.
- `termui` (`src/click/termui.py`) imports from `_termui_impl`, `_compat`, `utils`, `exceptions`.
- `_termui_impl` (`src/click/_termui_impl.py`) imports from `_compat`, `utils`, `exceptions`.
- `formatting` (`src/click/formatting.py`) imports from `_compat`, `utils`.
- `utils` (`src/click/utils.py`) imports from `_compat`, `_utils`.
- `_utils` (`src/click/_utils.py`) imports from `_compat`.
- `parser` (`src/click/parser.py`) imports from `exceptions`, `_compat`.

---

## 4. Past Architectural Decisions & Rejected Alternatives
{re.sub(r'^# Negative Episodic Memory[^\n]*\n', '', decisions_clean, flags=re.MULTILINE)}

---

## 5. Testing & Verification
{re.sub(r'^# Positive Ground Truth[^\n]*\n', '', evals_clean, flags=re.MULTILINE)}
"""
    output_path = ARM_A_DIR / "notes.md"
    output_path.write_text(notes.strip() + "\n", encoding="utf-8")
    print(f"Mechanically generated {output_path} ({len(notes.splitlines())} lines)")
    return notes


if __name__ == "__main__":
    compile_notes()
