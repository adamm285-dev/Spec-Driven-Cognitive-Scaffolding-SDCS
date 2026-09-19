# SPEC-001: Spec-Driven Cognitive Scaffolding (SDCS)

```text
Specification: SPEC-001
Title: Spec-Driven Cognitive Scaffolding: A Deterministic 7-Pillar Cognitive Architecture
Version: 1.3.0
Status: Active (Standard)
Author: Adam Murphy
Replaces: SPEC-001 v1.2.0
License: MIT
```

---

## 1. Abstract & Problem Statement

Autonomous coding agents routinely fail when deployed to production repositories, not due to parametric reasoning deficits, but as a direct consequence of **context conflation**. When architectural invariants, working scratchpad state, module topology, and historical telemetry are collapsed into a monolithic prompt or conversational context, three predictable failure modes occur:

1. **Context Drift:** Foundational system invariants degrade in attention weight as conversational turns accumulate debug telemetry and raw diffs.
2. **Cartographic Hallucination:** In the absence of an explicit structural index, agents burn token budgets executing recursive `grep`/`find` subroutines or inventing nonexistent module paths.
3. **Episodic Amnesia & Teleological Drift:** Agents lack structured negative memory and formal acceptance bounds, causing them to re-attempt empirically rejected hypotheses or mutate specifications to match broken implementations.

SPEC-001 defines a deterministic, file-based cognitive harness decoupling agent cognition into seven discrete, version-controlled artifacts and an isolated execution ledger.

---

## 2. The 7-Pillar Cognitive Topography

The system MUST decouple operational memory across seven specialized files maintained in repository root (or a designated `.agent/` control directory):

| # | Artifact | Pillar Role | Mutability Protocol | Ingestion Lifecycle |
| :-: | :--- | :--- | :--- | :--- |
| **1** | `spine.md` | Constitutional Invariants | **Immutable (Human-Only)** | Read Turn 1 on boot |
| **2** | `wiring.yaml` | Declarative Topology | **Static (Explicit PR)** | Read during Planning phase |
| **3** | `roadmap.md` | Macro Acceptance Contract | **Bimodal (`[INTENT]` vs `[MEASURED]`)** | Read Turn 1 on boot |
| **4** | `state.md` | Dynamic Working Memory | **High Volatility (Pruned per turn)** | Read Turn 1 on boot |
| **5** | `app_map.md` | Repository Cartography | **Deterministic (Index-driven)** | Read Turn 1 on boot |
| **6** | `decisions.md` | Negative Episodic Memory | **Append-Only (Strict schema)** | Read Turn 1 on boot |
| **7** | `evals.md` | Positive Episodic Memory | **Cryptographic (SHA-256 bound)** | Read Turn 1 & during verification |
| **+** | `sessions/*.md` | Flight Recorder Handoffs | **Immutable (Write-once per session)** | **NEVER ingested on boot** |

---

## 3. Pillar Specifications

### 3.1 Pillar 1: Constitutional Invariants (`spine.md`)

* **Role:** Establishes non-negotiable domain axioms, linters, static analysis criteria, and forbidden operational blast radii.
* **Invariant:** The agent MUST NOT modify, weaken, or negotiate constraints defined in `spine.md`.
* **The Permission Boundary (OS & VCS Enforcement):** Prompt-level instructions alone cannot guarantee invariant integrity against drifting models seeking task completion on late turns. Implementations MUST enforce defense-in-depth:
  1. *Behavioral Layer:* System prompt and `AGENTS.md` mandate zero tolerance for invariant mutation.
  2. *VCS Pre-Commit Layer:* Repository hooks (e.g., SDCS Gate C) MUST block commits modifying `spine.md` or `wiring.yaml` unless explicitly bypassed by human authorization (`SDCS_ALLOW_CONSTITUTIONAL_MUTATION=1`).
  3. *OS / Container Layer:* In automated execution sandboxes, `spine.md` and `wiring.yaml` SHOULD be set to read-only (`chmod 444`) or mounted as read-only volumes (`:ro`).

### 3.2 Pillar 2: Declarative Topology (`wiring.yaml`)

* **Role:** Formally maps component boundaries, interface bindings, runtime environment requirements, and tool dependencies.
* **Invariant:** All inter-module calls and external side effects MUST conform to the explicit input/output contracts declared in `wiring.yaml`.

### 3.3 Pillar 3: The Macro Acceptance Contract (`roadmap.md`)

