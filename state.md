# Dynamic Working Memory (The Blackboard)
<!-- SPEC-001 Pillar 4 | Mutability: HIGH VOLATILITY | Budget: <= 300 Tokens -->

## Current Objective
- [x] Sync public SDCS v1.9.7 upgrades: extract_symbol_window_slice in skeleton.py, sdcs check subcommand in cli.py, scale-adaptive AGENTS.md template with CacheForge Zero-Read protocol in init.py, adaptive hydration in hydrate.py, and 500t default ceiling in state verifier.
- [x] Synchronize sdcs_init.py and AGENTS.md with src/sdcs/init.py byte-for-byte.
- [x] Add comprehensive test coverage in test_skeleton.py and test_cli.py.
- [x] Maintain distinct naming for SDCS v1.9.7 and CacheForge (no SDCS v3).

## Status & Gate Verification
- Gate Q: 248/248 tests passing via pytest in both public and holdout repositories.
- Gate S: state.md verified within budget; canonical 3 headings preserved.
- sdcs check: PASS (TESTS, SYNC, GATES all green).
- Zero em-dashes verified across all updated source, test, template, and documentation files.

## Immediate Next Action
- Stage, commit, and push upgrades to origin/main.
