# Contributing to Spec-Driven Cognitive Scaffolding (SDCS)

Thank you for contributing to SDCS and the SPEC-001 specification. We treat agent harness development with the same rigor as systems engineering: unmeasured claims are discarded, invariants are non-negotiable, and every pull request must leave the cognitive memory bank cleaner than it was found.

---

## 1. Guiding Philosophy

1. **Determinism over Inference:** If a behavior can be verified by a deterministic script, test suite, or schema, never offload it to an ambiguous prompt instruction.
2. **Empirical Grounding:** We do not accept subjective performance claims. Every optimization or architectural shift must provide reproducible baseline numbers.
3. **Symmetric Memory Integrity:** Changes that modify operational logic must record positive verification in `evals.md` or negative rejection criteria in `decisions.md`.

---

## 2. The Contribution Verification Gate

Before opening a pull request, your branch must satisfy the four verification gates defined in `spine.md`:

| Gate | Check | Command / Verification |
| :--- | :--- | :--- |
| **Lint & Style** | Ruff & Black formatting | `ruff check . && black --check .` |
| **Static Types** | Mypy strict adherence | `mypy .` |
| **Unit Suite** | Automated regression checks | `pytest -v` |
| **Corpus Diversity** | No duplicate test fixtures | `python audit_evals_corpus.py` |

Pull requests with failing checks or broken integrity hashes will not be reviewed.

---

## 3. Harness Compliance Rules

When modifying code or docs, follow these rules across the SDCS files:

### `spine.md` (Constitutional Invariants)
* **Status:** Human-governed.
* Pull requests modifying `spine.md` must include explicit rationale in the PR body. Agents and automated contributors are strictly forbidden from weakening or removing axioms without the `allow-invariant-mutation` label or `SDCS_ALLOW_INVARIANT_MUTATION=1`.

### `wiring.yaml` (Declarative Topology & Contracts)
* **Status:** Protected architecture contract.
* Encodes subsystem boundaries, service interfaces, external tool whitelists, and runtime environment contracts.
* If your PR introduces a new dependency, alters component contracts, or expands tool permissions, update `wiring.yaml` to reflect the change. Like `spine.md`, unauthorized mutations to `wiring.yaml` trigger Gate C pre-commit and CI verification blocks.

### `roadmap.md` (Macro Acceptance Contract)
* Encodes user acceptance criteria (`[INTENT]`) and verified implementation states (`[MEASURED]`).
* Strictly carries **no ephemeral task queue**; active tasks live in `state.md`.

### `state.md` (Dynamic Working Memory)
* Houses the active milestone objective, immediate blockers, and pending test gates (~300 token budget).
* Do not commit local, personal scratchpad tasks to `state.md`. Reset `state.md` to reflect the branch's clean, ready-for-review state. Any PR touching $\ge 40$ lines of code must synchronize `state.md` (enforced by Gate S).

### `app_map.md` (Cartography)
* If you introduce, rename, or delete a source file, update `app_map.md` with the new physical path and a concise description of module responsibility.
* Do not list transient or untracked directories (`node_modules`, `__pycache__`, `.venv`).

### `decisions.md` (Negative Memory)
* If your PR explores an architectural fork that was tested and rejected, document it.
* Every entry must conform to the 3-line format:
  * **The Claim:** What was attempted.
  * **The Measurement:** Concrete numerical cost or regression delta.
  * **What Would Reopen It:** Explicit condition under which the trade-off should be re-evaluated.

### `evals.md` (Positive Ground Truth)
* Any new test asset added to `/tests/fixtures` must be registered in the Golden Reference table.
* Compute and record the fixture's SHA-256 hash (or run `sdcs audit --update-pending`).
* Run `python audit_evals_corpus.py` to confirm zero hash collisions or near-duplicate fixtures.

### `sessions/*.md` (Historical Shift Handoffs)
* Immutable post-shift engineering handoffs. Do not commit temporary agent session scratchpads unless documenting a persistent multi-day research spike.
* Never ingest past session files into Turn 1 system boot context.

---

## 4. Pull Request Lifecycle

1. **Fork and Branch:** Create a focused feature branch from `main`:
   ```bash
   git checkout -b feat/evals-sha-auto-repair
   ```

2. **Implement & Test:** Write clean, minimal code conforming to Python 3.10+ standards.
3. **Audit Ground Truth:** Verify that benchmark integrity passes:
   ```bash
   python audit_evals_corpus.py
   ```

4. **Format Commits:** Use conventional commit messages:
   * `feat(evals): add automated fixture collision reporter`
   * `fix(init): handle missing .env files gracefully`
   * `docs(spec): bump SPEC-001 to v1.3.0`

5. **Open PR:** Provide a brief summary of what was changed, the test results, and any relevant ADR numbers from `decisions.md`.