* **Role:** Anchors high-level human objectives to verifiable empirical reality, preventing teleological drift and scope mutation.
* **Theoretical Foundation:** Grounded in Michael A. Jackson’s *Optative vs. Indicative Logic* (1995) and Norbert Wiener’s *Closed-Loop Cybernetic Control* (1948).
* **Specification Requirements:**
  1. **Strict Mood Dichotomy:** Every milestone MUST be decoupled into:
     - `[INTENT]` (Optative): Verbatim human acceptance criteria. Agents are strictly prohibited from altering, reframing, or "optimizing" this block.
     - `[MEASURED]` (Indicative): Empirical telemetry derived from executed test suites, coverage reports, and benchmarks.
  2. **Anti-Scratchpad Rule (No Task Queues):** `roadmap.md` MUST NOT contain ephemeral to-do lists, task queues, or in-progress tickets. Ephemeral execution state belongs exclusively in `state.md`.
  3. **Telemetry Freshness:** Every `[MEASURED]` data point MUST reference a verifiable git commit hash or timestamp. Telemetry exceeding the project freshness window (default: 30 days or 50 commits) MUST be re-verified or tagged as `[STALE]`.

* **Standard Format:**
```markdown
# Acceptance Contract (Roadmap)

## Milestone M-004: Vector Search Subsystem
* [INTENT]: Sub-50ms p99 latency across 100k indexed vectors under 500 RPS concurrent load. Zero disk spillover.
* [MEASURED]: 41.2ms p99 latency at 500 RPS (Commit `a9f4c21`); memory ceiling holds at 384MB. Gate PASSED.
```

### 3.4 Pillar 4: Dynamic Working Memory (`state.md`)

* **Role:** Serves as the ephemeral whiteboard recording active sub-objectives, blockers, and pending validation gates.
* **Budget Constraint:** MUST be hard-pruned to a ceiling of approximately 300 tokens.
* **Invariant:** Completed tasks MUST be pruned immediately upon verification; task logs MUST NOT accumulate across turns.

### 3.5 Pillar 5: Repository Cartography (`app_map.md`)

* **Role:** External structural page table defining module responsibilities and exports.
* **Access Rule:** Agents MUST resolve file paths in `app_map.md` prior to filesystem mutations and page only strictly relevant source files into context. Brute-force directory traversals (`find`, recursive `grep`) are forbidden.
* **Hierarchical Scaling (Multi-Level App Maps):** In enterprise monorepos or codebases exceeding 50 modules (>1,000 files), cartography MUST be organized hierarchically:
  1. *Root `app_map.md`:* High-level directory and package index mapping major subsystem interfaces (enforcing a strict <1,000 token ceiling).
  2. *Subsystem `app_map.md`:* Granular file-level responsibility maps maintained within specific module directories (e.g., `services/auth/app_map.md`), paged in *only* when an agent enters that execution domain. Adopts Peter Denning's Two-Level Paging model.

### 3.6 Pillar 6: Negative Episodic Memory (`decisions.md`)

* **Role:** An append-only rejection graveyard documenting falsified architectural hypotheses.
* **Schema Enforcement:** Every entry MUST follow the strict 3-part rejection contract:

```markdown
## REJ-[ID]: [Descriptive Title]
THE CLAIM: [Hypothesis or attempted optimization]
THE MEASUREMENT: [Empirical failure metric or broken invariant]
WHAT WOULD REOPEN IT: [Concrete, falsifiable condition required to re-evaluate]
```

* **Compaction & Pruning Lifecycle:** To prevent negative memory bloat over multi-month lifecycles:
  1. *Active Working Set:* `decisions.md` SHOULD carry no more than 10–15 active, high-relevance rejections (~1,000 token budget).
  2. *Archival Protocol:* When subsystems are completely decommissioned, refactored, or replaced, superseded rejections MUST be compacted into `decisions/archive/` or `decisions.archive.md`.

### 3.7 Pillar 7: Positive Episodic Memory (`evals.md`)

* **Role:** Establishes current empirical standing against locked benchmark fixtures.
* **Corpus Diversity Scope & Anti-Evasion:**
  1. *Baseline Sanity Gate:* Every fixture path MUST be mapped to a valid SHA-256 digest. Identical raw hashes across distinct benchmark paths constitute an immediate *Phantom Corpus Violation* and halt execution.
  2. *Normalized Text Hashing:* To defeat trivial whitespace, comment, or blank-line injection evasion, validation tooling MUST compute normalized text hashes (stripping trailing line spaces and empty lines) across textual fixtures.
  3. *Advanced Semantic Verification (Roadmap):* AST structural hashing and token-distance embeddings are recommended for multi-modal or compiled benchmark suites.

