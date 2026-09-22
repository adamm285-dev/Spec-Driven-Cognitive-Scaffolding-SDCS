# SPEC-001: Spec-Driven Cognitive Scaffolding (SDCS)

```text
Specification: SPEC-001
Title: Spec-Driven Cognitive Scaffolding: A Deterministic 7-Pillar Cognitive Architecture
Version: 1.7.0
Status: Active (Standard)
Author: Adam Murphy
Replaces: SPEC-001 v1.6.0
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

### 2.1 The Operational Ontology & Cybernetic Closure

Autonomous coding agents cannot operate reliably within an unstructured software repository. SPEC-001 models the codebase not as passive files, but as a closed cybernetic control system structured across three physical layers governed by an external setpoint:

1. **The Teleological Anchor (Set-Point / The "Why"):**
   - **Artifact:** `roadmap.md` (Pillar 3: The North Star).
   - **Ontological Role:** Anchors human optative intent (`[INTENT]`) against indicative empirical reality (`[MEASURED]`). It supplies the cybernetic control loop with its error signal ($\Delta = \text{Intent} - \text{Measured}$). The agent's sole objective is driving $\Delta \to 0$.

2. **The Semantic Layer (Definitions / What Exists):**
   - **Artifacts:** `spine.md` (Pillar 1: Axioms & Laws), `wiring.yaml` (Pillar 2: Declarative Mesh & Sandboxing), and `app_map.md` (Pillar 5: Spatial Cartography).
   - **Ontological Role:** Defines the universe of legal entities, system axioms, subsystem boundaries, repository cartography, and declarative tool/path sandboxing permissions. An agent is strictly prohibited from hallucinating entities or accessing paths outside this declared ontology.

3. **The Kinetic Layer (Actions / The Laws of Motion):**
   - **Artifacts & Engines:** Gate T AST/Polyglot boundary auditor (`sdcs verify --topology`), Gate M cartography drift engine (`sdcs map --check`), Gate C (Contract Immutability), Gate S token budget linter (`sdcs verify --state`), Gate P declarative sandbox guard (`sdcs verify --sandbox`), Gate E evaluation standing auditor (`sdcs eval` / `sdcs audit`), Gate D telemetry staleness & pruning engine (`sdcs decay`), and physical VCS hooks (`.githooks/pre-commit`).
   - **Ontological Role:** Enforces physical transition rules across Spatial/Structural (Gates T, M, C, P) and Cognitive/Temporal (Gates S, E, D) tiers. Every code modification represents a state transition $y = f(x)$. If an agent attempts an illegal cross-subsystem import, uncontracted sandbox mutation, or drifted file commit, the kinetic layer physically halts the operation on disk (`exit 1`).

4. **The Dynamic Layer (Memory, Causality, and Time Evolution):**
   - **Artifacts & Ledgers:** `decisions.md` (Pillar 6: Negative Memory), `evals.md` (Pillar 7: Positive Memory & Merkle/SHA-256 standing), `state.md` (Pillar 4: Working Memory Blackboard & Subagent Slices), and `sessions/manifest.jsonl` (+1 Flight Recorder Causal Lineage).
   - **Ontological Role:** Models state evolution over time with symmetric episodic memory. Failed hypotheses are serialized into negative memory (`REJ-XXX`), verified milestones are locked into cryptographic standing (`evals.md`), working memory is pruned to $\le 300$ tokens, parallel subagent states are reconciled via rollup, and shift causality is tracked via immutable flight recorder indexes.

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
* **Declarative Sandboxing & Blast-Radius:**
  `wiring.yaml` declares physical boundary constraints for sensitive files and permitted execution tools:
  ```yaml
  sandbox:
    protected_paths:
      - ".env*"
      - "*.jks"
      - "*.pem"
      - "credentials/**"
    allowed_commands:
      - "pytest"
      - "git"
      - "ruff"
      - "sdcs"
    prohibited_flags:
      - "--no-verify"
      - "-f"
      - "--force"
  ```
  Gate P interceptors audit staged mutations against `protected_paths`. Attempted staging of protected paths without explicit human authorization (`SDCS_ALLOW_SANDBOX_OVERRIDE=1`) is rejected on disk.

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
* **Budget Constraint:** MUST be hard-pruned to a ceiling of approximately 300 tokens (Gate S enforces a strict 350-token commit ceiling).
* **Invariant:** Completed tasks MUST be pruned immediately upon verification; task logs MUST NOT accumulate across turns.
* **Subagent Blackboard Forking & Rollup Protocol:**
  When executing parallel tasks or spawning autonomous subagents, workers MUST NOT mutate root `state.md` concurrently.
  1. *Blackboard Fork:* A scoped blackboard slice is instantiated for the worker: `state.<worker-id>.md` via `sdcs state fork <worker-id>`.
  2. *Isolated Mutation:* The subagent mutates only its local blackboard slice during execution.
  3. *Rollup Gate:* Upon task completion, `sdcs state rollup <worker-id>` executes a deterministic rollup: synthesizes the worker's status and blockers into root `state.md`, verifies the $\le 350$-token ceiling via Gate S, and deletes the ephemeral subagent slice.

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
  3. *Automated Temporal Decay (`sdcs decay`):* Automated kinetic routines inspect git commit distance for `roadmap.md` (`>50` commits tagged `[STALE]`) and archive active rejections exceeding 15 entries into `decisions/archive/YYYY-QX.md` with an inline index table.

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

### 5.1 The Deterministic Context Compiler (`sdcs hydrate`)

To guarantee profile compliance and eliminate multi-tool token burn, the `sdcs hydrate` command compiles and streams a pre-budgeted, single-pass markdown payload directly to stdout:

```bash
sdcs hydrate [--profile lite|standard|full] [-s <subsystem>]
```

This condenses 5–7 separate Turn 1 tool calls into 1 atomic CLI invocation, reducing boot latency and preventing context conflation.

---

## 6. The Autonomous Execution Cycle

Autonomous agents conforming to SPEC-001 MUST execute within a deterministic 4-phase finite state machine:

```text
      ┌─────────────────────────────────────────────────────────┐
      │                   1. ORIENTATION                        │
      │  Hydrate context according to selected Scale Profile:   │
      │  (Full: spine -> roadmap -> app_map -> decisions        │
      │   -> evals -> state.md OR sdcs hydrate --profile ...)   │
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

