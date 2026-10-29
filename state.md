# Dynamic Working Memory (The Blackboard)
<!-- SPEC-001 Pillar 4 | Mutability: HIGH VOLATILITY | Budget: <= 300 Tokens -->

## Current Objective
- Rewrite `TEMPLATE_AGENTS` / `AGENTS.md`: plain "What SDCS Is" explainer (Section 0) replaces the ontology jargon; repeated `state.md` / commit / pre-hydration rules deduped (2,447 -> 1,785 tokens).

## Status & Gate Verification
- Gate Q: `243/243` unit tests passing via `pytest`, incl. new `test_root_agents_md_matches_template`.
- `sdcs verify --all`: PASSED (T, S, cycles, Q, E, C-Cache, L, evals).
- Gate M: drift only from pre-existing untracked files (PNGs, `observation.md`, `.sdcs/`, `uv.lock`).
- Synced: `src/sdcs/init.py`, `sdcs_init.py`, root `AGENTS.md`.

## Immediate Next Action
- Human review of the new template wording; no version bump or tag yet.
