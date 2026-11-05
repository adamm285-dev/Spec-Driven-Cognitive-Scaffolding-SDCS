# Release Notes: Spec-Driven Cognitive Scaffolding (SDCS) v1.9.8

**Released:** 2026-11-01 : **Spec:** SPEC-001 v1.9.8 : **Replaces:** v1.9.7

SDCS v1.9.8 introduces the Dynamic Elastic State Regulation Equation (`compute_elastic_state_budget`), per-bullet density auditing, compaction backlog sentinels, and strict fixed-budget verification controls.

---

## Key Highlights in v1.9.8

### 1. Scope-Elastic Token Regulation Equation (`compute_elastic_state_budget`)
- **Deterministic Working Memory Scaling:** Replaces static token ceilings with an AST-grounded, scope-elastic formula that dynamically scales working memory headroom based on specification complexity:
  $$\text{Budget} = \min\Big(1200, \; 350 + \max(0, N_{\text{active}} - 4) \times 28 + \max(0, N_{\text{pkg}} - 1) \times 25\Big)$$
- **Baseline Allocation:** Standard tasks with $\le 4$ active requirement bullets retain a compact 350-token baseline.
- **Sprint & Multi-Package Headroom:** Expands by $+28$ tokens for each active requirement bullet beyond 4, and $+25$ tokens for each distinct package in multi-package monorepos.
- **Hard Safety Ceiling:** Enforces an absolute maximum cap of 1,200 tokens to ensure working memory never floods downstream model contexts.

### 2. Per-Bullet Density & Compaction Sentinels
- **Density Target Auditing:** Emits `[DENSITY ADVISORY]` notifications when individual active bullets exceed 55 tokens, catching hidden sub-task bundling and prompt pollution early.
- **Compaction Backlog Warnings:** Alerts developers and autonomous loops when more than 5 completed (`- [x]`) requirement items accumulate without compaction, maintaining clean, lightweight handoffs.

### 3. Strict Mode CLI Flag (`--no-elastic`)
- **Fixed-Ceiling Environments:** Adds `--no-elastic` across `sdcs verify --state` and `sdcs check` subcommands to allow teams and CI/CD pipelines to enforce strict, unyielding token budgets when needed.

### 4. Git Hook & Toolchain Synchronization
- **Pre-Commit Enforcement:** Updated `.githooks/pre-commit`, `sdcs_init.py`, and `src/sdcs/init.py` templates to evaluate Gate S through the dynamic elastic equation.
- **Seamless Bootstrap:** Downstream repositories initialized with `sdcs init` automatically receive elastic state verification.

---

## Verification Telemetry

- **Test Suite:** **256/256 unit tests passing** via pytest (including dedicated elastic scaling, density target, and strict CLI test fixtures).
- **Kinetic Gates:** All 7 SDCS gates verified clean via `sdcs check` and `sdcs verify --all`.
- **Zero Em-Dashes:** 100% verified clean across all codebase, template, test, and documentation files.

---

## Upgrading to v1.9.8

```bash
pip install --upgrade sdcs
sdcs check
```