### 6.1 Post-Compaction Fast-Resume Protocol (Cold-Start Eliminator)

When an agent context window is compacted (`/compact` or context roll-off), conversational history is compressed. To eliminate cold-start hesitation and redundant exploratory surveys:
1. Inspect `state.md` immediately upon post-compaction wakeup.
2. If `## Immediate Next Action (Post-Compact)` contains an active, uncompleted task, the agent MUST bypass full exploratory re-orientation.
3. Transition directly to execution on the designated action.

---

## 7. Failure Modes & Operational Mitigations

Autonomous multi-turn agent systems exhibit distinct operational failure modes when executing against repository scaffolding. Conforming implementations of SPEC-001 MUST address these failure modes through the following defensive mitigations.

### 7.1 Gate C: Constitutional Invariant Gating & Permission Boundary

* **Failure Mode (Soft Invariant Bypass):** Because LLM coding agents typically execute with ambient shell or filesystem privileges, an agent encountering a failing test gate or strict invariant in `spine.md` may attempt to edit `spine.md`, relax linter configurations, or bypass validation flags in order to declare a task complete.
* **REQ-GATE-C-01 (Constitutional Immutability):** Pre-commit and CI hooks MUST block any commit transaction that modifies `spine.md` or `wiring.yaml` unless explicitly bypassed by human authorization (`SDCS_ALLOW_CONSTITUTIONAL_MUTATION=1` or `SDCS_ALLOW_INVARIANT_MUTATION=1`).
* **Mitigations:**
  1. **OS-Level Write Isolation:** Production deployments SHOULD set explicit POSIX filesystem permissions rendering `spine.md` and `wiring.yaml` read-only to the agent process:
     ```bash
     chmod 444 spine.md wiring.yaml
     ```
  2. **Pre-Commit Integrity Gating (Gate C):** The repository's git hook harness (`.githooks/pre-commit`) MUST verify that staged diffs do not mutate `spine.md` or `wiring.yaml` during autonomous runs. If mutations are detected without an explicit human override flag, the commit MUST abort:
     ```bash
     if git diff --cached --name-only | grep -E '^(spine\.md|wiring\.yaml|\.agent/spine\.md|\.agent/wiring\.yaml)$'; then
       echo "CRITICAL: Autonomous mutation of constitutional invariants is prohibited (Gate C)."
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

### 7.4 Gate E: Evaluation Standing & Anti-Evasion Fixture Locks

* **Failure Mode (Phantom Corpus Drift & Trivial Mutation):** While SHA-256 fingerprinting in `evals.md` prevents verbatim file duplication, an autonomous agent attempting to artificially inflate test coverage could bypass duplicate detection by injecting trailing whitespace, comments, or dummy bytes into duplicate fixtures.
* **REQ-GATE-E-01 (Corpus Diversity Invariant):** Evaluation auditing tools (`sdcs eval`, `sdcs audit`) MUST assert that no two declared test fixtures share identical normalized SHA-256 digests. Duplicate digests across distinct asset paths constitute an immediate *Phantom Corpus Violation* and halt execution.
* **REQ-GATE-E-02 (Digest Verification & Freshness):** Recorded digests in `evals.md` MUST match current normalized on-disk fixture content. Discrepancies MUST be resolved via the First-Class Recalibration Protocol (`sdcs eval record <Asset-ID>|all`).
* **Mitigations:**
  1. **Canonical Normalization Before Hashing:** Conforming audit tools (`audit_evals_corpus.py`, `src/sdcs/audit.py`) MUST strip insignificant trailing whitespace, formatting tokens, and comment blocks (Python `#`, JS/C `//`, HTML `<!-- -->`) prior to digest calculation for supported text formats.
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

