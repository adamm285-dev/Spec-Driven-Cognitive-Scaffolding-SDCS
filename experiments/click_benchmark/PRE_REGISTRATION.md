# Pre-Registration: Pallets/Click A/B Comparative Benchmark Study
<!-- SPEC-001 Verification Standard | Status: PRE-REGISTERED (NOT YET RUN) -->

**Date:** 2026-09-22  
**Status:** **NOT YET RUN** (Pre-registered protocol locked; awaiting live agent pilot execution).  
**Target Repository:** `pallets/click` (`https://github.com/pallets/click.git`)  
**Base Commit Baseline:** `8b44edf` / `047adef` (pre-August 2026 stable baseline)  
**Agent Model:** `gemini-2.5-pro` (or reviewer-selected model at $T = 0.0$)  
**Matrix:** 1 Repository $\times$ 5 Tasks $\times$ 2 Arms $\times$ 3 Runs = **30 Total Evaluated Runs**  

> **Methodological Invariant:** Per SPEC-001 rules, synthetic or simulated token/turn numbers are strictly forbidden. Telemetry must be populated exclusively from real autonomous agent sessions, raw transcripts, and live API usage fields.

---

## 1. Experimental Arms

### Arm A: Unstructured Domain Baseline (`notes.md`)
- Single flat `notes.md` file at repository root.
- Mechanically compiled from Arm B's 7 pillars via `compile_notes.py` to guarantee 100% factual and informational parity.
- Stripped of SDCS operational tags, Gate T AST declarations, HUD endpoints, and Gate S working memory budgets.
- Prompt instructs agent to read `notes.md` and solve the problem statement.

### Arm B: Spec-Driven Cognitive Scaffolding (SDCS 7 Pillars)
- Standard SDCS repository scaffolding:
  - `spine.md` (Constitutional Invariants)
  - `wiring.yaml` (Subsystem Boundaries & Gate T Topology)
  - `roadmap.md` (Teleological North Star: Intent vs. Measured)
  - `state.md` (Dynamic Working Blackboard $\le 350$ tokens)
  - `app_map.md` (Repository Cartography)
  - `decisions.md` (Negative Episodic Memory / Graveyard)
  - `evals.md` (Positive Ground Truth & Fixture Locks)
  - `AGENTS.md` (Operational instructions for 4-phase execution cycle and Turn 1 boot hydration)
- Prompt instructs agent to follow `AGENTS.md`, hydrate Turn 1 state, verify Gate T boundaries, and maintain `state.md`.

---

## 2. Benchmark Tasks (August – September 2026)

All 5 tasks postdate the July 2026 model training cutoff, have been verified fail-to-pass on disk, and determinism has been verified across 3 consecutive runs.

| Task ID | Fix Commit | Subsystem | Nature of Bug | Test Status (Base $\to$ Fix) |
| :--- | :--- | :--- | :--- | :--- |
| `click-3571-progressbar-pos` | `f316d5c` | `src/click/_termui_impl.py` | `progressbar` freezes below total when `update_min_steps` does not divide length. | 6 FAIL $\to$ 12 PASS |
| `click-3731-pager-windows` | `1f9cd54` | `src/click/_termui_impl.py` | Tempfile pager unlinks open handle on error, raising `PermissionError: [WinError 32]` on Windows. | 1 FAIL $\to$ 1 PASS |
| `click-3805-sentinel-pickle` | `f58ca3e` | `src/click/_utils.py` | `Sentinel` members & `Parameter` fail `copy()`, `deepcopy()`, `pickle` with `ValueError`. | 3 FAIL $\to$ 10 PASS |
| `click-3802-keyboard-race` | `fc518e4` | `src/click/core.py` | `KeyboardInterrupt` during `Command.main()` abort/error output escapes unhandled as traceback. | 5 FAIL $\to$ 8 PASS |
| `click-3865-shorthelp-abbr` | `f67c2bb` | `src/click/utils.py` | `_make_default_short_help` truncates at abbreviation periods (`vs.`, `e.g.`) inside first sentence. | 6 FAIL $\to$ 36 PASS |

---

## 3. Pre-Registered Metrics

For each run $i \in \{1, 2, 3\}$, task $t \in \{1, \dots, 5\}$, and arm $\alpha \in \{A, B\}$:

1. **Task Resolution ($R_{\text{solve}} \in \{0, 1\}$):**
   $R_{\text{solve}} = 1$ if and only if:
   - The task's reproduction test suite passes 100%.
   - The full Click test suite (`pytest -o pythonpath=src`) has zero regressions ($K_{\text{regress}} = 0$).
   Otherwise $0$.

2. **Total Tokens Consumed ($C_{\text{tokens}}$):**
   Sum of input tokens and output tokens across all agent turns in the run.

3. **Turn Count ($N_{\text{turns}}$):**
   Total agent interaction turns to completion or timeout (max 10 turns).

4. **Test Regressions ($K_{\text{regress}}$):**
   Number of previously passing tests broken during candidate edits.

5. **Dead-End Re-proposal Count ($D_{\text{deadends}}$):**
   Count of times an edit or rejected hypothesis from negative memory was re-attempted.

6. **Measured Test Execution Time ($T_{\text{test\_ms}}$):**
   Wall-clock execution time measured directly with `time.perf_counter()` in milliseconds.

---

## 4. Pre-Registered Win Condition

Let $\bar{M}_A$ and $\bar{M}_B$ denote the sample means of metric $M$ across the 3 runs, and let $s_A^2$ and $s_B^2$ be their sample variances:
$$s_{\alpha}^2 = \frac{1}{N-1} \sum_{i=1}^N (M_{\alpha, i} - \bar{M}_{\alpha})^2 \quad (N = 3)$$

The pooled sample standard deviation is:
$$s_{\text{pooled}} = \sqrt{\frac{s_A^2 + s_B^2}{2}}$$

**SDCS (Arm B) achieves a pre-registered victory over Unstructured Notes (Arm A) if and only if:**
1. **Solve Rate Non-Inferiority:**
   $$\bar{R}_{\text{solve}}(B) \ge \bar{R}_{\text{solve}}(A)$$
2. **Statistical Separation Exceeding 3-Run Variance:**
   The performance delta $\Delta = |\bar{M}_B - \bar{M}_A|$ strictly exceeds $s_{\text{pooled}}$:
   $$\Delta > s_{\text{pooled}}$$
   in at least one core efficiency or quality dimension:
   - **Task Resolution:** $\bar{R}_{\text{solve}}(B) - \bar{R}_{\text{solve}}(A) > s_{\text{pooled}}$
   - **Token Efficiency:** $\bar{C}_{\text{tokens}}(A) - \bar{C}_{\text{tokens}}(B) > s_{\text{pooled}}$
   - **Turn Efficiency:** $\bar{N}_{\text{turns}}(A) - \bar{N}_{\text{turns}}(B) > s_{\text{pooled}}$
   - **Regression Suppression:** $\bar{K}_{\text{regress}}(A) - \bar{K}_{\text{regress}}(B) > s_{\text{pooled}}$ with $\bar{K}_{\text{regress}}(B) = 0$.

---

## 5. Methodological Invariants
- **No Fabricated Telemetry:** All test runtimes and test statuses are executed directly against the local Click codebase.
- **Blinded Pillars:** Arm B's pillars contain zero mentions of the 5 bug tasks.
- **Mechanical Parity:** Arm A's `notes.md` is compiled mechanically from Arm B's pillars.
- **Pre-Registration Lock:** This document is committed to disk before the first benchmark run commences.
