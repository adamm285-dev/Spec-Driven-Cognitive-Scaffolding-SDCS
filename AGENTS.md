# Agent Instructions (SDCS Framework v1.2)

This repository follows **Spec-Driven Cognitive Scaffolding (SDCS / SPEC-001 v1.2)**.

## 1. Orientation & Hydration Order
Before planning or modifying code, orient yourself by reading the 7 cognitive pillars in this sequence:
1. **`spine.md`** (or `.agent/spine.md`): Constitutional invariants, axioms, and forbidden blast-radius actions.
2. **`roadmap.md`** (or `.agent/roadmap.md`): Macro acceptance contract. Understand human `[INTENT]` vs `[MEASURED]` reality.
3. **`app_map.md`** (or `.agent/app_map.md`): Repository cartography. Use this to locate relevant files instead of running exhaustive `grep`/`find` scans.
4. **`decisions.md`** (or `.agent/decisions.md`): Negative episodic memory (rejection log). Confirm you are not reverting prior intentional trade-offs or retrying measured failures.
5. **`evals.md`** (or `.agent/evals.md`): Positive episodic memory (ground truth standing, benchmarks, and diversity guard).
6. **`state.md`** (or `.agent/state.md`): Working memory blackboard. Understand the active objective and current test gates.
7. **`wiring.yaml`** (or `.agent/wiring.yaml`): Declarative dependency mesh and environment contracts.

## 2. Invariant Rules
- **Context Isolation:** Do not load arbitrary files into context. Consult `app_map.md` and load only what is strictly relevant to the task.
- **Do NOT Ingest `sessions/` on Boot:** `sessions/*.md` acts as an auditable flight recorder, NOT boot context. Auto-loading past sessions recreates context drift and amnesia. Query individual session files only on demand for targeted forensic debugging.
- **No Task Queue in Roadmap:** Never treat `roadmap.md` as an ephemeral to-do list. Active tasks live strictly in `state.md`.
- **Non-Regression:** Never undo a decision or retry a measured rejection documented in `decisions.md` without explicit human sign-off.
- **Empirical Standing:** Verify changes against the baseline scorecard in `evals.md`. Run `audit_evals_corpus.py` when adding or modifying test fixtures.
- **Empirical Verification:** Always run existing tests, typechecks, and eval gates before reporting completion.

## 3. Concluding Instruction (Mandatory)
Before declaring any task complete or staging files:
> **Update `state.md` with current verification status and discovered edge cases, log any architectural decisions in `decisions.md`, verify scores in `evals.md`, and update `app_map.md` if new files were created. At the end of an engineering shift, append an immutable flight recorder log in `sessions/YYYY-MM-DD_<topic>.md`.**
