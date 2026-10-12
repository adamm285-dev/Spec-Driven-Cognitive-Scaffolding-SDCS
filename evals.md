# Positive Episodic Memory (The Baseline Scorecard)
<!-- SPEC-001 Pillar 7 | Positive Ground Truth | Cryptographically Locked (SHA-256) -->

## Verified Empirical Fixture Scorecard

| Fixture ID | Path | SHA-256 Hash | Status |
| :--- | :--- | :--- | :--- |
| `EVAL-QUAL-001` | `tests/test_quality.py` | `8b905e5a90868cf692db03c518c403f04e64e8ac42fd6585e230edc634908458` | active |
| `EVAL-CYCL-001` | `tests/test_cycles.py` | `d4b737c0c77e449bf04a1a8fbf32e9277005054761a02bf683c7f930f2b93278` | active |
| `EVAL-DECA-001` | `tests/test_decay.py` | `322fd2b729b770a8a31aade87ba33dc79dcce866ab659fd6a11df6ee79c6a18b` | active |
| `EVAL-TOPO-001` | `tests/test_topology.py` | `5ab967d4dc39efcad92e2212c2426bc3e903aaa2b6d9d25b6ad620cc5dcdc57d` | active |
| `EVAL-CACH-001` | `tests/test_cache.py` | `80be1f11522173bd756e94da9fee1e2a4e4ce83504779f2cbcab0b43a8061e7e` | active |
| `EVAL-AUDT-001` | `tests/test_audit.py` | `bb738ac70bedd01e78a27ab8bab9b55007007ba4625d721cbced3964f57e080d` | active |

---

## The Empty-Band Measurement Scorecard

Conforming to SPEC-001 §7.5 (The Empty-Band Kinetic Gate Verification Standard).
Gates are tested against two distinct populations to prove precision before entering strict mode:

### 1. Gate Q (Test Quality & Anti-Mock AST Auditor)
* **Population A (Framework & Mature Test Suites):**
  - SDCS Framework Test Suite (236 test functions): **0 flagged (0.0% false-positive rate)**
  - Sound Control Corpus (`tests/fixtures/reviewer_hollow_corpus.py.txt`): **15 / 15 clean pass (0.0% false-positive rate)**
* **Population B (Seeded Hollow / Evasive Corpus):**
  - Trivial assertions (`assert True`, `self.assertTrue(True)`, `self.assertEqual(1, 1)`): **100% intercepted**
  - Swallowed exceptions (`try ... except Exception: pass`): **100% intercepted**
  - Assertless test functions without no-raise pragma: **100% intercepted**
  - Hollow mock abuse (3+ mocks with 0 substantive execution): **100% intercepted**
* **The Empty Band:** **100.0%** (0.0% false-positive rate vs. 100.0% true-positive catch rate).

### 2. Circuit Breaker (Semantic Thrashing & Diff Inversion)
* **Population A (Iterative Progressive Commits & TDD Rhythms):**
  - Progressive Feature Development & Alternating Code/Test Commits: **0 false trips**
  - Land-Revert-Reland Development Workflows: **0 false trips**
* **Population B (Ship-then-Revert Oscillation & Thrashing):**
  - Repeated Diff Reversals ($\ge 3$ reversals on identical blocks): **TRIPPED (100% true-positive recall)**
* **The Empty Band:** Complete separation between progressive feature commits and semantic diff reversals.
