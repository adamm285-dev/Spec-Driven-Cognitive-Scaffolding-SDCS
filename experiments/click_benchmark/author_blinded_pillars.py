"""Authors the 7 blinded SDCS pillars for pallets/click.

Invariant: Blinded authoring. Describes Click's architecture, boundaries,
and invariants as of pre-August 2026 with ZERO knowledge of the 5 bug tasks.
"""

from pathlib import Path

DEST_DIR = Path(__file__).parent / "arm_b_sdcs"

SPINE_CONTENT = """# Constitutional Invariants (The Spine)
<!-- SPEC-001 Pillar 1 | Mutability: IMMUTABLE -->

This document declares the non-negotiable architectural axioms governing `pallets/click`.

## Axiom 1: Zero External Dependencies
`click` is a foundational CLI framework. It must never depend on non-standard-library packages at runtime. All terminal formatting, option parsing, and ANSI manipulations are implemented internally.

## Axiom 2: Strict Context Lifecycle & Resource Cleanup
- A command invocation executes within a hierarchical `Context` tree.
- Context resources registered via `call_on_close` and `with_resource` must always be closed/cleaned up deterministically on exit or abort.
- Standalone mode handles exceptions and converts them into user-facing output with deterministic exit codes; non-standalone mode allows exceptions to propagate to callers.

## Axiom 3: Cross-Platform File & Terminal Safety
- Windows console and POSIX terminal abstractions in `click._termui_impl` must isolate OS differences.
- Any temporary file opened for paging or editor operations must ensure handles are properly closed before filesystem mutations or unlinking, avoiding platform-specific handle locks.
- Stream operations must handle binary and text encodings gracefully without unintended byte-string type collisions.

## Axiom 4: Singleton Immutability & Identity
- Internal sentinel representations used to indicate unset arguments, missing options, or default overrides must preserve identity under standard copy, deepcopy, and serialization operations.

## Axiom 5: Public API Stability
- Public classes (`Command`, `Group`, `Context`, `Parameter`, `Option`, `Argument`, `ParamType`) must preserve signature backwards compatibility.
- Help formatting must produce deterministic, readable output across all supported terminal dimensions.
"""

WIRING_CONTENT = """# Declarative Topology & Subsystem Mesh (The Wiring)
# SPEC-001 Pillar 2 | Mutability: READ-ONLY

version: "8.5.0"

subsystems:
  core:
    path: "src/click/core.py"
    description: "Core CLI command execution engine, Context tree, and parameter binding."
    allowed_imports:
      - "click.types"
      - "click.utils"
      - "click.exceptions"
      - "click.formatting"
      - "click.globals"
      - "click._compat"
      - "click._termui_impl"

  types:
    path: "src/click/types.py"
    description: "Parameter types, type conversion, and input validation hierarchy."
    allowed_imports:
      - "click.exceptions"
      - "click.utils"
      - "click._compat"

  termui:
    path: "src/click/termui.py"
    description: "High-level terminal UI convenience utilities: echo, prompt, confirm, progressbar."
    allowed_imports:
      - "click._termui_impl"
      - "click._compat"
      - "click.utils"
      - "click.exceptions"

  _termui_impl:
    path: "src/click/_termui_impl.py"
    description: "Low-level cross-platform terminal implementation, pager, and progress rendering."
    allowed_imports:
      - "click._compat"
      - "click.utils"
      - "click.exceptions"

  formatting:
    path: "src/click/formatting.py"
    description: "Help table generation and text wrapping."
    allowed_imports:
      - "click._compat"
      - "click.utils"

  utils:
    path: "src/click/utils.py"
    description: "General text utilities, short help formatting, and file opening helpers."
    allowed_imports:
      - "click._compat"
      - "click._utils"

  _utils:
    path: "src/click/_utils.py"
    description: "Internal singletons and sentinel helpers."
    allowed_imports:
      - "click._compat"

  parser:
    path: "src/click/parser.py"
    description: "Command line argument and option parser."
    allowed_imports:
      - "click.exceptions"
      - "click._compat"

sandbox:
  protected_paths:
    - "docs/**"
    - "CHANGES.md"
  allowed_commands:
    - "pytest"
    - "git"
    - "python"
"""

ROADMAP_CONTENT = """# Teleological Roadmap (The North Star)
<!-- SPEC-001 Pillar 3 | Mutability: PROGRESSIVE APPEND-ONLY -->

## Milestone: Click Maintenance & Stability (v8.5.x)
- Intent: Maintain zero regressions across all 2,000+ unit tests across POSIX and Windows.
- Acceptance Contract:
  - [MEASURED]: 2,022 passed, 101 skipped, 1 xfailed in pytest suite.
  - [INTENT]: Bug fixes must strictly increase or maintain test coverage without introducing regressions.
  - [INTENT]: Cross-platform file, signal, and terminal interactions must remain completely clean.
"""

STATE_CONTENT = """# Dynamic Working Memory (The Blackboard)
<!-- SPEC-001 Pillar 4 | Mutability: HIGH VOLATILITY | Budget: <= 350 Tokens -->

## Current Objective
- Initialize task context; execute reproduction test to isolate the failure.

## Status & Gate Verification
- Codebase: pallets/click baseline loaded.
- Tests: pytest execution verified with pythonpath=src.

## Immediate Next Action (Post-Compact)
- Run targeted reproduction test; analyze source module under test; apply minimal fix; re-verify.
"""

