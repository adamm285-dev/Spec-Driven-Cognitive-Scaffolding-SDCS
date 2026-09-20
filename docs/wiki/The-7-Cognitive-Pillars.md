# The 7 Cognitive Pillars (+1 Flight Recorder)

SDCS externalizes agent cognition across seven deterministic repository artifacts and an isolated flight recorder:

| # | Artifact | Pillar Role | Analogy | Token Budget | Primary Invariant |
| :-: | :--- | :--- | :--- | :-: | :--- |
| **1** | `spine.md` | Constitutional Invariants | **The Law** | ~300 tokens | Non-negotiable domain axioms; protected by Gate C pre-commit hook. |
| **2** | `wiring.yaml` | Declarative Topology | **The Mesh** | Scalable | Subsystem boundaries & permitted import edges; audited statically by Gate T. |
| **3** | `roadmap.md` | Macro Acceptance Contract | **The North Star** | Scalable | Strict separation of human `[INTENT]` vs empirical `[MEASURED]`. Carries NO task queue. |
| **4** | `state.md` | Active Working Memory | **The Blackboard** | $\le 300$ tokens | Read on Turn 1 boot; strictly pruned across turns and compactions (Gate A). |
| **5** | `app_map.md` | Repository Cartography | **The Compass** | $\le 1,000$ tokens | Page table of physical file paths; synchronized via Gate M (`sdcs map --check/--sync`). |
| **6** | `decisions.md` | Negative Episodic Memory | **The Graveyard** | ~1,000 tokens | Rejection log of measured dead ends (`Claim` $\to$ `Measurement` $\to$ `Reopen Condition`). |
| **7** | `evals.md` | Positive Episodic Memory | **The Scorecard** | Scalable | Ground truth baseline standing; golden fixtures anchored via SHA-256 (Gate E). |
| **+** | `sessions/*.md` | Historical Shift Logs | **The Flight Recorder**| Append-only | **CRITICAL INVARIANT: NEVER ingested on system boot.** Queried on demand via manifest. |

---

### Pillar 1: `spine.md` (The Law)
* **Purpose:** Defines blast-radius rules, core requirements, and forbidden actions (e.g. tampering with test definitions, committing unvetted dependencies, altering architecture invariants).
* **Lifecycle:** Static, modified only under explicit human instruction (`SDCS_ALLOW_CONSTITUTIONAL_MUTATION=1`).

### Pillar 2: `wiring.yaml` (The Mesh)
* **Purpose:** Declarative service mesh defining packages, subsystems, and their permitted dependency directions.
* **Invariant:** Audited statically via Abstract Syntax Tree (AST) inspection (`sdcs verify --topology`). Cyclic dependencies or unpermitted cross-subsystem imports trigger immediate rejection.

### Pillar 3: `roadmap.md` (The North Star)
* **Purpose:** Captures macro project acceptance.
* **The Strict Invariant:** Every milestone separates human `[INTENT]` (what must be built to achieve acceptance) from empirical `[MEASURED]` reality (test results, benchmark numbers, commit hashes). It carries **NO task queue**.

### Pillar 4: `state.md` (The Blackboard)
* **Purpose:** Active working memory whiteboard tracking only the immediate subtask, active blockers, and pending gate verification.
* **Budget:** Strictly capped at $\le 300$ tokens. Contains exactly three sections:
  1. `## Current Objective`
  2. `## Status & Gate Verification`
  3. `## Immediate Next Action`

### Pillar 5: `app_map.md` (The Compass)
* **Purpose:** Codebase cartography. The agent consults this index first, eliminating brute-force recursive file scans.
* **Subsystem Slicing:** Large monorepos use `sdcs map -s <subsystem>` to extract localized page tables, reducing token consumption by up to 85%.

### Pillar 6: `decisions.md` (The Graveyard)
* **Purpose:** Negative episodic memory. When an approach or optimization fails, it is serialized as an Inverted ADR:
  * **THE CLAIM:** What was attempted.
  * **THE MEASUREMENT:** Exact empirical metric showing why it failed.
  * **WHAT WOULD REOPEN IT:** Concrete falsifiable condition required before retrying.
* **Rule:** A rejection without numbers gets retried.

### Pillar 7: `evals.md` (The Scorecard)
* **Purpose:** Positive ground truth. Cryptographically anchors benchmark fixtures to SHA-256 digests, eliminating the "Phantom Corpus Trap" where duplicate files masquerade as independent test coverage.

### +1 Flight Recorder: `sessions/*.md`
* **Purpose:** Discrete post-shift engineering handoff logs.
* **Invariant:** Stored as discrete files (`sessions/YYYY-MM-DD_<topic>.md`). **Strictly forbidden from boot ingestion**, eliminating Compaction Amnesia and token bloat. Queried on demand via `sessions/manifest.jsonl`.
