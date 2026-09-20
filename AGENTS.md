# Agent Instructions (SDCS Framework v1.3)

This repository follows **Spec-Driven Cognitive Scaffolding (SDCS / SPEC-001 v1.3)**.

## 1. Orientation & Hydration Order
Before planning or modifying code, orient yourself by reading the 7 cognitive pillars in this sequence:
1. **`spine.md`** (or `.agent/spine.md`): Constitutional invariants, axioms, and forbidden blast-radius actions. (Pillar 1: The Law)
2. **`roadmap.md`** (or `.agent/roadmap.md`): Macro acceptance contract. Understand human `[INTENT]` vs `[MEASURED]` reality. (Pillar 3: The North Star)
3. **`app_map.md`** (or `.agent/app_map.md`): Repository cartography. Use this to locate relevant files instead of running exhaustive `grep`/`find` scans. (Pillar 5: The Compass)
4. **`decisions.md`** (or `.agent/decisions.md`): Negative episodic memory (rejection log). Confirm you are not reverting prior intentional trade-offs or retrying measured failures. (Pillar 6: The Graveyard)
5. **`evals.md`** (or `.agent/evals.md`): Positive episodic memory (ground truth standing, benchmarks, and diversity guard). (Pillar 7: Positive Ground Truth)
6. **`state.md`** (or `.agent/state.md`): Working memory blackboard. Understand the active objective and current test gates. (Pillar 4: The Blackboard)
7. **`wiring.yaml`** (or `.agent/wiring.yaml`): Declarative dependency mesh, subsystem boundaries, and tool contracts. (Pillar 2: The Mesh)

## 2. Invariant Rules
- **Context Isolation:** Do not load arbitrary files into context. Consult `app_map.md` and load only what is strictly relevant to the task.
- **Do NOT Ingest `sessions/` on Boot (+1 Flight Recorder):** `sessions/*.md` acts as an auditable flight recorder, NOT boot context. Auto-loading past sessions recreates context drift and amnesia. Query individual session files only on demand for targeted forensic debugging.
- **No Task Queue in Roadmap:** Never treat `roadmap.md` as an ephemeral to-do list. Active tasks live strictly in `state.md`.
- **Non-Regression:** Never undo a decision or retry a measured rejection documented in `decisions.md` without explicit human sign-off.
- **Topological Invariant (Gate T):** Code must respect subsystem boundary contracts declared in `wiring.yaml`. Prohibited imports will be rejected and serialized to `decisions.md`.
- **Wiring Mutation Invariant (Pillar 2):** When introducing new subsystems, modules, or packages, update `wiring.yaml` in-stride with code modifications. Modifying `wiring.yaml` to relax existing architectural boundaries, add circular dependencies, or bypass Gate T rejections without explicit human authorization (`SDCS_ALLOW_INVARIANT_MUTATION=1`) is strictly forbidden.
- **Empirical Standing:** Verify changes against the baseline scorecard in `evals.md`. Run `audit_evals_corpus.py` when adding or modifying test fixtures.
- **Empirical Verification:** Always run existing tests, typechecks, and eval gates before reporting completion.

## 3. Mid-Shift Checkpoint Protocol ("prepare for compact")
When instructed to "prepare for compact", or when context window exhaustion nears prior to session compaction:
1. **Topology & Subsystem Audit:** Run `sdcs verify --topology` to verify that all imports comply with `wiring.yaml`. If new modules or packages were created during the shift, ensure they are declared in `wiring.yaml`.
2. **Flight Recorder Checkpoint:** Write an immutable checkpoint log to `sessions/YYYY-MM-DD_<topic>.md` capturing work completed, verification status, active blockers, and immediate post-compact next steps.
3. **Blackboard Pruning (`state.md`):** Aggressively prune and overwrite `state.md` strictly to <= 300 tokens containing only:
   - `## Current Objective`
   - `## Status & Gate Verification`
   - `## Immediate Next Action (Post-Compact)`
4. **Episodic Sweeps:**
   - Log any rejected approaches or failed experiments to `decisions.md`.
   - Synchronize `app_map.md` if files were created, moved, or deleted.
   - Update `roadmap.md` [MEASURED] blocks if milestones or acceptance criteria were met.
5. **Readiness Signal:** Output a brief confirmation that all 7 pillars and the flight recorder are synchronized, and state: "Ready for compaction."

## 4. Close-Out Protocol (Mandatory)
Before declaring any task complete or staging files at the end of an engineering shift:
1. Prune and overwrite `state.md` with current verification status (<= 300 token budget).
2. Update `roadmap.md` [MEASURED] blocks with real test telemetry.
3. If an attempted optimization or architecture failed, log it to `decisions.md`.
4. Update `app_map.md` if new files were created.
5. Verify `wiring.yaml` matches codebase topology (`sdcs verify --topology`).
6. Append an immutable flight recorder log in `sessions/YYYY-MM-DD_<topic>.md`.