APP_MAP_CONTENT = """# Repository Cartography (The App Map)
<!-- SPEC-001 Pillar 5 | Mutability: DETERMINISTIC SYNC -->

## 1. Top-Level Layout
- `src/click/`: Primary package source.
  - `core.py`: CLI execution engine, `BaseCommand`, `Command`, `Group`, `Context`, `Parameter`, `Option`, `Argument`.
  - `types.py`: `ParamType`, `StringParamType`, `IntParamType`, `FloatParamType`, `BoolParamType`, `Choice`, `Path`, `File`, `DateTime`.
  - `termui.py`: User-facing terminal routines: `echo()`, `prompt()`, `confirm()`, `progressbar()`, `edit()`, `launch()`, `clear()`.
  - `_termui_impl.py`: Driver classes for `ProgressBar`, pager implementations (`_tempfilepager`, `_nullpager`), and editor spawning.
  - `utils.py`: Text formatting helpers: `make_default_short_help()`, `echo()`, `format_filename()`, `open_file()`, `LazyFile`.
  - `_utils.py`: Internal singletons: `Sentinel`, `UNSET`, `FLAG_NEEDS_VALUE`.
  - `formatting.py`: `HelpFormatter`, `wrap_text()`, and section formatting.
  - `parser.py`: Low-level CLI parsing split into options and arguments.
  - `exceptions.py`: `ClickException`, `UsageError`, `BadParameter`, `Abort`, `Exit`.
  - `testing.py`: `CliRunner` test utility.
- `tests/`: Extensive test suite.
  - `test_termui.py`: Terminal UI, progress bar, and pager tests.
  - `test_basic.py`: Basic command parsing and context execution.
  - `test_utils/`: Targeted test modules for internal and public utility functions.
  - `test_types/`: ParamType unit tests.
"""

DECISIONS_CONTENT = """# Negative Episodic Memory (The Graveyard)
<!-- SPEC-001 Pillar 6 | Mutability: APPEND-ONLY -->

## REJ-001: External Runtime Dependencies (e.g. Colorama)
- Proposal: Rely on external packaging for Windows ANSI colors.
- Rejection: Click 8.2 dropped Colorama; modern Windows 10+ supports native ANSI virtual terminal processing. Click maintains zero non-stdlib dependencies.
- Reopen Condition: Never. Zero runtime dependencies is a constitutional invariant.

## REJ-002: Eager Import of Heavy Modules
- Proposal: Import `shutil`, `tempfile`, `subprocess`, and formatting engines eagerly at module top-level in `utils.py` and `_termui_impl.py`.
- Rejection: Increases CLI startup latency. Infrequently used subroutines (like editor launches or specific formatting algorithms) must import heavy modules lazily.
- Reopen Condition: Benchmark proving zero impact on microsecond startup time.

## REJ-003: Swallowing Cleanup Exceptions During Paging/Subprocesses
- Proposal: Use broad `except Exception: pass` around cleanup code in context managers.
- Rejection: Masks critical resource leaks and makes debugging platform file-locking errors impossible. Cleanup must explicitly manage resource state (e.g. closing handles before unlink).
- Reopen Condition: Documented OS-level requirement where cleanup cannot be made deterministic.
"""

EVALS_CONTENT = """# Positive Ground Truth (The Evals)
<!-- SPEC-001 Pillar 7 | Mutability: READ-ONLY -->

## Test Execution Invariant
All test runs must set `pythonpath=src` (or environment variable `PYTHONPATH=src`) to ensure tests execute against the repository source rather than system-installed packages.

## Test Baseline
- Command: `pytest -o pythonpath=src -q`
- Expected: ~2,022 passed in ~3.8 seconds.
- Regression Gate: Zero regression tolerance on existing passing tests.
"""

AGENTS_CONTENT = """# Agent Instructions (Click Maintenance)
<!-- SDCS Operational Protocol -->

## Turn 1 Boot Hydration Order
1. `spine.md` -> Constitutional invariants (zero external deps, resource lifecycle).
2. `roadmap.md` -> Teleological target [INTENT] vs [MEASURED].
3. `app_map.md` -> Cartography of modules and test directories.
4. `decisions.md` -> Negative episodic memory / rejected patterns.
5. `evals.md` -> Test execution baseline (`pytest -o pythonpath=src`).
6. `state.md` -> Active working blackboard (<= 350 tokens).
7. `wiring.yaml` -> Subsystem import boundaries.

## 4-Phase Autonomous Execution Cycle
1. **Orientation:** Hydrate constraints; locate target module in `app_map.md`.
2. **Planning:** Formulate minimal, atomic fix preserving subsystem boundaries.
3. **Execution:** Apply code mutation; run targeted reproduction test.
4. **Close-Out:** Run full test suite (`pytest -o pythonpath=src`) to verify zero regressions; prune `state.md`.
"""


def main():
    DEST_DIR.mkdir(parents=True, exist_ok=True)
    files = {
        "spine.md": SPINE_CONTENT,
        "wiring.yaml": WIRING_CONTENT,
        "roadmap.md": ROADMAP_CONTENT,
        "state.md": STATE_CONTENT,
        "app_map.md": APP_MAP_CONTENT,
        "decisions.md": DECISIONS_CONTENT,
        "evals.md": EVALS_CONTENT,
        "AGENTS.md": AGENTS_CONTENT,
    }
    for filename, content in files.items():
        filepath = DEST_DIR / filename
        filepath.write_text(content.strip() + "\\n", encoding="utf-8")
        print(f"Wrote {filepath.name} ({len(content.splitlines())} lines)")


if __name__ == "__main__":
    main()
