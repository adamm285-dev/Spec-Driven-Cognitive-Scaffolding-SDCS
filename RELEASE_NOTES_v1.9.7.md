# Release Notes: Spec-Driven Cognitive Scaffolding (SDCS) v1.9.7

**Released:** 2026-10-31 : **Spec:** SPEC-001 v1.9.7 : **Replaces:** v1.9.6 / v1.9.1

SDCS v1.9.7 integrates CacheForge AST symbol-window slicing, the one-shot `sdcs check` verification subcommand, scale-adaptive boot context with Zero-Read Workspace Bundles, Turn-1 mid-session spec locking, and an updated 500-token working memory budget ceiling.

---

## Key Highlights in v1.9.7

### 1. One-Shot Compact Verification Subcommand (`sdcs check`)
- **Deterministic 3-Line Receipt:** Runs `pytest -q`, quietly reconciles `app_map.md` cartography and `evals.md` fixture hashes, audits all 7 kinetic gates (Topology, State Budget, Cycles, Quality, Env, Cache Invariance, and Mocks), and emits a compact receipt:
  ```text
  TESTS: PASS (248 passed in 38.98s)
  SYNC : PASS (app_map.md & evals.md SHA-256 corpus synced)
  GATES: PASS (All 7 SDCS gates clean; state.md <= 500t)
  ```
- **CLI Options:** Supports `--repo-root <path>`, `--max-tokens <int>` (default: 500), and `--skip-pytest`.
- **Pre-Commit and Close-Out Synergy:** Provides autonomous agents with an unambiguous, non-LLM oracle to confirm all requirements and gates are satisfied before calling `finish` or committing.

### 2. CacheForge AST Symbol-Window Slicer (`extract_symbol_window_slice`)
- **Byte-Exact Target Targeting:** Module-level imports, constants, `@dataclass` definitions, `Enum` classes, and exception classes are preserved verbatim.
- **Target and Caller Retention:** Functions and methods matching active target symbols (or `__init__`) are kept 100% byte-for-byte from disk so `edit_file` `Target` strings never fail.
- **Untouched Helper Collapsing:** Helper methods and functions (`>= 2` body lines) not referenced by target symbols are collapsed to 1-line `...` stubs, reducing KV-cache token consumption by up to 85% while preserving valid syntax.

### 3. Scale-Adaptive Boot Context (`sdcs hydrate --profile adaptive`)
- **Small Repositories (<= 4,000 source tokens, <= 10 files):** Turn 1 boot pre-hydrates `AGENTS.md` + `state.md` + `# [PRE-HYDRATED SOURCE FILES]` (Zero-Read Workspace Bundle), allowing agents to modify code immediately on Turn 1 without burning tool calls on exploratory `read_file` or `list_files`.
- **Large Repositories / Monorepos (> 4,000 source tokens):** Hydrates `# [AST SKELETAL INTERFACES]` and repository cartography, guiding agents to page focused subsystem slices (`sdcs map -s <subsystem>`) instead of flooding context.

### 4. Turn-1 Mid-Session Spec Lock (`state.md` <= 500 tokens)
- **Immediate Requirement Anchor:** Whenever a user message introduces multi-package or mid-session sprint requirements not in `TASK.md`, the agent's **VERY FIRST tool call** must be `edit_file` on `state.md` to lock exact parameter names, default values, formulas, return shapes, and ordering rules **BEFORE** editing any `.py` code files.
- **Traceable In-Stride Progress:** Completed requirements are marked `- [x]` in `state.md` as they land.
- **Budget Ceiling Alignment:** Gate S working memory default ceiling adjusted from 300 to 500 tokens across verifier and pre-commit hooks, providing sufficient headroom for complex cross-module contracts.

### 5. Template & Documentation Synchronization
- **Byte-Exact Protocol Parity:** Synchronized `src/sdcs/init.py`, `sdcs_init.py`, and root `AGENTS.md` character-for-character, including `CACHEFORGE_PROTOCOL_BLOCK` and `TEMPLATE_AGENTS`.
- **Full Wiki & README Modernization:** Updated all 10 documentation pages in `docs/wiki/` and `README.md` to reflect `sdcs check`, symbol windowing, adaptive hydration, and 500-token budgets.
- **Zero Em-Dashes:** 100% verified clean across all codebase, template, test, and documentation files.

---

## Verification Telemetry

- **Test Suite:** **248/248 unit tests passing** via pytest across public and holdout repositories.
- **Kinetic Gates:** All 7 SDCS gates verified clean via `sdcs check` and `sdcs verify --all`.
- **Packaging:** Verified clean build via `python -m build` and `twine check dist/*`.

---

## Upgrading to v1.9.7

```bash
pip install --upgrade sdcs
sdcs check
```
