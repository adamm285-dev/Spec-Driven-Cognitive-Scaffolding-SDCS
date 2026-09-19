# Changelog

All notable changes to Spec-Driven Cognitive Scaffolding (SDCS) and the SPEC-001 specification will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.2.0] - 2026-09-19

### Added
- **Pillar 7: `roadmap.md` (Macro Acceptance Contract):** Encodes the North Star acceptance contract directly separating human `[INTENT]` from empirical `[MEASURED]` reality. Strictly enforces that the roadmap carries NO ephemeral task queue (which belongs exclusively in `state.md`).
- **Authoring Protocol (`prompts/grillme.md` & `sdcs grill`):** Added the `/grillme` Adversarial Spec Elicitation Protocol to interrogate human stakeholders and harden requirements into quantifiable `[INTENT]` contracts before code generation. Scaffolded automatically and callable via `sdcs grill` / `python sdcs_init.py --grill`.
- **Presentation Slide Deck Integration:** Embedded all 10 presentation slides into `README.md` with fully refreshed 7-pillar graphics (`media/slides/slide_03.png`).
- **Architectural Lineage & Theoretical Foundations:** Formalized direct citations to classical computer science paradigms (Blackboard Pattern, Design by Contract, Virtual Memory Page Tables, Optative vs Indicative Requirements, Cybernetic Feedback, and Cryptographic Diversity Guards).
- **Standard Python Packaging (`pyproject.toml`):** Shipped zero-dependency package setup with standard CLI entry points (`sdcs`, `sdcs-init`, `sdcs-audit`).
- **Automated Regression Suite (`tests/`):** 9 comprehensive unit tests covering scaffolding, SHA-256 calculation, duplicate fixture detection, and CLI invocation.
- **GitHub Governance & Templates:** Added `.github/ISSUE_TEMPLATE/adr_rejection.md`, `.github/ISSUE_TEMPLATE/feature_intent.md`, and `.github/pull_request_template.md`.
- **GitHub Actions CI Workflow:** Added `.github/workflows/verify-pr.yml` enforcing linting (`ruff`, `black`), static type checking (`mypy`), `pytest`, and `audit_evals_corpus.py` on PRs.

---

## [1.1.0] - 2026-09-19: Deterministic Ground Truth & Flight Recorder Protocol

Spec-Driven Cognitive Scaffolding (SPEC-001 v1.1.0) transitions autonomous coding agents from probabilistic "prompt-and-pray" loops into deterministic systems with externalized memory, constitutional invariants, and cryptographic test verification.

### What's New in v1.1.0
- **Pillar 6: `evals.md` (Empirical Standing):** Introduced positive episodic memory as the direct counterpart to `decisions.md`. Establishes empirical baselines and anchors benchmark results to commit hashes and physical test fixtures.
- **`audit_evals_corpus.py` Auditor:** Shipped an automated verification tool that validates fixture paths and calculates SHA-256 digests across all declared benchmarks. Eliminates the "Phantom Corpus" failure mode by detecting byte-identical fixtures masquerading under different filenames.
- **The Flight Recorder Protocol:** Formalized the strict architectural boundary between `state.md` (the volatile whiteboard read on boot) and `sessions/*.md` (discrete, write-once shift handoff logs strictly forbidden from boot ingestion).
- **Full Scaffolding Engine (`sdcs_init.py`):** Automated generation of `spine.md`, `wiring.yaml`, `app_map.md`, `state.md`, `decisions.md`, `evals.md`, `AGENTS.md`, and `sessions/template.md`.
- **Negative Memory Schema:** Enforced the mandatory 3-part rejection schema in `decisions.md` (The Claim $\rightarrow$ The Measurement $\rightarrow$ What Would Reopen It) to stop multi-turn regression loops before tokens are burned.

### Quickstart
Initialize the scaffold into any existing repository:
```bash
python sdcs_init.py
```

Audit test fixture integrity and detect duplicate corpus hashes:
```bash
python audit_evals_corpus.py
```

Read the complete formal specification in [`SPEC-001.md`](SPEC-001.md).

**Author:** Adam Murphy  
**License:** [MIT](LICENSE)
