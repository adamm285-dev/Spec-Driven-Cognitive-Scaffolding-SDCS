# Empirical Evidence & Benchmark Telemetry (SDCS v1.8.1)
<!-- SPEC-001 Verification Standard | Status: EMPIRICALLY MEASURED -->

This document records physical telemetry, AST structural measurements, and reproducible gate audits gathered directly from executing commands across the SDCS codebase and reference production codebases.

> **Methodological Invariant:** Every figure below is generated dynamically by `scripts/generate_evidence.py` executing live CLI commands, AST outline transforms, and headless test runners. No static fabricated strings, unmeasured comparisons, or ungrounded baseline claims are permitted.

---

## 1. Executive Summary: Measured Telemetry

- **Repository Version:** SDCS `e08a789 (dirty)`
- **Active Tokenizer:** tiktoken (`cl100k_base`)
- **Single-Pass Hydration Payload (Standard):** 4081 tokens (312 lines across 5 pillars in 1 atomic read)
- **Single-Pass Hydration Payload (Lite):** 566 tokens (34 lines across 2 pillars in 1 atomic read)
- **AST Skeletal Compactor (`sdcs slice`):** 77.8% – 98.9% token reduction across codebase modules
- **Working Blackboard State (`state.md`):** 254 tokens (strictly within <= 350 token working memory budget)
- **Gate Q Recall on Evasive Corpus:** 11/11 hollow tests caught (100.0%), 15/15 sound controls passed (100.0%)
- **Circuit Breaker False Block Prevention:** 0 blocking trips on progressive TDD alternating rhythms and land-revert-reland workflows (3/3 reviewer tests passed)
- **Circuit Breaker Thrash Detection:** Hard block fired on repeated identical diff reversals (>= 3 reversals)
- **Floorsmith History Replay (544 commits):** 0 of 538 windows tripped (0.0% false block rate)
- **Floorsmith Reversal Chain Reach:** 5/5 known reversal links detected across 6-commit sliding window
- **Floorsmith Decisions Reopen Protection:** 20/34 (58.8%) rejections carrying active reopen conditions preserved
- **Floorsmith Decisions Opt-In Archiving:** 0 superseded entries eligible for archiving (100.0% standing rejection preservation)
- **Click Comparative Benchmark:** Protocol pre-registered across 5 validated post-cutoff tasks; marked as NOT YET RUN (awaiting live agent pilot execution).

---

## 2. Benchmark 1: Turn-1 Boot Context Compression (`sdcs hydrate`)

SDCS compiles a single-pass, pre-budgeted context stream directly into memory via `sdcs hydrate --profile <profile>`.
Token counts are computed using tiktoken (`cl100k_base`).

### Standard Profile Telemetry (`sdcs hydrate --profile standard`)

| Pillar File | Role | Lines on Disk | Measured Tokens |
| :--- | :--- | :--- | :--- |
| `spine.md` | Pillar 1: Invariant Spine | 20 lines | 312 tokens |
| `roadmap.md` | Pillar 3: Teleological Roadmap | 14 lines | 979 tokens |
| `app_map.md` | Pillar 5: Repository Cartography | 213 lines | 1407 tokens |
| `decisions.md` | Pillar 6: Negative Memory | 51 lines | 1129 tokens |
| `state.md` | Pillar 4: Working Memory State | 14 lines | 254 tokens |
| **TOTAL COMPILED PAYLOAD** | **5 Pillars Combined** | **312 lines** | **4081 tokens** |

### Lite Profile Telemetry (`sdcs hydrate --profile lite`)
- Combined Payload: **566 tokens** (34 lines across `spine.md` + `state.md`).

---

## 3. Benchmark 2: AST Structural Outlining (`sdcs slice`)

`sdcs slice` executes a deterministic AST transformation replacing function/method execution bodies with `...` while retaining classes, signatures, type annotations, and docstrings.
Token counts measured using tiktoken (`cl100k_base`).

### Measured Compression across Repository Modules

