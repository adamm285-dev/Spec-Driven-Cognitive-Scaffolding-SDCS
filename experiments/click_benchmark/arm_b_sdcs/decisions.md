# Negative Episodic Memory (The Graveyard)
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
- Reopen Condition: Documented OS-level requirement where cleanup cannot be made deterministic.\n