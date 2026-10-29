# Agent Instructions (SDCS Framework v1.9.0)
<!-- Conforming to SPEC-001 v1.9.0 -->

This repository follows **Spec-Driven Cognitive Scaffolding (SDCS / SPEC-001 v1.9.0)**.

## 1. The Operational Ontology
You are operating inside a deterministic cybernetic control system, not an unconstrained environment. The codebase is organized across three layers that hold the 7 pillars, governed by a teleological anchor:

- **0. Teleological Anchor (The Target):** `roadmap.md` (Pillar 3: The North Star). Macro acceptance contract: `[INTENT]` vs `[MEASURED]`. Your sole task is driving the measured delta to zero.
- **1. Semantic Layer (What Exists):** `spine.md` (Pillar 1: Constitutional Invariants & Axioms), `wiring.yaml` (Pillar 2: Subsystem Boundaries & Dependency Mesh), and `app_map.md` (Pillar 5: Repository Cartography). You cannot invent entities or subsystems outside this declared schema.
- **2. Kinetic Layer (The Laws of Motion):** Gate T AST boundary audits (`sdcs verify --topology`), Gate M cartography drift checks (`sdcs map --check`), Gate C (Contract Immutability), Gate S (Working Memory Budget), Gate P (Sandbox Guard), Gate W (Secret Sanitizer), Gate Q (Test Quality & Anti-Mock), Gate E & `sdcs doctor` (Environment Invariant Lock), Gate C-Cache (`sdcs verify --cache-invariance`), Gate L (Mock Ledger, `sdcs verify --mocks`), the Circuit Breaker (`sdcs verify --cycles`), and physical pre-commit hooks (`.githooks/pre-commit`). Every code mutation is a kinetic state transition; attempts to violate contracts are physically rejected on disk.
- **3. Dynamic Layer (Memory & Time Evolution):** `decisions.md` (Pillar 6: Negative Episodic Memory / Graveyard), `evals.md` (Pillar 7: Positive Episodic Memory / Empirical Standing & SHA-256 fixture locks), `state.md` (Pillar 4: Active Working Blackboard $\le 300$ tokens), and `sessions/manifest.jsonl` (+1 Flight Recorder Causal Lineage).


## 2. Turn 1 Boot Hydration Order (7 Pillars)
- **ZERO-READ PRE-HYDRATED RULE:**
  - **If `SDCS DETERMINISTIC CONTEXT COMPILER` (`sdcs hydrate`) is present in your prompt:** All 7 Pillars (`spine.md`, `roadmap.md`, `app_map.md`, `decisions.md`, `evals.md`, `state.md`, `wiring.yaml`), `# [AST SKELETAL INTERFACES]`, and `# [PRE-HYDRATED SOURCE FILES]` are **ALREADY hydrated in your prompt**.
  - **NEVER call `list_files` or `read_file` on any pillar file or any file already shown in `# [PRE-HYDRATED SOURCE FILES]`—in either Session 1 OR Session 2!** Begin editing target `.py` files immediately on Turn 1 using `edit_file` or `write_file`.
  - Only read the 7 pillar files manually from disk if your prompt does NOT contain the `SDCS DETERMINISTIC CONTEXT COMPILER` payload.

If your prompt is NOT pre-hydrated, hydrate state across the 7 cognitive pillars in this sequence on Turn 1:
1. `spine.md`        -> Constitutional invariants & forbidden actions (Pillar 1: The Law)
2. `roadmap.md`      -> Active milestone [INTENT] vs [MEASURED] (Pillar 3: The North Star)
3. `app_map.md`      -> Repository cartography (resolve target paths first) (Pillar 5: The Compass)
4. `decisions.md`    -> Negative episodic memory (rejected hypotheses) (Pillar 6: The Graveyard)
5. `evals.md`        -> Verified empirical baseline & ground truth (Pillar 7: Positive Ground Truth)
6. `state.md`        -> Turn-by-turn active working memory (Pillar 4: The Blackboard)
7. `wiring.yaml`     -> Declarative topology & subsystem boundaries (Pillar 2: The Mesh)

*Single-Pass Hydration:* Alternatively, run `sdcs hydrate --profile standard [-s <subsystem>]` (or `--profile lite` / `--profile full`) to stream a pre-budgeted, single-pass context payload in 1 atomic tool call.

## +0 Fast-Resume Protocol (Cold-Start Eliminator)
When booting or waking up after context compaction (`/compact`), inspect `state.md` first.
If `## Immediate Next Action (Post-Compact)` contains an active, uncompleted action, verify essential prerequisites (check that target files exist and recent tests still pass), then proceed directly to executing that action. Avoid redundant whole-repository surveys or historical archive exploration when an active, unblocked next step is pending.

## +1 Flight Recorder Invariant
Do not hydrate historical files in `sessions/*.md` during standard boot. `sessions/*.md` serves as an immutable post-hoc flight recorder, not operational working memory. Auto-loading historical sessions causes context drift and token waste. Query individual sessions or `sessions/manifest.jsonl` on demand for forensic debugging (`sdcs session`).

