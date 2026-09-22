# The Kinetic Enforcement Gates: Closed-Loop Defense-in-Depth

In **SDCS v1.8.0**, repository constraints are not suggestions—they are **physical laws of motion** enforced across spatial, cognitive, and epistemic defense tiers:

| Defense Tier | Gate | Name | Trigger / Command | Physical Failure Prevented |
| :--- | :--- | :--- | :--- | :--- |
| **Spatial & Structural** | **Gate C** | Constitutional Immutability | `.githooks/pre-commit` | Unauthorized tampering or loosening of `spine.md` or `wiring.yaml`. |
| **Spatial & Structural** | **Gate T** | Topological Invariant Gate | `sdcs verify --topology` | Prohibited AST cross-subsystem imports violating `wiring.yaml`. |
| **Spatial & Structural** | **Gate P** | Blast-Radius Sandbox Guard | `sdcs verify --sandbox` | Staging modifications within declared `protected_paths`. |
| **Spatial & Structural** | **Gate M** | Cartography Drift Gate | `sdcs map --check` | Commits with untracked new files or orphaned paths in `app_map.md`. |
| **Cognitive & Temporal** | **Gate S** | Working Memory Budget Gate | `sdcs verify --state` | Context window amnesia caused by bloated `state.md` (>350 tokens) & subagent lifecycle. |
| **Cognitive & Cache** | **Gate C-Cache** | KV-Cache Prefix Invariance | `sdcs verify --cache-invariance` | Cache-busting volatile tokens (timestamps, turn counters) in system prompt prefix. |
| **Cognitive & Fleet** | **Gate W** | Secret & PII Sanitizer | `sdcs warehouse publish` | Publishing sensitive API keys, tokens, emails, phone numbers, or IPs to central warehouse. |
| **Epistemic & Quality** | **Gate Q** | Test Quality & Anti-Mock Gate | `sdcs verify --quality` | "Hollow tests" asserting `True`, assertless test functions, or swallowed exceptions. |
| **Epistemic & Toolchain** | **Gate E** | Toolchain & Environment Gate | `sdcs doctor` / `--env` | Blaming valid application code for local runtime, interpreter, or toolchain drift. |
| **Kinetic Circuit** | **Breaker** | The Circuit Breaker | `sdcs verify --cycles` | Alternating period-2 file thrashing ($A \to B \to A \to B$) and infinite token loops. |

---

## 1. Gate C: Constitutional Immutability
* **Mechanism:** Git pre-commit hook checks `git diff --cached --name-only` for `spine.md` and `wiring.yaml`.
* **Enforcement:** Aborts commit unless overridden by explicit human environment variable:
  ```bash
  export SDCS_ALLOW_CONSTITUTIONAL_MUTATION=1
  ```

## 2. Gate T: Topological Invariant Gate
* **Mechanism:** Evaluates Python Abstract Syntax Trees (AST) using Python's native `ast` module (plus polyglot JS/TS support). Does not execute untrusted code or trigger module initializers.
* **Contract:** Validates every import against `allowed_dependencies` declared in `wiring.yaml`.
* **Zero-Argumentation Loop:** When an import fails Gate T:
  ```bash
  # Automatically formats boundary violation into Inverted ADR (## REJ-XXX)
  # and appends it to decisions.md
  sdcs verify --topology --append-rejections
  ```
  The rejection remains unstaged on disk, forcing the agent to reflect on negative memory and refactor.

## 3. Gate P: Blast-Radius Sandbox Guard
* **Mechanism:** Verifies staged git modifications against declarative `protected_paths` in `wiring.yaml`.
* **Enforcement:** Halts commits attempting to mutate infrastructure, deployment configurations, or protected schemas without explicit authorization (`sdcs verify --sandbox`).

## 4. Gate M: Cartography Drift Gate
* **Mechanism:** Statically compares tracked Git repository files against entries in `app_map.md`.
* **Enforcement:** Integrated into `.githooks/pre-commit`. Halts `git commit` if new files exist without cartography entries.
* **Remediation:**
  ```bash
  # Check for drift
  sdcs map --check

  # Reconcile app_map.md with disk in-stride, preserving developer annotations
  sdcs map --sync
  ```

## 5. Gate S: Working Memory Budget Gate
* **Mechanism:** Deterministic token-budget linter verifying token counts and canonical 3-section schema of `state.md`.
* **Enforcement:** Requires `state.md` $\le 350$ tokens (or custom ceiling via `--max-tokens`) and enforces canonical headers: `## Current Objective`, `## Status & Gate Verification`, `## Immediate Next Action`. Also handles ephemeral subagent blackboard lifecycle (`sdcs state fork` and `sdcs state rollup`).

## 6. Gate W: Secret & PII Sanitizer
* **Mechanism:** Static AST and regex scanner inspecting code and documentation before publication to the central cognitive warehouse.
* **Enforcement:** Automatically redacts Google, OpenAI, GitHub, and AWS API keys, bearer tokens, email addresses, phone numbers, and routable IPv4 addresses (`sdcs verify --warehouse` and `sdcs warehouse publish`).

## 7. Gate Q: Test Quality & Anti-Mock AST Auditor
* **Mechanism:** Static AST inspector auditing newly created or modified test suites.
* **Enforcement:** Halts commits introducing:
  - **Rule Q1 (Trivial Assertions):** Tests asserting `True`, `not False`, or `x is not None`.
  - **Rule Q2 (Assertless Tests):** Test functions executing code without assertions.
  - **Rule Q3 (Swallowed Exceptions):** Masking test failures via `try...except Exception: pass`.
  - **Rule Q4 (Mock Abuse):** Mocks exceeding assertions without invoking the target unit.

## 8. Gate E: Toolchain & Environment Invariant Lock
* **Mechanism:** Verifies local Python runtime interpreter, system tools (`git`, `pytest`), and required environment variables declared in `wiring.yaml` or `pyproject.toml`.
* **Enforcement:** Blocks commits if the environment is misconfigured (`sdcs verify --env`), and provides comprehensive diagnostic reporting via `sdcs doctor`.

## 9. The Circuit Breaker (File Oscillation & Thrashing Prevention)
* **Mechanism:** Static transition graph analyzer tracking modified file sets across consecutive commits and turns.
* **Enforcement:** Detects period-2 alternating thrashing loops ($A \to B \to A \to B$) and isolated single-file thrashing. Trips immediately to prevent agents from burning tokens and introducing Frankenstein patches (`sdcs verify --cycles`).

## 10. Gate C-Cache: KV-Cache Prefix Invariance Guard
* **Mechanism:** Static token and regex analyzer auditing system prompts, boot instructions, and hydration templates.
* **Enforcement:** Rejects cache-busting volatile tokens (ISO timestamps, turn counters like `Turn 4 of 20`, process IDs) from being positioned in the static prompt prefix. Guarantees 100% KV-cache hit rate across multi-turn trajectories (`sdcs verify --cache-invariance`).

## 11. Deterministic Pre-Flight Auto-Repair
* **Mechanism:** Sandbox execution hook intercepting code changes before kinetic gates and test suites run.
* **Enforcement:** Runs local determinist formatters (`ruff --fix`, `black`, `prettier`, `gofmt`) using **0 LLM inference tokens**, eliminating unnecessary LLM turns caused by trivial style and formatting failures (`sdcs repair`).
