# Pallets/Click Developer Notes

This document contains general architecture notes, code conventions, module layout, subsystem boundaries, maintenance targets, and test instructions for working on `pallets/click`.

---

## 1. Core Architectural Invariants

This document declares the non-negotiable architectural axioms governing `pallets/click`.

## Axiom 1: Zero External Dependencies
`click` is a foundational CLI framework. It must never depend on non-standard-library packages at runtime. All terminal formatting, option parsing, and ANSI manipulations are implemented internally.

## Axiom 2: Strict Context Lifecycle & Resource Cleanup
- A command invocation executes within a hierarchical `Context` tree.
- Context resources registered via `call_on_close` and `with_resource` must always be closed/cleaned up deterministically on exit or abort.
- Standalone mode handles exceptions and converts them into user-facing output with deterministic exit codes; non-standalone mode allows exceptions to propagate to callers.

## Axiom 3: Cross-Platform Terminal Safety
- Windows console and POSIX terminal abstractions in `click._termui_impl` must isolate OS differences.
- Standard terminal styling, cursor movement, and paging operations must function consistently across supported operating systems.
- Stream operations must handle binary and text encodings gracefully without unintended byte-string type collisions.

## Axiom 4: Internal Sentinel Semantics
- Internal sentinel values representing missing or unset options are private framework markers and must be treated as distinct from user-provided values.

## Axiom 5: Public API Stability
- Public classes (`Command`, `Group`, `Context`, `Parameter`, `Option`, `Argument`, `ParamType`) must preserve signature backwards compatibility.
- Help formatting must produce deterministic, readable output across all supported terminal dimensions.

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
  - `test_types/`: ParamType unit tests.

---

## 3. Subsystem Architecture & Boundary Contracts
Here are the subsystem boundaries and dependency rules:
- `core` (`src/click/core.py`): Core CLI command execution engine, Context tree, and parameter binding.
  Allowed imports: click.types, click.utils, click.exceptions, click.formatting, click.globals, click._compat, click._termui_impl
- `types` (`src/click/types.py`): Parameter types, type conversion, and input validation hierarchy.
  Allowed imports: click.exceptions, click.utils, click._compat
- `termui` (`src/click/termui.py`): High-level terminal UI convenience utilities: echo, prompt, confirm, progressbar.
  Allowed imports: click._termui_impl, click._compat, click.utils, click.exceptions
- `_termui_impl` (`src/click/_termui_impl.py`): Low-level cross-platform terminal implementation, pager, and progress rendering.
  Allowed imports: click._compat, click.utils, click.exceptions
- `formatting` (`src/click/formatting.py`): Help table generation and text wrapping.
  Allowed imports: click._compat, click.utils
- `utils` (`src/click/utils.py`): General text utilities, short help formatting, and file opening helpers.
  Allowed imports: click._compat, click._utils
- `_utils` (`src/click/_utils.py`): Internal singletons and sentinel helpers.
  Allowed imports: click._compat
- `parser` (`src/click/parser.py`): Command line argument and option parser.
  Allowed imports: click.exceptions, click._compat

Sandbox constraints:
- Protected paths: docs/**, CHANGES.md
- Allowed commands: pytest, git, python

---

## 4. Maintenance Targets & Acceptance Contract

## Milestone: Click Maintenance & Stability (v8.5.x)
- Intent: Maintain zero regressions across all 2,000+ unit tests across POSIX and Windows.
- Acceptance Contract:
  - [MEASURED]: 2,022 passed, 101 skipped, 1 xfailed in pytest suite.
  - [INTENT]: Bug fixes must strictly increase or maintain test coverage without introducing regressions.

---

## 5. Past Architectural Decisions & Rejected Alternatives

## REJ-001: External Runtime Dependencies (e.g. Colorama)
- Proposal: Rely on external packaging for Windows ANSI colors.
- Rejection: Click 8.2 dropped Colorama; modern Windows 10+ supports native ANSI virtual terminal processing. Click maintains zero non-stdlib dependencies.
- Reopen Condition: Never. Zero runtime dependencies is a constitutional invariant.

## REJ-002: Eager Import of Heavy Modules
- Proposal: Import `shutil`, `tempfile`, `subprocess`, and formatting engines eagerly at module top-level in `utils.py` and `_termui_impl.py`.
- Rejection: Increases CLI startup latency. Infrequently used subroutines (like editor launches or specific formatting algorithms) must import heavy modules lazily.
- Reopen Condition: Benchmark proving zero impact on microsecond startup time.

## REJ-003: Swallowing Cleanup Exceptions During Teardown
- Proposal: Use broad `except Exception: pass` around cleanup code in context managers.
- Rejection: Masks critical resource leaks and makes debugging unexpected system failures impossible. Teardown routines must allow unexpected failures to surface cleanly.
- Reopen Condition: Documented OS-level requirement where cleanup cannot be made deterministic.

---

## 6. Testing & Verification

## Test Execution Invariant
All test runs must set `pythonpath=src` (or environment variable `PYTHONPATH=src`) to ensure tests execute against the repository source rather than system-installed packages.

## Test Baseline
- Command: `pytest -o pythonpath=src -q`
- Expected: ~2,022 passed in ~3.8 seconds.
- Regression Gate: Zero regression tolerance on existing passing tests.

---

## 7. Baseline Environment & Initial State

## Current Objective
- Initialize task context; execute reproduction test to isolate the failure.

## Status & Gate Verification
- Codebase: pallets/click baseline loaded.
- Tests: pytest execution verified with pythonpath=src.

## Immediate Next Action (Post-Compact)
- Run targeted reproduction test; analyze source module under test; apply minimal fix; re-verify.
