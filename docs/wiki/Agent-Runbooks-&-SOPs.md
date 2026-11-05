# Agent Runbooks & Standard Operating Procedures (SOPs)

This document specifies the operational runbooks governing autonomous coding agents operating within SDCS v1.9.8 repositories.

---

## SOP-001: Turn 1 Boot Hydration Sequence

On Turn 1 of any task (or upon session startup / post-compaction recovery), the agent MUST hydrate state across the 7 cognitive pillars in this non-negotiable sequence:

```
1. spine.md       ──► Constitutional Invariants & Forbidden Actions (The Law)
2. roadmap.md     ──► Active Milestone: [INTENT] vs [MEASURED] (The North Star)
3. app_map.md     ──► Repository Cartography: Resolve paths first (The Compass)
4. decisions.md   ──► Negative Episodic Memory: Rejected hypotheses (The Graveyard)
5. evals.md       ──► Verified Baseline & Golden Hash Scorecard (Positive Ground Truth)
6. state.md       ──► Active Working Memory Blackboard <= 500 tokens (The Whiteboard)
7. wiring.yaml    ──► Declarative Topology & Component Boundaries (The Mesh)
```

### Critical Invariant: The Flight Recorder Isolation Rule
* **NEVER** auto-load or hydrate `sessions/*.md` on boot.
* Historical sessions serve as an immutable, write-once flight recorder. Auto-loading raw session prose recreates context dilution and amnesia.
* Query `sessions/manifest.jsonl` on-demand via `sdcs session list --query <topic>` only when forensic debugging is explicitly required.

---

## SOP-002: In-Stride Subsystem Wiring (Pillar 2)

When an agent introduces new packages, modules, or subsystems:
1. **Additive In-Stride Rule:** The agent MUST update `wiring.yaml` in the same commit or turn as the code addition.
2. **Prohibited Boundary Relaxation:** Modifying `wiring.yaml` to relax existing boundaries, introduce circular dependencies, or bypass Gate T rejections without explicit human sign-off (`SDCS_ALLOW_INVARIANT_MUTATION=1`) is strictly forbidden.
3. **Remediation on Boundary Breach:** If Gate T halts a commit, decouple the component via dependency inversion or interface segregation.

---

## SOP-003: Baseline Fixture Recalibration Protocol

When a legitimate refactor or feature changes benchmark scores or test fixtures:
1. **Do Not Manually Edit Tables:** The agent must never hand-edit SHA-256 hash strings in `evals.md`.
2. **Execute First-Class Recalibration:**
   ```bash
   # Recalibrate a specific fixture
   sdcs eval record <Asset-ID>

   # Recalibrate all declared fixtures simultaneously
   sdcs eval record all
   ```
3. **Verify Anti-Phantom Corpus:** Run `sdcs audit` to ensure no two fixtures share identical normalized digests.

---

## SOP-004: Engineering Shift Close-Out Protocol

Before declaring any task complete or staging files at the conclusion of an engineering shift:
1. **Prune `state.md`:** Overwrite with current verification status ($\le 300$ tokens via `sdcs verify --state`).
2. **Update Telemetry:** Record empirical test numbers and commit hashes into `roadmap.md` `[MEASURED]` blocks.
3. **Serialize Dead Ends:** If an attempted architecture or optimization failed, record it to `decisions.md`.
4. **Synchronize Cartography:** Audit and sync `app_map.md` via Gate M (`sdcs map --check` / `sdcs map --sync`).
5. **Verify Topology:** Ensure 100% compliance with `wiring.yaml` via Gate T (`sdcs verify --topology`).
6. **Append Flight Record:** Create `sessions/YYYY-MM-DD_<topic>.md` and sync manifest (`sdcs session index`).

---

## SOP-005: Mock Ledger Invariant (Gate L)

When product code must simulate external dependencies or fake real behavior:
1. **Declare In-Stride:** Stamp every product-code mock with a `# MOCK(M-NNN)` marker and register it in `MOCKS.md` with all four required fields (`Where`, `What it fakes`, `Why`, `To make it real`) in the same commit.
2. **No Fake Success (`REQ-GATE-L-06`):** Never implement error fallbacks in `except` or `catch` blocks that pretend a failure was a success or return mock objects.
3. **Verify:** Run `sdcs verify --mocks` before committing.

---

## SOP-006: Scale-Adaptive Boot Hydration & Zero-Read Workspace Bundles

In SDCS v1.9.8, repository scale governs Turn 1 boot hydration adaptively:
1. **Small Repositories (<= 4,000 source tokens, <= 10 files):**
   - When `# [PRE-HYDRATED SOURCE FILES]` (or `# [CacheForge Zero-Read Workspace Bundle]`) is present in the prompt, the exact verbatim file contents are pre-hydrated directly from disk.
   - Do **NOT** call `list_files` or `read_file` on those files; start editing target `.py` files immediately on Turn 1 using `edit_file`.
2. **Large Repositories / Monorepos (> 4,000 source tokens):**
   - Hydrate `# [AST SKELETAL INTERFACES]` and page focused subsystem cartography via `sdcs map -s <subsystem>`.

---

## SOP-007: Turn-1 Mid-Session Spec Lock (`state.md` <= 500 tokens)

Whenever a user message introduces multi-package or mid-session sprint requirements not in `TASK.md`:
1. **The In-Stride Lock Rule:** Your **VERY FIRST tool call** MUST be `edit_file` on `state.md` to record every requirement's exact parameter names, default values, formulas, inequalities, return types, and target `.py` file paths under `## Current Objective` and `## Immediate Next Action` **BEFORE** reading or editing any `.py` code files.
2. **Budget Constraint:** Keep `state.md` <= 500 tokens (Gate S) by using concise 1-line bullets while preserving exact formulas.
3. **Traceability:** Mark completed items `- [x]` in `state.md` as each component lands.

---

## SOP-008: Symbol-Windowed Editing & One-Shot `sdcs check` Close-Out

1. **Symbol-Windowed Editing:** When modifying modules with collapsed stubs, leave untouched helper methods (`...`) untouched. Pass only exact verbatim target function and class lines as `Target` to `edit_file`.
2. **The Verification Receipt:** Before calling `finish` or committing, run `sdcs check` to verify unit tests pass, fixture hashes synchronize, and all 7 kinetic gates stay clean.