---

## 4. The Flight Recorder Protocol (`sessions/*.md`)

Working memory and historical auditing MUST be physically separated across the filesystem:

* `state.md` is volatile and read on boot.
* `sessions/YYYY-MM-DD_<topic>.md` files are write-once, immutable post-shift handoffs written at session close-out.
* **The Firewall Invariant:** Files located under `sessions/` MUST NOT be ingested on agent boot. Historical context retrieval MUST occur strictly on-demand via targeted grep/read targeting explicit session timestamps.

---

## 5. Operational Scale Profiles

To eliminate ceremony overhead on lightweight tasks while providing full cognitive guardrails during unattended shifts, SDCS defines three operational profiles:

| Profile | Hydration Set | Token Budget | Target Workload |
| :--- | :--- | :--- | :--- |
| **Lite** | `spine.md` + `state.md` | ~400 tokens | Interactive pair-programming, single-file bug fixes, UI/CSS tweaks, rapid iterations. |
| **Standard** | `spine.md` + `roadmap.md` + `app_map.md` + `state.md` | ~1,500 tokens | Single-subsystem feature development, localized refactors, unit test expansions. |
| **Full Shift** | All 7 Pillars + `sessions/template.md` on close-out | ~2,500–3,500 tokens | Multi-turn unattended autonomous agent runs, overnight refactors, cross-subsystem migrations. |

---

## 6. The Autonomous Execution Cycle

Autonomous agents conforming to SPEC-001 MUST execute within a deterministic 4-phase finite state machine:

```text
      ┌─────────────────────────────────────────────────────────┐
      │                   1. ORIENTATION                        │
      │  Hydrate context according to selected Scale Profile:   │
      │  (Full: spine -> roadmap -> app_map -> decisions        │
      │   -> evals -> state.md)                                 │
      └────────────────────────────┬────────────────────────────┘
                                   │
                                   ▼
      ┌─────────────────────────────────────────────────────────┐
      │                     2. PLANNING                         │
      │  Formulate atomic diffs against state.md.               │
      │  Consult wiring.yaml + target source files ONLY.        │
      └────────────────────────────┬────────────────────────────┘
                                   │
                                   ▼
      ┌─────────────────────────────────────────────────────────┐
      │                    3. EXECUTION                         │
      │  Apply code mutations. Run deterministic test harness   │
      │  and cryptographic gates defined in evals.md.           │
      └────────────────────────────┬────────────────────────────┘
                                   │
                                   ▼
      ┌─────────────────────────────────────────────────────────┐
      │                    4. CLOSE-OUT                         │
      │  Prune/update state.md. Update roadmap.md [MEASURED].   │
      │  Append failed hypotheses to decisions.md.              │
      │  Emit write-once handoff log to sessions/*.md.          │
      └─────────────────────────────────────────────────────────┘
```

---

## 7. Failure Modes & Operational Mitigations

Autonomous multi-turn agent systems exhibit distinct operational failure modes when executing against repository scaffolding. Conforming implementations of SPEC-001 MUST address these failure modes through the following defensive mitigations.

### 7.1 The Permission Illusion & Invariant Tampering

* **Failure Mode (Soft Invariant Bypass):** Because LLM coding agents typically execute with ambient shell or filesystem privileges, an agent encountering a failing test gate or strict invariant in `spine.md` may attempt to edit `spine.md`, relax linter configurations, or bypass validation flags in order to declare a task complete.
* **Mitigations:**
  1. **OS-Level Write Isolation:** Production deployments SHOULD set explicit POSIX filesystem permissions rendering `spine.md` and `wiring.yaml` read-only to the agent process:
     ```bash
     chmod 444 spine.md wiring.yaml
     ```
  2. **Pre-Commit Integrity Gating:** The repository's git hook harness (`.githooks/pre-commit`) MUST verify that staged diffs do not mutate `spine.md` or `wiring.yaml` during autonomous runs. If mutations are detected without an explicit human override flag (e.g., `SDCS_ALLOW_INVARIANT_MUTATION=1`), the commit MUST abort:
     ```bash
     if git diff --cached --name-only | grep -E '^(spine\.md|wiring\.yaml|\.agent/spine\.md|\.agent/wiring\.yaml)$'; then
       echo "CRITICAL: Autonomous mutation of constitutional invariants is prohibited."
       exit 1
     fi
     ```
  3. **CI/CD Origin Pinning:** Upstream build pipelines MUST assert that the SHA-256 digest of `spine.md` matches the canonical digest registered in the base repository branch, rejecting unauthorized PR modifications automatically.

