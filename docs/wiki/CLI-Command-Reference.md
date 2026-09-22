# CLI Command Reference (`sdcs`)

The `sdcs` command-line utility provides zero-dependency and standard-library tooling for initializing, auditing, verifying, and monitoring Spec-Driven Cognitive Scaffolding repositories (SPEC-001 v1.8.0).

---

## 1. Living Office HUD: `sdcs watch`

Launches the real-time background file watcher and local HTTP/SSE telemetry server with an interactive 16-bit isometric pixel-art HUD.

```bash
# Launch living office HUD (opens http://127.0.0.1:8765 in browser)
sdcs watch

# Run in headless or CI environments on a custom port
sdcs watch --no-browser --port 8765

# Configure custom polling interval
sdcs watch --poll-interval 0.5
```

---

## 2. System Diagnostics: `sdcs doctor`

Runs a comprehensive health check across runtime interpreter, system tools (`git`, `pytest`), and all 7 cognitive pillars.

```bash
# Run comprehensive diagnostic report
sdcs doctor

# Audit environment invariants (Gate E)
sdcs verify --env
```

---

## 3. Context Compiler: `sdcs hydrate`

Compiles and streams a deterministic, pre-budgeted context payload in a single atomic pass, breaking the LLM "Grep Reflex" on boot.

```bash
# Standard profile (~1,500 tokens)
sdcs hydrate --profile standard

# Lite profile for small fixes (~400 tokens)
sdcs hydrate -p lite

# Full shift profile (~3,500 tokens)
sdcs hydrate -p full

# Subsystem-focused context slicing
sdcs hydrate -p standard -s core
```

---

## 4. Verification Suite: `sdcs verify`

Audits code mutations against declared kinetic gates.

```bash
# Gate T: Audit AST imports against wiring.yaml contracts
sdcs verify --topology

# Gate T + Inverted ADR: Format and append boundary failures to decisions.md
sdcs verify --topology --append-rejections

# Gate S: Audit state.md working memory budget (default <= 350 tokens)
sdcs verify --state

# Gate P: Audit staged files against wiring.yaml sandbox protected_paths
sdcs verify --sandbox

# Gate W: Audit warehouse records and rejections against secret/PII filters
sdcs verify --warehouse

# Circuit Breaker: Detect cyclic file oscillations and thrashing loops
sdcs verify --cycles

# Gate Q: Audit test files for hollow tests and anti-mocking violations
sdcs verify --quality

# Gate E: Audit toolchain and runtime invariants
sdcs verify --env

# Execute all verification gates simultaneously
sdcs verify --all
```

---

## 5. Initializer: `sdcs init` (or `python sdcs_init.py`)

Scaffolds the 7 pillars, `sessions/`, and `AGENTS.md` into any repository.

```bash
# Scaffold in repository root
sdcs init

# Scaffold into dedicated .agent/ directory
sdcs init --use-agent-dir

# Generate hierarchical multi-tiered cartography for monorepos
sdcs init --hierarchical

# Overwrite existing scaffolding
sdcs init --force
```

---

## 6. Cartography Engine: `sdcs map`

Manages repository cartography (`app_map.md`) and token-optimized subsystem paging.

```bash
# Gate M: Check for unmapped new files or orphaned entries (exit code 1 on drift)
sdcs map --check

# Synchronize app_map.md with disk additions/deletions, preserving annotations
sdcs map --sync

# Subsystem Slicing: Page only the cartography for a specific subsystem
sdcs map --subsystem proxy
sdcs map -s src/sdcs
```

---

## 7. Working Memory Blackboard: `sdcs state`

Manages volatile working memory and ephemeral blackboards for parallel subagent workers.

```bash
# Fork an ephemeral blackboard for a parallel subagent
sdcs state fork worker-1 --objective "Implement auth endpoints"

# Rollup subagent findings into root state.md and cleanup
sdcs state rollup worker-1
```

---

