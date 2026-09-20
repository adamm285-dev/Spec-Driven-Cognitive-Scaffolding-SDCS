# CLI Command Reference (`sdcs`)

The `sdcs` command-line utility provides zero-dependency and standard-library tooling for initializing, auditing, and verifying Spec-Driven Cognitive Scaffolding repositories.

---

## 1. Initializer: `sdcs init` (or `python sdcs_init.py`)

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

## 2. Verification Suite: `sdcs verify`

Audits code mutations against declared kinetic gates.

```bash
# Gate T: Audit AST imports against wiring.yaml contracts
sdcs verify --topology

# Gate T + Inverted ADR: Format and append boundary failures to decisions.md
sdcs verify --topology --append-rejections

# Gate A: Audit state.md working memory budget (default <= 350 tokens)
sdcs verify --state

# Gate A: Custom token budget ceiling
sdcs verify --state --max-tokens 300

# Execute all verification gates (topology, state budget, evals)
sdcs verify --all
```

---

## 3. Cartography Engine: `sdcs map`

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

## 4. Evaluation Suite: `sdcs eval` & `sdcs audit`

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

## 5. Flight Recorder Manager: `sdcs session`

Indexes and queries discrete shift handoff logs without violating boot amnesia.

```bash
# Index historical sessions into sessions/manifest.jsonl
sdcs session index

# List recent sessions in an aligned terminal table
sdcs session list

# Forensically search sessions by keyword or milestone
sdcs session list --query "Gate T"

# Output structured records as JSON
sdcs session list --json
```

---

## 6. Topology Visualizer: `sdcs graph`

Transforms `wiring.yaml` contracts into visual graphs.

```bash
# Render ASCII directed acyclic graph in terminal
sdcs graph --format ascii

# Export Mermaid diagram for documentation or GitHub markdown
sdcs graph --format mermaid --output docs/topology.mmd
```

---

## 7. Adversarial Spec Elicitation: `sdcs grill`

Emits the `/grillme` adversarial interview prompt to harden requirements before writing code.

```bash
# Print general elicitation prompt
sdcs grill

# Target a specific milestone contract
sdcs grill --milestone M-001
```