### 7.2 Cartographic Scaling Cliff (Monorepo Cartography)

* **Failure Mode (Cartographic Saturation):** In large repositories (>150 modules or multi-package monorepos), storing every source path and export definition in a single flat `app_map.md` consumes thousands of tokens, triggering context dilution and re-introducing cartographic hallucinations.
* **Mitigations:**
  1. **Hierarchical Cartography (Root + Sub-Maps):** Large systems MUST decouple `app_map.md` into a two-tiered hierarchical index:
     * **Root `app_map.md` (Top-Level Topology):** Bounded strictly to high-level subsystem boundaries, microservice roots, entry-point scripts, and cross-package interfaces (budget ceiling: $\le 800$ tokens).
     * **Sub-Domain Maps (`<package>/app_map.md`):** Individual subdirectories or packages maintain local cartography maps containing granular module paths, class exports, and internal dependencies.
  2. **Lazy Cartographic Paging:** During Phase 1 (Orientation), the agent hydrates *only* the root `app_map.md`. The agent pages a package-level `app_map.md` into working context *only* after identifying the target subsystem.

### 7.3 Epistemic Bloat & State Rot

* **Failure Mode (Historical Memory Saturation):** Over prolonged repository lifecycles, `decisions.md` can accumulate dozens of rejection records, and `roadmap.md` can retain stale `[MEASURED]` baselines that no longer reflect the refactored reality of the code, polluting working memory.
* **Mitigations:**
  1. **Compaction Policy for `decisions.md`:**
     * Active `decisions.md` MUST prioritize active architectural frontiers.
     * When a subsystem is completely deprecated or rewritten, superseded rejection records MUST be archived out of the boot context to `decisions/archive/YYYY-QX.md`.
     * The primary `decisions.md` SHOULD maintain a rolling cap of active rejection constraints, cross-referencing archived ledgers by ID.
  2. **Measurement Expiration (TTL on `[MEASURED]`):**
     * `[MEASURED]` entries in `roadmap.md` are bound to explicit commit hashes.
     * If the commit distance between the active `HEAD` and the recorded `[MEASURED]` baseline exceeds a configured threshold (e.g., >50 commits or major structural refactors), the baseline is marked `[STALE]` and MUST be re-verified by running the empirical evaluation harness.
  3. **Hard Ceiling on `state.md`:**
     * Agents MUST prune completed milestone steps, intermediate debug thoughts, and resolved blockers during Phase 4 (Close-Out).
     * `state.md` MUST NOT exceed approximately 300 tokens. Violation of this ceiling triggers an advisory warning from `sdcs audit`.

### 7.4 Trivial Hashing Evasion (Phantom Corpus Drift)

* **Failure Mode (Trivial Fixture Mutation):** While SHA-256 fingerprinting in `evals.md` prevents verbatim file duplication, an autonomous agent attempting to artificially inflate test coverage could bypass duplicate detection by injecting trailing whitespace, comments, or dummy bytes into duplicate fixtures.
* **Mitigations:**
  1. **Canonical Normalization Before Hashing:** Conforming audit tools (`audit_evals_corpus.py`) SHOULD strip insignificant whitespace, formatting tokens, or comment blocks prior to digest calculation for supported text formats.
  2. **Structural Size & Dimension Diversity:** Benchmark sets containing structured inputs (e.g., images, PDFs, tabular data) MUST define secondary diversity attributes (byte size distribution, dimensional variances, or token counts) alongside cryptographic hashes to ensure representative corpus coverage.

### 7.5 Gate T: Automated Topological Invariant Gating (AST Verification & Negative Memory Serialization)

Gate T enforces the architectural contracts declared in **Pillar 2 (`wiring.yaml`)** at the Abstract Syntax Tree (AST) level, programmatically coupling boundary failures to **Pillar 6 (`decisions.md`)**. While Gate C guarantees physical immutability of the specification files, Gate T guarantees that code generated by autonomous agents strictly obeys subsystem boundaries.

