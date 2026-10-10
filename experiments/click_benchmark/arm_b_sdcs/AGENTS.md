# Agent Instructions (Click Maintenance)
<!-- SDCS Operational Protocol -->

## Turn 1 Boot Hydration Order
1. `spine.md` -> Constitutional invariants (zero external deps, resource lifecycle).
2. `roadmap.md` -> Teleological target [INTENT] vs [MEASURED].
3. `app_map.md` -> Cartography of modules and test directories.
4. `decisions.md` -> Negative episodic memory / rejected patterns.
5. `evals.md` -> Test execution baseline (`pytest -o pythonpath=src`).
6. `state.md` -> Active working blackboard (<= 350 tokens).
7. `wiring.yaml` -> Subsystem import boundaries.

## 4-Phase Autonomous Execution Cycle
1. **Orientation:** Hydrate constraints; locate target module in `app_map.md`.
2. **Planning:** Formulate minimal, atomic fix preserving subsystem boundaries.
3. **Execution:** Apply code mutation; run targeted reproduction test.
4. **Close-Out:** Run full test suite (`pytest -o pythonpath=src`) to verify zero regressions; prune `state.md`.\n