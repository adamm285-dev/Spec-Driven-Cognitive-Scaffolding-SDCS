# Positive Episodic Memory (The Baseline Scorecard)
<!-- SPEC-001 Pillar 7 | Positive Ground Truth | Cryptographically Locked (SHA-256) -->

## Verified Empirical Fixture Scorecard

| Fixture ID | Path | SHA-256 Hash | Status |
| :--- | :--- | :--- | :--- |
| `EVAL-QUAL-001` | `tests/test_quality.py` | `2f94152ebe2c99851fc92a425cc79d43c3723213e01712cc4fed0881f3ce8da4` | active |
| `EVAL-CYCL-001` | `tests/test_cycles.py` | `f826fd2d5dd2edc7b3d0071d96ec1b64b0ff94fd761efcc9d845c9dcbeb67d76` | active |
| `EVAL-DECA-001` | `tests/test_decay.py` | `dfb1d5eb8d9735f8dc3dcf8aa82f723383bb0eba49503023f47283ca21b2bccd` | active |
| `EVAL-TOPO-001` | `tests/test_topology.py` | `6b44c5d4d84dfa8687457754b9ff4cd2a053119e2268d671232e25526748d423` | active |
| `EVAL-CACH-001` | `tests/test_cache.py` | `07b01facfd722b544c9c41c386f7262127f42f5a7374e4f16fd50bcfe52b5bfa` | active |
| `EVAL-AUDT-001` | `tests/test_audit.py` | `42fdd14023635c86aeb4dea5ee032c296ef920d3e5bb42b2450bce98cef79010` | active |

---

## The Empty-Band Measurement Scorecard

Conforming to SPEC-001 §7.5 (The Empty-Band Kinetic Gate Verification Standard).
Gates are tested against two distinct populations to prove precision before entering strict mode:

### 1. Gate Q (Test Quality & Anti-Mock AST Auditor)
* **Population A (Mature Unittest & Pytest Suites):**
  - Floorsmith Estimator (Commit `813bc95`, 2,161 test functions): **0 / 2,161 flagged (0.0% false-positive rate)**
  - SDCS Framework Suite (128 test functions): **0 / 128 flagged (0.0% false-positive rate)**
* **Population B (Seeded Hollow / Evasive Corpus):**
  - Trivial assertions (`assert True`, `self.assertTrue(True)`, `self.assertEqual(1, 1)`): **100% intercepted**
  - Swallowed exceptions (`try ... except Exception: pass`): **100% intercepted**
  - Assertless test functions without no-raise pragma: **100% intercepted**
  - Hollow mock abuse (3+ mocks with 0 substantive execution): **100% intercepted**
* **The Empty Band:** **100.0%** (0.0% false-positive rate vs. 100.0% true-positive catch rate).

### 2. Circuit Breaker (Semantic Thrashing & Diff Inversion)
* **Population A (Iterative Progressive Commits):**
  - Floorsmith Estimator (544 commits, consecutive same-file feature work on `finish_areas.py`): **0 false trips (down from 24)**
* **Population B (Ship-then-Revert Oscillation):**
  - Floorsmith Estimator (Tiled OCR revert `0f07c0b` on `9457000` / `117ce8c`): **TRIPPED (100% true-positive recall)**
* **The Empty Band:** Complete separation between progressive feature commits and semantic diff reversals.