### 7.6 Fixture Recalibration Protocol (`sdcs eval record` / `sdcs audit --recalibrate`)

When test fixtures intentionally evolve during legitimate engineering refactors or milestone upgrades, manual updates to `evals.md` risk transcription errors or table malformations. 

* **REQ-AUDIT-05 (Atomic Recalibration):** Tooling MUST provide atomic recalibration via `sdcs eval record <Asset-ID>|all` (and `sdcs audit --recalibrate <Asset-ID>|all`).
* **Behavior:** Computes the current normalized SHA-256 digest of target fixtures on disk and updates the recorded hashes directly within the `evals.md` markdown table in a single atomic pass, eliminating the intermediate `pending` placeholder edit dance.

```bash
# Recalibrate a single fixture atomically
sdcs eval record TC-001
# (Equivalent to: sdcs audit --recalibrate TC-001)

# Recalibrate all registered fixtures simultaneously
sdcs eval record all
```

### 7.7 Cross-Platform Pre-Commit Hook Portability

Autonomous agent environments run across diverse host platforms (Linux, macOS, Windows Git Bash, MSYS2). Pre-commit hooks MUST maintain execution portability without hanging or failing on OS-specific execution aliases.

* **REQ-HOOK-01 (Multi-Tier Python Resolution):** Pre-commit hooks (`.githooks/pre-commit`) MUST inspect runtime environments in the following order:
  1. Active virtual environment binaries: `$VIRTUAL_ENV/Scripts/python.exe` (Windows) and `$VIRTUAL_ENV/bin/python` (Unix).
  2. System candidate binaries (`python3`, `python`, `py`).
  3. Non-interactive validation test: `candidate -c "import sys"` to safely bypass Windows Store 0-byte execution stubs.
* **REQ-HOOK-02 (Graceful Degradation):** If no functional Python interpreter is available on the host PATH, the hook MUST issue a descriptive warning rather than hanging or blocking legitimate manual human operations.
* **REQ-HOOK-03 (Gate M: Pre-Commit Enforcement):** Pre-commit hooks MUST execute `sdcs map --check`. If any tracked files on disk are unmapped in `app_map.md` or orphaned, the commit transaction MUST be rejected with instructions to execute `sdcs map --sync`.

