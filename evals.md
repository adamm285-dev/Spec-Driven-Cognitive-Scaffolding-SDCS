# Positive Episodic Memory (The Baseline Scorecard)
<!-- SPEC-001 Pillar 7 | Positive Ground Truth | Cryptographically Locked (SHA-256) -->

## Verified Empirical Fixture Scorecard

| Fixture ID | Path | SHA-256 Hash | Status |
| :--- | :--- | :--- | :--- |
| `EVAL-QUAL-001` | `tests/test_quality.py` | `030e1aa4025eb7d9d534fb0871a180060d30890e1799ab55aca2db598895f0ee` | active |
| `EVAL-CYCL-001` | `tests/test_cycles.py` | `a99a241bd3cb33fe586860d4aaaf4ec57f8191296730242ebe5d26477d50c1c8` | active |
| `EVAL-DECA-001` | `tests/test_decay.py` | `4e751b357ab32e7339266741266f4c2e307987667a86b850af92aa49d2a2fec5` | active |
| `EVAL-TOPO-001` | `tests/test_topology.py` | `78ac900e29d9785b7ae1de0c8c7c67ca4f2acd1a2dcb89ece301416412217c44` | active |
| `EVAL-CACH-001` | `tests/test_cache.py` | `0d0ae7a4ec6bdb76eb63330fd36833de05cd7db149fc13bccb904fdb2f1fbc3e` | active |
| `EVAL-AUDT-001` | `tests/test_audit.py` | `17b79de0d095561cda570b246d2cb8912bbe12be0c66aca0771aa8ece9773b92` | active |

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
