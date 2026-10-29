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
- **Pre-Hydrated Context Fast Path:**
  - If `SDCS DETERMINISTIC CONTEXT COMPILER` (`sdcs hydrate`) is already present in your prompt, all 7 Pillars (`spine.md`, `roadmap.md`, `app_map.md`, `decisions.md`, `evals.md`, `state.md`, `wiring.yaml`), `# [AST SKELETAL INTERFACES]`, and `# [PRE-HYDRATED SOURCE FILES]` are already loaded in your context.
  - Do not make redundant `list_files` or `read_file` calls on pillar files or source files already shown in `# [PRE-HYDRATED SOURCE FILES]`—either on initial boot or when resuming after a context reset or compaction. Begin implementing edits directly on Turn 1.
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

## 2b. Practical Pillar Usage & Continuity Guide
1. **Zero-Discovery Navigation (`app_map.md` + AST Skeletons + Pre-Hydrated Source):** Use `app_map.md` to resolve file paths without directory scans, `# [AST SKELETAL INTERFACES]` to inspect class/dataclass/function signatures across modules, and `# [PRE-HYDRATED SOURCE FILES]` to edit target `.py` files directly on Turn 1 without redundant file reads.
2. **Boundary Enforcement (`wiring.yaml` + `spine.md`):** Before adding any `import`, check `allowed_dependencies` in `wiring.yaml` (and module-boundary rules) so you never introduce a forbidden cross-module dependency.
3. **In-Stride Requirement Locking (`state.md` <= 300 tokens):**
   - `state.md` must preserve its 3 `##` headings (`## Current Objective`, `## Status & Gate Verification`, `## Immediate Next Action`) and stay `<= 300` tokens (Gate S).
   - Do not duplicate `app_map.md` or `# [AST SKELETAL INTERFACES]` by listing full module-by-module signature inventories in `state.md`.
   - Existing unit test suites often cover only baseline specifications and may not test newly introduced mid-session requirements.
   - Whenever new requirements arrive, wire every required parameter, field, default value, and return key across all affected modules, record the newly added parameter/field names and any unverified modules in `state.md`, and immediately commit your changes so verified progress is persisted in git history.
4. **Post-Compaction / Resumed-Context Verification:**
   - When resuming work after a context reset or compaction, do not assume the task is complete solely because the existing test suite passes.
   - Review `state.md` (`## Immediate Next Action`) and `# [PRE-HYDRATED SOURCE FILES]` (or target source files if not pre-hydrated) to verify that every requirement recorded in `state.md` is fully wired across all modules before completing the task.

## 3. The 4-Phase Autonomous Execution Cycle
Execute every turn through the 4-phase engine:
1. **Orientation:** Hydrate constraints and ground truth from the Semantic and Dynamic layers.
2. **Planning:** Formulate atomic diffs against `state.md` respecting boundaries in `wiring.yaml`.
3. **Execution:** Apply code mutations and verify against kinetic gates (Gate T AST audits) and empirical baselines (`evals.md`).
4. **Close-Out:** Update `state.md` ($\le 300$ tokens), commit verified changes, and update structural pillars when their triggering events occur.

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
When explicitly instructed to "prepare for compact", or when context window exhaustion nears prior to session compaction:
1. **Topology & Subsystem Audit:** Run `sdcs verify --topology` to verify that all imports comply with `wiring.yaml`.
2. **Blackboard Pruning (`state.md`):** Aggressively prune and overwrite `state.md` strictly to <= 300 tokens containing only `## Current Objective`, `## Status & Gate Verification`, and `## Immediate Next Action (Post-Compact)`.
3. **Checkpoint Sweeps:** Synchronize `app_map.md` (`sdcs map --sync`) if files were added/removed, log any rejected experiments to `decisions.md`, update `roadmap.md` `[MEASURED]` blocks if milestones were met, and write a checkpoint to `sessions/YYYY-MM-DD_<topic>.md` (`sdcs session index`).
4. **Readiness Signal:** Output a brief confirmation and state: "Ready for compaction."

## 6. Close-Out Protocol & Pillar Update Cadence
Maintain each cognitive pillar according to its SPEC-001 mutability cadence:
1. **In-Stride Working Memory (`state.md` — Every Commit):**
   - Whenever you modify code or receive updated requirements, prune and update `state.md` (`<= 300` tokens, preserving `## Current Objective`, `## Status & Gate Verification`, and `## Immediate Next Action`) and **commit your working code + `state.md` first** so verified progress is immediately locked into git history.
2. **Event-Driven Structural Pillars (Only When Triggered):**
   - **Cartography (`app_map.md`):** Synchronize (`sdcs map --sync`) **only when files or directories are created, moved, or deleted** (no update needed when editing existing files).
   - **Topology (`wiring.yaml`):** Update **only when introducing new subsystems or modules** (`sdcs verify --topology`).
   - **Rejection Graveyard (`decisions.md`):** Append an entry **only when an attempted architecture or hypothesis fails and is rejected**.
   - **Ground Truth (`evals.md`):** Recalibrate (`sdcs eval record` / `sdcs audit`) **only when golden test fixtures are added or modified**.
3. **Milestone & Compaction Checkpoints (`roadmap.md` & `sessions/`):**
   - Update `roadmap.md` `[MEASURED]` blocks and write a shift handoff log to `sessions/YYYY-MM-DD_<topic>.md` (`sdcs session index`) when completing a macro milestone or when instructed to `"prepare for compact"`.