| Source File | Raw Lines | Raw Tokens | Sliced Lines | Sliced Tokens | Token Compression |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `src/sdcs/cli.py` | 1100 lines | 7662 tokens | 14 lines | 85 tokens | **98.9%** |
| `src/sdcs/verifier/quality.py` | 612 lines | 5084 tokens | 67 lines | 525 tokens | **89.7%** |
| `src/sdcs/decay.py` | 366 lines | 3264 tokens | 53 lines | 515 tokens | **84.2%** |
| `src/sdcs/verifier/cycles.py` | 417 lines | 3649 tokens | 65 lines | 740 tokens | **79.7%** |
| `src/sdcs/skeleton.py` | 288 lines | 2386 tokens | 71 lines | 530 tokens | **77.8%** |

---

## 4. Benchmark 3: Working Memory State Budget (`state.md` / Gate S)

- **Active Working Blackboard (`state.md`):**
  - Measured Token Count: **254 tokens**
  - Maximum Allowed Budget: **350 tokens** (enforced by Gate S)
  - Verification Command: `python -m sdcs.cli verify --state`
- **Compaction Recovery Guarantee:**
  - Post-compaction agents inspect `state.md` directly on Turn 1.
  - The `## Immediate Next Action (Post-Compact)` block provides direct resumption without whole-repository discovery.

---

## 5. Benchmark 4: Gate Q Accuracy & Anti-Mock AST Auditor

Gate Q inspects test files for hollow patterns (`assert True`, swallowed exceptions, mock-only abuse, assertless execution) while protecting sound contracts.

### 1. Reviewer Hollow Test Corpus (`tests/test_reviewer_hollow_corpus.py`)

Evaluated against the independent benchmark corpus (`tests/fixtures/reviewer_hollow_corpus.py.txt`):

| Population Group | Tests in Group | Gate Q Result | Catch / Pass Rate |
| :--- | :--- | :--- | :--- |
| **Hollow Tests (`test_H*`)** | 11 tests | 11 flagged | **100.0% Catch Rate** |
| **Sound Controls (`test_C*`)** | 15 tests | 15 passed clean | **100.0% Clean Pass Rate** |
| **Total Evaluated Items** | 27 items | 27 / 27 tests passed | **100.0% Complete Separation** |

### 2. Production Suite Audit (Floorsmith Estimator: 2,161 test functions across 144 test files)

- Total Test Functions Evaluated: **2,161** across 144 test files
- Sound Tests Falsely Flagged: **0**
- Assertless Tests Flagged: **1** (`test_parse_blueprints.py:99 [Q2_ASSERTLESS_TEST] test_log_extraction_metrics_does_not_raise` - assertless smoke test lacking `# sdcs: no-raise` pragma)
- Contract-based assertions testing non-None returns (`assertIsNotNone`), determinism tests comparing identical calls (`assertEqual(f(), f())`), and mock tests where real code executes without calling the mocked dependency pass clean without false flags.

---

## 6. Benchmark 5: Circuit Breaker History Replay & Repeated Reversal Blocking

The circuit breaker monitors commit diffs to detect unproductive thrashing loops while allowing healthy TDD commit rhythms.

### 1. Synthetic Discrimination Cases (`tests/test_reviewer_breaker_cases.py`)

| Test Case | History Pattern | Circuit Breaker Action | Status |
| :--- | :--- | :--- | :--- |
| **TDD Rhythm** | 5 commits alternating code and tests (all forward diffs) | 0 blocking violations | **PASSED (Allowed)** |
| **Land-Revert-Reland** | 2 identical reversals (CI flake backing out and relanding) | 0 blocking violations (advisory only) | **PASSED (Allowed)** |
| **Repeated Thrash** | Same block added and removed 5 times in a row (>= 3 reversals) | 1 blocking violation (repeated identical reversal) | **PASSED (Hard Blocked)** |

### 2. Whole-History Replay on Floorsmith (544 commits, window 6)

- Total Sliding Windows Replayed: **538**
- Blocking Windows Tripped: **0 of 538** (0.0% false block rate)
- Distinct Advisory Reversals Detected: **16** (all intentional withdrawals or refined restores documented in git commit history)
- Known Reversal Chain Reach: **5 of 5 links detected** across sliding window reach
  - `c410d7a -> 7429698` (stated-wall envelope withdrawal, 3 commits apart): Detected (`is_diff_reversal=True`)
  - `7429698 -> cd3eabb` (stated-wall envelope restoration with guards, 2 commits apart): Detected (`is_diff_reversal=True`)
  - `19f0ac2 -> e406648` (leaf rule withdrawal, 1 commit apart): Detected (`is_diff_reversal=True`)
  - `e406648 -> 4d10d4c` (leaf rule restoration with doors, 1 commit apart): Detected (`is_diff_reversal=True`)
  - `ee9f58a -> b0ae632` (tab8 network moved from PNG to viewer, 2 commits apart): Detected (`is_diff_reversal=True`)

