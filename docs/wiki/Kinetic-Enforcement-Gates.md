# The Kinetic Enforcement Gates: Closed-Loop Defense-in-Depth

In SDCS v1.4.1, repository constraints are not suggestions—they are **physical laws of motion** enforced across two ontological defense tiers:

| Defense Tier | Gate | Name | Trigger / Command | Physical Failure Prevented |
| :--- | :--- | :--- | :--- | :--- |
| **Spatial & Structural** | **Gate T** | Topological Invariant Gate | `sdcs verify --topology` | Prohibited AST cross-subsystem imports violating `wiring.yaml`. |
| **Spatial & Structural** | **Gate M** | Cartography Drift Gate | `sdcs map --check` | Commits with untracked new files or orphaned paths in `app_map.md`. |
| **Spatial & Structural** | **Gate C** | Constitutional Immutability | `.githooks/pre-commit` | Unauthorized tampering with `spine.md` or `wiring.yaml`. |
| **Cognitive & Temporal** | **Gate A** | Working Memory Budget Gate | `sdcs verify --state` | Context window amnesia caused by bloated `state.md` (>300–350 tokens). |
| **Cognitive & Temporal** | **Gate E** | Evaluation Standing Gate | `sdcs eval` / `sdcs audit` | Phantom corpus duplicate fixtures & SHA-256 baseline hash drift. |
| **Cognitive & Temporal** | **Gate S** | Working Memory Sync Gate | CI diff trigger ($\ge 40$ lines) | Merging large pull requests with stale working memory. |

---

## 1. Gate T: Topological Invariant Gate
* **Mechanism:** Evaluates Python Abstract Syntax Trees (AST) using Python's native `ast` module. Does not execute code or trigger module initializers.
* **Contract:** Validates every import against `allowed_dependencies` declared in `wiring.yaml`.
* **Zero-Argumentation Loop:** When an import fails Gate T:
  ```bash
  # Automatically formats boundary violation into Inverted ADR (## REJ-XXX)
  # and appends it to decisions.md
  sdcs verify --topology --append-rejections
  ```
  The rejection remains unstaged on disk, forcing the agent to reflect on negative memory and refactor.

## 2. Gate M: Cartography Drift Gate (v1.4.1)
* **Mechanism:** Statically compares tracked Git repository files against entries in `app_map.md`.
* **Enforcement:** Integrated into `.githooks/pre-commit`. Halts `git commit` if new files exist without cartography entries.
* **Remediation:**
  ```bash
  # Check for drift
  sdcs map --check

  # Reconcile app_map.md with disk in-stride, preserving developer annotations
  sdcs map --sync
  ```

## 3. Gate C: Constitutional Immutability
* **Mechanism:** Git pre-commit hook checks `git diff --cached --name-only` for `spine.md` and `wiring.yaml`.
* **Enforcement:** Aborts commit unless overridden by explicit human environment variable:
  ```bash
  export SDCS_ALLOW_CONSTITUTIONAL_MUTATION=1
  ```

## 4. Gate A: Working Memory Budget Gate
* **Mechanism:** Token-budget linter verifying word counts and canonical schema of `state.md`.
* **Enforcement:** Requires `state.md` $\le 300$ tokens (or custom ceiling via `--max-tokens`) and enforces the 3 canonical headers: `## Current Objective`, `## Status & Gate Verification`, `## Immediate Next Action`.

## 5. Gate E: Evaluation Standing Gate
* **Mechanism:** Validates that every benchmark fixture in `evals.md` exists, computes normalized SHA-256 digests (stripping comments and trailing whitespace), and detects duplicate fixtures.
* **Enforcement:** Halts execution if two fixtures share identical normalized hashes under different filenames (Phantom Corpus detection).

## 6. Gate S: Working Memory Sync Gate
* **Mechanism:** CI workflow (`sdcs-ci.yml`) and pre-commit hook calculate changed code lines in pull requests.
* **Enforcement:** If code diff exceeds 40 lines, `state.md` must be staged and modified in the same commit transaction.