## 8. Cognitive Warehouse: `sdcs warehouse`

Federates organizational memory and failure modes across fleets without leaking proprietary IP.

```bash
# Synchronize global traps and rejections into local cache
sdcs warehouse sync

# Promote a local rejection to warehouse with Gate W secret/PII scrubbing
sdcs warehouse publish REJ-001

# List cached warehouse traps
sdcs warehouse list
sdcs warehouse list --tag performance
```

---

## 9. Staleness Decay Engine: `sdcs decay`

Audits telemetry staleness in `roadmap.md` and prunes dead ends in `decisions.md`.

```bash
# Audit staleness across roadmap and decisions
sdcs decay --check

# Prune active rejections exceeding ceiling (>15 entries)
sdcs decay --prune

# Automatically tag stale [MEASURED] entries (>50 commits)
sdcs decay --tag-stale
```

---

## 10. Evaluation Suite: `sdcs eval` & `sdcs audit`

Audits ground truth test fixtures, computes SHA-256 digests, and recalibrates baselines.

```bash
# Audit evals.md test fixtures and SHA-256 digests
sdcs audit
sdcs eval audit

# Replace 'pending' entries in evals.md with computed SHA-256 hashes
sdcs audit --update-pending

# Recalibrate a specific fixture's SHA-256 digest
sdcs eval record TC-001
sdcs audit --recalibrate TC-001

# Recalibrate all declared fixtures simultaneously
sdcs eval record all
```

---

## 11. Flight Recorder: `sdcs session`

Indexes and queries discrete shift handoff logs without violating boot amnesia.

```bash
# Index historical sessions into sessions/manifest.jsonl
sdcs session index

# List recent sessions in an aligned terminal table
sdcs session list

# Forensically search sessions by keyword or milestone
sdcs session list --query "Circuit Breaker"

# Output structured records as JSON
sdcs session list --json
```

---

## 12. Topology Visualizer: `sdcs graph`

Transforms `wiring.yaml` contracts into visual graphs.

```bash
# Render ASCII directed acyclic graph in terminal
sdcs graph --format ascii

# Export Mermaid diagram for documentation or GitHub markdown
sdcs graph --format mermaid --output docs/topology.mmd
```

---

## 13. Adversarial Spec Elicitation: `sdcs grill`

Emits the `/grillme` adversarial interview prompt to harden requirements before writing code.

```bash
# Print general elicitation prompt
sdcs grill

# Target a specific milestone contract
sdcs grill --milestone M-001
```

---

## 14. AST Skeletal Compactor: `sdcs slice`

Extracts structural AST skeletons (classes, methods, type hints, docstrings) while replacing execution bodies with `...`, yielding 85%–95% token savings across Python, TypeScript, JavaScript, Go, and Rust.

```bash
# Extract skeleton of a specific file
sdcs slice src/sdcs/verifier/topology.py

# Explicit flag syntax
sdcs slice --skeleton path/to/module.py
```

---

## 15. Deterministic Pre-Flight Auto-Repair: `sdcs repair`

Intercepts code modifications in the sandbox to execute local formatters and linters (`ruff --fix`, `black`, `prettier`, `gofmt`) using 0 LLM inference tokens before kinetic gates or test suites run.

```bash
# Auto-repair staged/modified files in place
sdcs repair

# Check if repairs are needed without modifying files
sdcs repair --check-only

# Target only git-staged files
sdcs repair --staged
```

---

## 16. Governed Model Tier Router: `sdcs route`

Evaluates deterministic escalation triggers to decide whether to route the next turn to Workhorse tier (`flash`/`haiku`) or Frontier tier (`pro`/`sonnet`), implementing a Sticky Escalation Lock.

```bash
# Evaluate tier routing for a file under edit
sdcs route --file src/sdcs/core.py

# Evaluate with consecutive gate failure count
sdcs route --file src/sdcs/core.py --failures 3

# Evaluate during planning phase (always routes to Frontier)
sdcs route --planning
```