### 7.8 Gate M: Automated Cartography Drift Detection & Subsystem Paging (`sdcs map`)

As an autonomous agent creates new files or refactors modules, `app_map.md` can drift out of synchronization, inducing cartographic amnesia on subsequent turns.

* **REQ-MAP-01 (Static Drift Audit):** Tooling MUST provide `sdcs map --check` to compare disk files against `app_map.md` entries without executing runtime code.
* **REQ-MAP-02 (Automatic Cartographic Sync):** `sdcs map --sync` MUST reconcile disk state with `app_map.md`:
  - Preserve developer annotations on existing entries.
  - Append unmapped files under their corresponding directory headers.
  - Prune orphaned records for deleted files.
* **REQ-MAP-03 (Subsystem Paging):** Tooling MUST provide `sdcs map --subsystem <name|path>` (`-s`) to filter cartography to a specific subsystem (resolving declared roots in `wiring.yaml`) or directory prefix, allowing agents in large codebases or monorepos to page only focused cartographic slices into working context.

```bash
# Check for cartographic drift (returns exit code 1 if drift detected)
sdcs map --check

# Synchronize app_map.md with current disk state
sdcs map --sync

# Page a focused cartography slice for a subsystem or module prefix
sdcs map --subsystem proxy
sdcs map -s src/storage
```

### 7.9 Gate A: Deterministic Working Memory Token Budget Linter (`sdcs verify --state`)

To prevent working memory bloat and context exhaustion prior to session compaction, `state.md` is strictly constrained to a finite token budget.

* **REQ-GATE-A-01 (Working Memory Budget Ceiling):** Active working memory in `state.md` MUST NOT exceed 300–350 tokens (default threshold: 350 tokens) during engineering turn checkpoints.
* **REQ-STATE-01 (Token Ceiling Enforcement):** `sdcs verify --state` MUST fail with exit code `1` if word-count token estimations exceed the configured threshold.
* **REQ-STATE-02 (Canonical Section Schema):** `state.md` MUST conform to the three canonical sections:
  1. `## Current Objective`
  2. `## Status & Gate Verification`
  3. `## Immediate Next Action (Post-Compact)`
* **REQ-STATE-03 (Linter Tooling):** `sdcs verify --state [--max-tokens 350]` deterministically audits token consumption and section structure, failing with exit code `1` if budget is breached.

```bash
# Audit working memory token budget (default: 350 tokens)
sdcs verify --state

# Enforce custom token budget ceiling
sdcs verify --state --max-tokens 300
```

### 7.10 Structured Flight Recorder Indexing (`sessions/manifest.jsonl`)

The Flight Recorder Invariant strictly forbids ingesting historical session prose (`sessions/*.md`) on boot. However, forensic analysis across multiple engineering shifts requires structured queryability.

* **REQ-SESSION-01 (Single-Line Metadata Manifest):** Tooling MUST maintain `sessions/manifest.jsonl` where each entry is a compact JSON object:
  `{"file": "sessions/...", "timestamp": "...", "topic": "...", "verdict": "...", "summary": "..."}`
* **REQ-SESSION-02 (Subcommand Interface):**
  - `sdcs session index`: Scans `sessions/*.md` and generates or updates `manifest.jsonl`.
  - `sdcs session list [--query <text>] [--json]`: Filters and displays session logs in a clean tabular view or machine-readable JSON without reading the full markdown documents into memory.

```bash
# Index all historical flight recorder logs
sdcs session index

# Query sessions by topic or keyword
sdcs session list --query "GPU"
```

### 7.11 Declarative Topology Graph Visualizer (`sdcs graph`)

To grant autonomous agents and human architects instant cognitive clarity of architectural boundaries, `wiring.yaml` contracts must be visualizable as topological graphs.

* **REQ-GRAPH-01 (Format Support):** Tooling MUST support rendering `wiring.yaml` into:
  - `mermaid`: Flowchart TD syntax for GitHub markdown rendering and documentation.
  - `ascii`: Compact terminal directed acyclic graph (DAG) sorted in topological consumer-to-primitive order.
