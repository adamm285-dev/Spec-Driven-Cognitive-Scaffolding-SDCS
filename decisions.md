# Negative Episodic Memory (The Graveyard)
<!-- SPEC-001 Pillar 6 | Mutability: APPEND-ONLY | Working Set: <= 15 Entries -->

## REJ-001: Heavy Tree-Sitter / LLM Dependency for Core AST Parsing
Status: FOUNDATIONAL
Permanent: true
* **THE CLAIM:** Using full Tree-Sitter language bindings or LLM inference for code parsing would enable universal semantic understanding across all languages.
* **THE MEASUREMENT:** Incurred 45MB+ binary wheels, C/C++ compilation failures on Windows/ARM, and non-deterministic latency (>500ms).
* **WHY REJECTED:** Violates Constitutional Invariant 2 (Zero Heavy External Dependencies). Built-in Python `ast` and lightweight regex-based skeletal parsing execute in <5ms with 0 external C dependencies.
* **WHAT WOULD REOPEN IT:** Pure-Python zero-dependency universal grammar parser with <10ms execution latency.

## REJ-002: Naive FIFO Chronological Slicing in Decisions Decay
Status: FOUNDATIONAL
Permanent: true
* **THE CLAIM:** Slicing `entries[:excess_count]` automatically keeps decisions.md within a strict token budget.
* **THE MEASUREMENT:** On real production repositories (e.g. Floorsmith), naive FIFO slicing destroyed the oldest foundational architectural constraints (e.g. database concurrency locks, security boundaries), triggering amnesia and regression.
* **WHY REJECTED:** Architectural memory is non-linear; the oldest decisions are often the most foundational axioms.
* **WHAT WOULD REOPEN IT:** None. Pruning must be status-aware and prioritize superseded/resolved entries while protecting foundational entries.

## REJ-003: Naive Same-File Consecutive Commits as Circuit Breaker Thrashing
Status: FOUNDATIONAL
Permanent: true
* **THE CLAIM:** Modifying the same file in 3 consecutive commits indicates an agent is trapped in an unproductive thrashing loop.
* **THE MEASUREMENT:** On Floorsmith's 544 commits, this tripped 24 times on completely normal progressive development (iterative feature expansion in `finish_areas.py`, documentation refinements). 0 were genuine loops.
* **WHY REJECTED:** High false-positive rate (100% false positive on normal commits). Progressive commits must be distinguished from semantic diff reversals ($A \to B \to A$).
* **WHAT WOULD REOPEN IT:** None. Cycle detection must inspect diff inversion rather than punishing file proximity.

## REJ-004: Blind Post-Compact Fast-Resume Without Precondition Verification
Status: FOUNDATIONAL
Permanent: true
* **THE CLAIM:** Forcing an agent to blindly execute `state.md`'s next action without verifying disk reality eliminates turn-1 latency.
* **THE MEASUREMENT:** When underlying files, branches, or environments mutated across compaction boundaries, blind execution led to hallucinated tool calls and compounding regressions.
* **WHY REJECTED:** Execution without spatial awareness produces brittle agent behavior. Fast-resume must quickly verify prerequisites before mutating files.
* **WHAT WOULD REOPEN IT:** A formal deterministic environment guarantee that disk state cannot mutate externally.