```text
   [ git commit ]
         │
         ▼
┌─────────────────┐
│  Gate C Check   │ ──(Fails)──► [ ABORT: Invariant Tamper Detected ]
└────────┬────────┘
         │ (Passes)
         ▼
┌─────────────────┐
│  Gate T: AST    │
│ Topology Audit  │
└────────┬────────┘
         ├── (Violations Detected)
         │        │
         │        ▼
         │   [ Deduplication Filter ]
         │        │
         │        ▼
         │   [ Append REJ-XXX to decisions.md ]
         │        │
         │        ▼
         │   [ ABORT COMMIT (exit 1) ]
         │
         └── (0 Violations) ──► [ PROCEED TO COMMIT ]
```

#### 7.5.1 Core Invariants

* **REQ-GATE-T-01 (Static Inspection):** Gate T MUST inspect repository files via abstract syntax tree parsing without loading or executing module code. Dynamic imports or runtime reflection checks are prohibited within the gate harness.
* **REQ-GATE-T-02 (Topological Conformance):** Every import edge extracted from source files MUST resolve to a subsystem defined in `wiring.yaml`. If subsystem $A$ imports from subsystem $B$, $B$ MUST exist in $A$'s `allowed_dependencies`.
* **REQ-GATE-T-03 (Automated Negative Memory Serialization):** Upon detecting a boundary violation during a pre-commit or compilation pass, the harness MUST automatically format the failure signature into an Inverted Architecture Decision Record (`## REJ-XXX`) and persist it to `decisions.md`.
* **REQ-GATE-T-04 (Deduplication Guard):** The serializer MUST evaluate existing rejection signatures prior to appending. Duplicate violations matching the active `(source_file, imported_module)` tuple MUST NOT generate redundant entries.
* **REQ-GATE-T-05 (Unstaged Working Tree Persistence):** Generated rejection records MUST be written directly to `decisions.md` on disk but MUST remain **unstaged** in Git. The commit MUST abort with exit code `1`, requiring the agent to hydrate the negative memory, execute the architectural refactor, and stage both the fix and `decisions.md` atomically.

#### 7.5.2 Rejection Schema Contract

Every automated rejection appended by Gate T conforms strictly to the following schema:

```markdown
## REJ-[0-9]{3}: Prohibited Import Boundary (`{source_subsystem}` -> `{target_subsystem}`)
- **Date**: {ISO_8601_UTC_TIMESTAMP}
- **Target**: `{relative_source_path}:{line_number}`
- **Status**: REJECTED (AST Topology Invariant Gate T)

**Claim**:
Subsystem `{source_subsystem}` can import `{imported_module}` directly from `{target_subsystem}`.

**Measurement**:
- **Tool**: `sdcs verify --topology` (AST Static Analysis)
- **Violation**: `{relative_source_path}:{line_number}` imports prohibited module `{imported_module}`.
- **Declared Contract**: Allowed dependencies for `{source_subsystem}`: {allowed_dependencies_list}.
- **Result**: Automated Gate T pre-commit rejection.

**Reopen Condition**:
1. Decouple via dependency inversion (extract interface/protocol into an allowed layer).
2. Or request human architectural approval to mutate `wiring.yaml` under `{source_subsystem}.allowed_dependencies` via `SDCS_ALLOW_INVARIANT_MUTATION=1`.
```

#### 7.5.3 CLI Verification Interface

Gate T is exposed via the SDCS verification runner:

```bash
# Execute standalone AST topology verification
sdcs verify --topology

# Execute verification and automatically append violations to negative memory
sdcs verify --topology --append-rejections
```

---

## 8. Verification and Compliance Tooling

Conformity with SPEC-001 is validated via reference CLI tools:

* `sdcs_init.py` (`sdcs init`): Scaffolds the 7 pillars, configures `AGENTS.md`, and generates initial directory indexes.
* `sdcs grill` (`python sdcs_init.py --grill`): Runs the `/grillme` Adversarial Spec Elicitation Protocol to harden requirements into quantifiable `[INTENT]` contracts.
* `sdcs verify --topology` (`src/sdcs/verifier/topology.py`): Audits codebase AST against `wiring.yaml` subsystem boundaries and automatically writes violations to `decisions.md` (Gate T).
* `audit_evals_corpus.py` (`sdcs audit`): Traverses `evals.md`, cryptographically hashes test fixtures on disk (both raw and normalized), and enforces corpus diversity.
