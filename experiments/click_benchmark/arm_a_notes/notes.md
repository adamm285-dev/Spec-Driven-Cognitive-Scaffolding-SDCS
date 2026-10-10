# Pallets/Click Developer Notes

This document contains general architecture notes, code conventions, module layout, and test instructions for working on `pallets/click`.

---

## 1. Core Architectural Invariants

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
- Help formatting must produce deterministic, readable output across all supported terminal dimensions.\n

---

## 2. Subsystem Layout & Module Mapping

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
  - `test_types/`: ParamType unit tests.\n

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
- Reopen Condition: Documented OS-level requirement where cleanup cannot be made deterministic.\n

---

## 5. Testing & Verification

## Test Execution Invariant
All test runs must set `pythonpath=src` (or environment variable `PYTHONPATH=src`) to ensure tests execute against the repository source rather than system-installed packages.

## Test Baseline
- Command: `pytest -o pythonpath=src -q`
- Expected: ~2,022 passed in ~3.8 seconds.
- Regression Gate: Zero regression tolerance on existing passing tests.\n