* **REQ-GRAPH-02 (Output Routing):** Supports direct stdout output or saving to target files via `--output <path>`.

```bash
# Render ASCII topology DAG in terminal
sdcs graph --format ascii

# Export Mermaid diagram to file
sdcs graph --format mermaid --output docs/topology.mmd
```

### 7.12 Gate S: Working Memory Synchronization Gate (CI / Pull Request Verification)

When developers or autonomous agents submit large feature pull requests without updating `state.md`, future agents waking up on subsequent shifts inherit stale blackboard states, inducing amnesia loops.

* **REQ-GATE-S-01 (Diff Velocity Threshold):** CI workflows (`sdcs-ci.yml`) and pre-commit hooks MUST calculate modified source code lines across tracked programming language extensions (`CODE_EXTENSIONS="\.(py|kt|rs|go|ts|js|jsx|tsx|sol|c|cpp|h)$"`).
* **REQ-GATE-S-02 (Atomic State Sync):** If total code additions and deletions exceed 40 lines (`LINE_THRESHOLD=40`), the pull request or commit transaction MUST stage and modify `state.md`. Pull requests breaching this threshold with an untouched `state.md` MUST fail CI validation.

### 7.13 The Lossless Compaction Protocol ("prepare for compact") & In-Stride Wiring

In multi-turn autonomous coding shifts, AI context windows inevitably saturate. Environments like Claude Code (`/compact`), Cursor resets, and LLM context roll-offs summarize conversation history, wiping un-scaffolded working memory. Conforming systems eliminate Compaction Amnesia through mid-shift checkpoints and in-stride topology mutation:

* **REQ-COMPACT-01 (5-Step Checkpoint Cycle):** Upon receiving `"prepare for compact"` or nearing context capacity (~70–80%), agents MUST execute:
  1. *Topology Audit:* Verify all active packages are declared in `wiring.yaml` via `sdcs verify --topology`.
  2. *Flight Recorder Checkpoint:* Append an immutable shift log to `sessions/YYYY-MM-DD_<topic>.md` and update `sessions/manifest.jsonl` (`sdcs session index`).
  3. *Blackboard Pruning:* Overwrite `state.md` strictly to $\le 300$ tokens containing only `## Current Objective`, `## Status & Gate Verification`, and `## Immediate Next Action (Post-Compact)`.
  4. *Episodic Memory Sweeps:* Serialize rejected approaches into `decisions.md` and synchronize cartography via `sdcs map --sync`.
  5. *Readiness Signal:* Emit explicit confirmation: *"Ready for compaction."*
* **REQ-WIRING-01 (Additive In-Stride Rule):** When introducing new modules, packages, or subsystems, agents MUST update `wiring.yaml` in the same commit transaction as the code.
* **REQ-WIRING-02 (Prohibited Boundary Relaxation):** Modifying `wiring.yaml` to relax existing architectural boundaries, add circular dependencies, or bypass Gate T violations without explicit human authorization (`SDCS_ALLOW_INVARIANT_MUTATION=1`) is strictly prohibited.

### 7.14 The Circuit Breaker (File Oscillation & Cyclic Thrashing Detector)

Autonomous models encountering subtle bugs often fall into infinite ping-pong edits between two or three files (fixing bug A breaks bug B; reverting B breaks A). This burns API tokens and mangles repository code.

* **REQ-GATE-CYCLES-01 (Oscillation Detection):** Tooling (`sdcs verify --cycles`) MUST inspect recent git commit history or working tree transitions across a rolling window (default: 6 commits).
* **REQ-GATE-CYCLES-02 (Circuit Trip Condition):** If an alternating period-2 oscillation (e.g. $A \to B \to A \to B$) or repeated single-file isolated modification occurs across $\ge 3$ consecutive commits without architectural progression or net test error reduction, the circuit breaker MUST trip (`exit 1`), physically halting the agent and requesting human intervention.

### 7.15 Gate Q: Test Quality & Anti-Mock AST Auditor

Autonomous models pressured to satisfy passing test suites may commit "hollow" or fraudulent tests that inflate test pass rates without validating runtime logic.