## 2b. Practical Pillar Usage & Multi-Session Survival Guide
1. **Zero-Discovery Navigation (`app_map.md` + AST Skeletons + Pre-Hydrated Source):** Use `app_map.md` to know every file path in the repo without running `list_files`, use `# [AST SKELETAL INTERFACES]` to check exact class/dataclass/method signatures across modules, and use `# [PRE-HYDRATED SOURCE FILES]` to edit `.py` files immediately on Turn 1 without calling `read_file`.
2. **Boundary Enforcement (`wiring.yaml` + `spine.md`):** Before adding any `import`, check `allowed_dependencies` in `wiring.yaml` (and module-boundary rules) so you never introduce a forbidden cross-module dependency.
3. **In-Stride Mid-Session Requirement Locking (`state.md` <= 300 tokens):**
   - `state.md` must preserve its 3 `##` headings (`## Current Objective`, `## Status & Gate Verification`, `## Immediate Next Action`) and stay `<= 300` tokens (Gate S).
   - Visible unit tests (`pytest` / `run_tests`) often only cover initial baseline specifications—they do **NOT** automatically test new mid-session product requirements!
   - Whenever new requirements arrive mid-session, immediately wire every required parameter, field, default value, and return key across all affected modules (`models`, `rules`, `service`, `reporting`, etc.), record the exact parameter/field names and module checklist in `state.md`, and **commit before the session ends** (uncommitted changes are wiped when a session ends).
4. **Post-Wipe / Session-2 Verification Protocol:**
   - When starting a new session after a context wipe, **never finish early just because `pytest` / `run_tests` passes!**
   - On Turn 1 of Session 2, review the pre-hydrated `state.md` and `# [PRE-HYDRATED SOURCE FILES]` already shown in your prompt (**do NOT call `read_file` on files already shown in your prompt**).
   - Check whether every mid-session requirement from Session 1 is fully wired across all modules (`models`, `rules`, `service`, `reporting`, etc.). If any requirement is missing or incomplete, immediately edit the affected `.py` file(s), run tests, update `state.md`, and call `finish`! If all requirements are already wired in `# [PRE-HYDRATED SOURCE FILES]`, run `run_tests` once and call `finish` immediately.

## 3. The 4-Phase Autonomous Execution Cycle
Execute every turn through the 4-phase engine:
1. **Orientation:** Hydrate constraints and ground truth from the Semantic and Dynamic layers.
2. **Planning:** Formulate atomic diffs against `state.md` respecting boundaries in `wiring.yaml`.
3. **Execution:** Apply code mutations and verify against kinetic gates (Gate T AST audits) and empirical baselines (`evals.md`).
4. **Close-Out:** Prune `state.md` ($\le 300$ tokens) and immediately commit/finish.

## 4. Invariant Rules
- **Context Isolation & Reality Verification:** Consult `app_map.md` first to locate relevant modules and avoid aimless whole-repo scans. Use targeted search or grep to verify actual symbols, function signatures, and disk reality against the map before making modifications.
- **No Task Queue in Roadmap:** Active tasks live strictly in `state.md`.
- **Non-Regression & Reopen Conditions:** Do not retry a rejected hypothesis or revert an architectural decision documented in `decisions.md` unless its documented "WHAT WOULD REOPEN IT" condition has been satisfied (e.g. upgraded dependencies, altered interfaces) or explicit human sign-off is given.
- **Topological Invariant (Gate T):** Code must respect subsystem boundary contracts declared in `wiring.yaml`. Prohibited imports will be rejected and serialized to `decisions.md`.
- **Wiring Mutation Invariant (Pillar 2):** When introducing new subsystems, modules, or packages, update `wiring.yaml` in-stride with code modifications. Modifying `wiring.yaml` to relax existing architectural boundaries, add circular dependencies, or bypass Gate T rejections without explicit human authorization (`SDCS_ALLOW_INVARIANT_MUTATION=1`) is strictly forbidden.
- **Empirical Standing:** Verify changes against the baseline scorecard in `evals.md`. Run `sdcs eval record <Asset-ID>|all` (or `sdcs audit`) when adding, recalibrating, or modifying test fixtures.
- **Empirical Verification:** Always run existing tests, typechecks, and eval gates before reporting completion.
- **Mock Ledger Invariant (Gate L):** Any product code that stands in for real behavior (simulated responses, seeded or hardcoded data, demo-only keys or endpoints, offline stubs) gets a `MOCK(M-NNN)` comment marker and a matching entry in `MOCKS.md`, in the same commit. Remove markers and entry together. Never add a fallback that reports a failed call as a success. `sdcs verify --mocks` enforces this.

## 5. Mid-Shift Checkpoint Protocol ("prepare for compact")
When explicitly instructed by the user to "prepare for compact" in an interactive CLI session:
1. **Topology & Subsystem Audit:** Run `sdcs verify --topology` to verify that all imports comply with `wiring.yaml`.
2. **Blackboard Pruning (`state.md`):** Aggressively prune and overwrite `state.md` strictly to <= 300 tokens containing only `## Current Objective`, `## Status & Gate Verification`, and `## Immediate Next Action (Post-Compact)`.
3. **Interactive CLI Sweeps (only when unconstrained by a commit window):** Synchronize `app_map.md` (`sdcs map --sync`), log rejected experiments to `decisions.md`, and write a checkpoint to `sessions/YYYY-MM-DD_<topic>.md` (`sdcs session index`).
4. **Readiness Signal:** Output a brief confirmation and state: "Ready for compaction."

## 6. Fast-Commit & Close-Out Protocol (Mandatory)
- **CRITICAL COMMIT-WINDOW RULE:** Uncommitted changes are **wiped (`git reset --hard`)** when a session ends!
- Whenever a session is ending (`"This session is ending. Commit your work now."`) or when closing out a turn-limited session, **ONLY update `state.md` (`<= 300` tokens) and immediately call `commit` or `finish`!**
- **NEVER waste commit-window turns editing `roadmap.md`, `decisions.md`, `evals.md`, `app_map.md`, or `sessions/*.md`!** Updating `roadmap.md`, `decisions.md`, and `sessions/` is strictly for interactive CLI checkpoints when full CLI tools are available and turn budgets are unconstrained.
