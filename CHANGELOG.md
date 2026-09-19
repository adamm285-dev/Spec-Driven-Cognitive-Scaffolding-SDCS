# Changelog

All notable changes to Spec-Driven Cognitive Scaffolding (SDCS) and the SPEC-001 specification will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.3.0] - 2026-09-19: Automated Topological Invariant Gating (Gate T)

### Added
- **Topological Invariant Gate (Gate T & `sdcs verify --topology`):** Abstract Syntax Tree (AST) static boundary auditor enforcing `wiring.yaml` subsystem contracts without runtime code execution. Automatically serializes prohibited imports into Inverted Architecture Decision Records (`## REJ-XXX`) conforming to the **Claim $\rightarrow$ Measurement $\rightarrow$ Reopen Condition** schema and persists them to `decisions.md` (`--append-rejections`). Pre-commit hook (`.githooks/pre-commit`) blocks structural boundary breaches while preserving unstaged rejection records for immediate agent reflection.
- **PyYAML Runtime Dependency:** Added `PyYAML>=6.0` to `pyproject.toml` dependencies for deterministic AST wiring validation across local and CI environments.

---

## [1.2.0] - 2026-09-19

### Added
- **Pillar 7: `roadmap.md` (Macro Acceptance Contract):** Encodes the North Star acceptance contract directly separating human `[INTENT]` from empirical `[MEASURED]` reality. Strictly enforces that the roadmap carries NO ephemeral task queue (which belongs exclusively in `state.md`).
- **Constitutional Invariant Gate (Gate C):** Pre-commit and CI hooks that block autonomous agents from weakening or bypassing rules in `spine.md` or `wiring.yaml` without explicit human authorization (`SDCS_ALLOW_INVARIANT_MUTATION=1` or `allow-invariant-mutation` PR label).
- **Working Memory Sync Gate (Gate S):** CI enforcement requiring `state.md` to be updated and synchronized whenever pull requests introduce $\ge 40$ modified lines.
- **Anti-Evasion Ground Truth Auditor (`audit_evals_corpus.py` & `sdcs audit`):** Hardened fixture audit with comment stripping (Python `#`, JS/C `//`, HTML comments) and whitespace normalization to defeat trivial evasion. Added `--update-pending` to automatically resolve and populate hashes into `evals.md`.
- **Authoring Protocol (`prompts/grillme.md` & `sdcs grill`):** Added the `/grillme` Adversarial Spec Elicitation Protocol to interrogate human stakeholders and harden requirements into quantifiable `[INTENT]` contracts before code generation. Scaffolded automatically and callable via `sdcs grill` / `python sdcs_init.py --grill`.
- **Operational Scale Profiles (§5):** Formalized token budgets and structural tiers: Lite (~400 tokens), Standard (~1,500 tokens), and Full Shift (~2,500–3,500 tokens).
- **Failure Modes & Operational Mitigations (§7):** Hardened against Permission Illusion (OS write-isolation), Cartographic Scaling Cliff (hierarchical index), Epistemic Bloat (TTL & active rejection set compaction), and Trivial Hashing Evasion.
- **Security Policy & Hardening (`SECURITY.md`):** Complete vulnerability reporting guidelines (`security@adammurphy.dev`), threat model boundary, and production operational hardening recommendations.
- **Presentation Slide Deck Integration:** Embedded all 10 presentation slides into `README.md` with fully refreshed 7-pillar graphics (`media/slides/slide_03.png`).
- **Architectural Lineage & Theoretical Foundations:** Formalized direct citations to classical computer science paradigms (Blackboard Pattern, Design by Contract, Virtual Memory Page Tables, Optative vs Indicative Requirements, Cybernetic Feedback, and Cryptographic Diversity Guards).
- **Standard Python Packaging (`pyproject.toml`):** Zero-dependency package setup with standard CLI entry points (`sdcs`, `sdcs-init`, `sdcs-audit`).
- **Automated Regression Suite (`tests/`):** 15 comprehensive unit and CLI tests covering scaffolding, anti-evasion hashing, phantom corpus detection, pending hash resolution, and CLI flags.
- **Dual CI Pipelines (`.github/workflows/`):** Comprehensive `sdcs-ci.yml` (Gates C, S, E, T) and `verify-pr.yml` (Ruff, Black, Mypy, Pytest).
- **GitHub Governance & Templates:** Added `.github/ISSUE_TEMPLATE/adr_rejection.md`, `.github/ISSUE_TEMPLATE/feature_intent.md`, and `.github/pull_request_template.md`.

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
