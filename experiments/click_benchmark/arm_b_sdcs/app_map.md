# Repository Cartography (The App Map)
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
  - `test_types/`: ParamType unit tests.\n