* **REQ-GATE-Q-01 (No Trivial Assertions):** Test functions where all assertions are trivial constants (e.g. `assert True`, `assert not False`, `assert 1 == 1`, or `assert x is not None` as the sole assertion) MUST be rejected.
* **REQ-GATE-Q-02 (No Assertless Execution):** Test functions containing execution statements but zero assertions or expected exception contexts (`pytest.raises`) MUST be rejected.
* **REQ-GATE-Q-03 (No Swallowed Exceptions):** Wrapping test assertions in `try ... except Exception: pass` or bare `except: pass` silently masking failures MUST be rejected.
* **REQ-GATE-Q-04 (Mock Abuse Ceiling):** Test cases containing excessive mock patches relative to substantive target executions without an active call to the system under test MUST be flagged and rejected.

### 7.16 Gate E & `sdcs doctor`: Runtime & Toolchain Invariant Lock

When test suites fail due to mismatched local interpreters (e.g. Python 3.10 vs 3.12), missing system tools (`git`, `pytest`, `npm`), or unset environment variables, agents often misdiagnose the failure and rewrite valid application code.

* **REQ-GATE-ENV-01 (Environment Invariant Verification):** Runtime specifications declared in `wiring.yaml` (under `environment:`) or `pyproject.toml` MUST be audited via `sdcs verify --env`.
* **REQ-GATE-ENV-02 (Code Mutation Prohibition on Environment Mismatch):** If the local interpreter, required CLI tools, or required environment variables are absent, Gate E MUST abort execution and instruct the agent: *"DO NOT edit application code. Fix local environment first."*
* **REQ-DOCTOR-01 (Comprehensive Diagnostic Health Check):** The `sdcs doctor` command MUST execute a unified audit verifying toolchains, OS environment, all 7 cognitive pillars, and Git pre-commit hook installations.

---

## 8. Verification and Compliance Tooling

Conformity with SPEC-001 v1.7.0 is validated via reference CLI tools:

* `sdcs init` (`python sdcs_init.py`): Scaffolds the 7 pillars, configures `AGENTS.md`, and generates initial directory indexes.
* `sdcs doctor` (`sdcs doctor`): Executes complete system diagnostics across toolchains, environment invariants, cognitive pillars, and VCS hooks.
* `sdcs grill` (`python sdcs_init.py --grill`): Runs the `/grillme` Adversarial Spec Elicitation Protocol to harden requirements into quantifiable `[INTENT]` contracts.
* `sdcs verify` (`sdcs verify [--topology] [--state] [--sandbox] [--warehouse] [--cycles] [--quality] [--env] [--all]`): Audits codebase AST boundaries (Gate T), working state tokens (Gate S), sandbox blast-radius (Gate P), secret screening (Gate W), thrashing loops (Circuit Breaker), test quality (Gate Q), and toolchains (Gate E).
* `sdcs eval` / `sdcs audit` (`sdcs eval record <ID>|all`, `sdcs audit [--update-pending] [--recalibrate <ID>]`): Cryptographically verifies fixture integrity, normalizes anti-evasion variance, enforces corpus diversity, and recalibrates golden digests atomically.
* `sdcs map` (`sdcs map [--check] [--sync] [--subsystem <path|name>]`): Audits and synchronizes `app_map.md` against disk state (Gate M), and pages focused cartographic slices to conserve tokens.
* `sdcs hydrate` (`sdcs hydrate [--profile lite|standard|full]`): Compiles a pre-budgeted, single-pass boot payload in 1 atomic command.
* `sdcs decay` (`sdcs decay [--check|--prune]`): Automatically tags and archives stale rejections and telemetry exceeding active ceilings.
* `sdcs warehouse` (`sdcs warehouse [sync|publish|list]`): Hub-and-spoke federation engine synchronizing global vendor rejections with Gate W sanitization.
* `sdcs session` (`sdcs session [index|list]`): Indexes and forensically queries flight recorder shift handoffs via `sessions/manifest.jsonl`.
* `sdcs graph` (`sdcs graph [--format mermaid|ascii]`): Visualizes subsystem architecture and dependency flow as Mermaid diagrams or ASCII terminal DAGs.

