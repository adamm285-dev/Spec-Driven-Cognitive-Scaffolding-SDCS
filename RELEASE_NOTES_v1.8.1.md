# Release Notes: Spec-Driven Cognitive Scaffolding (SDCS) v1.8.1

> **Release Tag**: `v1.8.1`  
> **Date**: September 22, 2026  
> **Conforms To**: SPEC-001 v1.8.1  
> **PyPI**: `pip install --upgrade sdcs`  
> **Test Telemetry**: 128/128 Passed (100% Green in Pytest across 24 suites)  

---

## 🎯 Empirical Grounding & The Empty-Band Verification Standard

SDCS v1.8.1 delivers comprehensive empirical hardening across kinetic gates, test harnesses, and behavioral scaffolding. Motivated by rigorous external agent evaluation against mature production codebases (544 commits, 2,161 test functions), v1.8.1 introduces the **Empty-Band Method**: enforcing that every kinetic enforcement gate maintains complete separation between 0.0% false positives on mature suites and 100.0% true positive catch rates on hollow or oscillating anti-patterns.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                 SDCS v1.8.1 EMPIRICAL RECTIFICATION & EMPTY-BAND            │
├───────────────────────────────────┬─────────────────────────────────────────┤
│ 1. Gate Q AST Auditor             │ 0 / 2,161 false flags on unittest (0.0%)│
│ 2. Semantic Circuit Breaker       │ 0 false trips on 544 progressive commits│
│ 3. Status-Aware Decisions Decay   │ 100% preservation of foundational memory│
│ 4. Reality-Verifying Scaffolding  │ Targeted search unblocked; calm rules   │
│ 5. Empirical Evidence Suite       │ EVIDENCE.md benchmarks & reproduction   │
└───────────────────────────────────┴─────────────────────────────────────────┘
```

---

## 🚀 Key Highlights in v1.8.1

### 1. 🧪 Gate Q: Full `unittest.TestCase` & Helper Call Inspection
- **The Blind Spot:** Gate Q previously inspected only AST `assert` statements (`ast.Assert`), causing 1,569 false flags on 2,161 production tests using `unittest.TestCase` method calls (`self.assertEqual`, `self.assertTrue`, etc.).
- **Multi-Pass AST Propagation:**
  - Pass 1: Scans test files to map intra-file helper methods containing real assertions (e.g., `self._check(...)`, `_assert_pair(...)`).
  - Pass 2: Evaluates tests recognizing `self.assert*`, third-party assertions (`np.testing.assert_*`, `mock.assert_called_*`), custom helper calls, and context managers (`self.assertRaises`, `pytest.raises`).
- **Pragma & Intent Handling:** Recognizes `# sdcs: no-raise` / `# pragma: no-raise` and `does_not_raise` context managers for tests designed to verify lack of exceptions.
- **Trivial Assertion Logic:** A test is now flagged as trivial only if *all* its assertions are trivial (mixed assertions with `assert x is not None` plus `self.assertEqual(...)` are recognized as substantive).
- **Result:** **0 / 2,161 false positives (0.0%)** on mature production reference suites.

---

### 2. 🔄 Circuit Breaker: Semantic Diff Inversion (`is_diff_reversal`)
- **The Blind Spot:** Previous cycle detection flagged consecutive commits touching the same file ($\ge 3$ commits), producing 24 false alarms on standard iterative feature development.
- **Semantic Diff Inversion:** Analyzes git commit diffs for complementary line additions and deletions ($diff(N) \approx -diff(N-1)$) and recognizes commit subjects containing `Revert ...` matching earlier commit topics.
- **Result:** **0 false trips** across 544 progressive commits; **100% true-positive detection** on genuine ship-then-revert commits (such as tiled OCR commit `0f07c0b`).

---

### 3. 🧠 Decisions Decay: Status-Aware Negative Memory Protection
- **The Blind Spot:** Fixed-cap FIFO decay sliced rejections once total entries exceeded an arbitrary ceiling, inadvertently purging standing architectural rejections and dead ends recorded early in a project.
- **Opt-In Archival:** Standing active rejections (both with and without reopen lines) are permanently preserved in `decisions.md`. Archiving is strictly opt-in (`Status: SUPERSEDED`, `RESOLVED`, or `ARCHIVED`).
- **Result:** Institutional memory remains permanently protected against cyclical regression loops.

---

### 4. 📊 Empirical Evidence Suite (`EVIDENCE.md`)
- Published **[EVIDENCE.md](EVIDENCE.md)** containing live-computed benchmark telemetry:
  - Single-pass turn-1 boot hydration: **3,299 tokens** standard (5 pillars) / **650 tokens** lite (2 pillars) via `sdcs hydrate`.
  - AST interface inspection token reduction: **78.4% – 98.9%** token compression via `sdcs slice`.
  - Post-compact context recovery: **1 turn (<= 350 tokens)** via `state.md`.
  - Repeated hypothesis re-attempts: **0** via `decisions.md` and circuit breaker semantic diff reversal audits.
  - Empty-Band Scorecard formally locked in `evals.md`.
- Includes reproducible 60-second audit instructions for both agents and human developers.

---

### 5. 🛡️ Scaffolding Self-Dogfooding & Calmed Invariants
- The SDCS framework root repository now fully dogfoods all 7 cognitive pillars:
  - `spine.md` (Constitutional Invariants)
  - `wiring.yaml` (Subsystem Mesh & Gate T Boundaries)
  - `roadmap.md` (Teleological North Star: Intent vs. Measured)
  - `state.md` (Dynamic Working Blackboard $\le 350$ tokens)
  - `app_map.md` (Repository Cartography)
  - `decisions.md` (Episodic Negative Memory & Graveyard)
  - `evals.md` (Cryptographically Locked Positive Ground Truth)
- `sdcs doctor` achieves **100% PASS** (0 failures, 0 warnings across toolchains, pillars, and hooks).
- Refactored `AGENTS.md` and `SPEC-001.md`: softened shouting language, replaced whole-repo grep bans with reality-verifying guidelines (`app_map.md` first, then targeted search to verify disk truth), and added prerequisite checks to fast-resume.

---

## 📦 Upgrading to v1.8.1

```bash
# Upgrade via pip
pip install --upgrade sdcs

# Verify system health across all 7 pillars
sdcs doctor

# Verify positive ground truth fixtures
sdcs audit

# Run kinetic gate suite
sdcs verify --all
```
