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
* **THE MEASUREMENT:** Across complex production repositories, naive FIFO slicing destroyed the oldest foundational architectural constraints (e.g. database concurrency locks, security boundaries), triggering amnesia and regression.
* **WHY REJECTED:** Architectural memory is non-linear; the oldest decisions are often the most foundational axioms.
* **WHAT WOULD REOPEN IT:** None. Pruning must be status-aware and prioritize superseded/resolved entries while protecting foundational entries.

## REJ-003: Naive Same-File Consecutive Commits as Circuit Breaker Thrashing
Status: FOUNDATIONAL
Permanent: true
* **THE CLAIM:** Modifying the same file in 3 consecutive commits indicates an agent is trapped in an unproductive thrashing loop.
* **THE MEASUREMENT:** Across 500+ commits of progressive development, naive consecutive commit counting tripped 24 times on normal development (iterative feature expansion, documentation refinements) with 0 genuine loops.
* **WHY REJECTED:** High false-positive rate (100% false positive on normal commits). Progressive commits must be distinguished from semantic diff reversals ($A \to B \to A$).
* **WHAT WOULD REOPEN IT:** None. Cycle detection must inspect diff inversion rather than punishing file proximity.

## REJ-004: Blind Post-Compact Fast-Resume Without Precondition Verification
Status: FOUNDATIONAL
Permanent: true
* **THE CLAIM:** Forcing an agent to blindly execute `state.md`'s next action without verifying disk reality eliminates turn-1 latency.
* **THE MEASUREMENT:** When underlying files, branches, or environments mutated across compaction boundaries, blind execution led to hallucinated tool calls and compounding regressions.
* **WHY REJECTED:** Execution without spatial awareness produces brittle agent behavior. Fast-resume must quickly verify prerequisites before mutating files.
* **WHAT WOULD REOPEN IT:** A formal deterministic environment guarantee that disk state cannot mutate externally.

## REJ-005: Flagging Sole is-not-None as Trivial Assertion in Gate Q
Status: FOUNDATIONAL
Permanent: true
* **THE CLAIM:** Assertions testing only `assert x is not None` or `self.assertIsNotNone(x)` carry no substantive verification value and should be flagged as hollow tests (`Q1_TRIVIAL_ASSERTION`).
* **THE MEASUREMENT:** Across mature contract-driven test suites, this rule flagged sound contract tests where a non-None return is the explicit contract specification, versus 0 hollow tests caught (0% precision).
* **WHY REJECTED:** In contract-driven software design, verifying that an API returns an object rather than None (e.g. complaint object, spec path, fallback structure) is an intentional and sound contract test. Flagging it produces a 100% false-positive rate on sound contract tests.
* **WHAT WOULD REOPEN IT:** An empirical corpus demonstrating hollow tests that use `is not None` to evade quality gates without being caught by assertless (Q2) or mock (Q4) rules, alongside an AST heuristic that distinguishes contract returns from hollow checks.

## REJ-006: Hard Circuit Breaker Block on File-Set Alternation
Status: FOUNDATIONAL
Permanent: true
* **THE CLAIM:** Commits alternating between two files (e.g. A -> B -> A -> B) represent an unproductive ping-pong oscillation and should be hard blocked.
* **THE MEASUREMENT:** On synthetic commit sequences modeling TDD rhythms (`test_reviewer_breaker_cases.py`), alternating code and test commits (e.g. extending `area.py` then `test_area.py`) tripped the hard block despite 100% forward progress with zero undone lines.
* **WHY REJECTED:** File-set alternation without diff reversals is the healthy, canonical cadence of Test-Driven Development (TDD). Hard blocks must be reserved for repeated identical diff reversals where the same code diff is repeatedly undone and redone.
* **WHAT WOULD REOPEN IT:** None. When git diffs are available, circuit breaker blocking must inspect semantic diff reversals rather than file touch alternation.

## REJ-007: Folding the Product Mock Ledger into Gate Q
Status: FOUNDATIONAL
Permanent: false
* **THE CLAIM:** Gate Q already audits "anti-mock" violations, so checking a product-code mock ledger belongs inside Gate Q.
* **THE MEASUREMENT:** Gate Q's `TestASTVisitor` (`src/sdcs/verifier/quality.py`) inspects Python test functions only. In downstream polyglot application repositories, declared mocks live in non-test product code, and many are partly or wholly in TypeScript or other languages which Gate Q never parses.
* **WHY REJECTED:** Different targets and failure modes: Gate Q rejects hollow tests; the ledger reconciles declared stand-ins in shipping code across languages. Merging them would widen Gate Q's scan to product code and blur its precision guarantees.
* **WHAT WOULD REOPEN IT:** Gate Q gaining a polyglot product-code scan for an unrelated reason, making a shared scanner cheaper than two gates.
