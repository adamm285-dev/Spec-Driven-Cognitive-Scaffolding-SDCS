# Ontology Lexicon & Glossary

A formal glossary of terms, paradigms, and failure modes formalized across **SPEC-001 v1.4.1**.

---

### A
* **Abstract Syntax Tree (AST) Boundary Audit:** A static code analysis technique (implemented in Gate T) that inspects Python `ast.NodeVisitor` import paths without executing runtime code, module initializers, or network calls.
* **Adversarial Spec Elicitation (`/grillme`):** An authoring protocol where an LLM acts as an adversarial systems architect, interrogating the human stakeholder to eliminate subjective adjectives and extract quantifiable `[INTENT]` contracts before code generation begins.

### C
* **Cartographic Paging (`sdcs map -s`):** The process of filtering `app_map.md` to output only the cartography matching a specific subsystem name or directory prefix, reducing token consumption in monorepos by up to 85%.
* **Cognitive Scaffolding:** An externalized, repository-controlled structural harness that organizes an autonomous agent's memory into explicit semantic, kinetic, and dynamic layers to prevent context decay.
* **Compaction Amnesia:** The fatal pathology where an autonomous agent loses its active working hypothesis, mental cartography, and test gate state when the conversational context window is pruned or summarized by the IDE (e.g. `/compact`).

### D
* **Dynamic Layer:** The temporal layer of the SDCS ontology that tracks memory evolution over time (`state.md`, `decisions.md`, `evals.md`, and `sessions/manifest.jsonl`).

### E
* **Episodic Memory (Symmetric):** Memory that explicitly preserves both positive verified truths (`evals.md`) and negative measured dead ends (`decisions.md`) to prevent cyclical regression loops.

### F
* **Flight Recorder Protocol:** The architectural invariant mandating that historical engineering shift logs (`sessions/*.md`) must **never be auto-loaded into an agent's context window on boot**. Historical logs are queried strictly on-demand via `sessions/manifest.jsonl`.

### I
* **Inverted Architecture Decision Record (Inverted ADR):** An append-only negative memory entry in `decisions.md` that records a measured architectural rejection using the three-part schema: **THE CLAIM** $\to$ **THE MEASUREMENT** $\to$ **WHAT WOULD REOPEN IT**.
* **In-Stride Update:** The requirement that agents introduce new packages, modules, or tests must update declarative boundaries (`wiring.yaml`) and cartography (`app_map.md`) in the same commit transaction as the code.

### K
* **Kinetic Gate:** An automated, non-negotiable verification checkpoint (e.g., Gate T, Gate M, Gate C, Gate A, Gate E, Gate S) that physically halts git transactions or execution loops if architectural contracts are breached.

### P
* **Phantom Corpus Trap:** A deceptive failure mode where an agent claims 100% test pass rates across a benchmark suite, but multiple test files are actually byte-identical copies or empty templates sharing identical contents. SDCS eliminates this via Gate E's normalized SHA-256 fixture audits.

### S
* **Semantic Layer:** The structural layer of the SDCS ontology defining what exists in the repository (`spine.md`, `wiring.yaml`, and `app_map.md`).
* **Standing (Empirical Standing):** The cryptographic and benchmark credibility of a codebase's test suite, established by tying test fixtures and scores to specific git commit hashes and SHA-256 digests in `evals.md`.

### T
* **Teleological Anchor:** The cybernetic setpoint defined in `roadmap.md` (`Δ = [INTENT] - [MEASURED]`). The sole teleological purpose of an autonomous agent is driving this error delta to zero.
