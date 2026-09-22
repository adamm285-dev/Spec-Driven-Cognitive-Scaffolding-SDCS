# Acceptance Contract (Roadmap)
<!-- SPEC-001 Pillar 3 | The North Star | Teleological Target -->

## Milestone M-180: Sub-Dime Loop Engineering Suite
* [INTENT]: Deliver sub-dime autonomous development loops with AST skeletons (`sdcs slice`), 0-token formatters (`sdcs repair`), KV-cache invariance (`sdcs verify --cache-invariance`), and governed routing (`sdcs route`).
* [MEASURED]: 100% test pass (119/119 in commit `4146427`); AST compactor achieves 85-92% token compression; Gate C-Cache guarantees 0 prefix jitter; PyPI and GitHub releases published.

## Milestone M-181: Empirical Grounding & Gate False-Positive Elimination
* [INTENT]: Eliminate Gate Q false positives on standard `unittest.TestCase` assertions; eliminate Circuit Breaker false positives on consecutive progressive commits; protect foundational rejections in `sdcs decay`; publish comprehensive `EVIDENCE.md` benchmark suite.
* [MEASURED]: Gate Q updated with ast.Call, helper tracking & pragma support (0/2,161 false positives on Floorsmith); Circuit Breaker upgraded to diff reversal detection (0 false trips on progressive commits, 100% on reverts); sdcs decay upgraded to status-aware retention; 7 pillars dogfooded with 100% pass on sdcs doctor & audit; EVIDENCE.md published with Empty-Band scorecard; 128/128 tests pass cleanly; v1.8.1 packaging verified.