---

## 7. Benchmark 6: Decisions Decay Engine & Reopen Protection

The decisions decay engine inspects negative memory entries (`decisions.md`) to balance active working memory budget with permanent architectural protection.

- **Preservation Invariant:** Entries carrying explicit reopen conditions (`WHAT WOULD REOPEN IT:` / `*Reopens if:*`) are classified as foundational negative memory and permanently immune to FIFO pruning.
- **Opt-In Archival:** Standing active rejections are never pruned regardless of count. Archiving is strictly opt-in (`Status: SUPERSEDED`, `RESOLVED`, or `ARCHIVED`).

- **Floorsmith Decisions Ledger (`docs/map/decisions.md`):**
  - Total Rejection Entries Parsed: **34**
  - Entries Protected by Reopen Conditions: **20 of 34 (58.8%)**
  - Superseded Entries Eligible for Archiving: **0**
  - Standing Entries Preserved on Audit: **34 of 34 (100.0%)**

---

## 8. Benchmark 7: Gate C-Cache Static Prefix Invariance

- **Verification Check:** `python -m sdcs.cli verify --cache-invariance`
- **Prefix Audited:** `spine.md`, `wiring.yaml`, and system prompt templates.
- **Audit Result:** 100% static invariance (0 dynamic ISO timestamps, turn counters, or process IDs in prompt prefix).

---

## 9. Benchmark 8: Pallets/Click Comparative Experiment (Scaffolding vs. Unstructured Notes)

**Status:** NOT YET RUN (Pre-registered Protocol Locked; Awaiting Live Agent Pilot).

An empirical comparative study protocol has been designed and pre-registered to evaluate whether Spec-Driven Cognitive Scaffolding (SDCS 7 Pillars) provides measurable advantages over an unstructured domain knowledge baseline (`notes.md`) in a production codebase (`pallets/click`).

### Study Design & Controls
- **Specification:** `experiments/click_benchmark/PRE_REGISTRATION.md`
- **Matrix:** 1 Repo (`pallets/click`) x 5 Tasks x 2 Arms (Arm A: `notes.md`, Arm B: SDCS 7 Pillars) x 3 Runs = **30 Total Runs**
- **Validated Tasks:** 5 real bug fixes committed between August 15 and September 11, 2026, postdating model training cutoff. All 5 are verified fail-to-pass on disk and confirmed deterministic across 3 consecutive runs.
- **Blinded Scaffolding:** SDCS pillars for Click authored strictly from pre-August 2026 repository with 0 task keyword leaks.
- **Mechanical Parity:** Arm A's `notes.md` compiled mechanically from Arm B's pillars to guarantee identical factual repository knowledge.
- **Execution Requirements for Valid Run:** Real autonomous agent session per run, raw transcripts recorded, token counts extracted from LLM API usage fields, patches authored strictly by the model (harness never writes to `src/`), and test runtimes measured directly via `time.perf_counter()`.

> **Methodological Lock:** Synthetic numbers are strictly prohibited. Results will be populated exclusively from real agent run transcripts upon execution of the pilot by the reviewer/external runner.

---

## 10. How to Reproduce These Measurements Locally

To regenerate this document and re-verify every measurement directly from local disk execution:

```bash
# 1. Run the evidence generator (executes all benchmarks and updates EVIDENCE.md)
python scripts/generate_evidence.py

# 2. Verify all 7 Cognitive Pillars & Toolchain Health
python -m sdcs.cli doctor

# 3. Verify Positive Ground Truth & Fixture Hash Locks
python -m sdcs.cli audit

# 4. Verify All Kinetic Gates (Topology, State Budget, Cycles, Quality, Cache)
python -m sdcs.cli verify --all

# 5. Run the Reviewer Hollow Test Corpus
pytest tests/test_reviewer_hollow_corpus.py

# 6. Run the Reviewer Circuit Breaker Discrimination Cases
pytest tests/test_reviewer_breaker_cases.py

# 7. Run the Reviewer Decisions Decay Cases
pytest tests/test_reviewer_decay_cases.py

# 8. Run the Full Test Suite
pytest
```
