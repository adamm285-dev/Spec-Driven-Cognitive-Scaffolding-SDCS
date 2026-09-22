# Release Notes: Spec-Driven Cognitive Scaffolding (SDCS) v1.8.0

> **Release Tag**: `v1.8.0`  
> **Date**: September 22, 2026  
> **Conforms To**: SPEC-001 v1.8.0  
> **PyPI**: `pip install --upgrade sdcs`  
> **Test Telemetry**: 119/119 Passed (100% Green in Pytest across 24 suites)  

---

## 💡 Sub-Dime Loop Engineering: Slashing Token Costs in Autonomous Agent Harnesses

Transitioning from single-turn chat to autonomous multi-turn loops creates an economic inflection point. Without deterministic harness controls, autonomous agents compound token bloat across turns—burning millions of tokens and turning routine pull requests into unsustainable multi-dollar expenses.

**SDCS v1.8.0 introduces the Sub-Dime Loop Engineering Suite**, transforming loop economics through deterministic AST compaction, prefix pinning, zero-token pre-flight auto-repair, and governed model tier routing:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    SDCS v1.8.0 SUB-DIME LOOP HARNESS                        │
├───────────────────────────────────┬─────────────────────────────────────────┤
│ 1. AST Skeletal Compactor         │ 85%–95% token compression on file views │
│ 2. Pre-Flight Auto-Repair         │ 0 LLM tokens burned on style & lints    │
│ 3. Gate C-Cache (Prefix Pinning)  │ 100% KV-cache hit rate on static prefix │
│ 4. Governed Model Tier Router     │ Workhorse by default, Frontier on demand│
└───────────────────────────────────┴─────────────────────────────────────────┘
```

---

## 🚀 Key Highlights in v1.8.0

### 1. 🧬 Structural AST Skeletal Compactor (`sdcs slice`)
- **85%–95% Observation Token Compression:** Replaces raw file dumping with clean structural signatures. Extracts classes, method definitions, parameter types, return types, and docstrings while collapsing implementation bodies to `...`.
- **Polyglot Signature Engine:** Native Python AST NodeTransformer plus regex signature extractors for TypeScript, JavaScript, Go, and Rust.
- **Boot Hydration Integration:** `sdcs hydrate --skeletal` injects structural outlines during Turn 1 boot hydration, giving agents full architectural awareness without burning context.

```bash
# Extract compact skeleton of any source file
sdcs slice src/sdcs/verifier/topology.py

# Hydrate pre-budgeted context with structural skeletons
sdcs hydrate --profile standard --skeletal
```

---

### 2. ⚡ Deterministic Pre-Flight Auto-Repair (`sdcs repair`)
- **Zero LLM Inference Tokens:** Fixes syntax, formatting, and trivial lint failures locally using deterministic tools (`ruff --fix`, `black`, `prettier`, `gofmt`) directly in the sandbox before kinetic gates or test suites execute.
- **Pre-Commit Integration:** Wired into `.githooks/pre-commit` as Step 3.5, automatically staging cleaned files and eliminating costly LLM re-prompt loops.

```bash
# Auto-repair modified or staged files locally
sdcs repair

# Check if repairs are required without modifying files
sdcs repair --check-only
```

---

### 3. 📌 KV-Cache Prefix Invariance Guard (Gate C-Cache)
- **Split-Brain Context Architecture:** Enforces strict separation between the **Immutable System Prefix** (axioms, rules, topology) and the **Append-Only Dynamic Tail** (`state.md`, turns, execution output).
- **Gate C-Cache (`sdcs verify --cache-invariance`):** Statically audits prompts, boot templates, and instruction files to detect and reject volatile, cache-busting tokens (timestamps, turn counters, process IDs) from the prefix.
- **Guaranteed Cache Hit Rate:** Preserves provider KV-cache across 20+ turn trajectories, drastically reducing TTFT (time-to-first-token) and input token billing.

```bash
# Verify prefix invariance across repository instructions and templates
sdcs verify --cache-invariance
```

---

### 4. 🔀 Governed Model Tier Router (`sdcs route`)
- **Workhorse by Default:** Routes turns to low-cost Workhorse models (`flash` / `haiku`) for routine execution, formatting, and localized diffs.
- **4 Deterministic Escalation Triggers:** Escalates to Frontier models (`pro` / `sonnet`) ONLY when:
  1. **Planning Phase:** Turn 1 architectural planning or milestone scoping.
  2. **Consecutive Gate Failures:** $\ge 3$ physical verification gate failures.
  3. **AST Signature Mutation:** Changes modifying public class or function signatures.
  4. **Schema / Topology Error:** Mutations to `wiring.yaml` or constitutional contracts.
- **Sticky Escalation Lock:** Once escalated, the session remains locked on Frontier mode until the active file passes all kinetic verification gates, preventing thrashing oscillations between model tiers.

```bash
# Evaluate model tier routing for a file under edit
sdcs route --file src/sdcs/core.py --failures 0

# Evaluates to Frontier when failure threshold is reached
sdcs route --file src/sdcs/core.py --failures 3
```

---

## 🛡️ The Expanded 9-Gate Kinetic Enforcement Suite

All 9 kinetic gates and the Circuit Breaker are enforced in `.githooks/pre-commit` and callable via `sdcs verify`:

| Tier | Gate | Name | Command | Physical Failure Prevented |
| :--- | :--- | :--- | :--- | :--- |
| **Spatial** | **Gate C** | Constitutional Immutability | Pre-commit | Unauthorized mutation of `spine.md` or `wiring.yaml`. |
| **Spatial** | **Gate T** | Topological Invariant Gate | `sdcs verify --topology` | Prohibited AST cross-subsystem imports violating `wiring.yaml`. |
| **Spatial** | **Gate P** | Blast-Radius Sandbox Guard | `sdcs verify --sandbox` | Staging modifications within declared `protected_paths`. |
| **Spatial** | **Gate M** | Cartography Drift Gate | `sdcs map --check` | Commits with untracked new files or orphaned paths in `app_map.md`. |
| **Cognitive**| **Gate S** | Working Memory Budget Gate | `sdcs verify --state` | Context window amnesia (`state.md` > 350 tokens) & subagent lifecycle. |
| **Cognitive**| **Gate C-Cache**| KV-Cache Prefix Invariance | `sdcs verify --cache-invariance`| Cache-busting volatile tokens in system prompt prefix. |
| **Fleet** | **Gate W** | Secret & PII Sanitizer | `sdcs warehouse publish` | Leaking API keys, tokens, emails, or IPs to central warehouse. |
| **Quality** | **Gate Q** | Test Quality & Anti-Mock Gate | `sdcs verify --quality` | Hollow tests, trivial asserts, or swallowed exceptions. |
| **Toolchain**| **Gate E** | Toolchain & Environment Gate | `sdcs doctor` / `--env` | Blaming valid application code on tool or interpreter drift. |
| **Circuit** | **Breaker**| The Circuit Breaker | `sdcs verify --cycles` | Alternating period-2 file thrashing and token burn loops. |

---

## 📦 Packaging & Installation

### Upgrade via PyPI
```bash
pip install --upgrade sdcs
```

### Initialize Scaffold in Any Repository
```bash
# Initialize 7 pillars + pre-commit hook
sdcs init

# Run system diagnostic health check
sdcs doctor
```

### Full Verification
```bash
# Run all kinetic gates
sdcs verify --all

# Run full pytest test suite
pytest
```
