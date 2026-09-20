#!/usr/bin/env python3
"""
sdcs_init.py - Spec-Driven Cognitive Scaffolding (SDCS) Initializer
Conforming to SPEC-001 v1.4.0

Scaffolds the complete 7-pillar deterministic cognitive harness:
  1. spine.md        — Constitutional Invariants
  2. wiring.yaml     — Declarative Dependency Mesh
  3. roadmap.md      — Macro Acceptance Contract ([INTENT] vs [MEASURED])
  4. state.md        — Working Memory Blackboard (~300 token budget)
  5. app_map.md      — Repository Cartography (Flat or Hierarchical)
  6. decisions.md    — Negative Episodic Memory (Rejection Log)
  7. evals.md        — Positive Ground Truth (Empirical Scorecard & Corpus)
  +  AGENTS.md       — Operational Boot Instructions (Behavioral Scaffolding)
  +  sessions/       — Engineering Shift Handoff Templates (Flight Recorder)
  +  .githooks/      — Invariant Lock & State Sync Git Hook
"""

import argparse
import os
import stat
import sys
from pathlib import Path

SPEC_VERSION = "1.4.0"

# -----------------------------------------------------------------------------
# Pillar Templates
# -----------------------------------------------------------------------------

TEMPLATE_SPINE = """# Constitutional Invariants (The Law)
<!-- SPEC-001 v1.3.0 Pillar 1 | Mutability: IMMUTABLE (Human-Only) -->

## Non-Negotiable Domain Axioms
1. Determinism First: No silent fallbacks, unverified mocks, or unhandled exceptions in production pathways.
2. Invariant Protection: Agents MUST NOT mutate `spine.md` or relax validation gates.
3. Secret Hygiene: Zero plaintext secrets, API keys, or credentials committed to git.

## Deterministic Verification Gates
- Static Analysis: Must pass configured linters (`ruff`, `flake8`, `eslint`, etc.) with zero warnings.
- Test Coverage Baseline: Line coverage must not drop below established thresholds.
- Corpus Verification: Fixture integrity must pass `python audit_evals_corpus.py`.

## Absolute Forbidden Operations
- Destructive git operations (`git push --force`, `git reset --hard` on tracked remote branches).
- Bypassing pre-commit hooks via `--no-verify`.
- Reading `sessions/*.md` flight recorder archives during Turn 1 boot hydration.
"""

TEMPLATE_WIRING = """# Declarative Topology (The Mesh)
# SPEC-001 v1.3.0 Pillar 2 | Mutability: STATIC (Explicit PR)

version: "1.3"
subsystems:
  core:
    path: "src/"
    responsibilities: "Core domain logic and data pipelines"
    allowed_dependencies: []
  interfaces:
    path: "src/interfaces/"
    responsibilities: "External APIs, CLI controllers, adapters"
    allowed_dependencies: ["core"]

tool_boundaries:
  allowed_binaries: ["pytest", "git", "python", "ruff"]
  forbidden_flags: ["--no-verify", "-f", "--force"]

contracts:
  strict_imports: true
  circular_dependencies: false
"""

TEMPLATE_ROADMAP = """# Macro Acceptance Contract (The North Star)
<!-- SPEC-001 v1.3.0 Pillar 3 | Mutability: BIMODAL ([INTENT] vs [MEASURED]) -->
<!-- Iron Invariant: NO TASK QUEUES. Ephemeral tasks belong exclusively in state.md -->

## Milestone M-001: Initial Operational Capability
* [INTENT]: Scaffold and bootstrap the repository under SPEC-001 v1.3.0 invariants. Verify zero test fixture drift.
* [MEASURED]: Scaffolding complete; initial evals verified via SHA-256 audit. Status: VERIFIED.

<!--
Template for New Milestones:
## Milestone M-XXX: [Descriptive Milestone Name]
* [INTENT]: [Human acceptance criteria: explicit latencies, memory ceilings, error rates]
* [MEASURED]: [Empirical telemetry: test results, benchmark data, git commit hashes]
-->
"""

TEMPLATE_STATE = """# Dynamic Working Memory (The Blackboard)
<!-- SPEC-001 v1.3.0 Pillar 4 | Mutability: HIGH VOLATILITY | Budget: ~300 Tokens -->
<!-- Read on Turn 1 boot. Strictly pruned after milestone completion. -->

## Active Objective
- Complete repository bootstrapping and verify invariant enforcement hooks.

## Immediate Blockers
- None.

## Active Verification Gates
- [ ] Invariant pre-commit hook installed (`core.hooksPath` set).
- [ ] Initial test baseline recorded in `evals.md`.
- [ ] Root cartography mapped in `app_map.md`.
"""

TEMPLATE_DECISIONS = """# Negative Episodic Memory (The Graveyard)
<!-- SPEC-001 v1.3.0 Pillar 6 | Mutability: APPEND-ONLY -->
<!-- Mandatory 3-part schema: Claim -> Measurement -> Reopen Condition -->

## REJ-001: Monolithic Session Diary Ingestion
- **The Claim:** Ingesting all past session logs on Turn 1 boot provides comprehensive historical context.
- **The Measurement:** Exhausted 28k tokens of context window within 3 conversational turns; induced severe context drift and hallucinated file boundaries.
- **What Would Reopen It:** LLM architecture with sub-linear attention latency and zero needle-in-a-haystack degradation beyond 1M tokens.
"""

TEMPLATE_EVALS = """# Empirical Standing & Ground Truth (Evals)
<!-- SPEC-001 v1.3.0 Pillar 7 | Mutability: CRYPTOGRAPHIC -->
<!-- Corpus Diversity Invariant: Unique SHA-256 digests required across all golden fixtures -->

## 1. Golden Reference Corpus & Diversity
| Asset ID | Path / Scenario | SHA-256 (8-char) | Unique Characteristics | Target Subsystem |
| :--- | :--- | :--- | :--- | :--- |
| `TC-INIT` | `tests/fixtures/init.txt` | pending | Baseline golden reference | Core Engine |

## 2. Baseline Empirical Scorecard
- Baseline Commit: HEAD
- Test Suite Status: INITIALIZING
- Coverage Metric: Baseline pending
"""

TEMPLATE_AGENTS = """# AGENTS.md — Operational Harness Protocol
<!-- Conforming to SPEC-001 v1.4.0 -->

## 1. The Operational Ontology
You are operating inside a deterministic cybernetic control system, not an unconstrained environment. The codebase is organized across three physical layers governed by a teleological anchor:

- **0. Teleological Anchor (The Target):** `roadmap.md` (Pillar 3: The North Star). Macro acceptance contract: `[INTENT]` vs `[MEASURED]`. Your sole task is driving the measured delta to zero.
- **1. Semantic Layer (What Exists):** `spine.md` (Pillar 1: Constitutional Invariants & Axioms), `wiring.yaml` (Pillar 2: Subsystem Boundaries & Dependency Mesh), and `app_map.md` (Pillar 5: Repository Cartography). You cannot invent entities or subsystems outside this declared schema.
- **2. Kinetic Layer (The Laws of Motion):** Gate T AST boundary audits (`sdcs verify --topology`), Gate C (Contract Immutability), and physical pre-commit hooks (`.githooks/pre-commit`). Every code mutation is a kinetic state transition; attempts to violate topological contracts are physically rejected on disk.
- **3. Dynamic Layer (Memory & Time Evolution):** `decisions.md` (Pillar 6: Negative Episodic Memory / Graveyard), `evals.md` (Pillar 7: Positive Episodic Memory / Empirical Standing & SHA-256 fixture locks), `state.md` (Pillar 4: Active Working Blackboard <= 300 tokens), and `sessions/manifest.jsonl` (+1 Flight Recorder Causal Lineage).

## 2. Turn 1 Boot Hydration Order (7 Pillars)
On Turn 1 of any task, you MUST hydrate state across the 7 cognitive pillars in this exact sequence:
1. `spine.md`        -> Constitutional invariants & forbidden actions (Pillar 1: The Law)
2. `roadmap.md`      -> Active milestone [INTENT] vs [MEASURED] (Pillar 3: The North Star)
3. `app_map.md`      -> Repository cartography (resolve target paths first) (Pillar 5: The Compass)
4. `decisions.md`    -> Negative episodic memory (rejected hypotheses) (Pillar 6: The Graveyard)
5. `evals.md`        -> Verified empirical baseline & ground truth (Pillar 7: Positive Ground Truth)
6. `state.md`        -> Turn-by-turn active working memory (Pillar 4: The Blackboard)
7. `wiring.yaml`     -> Declarative topology & subsystem boundaries (Pillar 2: The Mesh)

## +1 Flight Recorder Invariant
CRITICAL INVARIANT: NEVER inspect or hydrate `sessions/*.md` on boot.
`sessions/*.md` serves as an immutable post-hoc flight recorder, NOT boot context. Auto-loading historical sessions recreates context drift and episodic amnesia. Query individual sessions or `sessions/manifest.jsonl` on demand for forensic debugging (`sdcs session`).

## 3. The 4-Phase Autonomous Execution Cycle
Execute every turn through the 4-phase engine:
1. **Orientation:** Hydrate constraints and ground truth from the Semantic and Dynamic layers.
2. **Planning:** Formulate atomic diffs against `state.md` respecting boundaries in `wiring.yaml`.
3. **Execution:** Apply code mutations and verify against kinetic gates (Gate T AST audits) and empirical baselines (`evals.md`).
4. **Close-Out:** Prune `state.md` (<= 300 tokens), log rejections in `decisions.md`, and record shift progress in `sessions/`.

## 4. Invariant Rules
- **Context Isolation:** Consult `app_map.md` and load only what is strictly relevant to the task.
- **No Task Queue in Roadmap:** Active tasks live strictly in `state.md`.
- **Non-Regression:** Never undo a decision or retry a measured rejection documented in `decisions.md` without explicit human sign-off.
- **Topological Invariant (Gate T):** Code must respect subsystem boundary contracts declared in `wiring.yaml`. Prohibited imports will be rejected and serialized to `decisions.md`.
- **Wiring Mutation Invariant (Pillar 2):** When introducing new subsystems, modules, or packages, update `wiring.yaml` in-stride with code modifications. Modifying `wiring.yaml` to relax existing architectural boundaries, add circular dependencies, or bypass Gate T rejections without explicit human authorization (`SDCS_ALLOW_INVARIANT_MUTATION=1`) is strictly forbidden.
- **Empirical Standing:** Verify changes against the baseline scorecard in `evals.md`. Run `audit_evals_corpus.py` (or `sdcs audit`) when adding or modifying test fixtures.
- **Empirical Verification:** Always run existing tests, typechecks, and eval gates before reporting completion.

## 5. Mid-Shift Checkpoint Protocol ("prepare for compact")
When instructed to "prepare for compact", or when context window exhaustion nears prior to session compaction:
1. **Topology & Subsystem Audit:** Run `sdcs verify --topology` to verify that all imports comply with `wiring.yaml`. If new modules or packages were created during the shift, ensure they are declared in `wiring.yaml`.
2. **Flight Recorder Checkpoint:** Write an immutable checkpoint log to `sessions/YYYY-MM-DD_<topic>.md` capturing work completed, verification status, active blockers, and immediate post-compact next steps. Update `sessions/manifest.jsonl` via `sdcs session --sync`.
3. **Blackboard Pruning (`state.md`):** Aggressively prune and overwrite `state.md` strictly to <= 300 tokens containing only:
   - `## Current Objective`
   - `## Status & Gate Verification`
   - `## Immediate Next Action (Post-Compact)`
4. **Episodic Sweeps:**
   - Log any rejected approaches or failed experiments to `decisions.md`.
   - Synchronize `app_map.md` if files were created, moved, or deleted (`sdcs map --sync`).
   - Update `roadmap.md` [MEASURED] blocks if milestones or acceptance criteria were met.
5. **Readiness Signal:** Output a brief confirmation that all 7 pillars and the flight recorder are synchronized, and state: "Ready for compaction."

## 6. Close-Out Protocol (Mandatory)
Before completing your shift:
1. Prune and overwrite `state.md` with current verification status (<= 300 token budget via `sdcs verify --state`).
2. Update `roadmap.md` [MEASURED] blocks with real test telemetry.
3. If an attempted optimization or architecture failed, log it to `decisions.md`.
4. Update `app_map.md` if new files were created (`sdcs map --check`).
5. Verify `wiring.yaml` matches codebase topology (`sdcs verify --topology`).
6. Emit an immutable handoff log to `sessions/YYYY-MM-DD_<topic>.md` and sync index (`sdcs session --sync`).
"""

TEMPLATE_SESSION_HANDOFF = """# Engineering Shift Handoff
<!-- Flight Recorder: Immutable historical log. Do NOT ingest on system boot. -->

## Date & Session
- Timestamp: {timestamp}
- Shift Focus: Repository Initial Scaffolding

## Completed Actions
- Initialized SPEC-001 v1.3.0 cognitive scaffolding.
- Registered pre-commit invariant protection hook.

## Verification Executed
- Lint: PASSED
- Evals Audit: Initialized
"""

TEMPLATE_PRE_COMMIT_HOOK = """#!/bin/sh
# SDCS SPEC-001 Pre-Commit Invariant & State Guard
# Enforces OS-level defense against autonomous invariant tampering.

# 1. Invariant Protection Gate (spine.md & wiring.yaml)
if [ "$ALLOW_INVARIANT_MUTATION" != "1" ] && [ "$SDCS_ALLOW_INVARIANT_MUTATION" != "1" ] && [ "$SDCS_ALLOW_CONSTITUTIONAL_MUTATION" != "1" ]; then
  TAMPERED_INVARIANTS=$(git diff --cached --name-only | grep -E '^(spine\\.md|wiring\\.yaml|\\.agent/spine\\.md|\\.agent/wiring\\.yaml)$')
  if [ -n "$TAMPERED_INVARIANTS" ]; then
    echo "===================================================================="
    echo " [SDCS VIOLATION] CONSTITUTIONAL INVARIANT TAMPERING DETECTED"
    echo "===================================================================="
    echo "Autonomous agents are prohibited from modifying invariants:"
    echo "  $TAMPERED_INVARIANTS"
    echo ""
    echo "To override as a human architect, rerun with:"
    echo "  ALLOW_INVARIANT_MUTATION=1 git commit"
    echo "===================================================================="
    exit 1
  fi
fi

# 2. Working Memory Synchronization Gate (state.md)
SDCS_MODE=$(git config sdcs.mode || echo "advisory")
DIFF_LINES=$(git diff --cached --shortstat | awk '{print $4+$6}')

if [ "${DIFF_LINES:-0}" -ge 40 ]; then
  STATE_TOUCHED=$(git diff --cached --name-only | grep -E '^(state\\.md|\\.agent/state\\.md)$')
  if [ -z "$STATE_TOUCHED" ]; then
    if [ "$SDCS_MODE" = "strict" ]; then
      echo "===================================================================="
      echo " [SDCS ERROR] STATE SYNCHRONIZATION REQUIRED (Strict Mode)"
      echo "===================================================================="
      echo "Commit affects >= 40 lines but state.md was not updated."
      echo "Please stage an updated state.md reflecting current working memory."
      echo "===================================================================="
      exit 1
    else
      echo "--------------------------------------------------------------------"
      echo " [SDCS ADVISORY] Working memory warning: >= 40 lines modified"
      echo " Remember to sync active objectives in state.md."
      echo "--------------------------------------------------------------------"
    fi
  fi
fi

# 3. Topological Invariant Gate (Gate T: wiring.yaml AST audit)
WIRING_FILE=""
if [ -f "wiring.yaml" ]; then
  WIRING_FILE="wiring.yaml"
elif [ -f ".agent/wiring.yaml" ]; then
  WIRING_FILE=".agent/wiring.yaml"
fi

if [ -n "$WIRING_FILE" ]; then
  PYTHON_BIN=""
  if [ -n "$VIRTUAL_ENV" ]; then
    if [ -x "$VIRTUAL_ENV/Scripts/python.exe" ]; then
      PYTHON_BIN="$VIRTUAL_ENV/Scripts/python.exe"
    elif [ -x "$VIRTUAL_ENV/bin/python" ]; then
      PYTHON_BIN="$VIRTUAL_ENV/bin/python"
    fi
  fi

  if [ -z "$PYTHON_BIN" ]; then
    for candidate in python3 python py; do
      if command -v "$candidate" >/dev/null 2>&1; then
        if "$candidate" -c "import sys" >/dev/null 2>&1; then
          PYTHON_BIN="$candidate"
          break
        fi
      fi
    done
  fi

  if [ -z "$PYTHON_BIN" ]; then
    echo "⚠️ [SDCS Warning] No functional Python interpreter found to run Gate T verification."
  else
    if ! "$PYTHON_BIN" -m sdcs.cli verify --topology --append-rejections; then
      if [ "$SDCS_MODE" = "strict" ]; then
        echo "===================================================================="
        echo " [SDCS VIOLATION] GATE T: TOPOLOGICAL BOUNDARY VIOLATION DETECTED"
        echo "===================================================================="
        echo "Import boundaries declared in $WIRING_FILE were violated."
        echo "Failure signature appended to decisions.md."
        echo "Please refactor code, stage the fix and decisions.md, then re-commit."
        echo "===================================================================="
        exit 1
      else
        echo "--------------------------------------------------------------------"
        echo " [SDCS ADVISORY] Gate T: Topology boundary violation detected."
        echo "--------------------------------------------------------------------"
      fi
    fi
  fi
fi

exit 0
"""


def generate_grillme_md(milestone: str | None = None) -> str:
    milestone_str = (
        milestone
        if (milestone and milestone.lower().startswith("milestone"))
        else f"Milestone {milestone}" if milestone else None
    )
    target_text = (
        f"target `{milestone_str}`"
        if milestone_str
        else "the target milestone (e.g., `Milestone M-001`)"
    )
    return f"""# /grillme — Adversarial Spec Elicitation Protocol

Act as a relentless Principal Systems Architect. Your objective is to extract unambiguous, falsifiable requirements from the user to populate `roadmap.md` ([INTENT]) and `spine.md` (Constitutional Invariants).

## RULES
1. **Zero Tolerance for Vague Adjectives:** Reject words like "fast", "scalable", "clean", "intuitive", "robust", or "secure".
2. **Demand Exact Numerical Ceilings & Floors:** Require exact empirical metrics (e.g., p99 latency <= 50ms, RPS >= 500, memory ceiling <= 384MB, branch coverage >= 90%).
3. **Probe Hidden Failure Modes:** Interrogate edge cases, network partitions, corrupted payloads, concurrency spikes, and race conditions.
4. **Enforce Falsifiable Formatting:** Interrogate until every single requirement can be written as:
   * `* [INTENT]: Concrete, non-negotiable production criteria.`
   * `* [MEASURED]: Verifiable test/benchmark assertion (e.g. Commit <hash>, 41.2ms p99 at 500 RPS). Gate PASSED/PENDING.`

## INTERVIEW WORKFLOW
1. Ask the user for the primary objective of {target_text}.
2. Identify the single biggest unstated assumption or ambiguity.
3. Challenge the assumption with a concrete edge case failure scenario.
4. Demand the exact numerical tolerance or threshold required to accept the system in production.
5. Once hardened, output the finalized markdown block ready to be committed directly into `roadmap.md`.
"""


# -----------------------------------------------------------------------------
# Cartography Generators
# -----------------------------------------------------------------------------

EXCLUDE_DIRS = {
    ".git",
    ".githooks",
    "__pycache__",
    "node_modules",
    ".venv",
    "venv",
    ".pytest_cache",
    ".ruff_cache",
    "dist",
    "build",
    ".egg-info",
    "sessions",
    ".idea",
    ".vscode",
    ".tox",
    ".mypy_cache",
}


def scan_repository_tree(root: Path) -> dict[str, list[str]]:
    """Index files grouped by directory, filtering noisy runtime artifacts."""
    tree: dict[str, list[str]] = {}
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in EXCLUDE_DIRS and not d.endswith(".egg-info")]
        rel_dir = os.path.relpath(dirpath, root).replace("\\", "/")
        if rel_dir == ".":
            rel_dir = "root"
        valid_files = [
            f
            for f in filenames
            if not f.endswith((".pyc", ".pyo", ".so", ".DS_Store", "Thumbs.db"))
        ]
        if valid_files:
            tree[rel_dir] = sorted(valid_files)
    return tree


def generate_flat_app_map(root: Path) -> str:
    """Generate a single top-level cartographic index."""
    tree = scan_repository_tree(root)
    lines = [
        "# Repository Cartography (The Compass)",
        "<!-- SPEC-001 v1.3.0 Pillar 5 | Flat Cartography -->",
        "<!-- Golden Rule: Consult this map FIRST. Read ONLY necessary target files. -->\n",
    ]
    for directory, files in sorted(tree.items()):
        lines.append(f"### `{directory}/`")
        for f in files:
            lines.append(f"- `{f}`")
        lines.append("")
    return "\n".join(lines)


def detect_subpackages(root: Path) -> list[Path]:
    """Detect independent packages or major subsystems for hierarchical maps."""
    subpackages: list[Path] = []
    indicators = {"__init__.py", "package.json", "Cargo.toml", "go.mod", "pyproject.toml"}

    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in EXCLUDE_DIRS]
        path = Path(dirpath)
        if path == root:
            continue
        if any(ind in filenames for ind in indicators):
            subpackages.append(path)
    return subpackages


def generate_hierarchical_cartography(root: Path, target_dir: Path, force: bool):
    """Generate root cartography index plus dedicated package-level app_map.md files."""
    subpackages = detect_subpackages(root)

    # 1. Root Cartography Index
    root_lines = [
        "# Root Repository Cartography (The Compass Index)",
        "<!-- SPEC-001 v1.3.0 Pillar 5 | Hierarchical Master Index -->",
        "<!-- Golden Rule: Page package-level app_map.md ONLY when entering subsystem context. -->\n",
        "## Subsystem Registry\n",
    ]

    if not subpackages:
        top_dirs = [
            d
            for d in root.iterdir()
            if d.is_dir() and d.name not in EXCLUDE_DIRS and not d.name.startswith(".")
        ]
        for d in sorted(top_dirs):
            rel = d.relative_to(root).as_posix()
            root_lines.append(f"- **Subsystem `{rel}/`**: Domain component root")
    else:
        for pkg in sorted(subpackages):
            rel = pkg.relative_to(root).as_posix()
            root_lines.append(f"- **Package [`{rel}/`](./{rel}/app_map.md)**: Modular subsystem")

            # 2. Local Sub-package app_map.md
            pkg_tree = scan_repository_tree(pkg)
            pkg_lines = [
                f"# Cartography: `{rel}/`",
                f"<!-- Sub-domain map for `{rel}` | Consult prior to modifying package files -->\n",
            ]
            for sub_dir, files in sorted(pkg_tree.items()):
                sub_dir_clean = sub_dir.replace("\\", "/")
                header = f"{rel}/{sub_dir_clean}" if sub_dir_clean != "root" else str(rel)
                pkg_lines.append(f"### `{header}/`")
                for f in files:
                    pkg_lines.append(f"- `{f}`")
                pkg_lines.append("")

            pkg_map_file = pkg / "app_map.md"
            if not pkg_map_file.exists() or force:
                pkg_map_file.write_text("\n".join(pkg_lines), encoding="utf-8")
                print(f"  + Sub-map: {pkg_map_file}")

    root_lines.append("\n## Shared / Root Entrypoints")
    root_files = [f.name for f in root.iterdir() if f.is_file() and not f.name.startswith(".")]
    for rf in sorted(root_files):
        root_lines.append(f"- `{rf}`")

    master_map_file = target_dir / "app_map.md"
    master_map_file.write_text("\n".join(root_lines), encoding="utf-8")
    print(f"  + Master Cartography: {master_map_file}")


# -----------------------------------------------------------------------------
# Scaffolding Engine
# -----------------------------------------------------------------------------


def write_file(path: Path, content: str, force: bool = False):
    if path.exists() and not force:
        print(f"  · Exists:  {path} (skipping)")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.strip() + "\n", encoding="utf-8")
    print(f"  + Created: {path}")


def install_githook(root: Path):
    """Installs the invariant protection pre-commit hook into .githooks/."""
    hook_dir = root / ".githooks"
    hook_dir.mkdir(parents=True, exist_ok=True)
    hook_file = hook_dir / "pre-commit"

    hook_file.write_text(TEMPLATE_PRE_COMMIT_HOOK, encoding="utf-8")
    try:
        st = hook_file.stat()
        hook_file.chmod(st.st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    except OSError:
        pass
    print(f"  + Hook:    {hook_file} (executable set)")


def init_scaffold(
    target_dir: Path = Path("."),
    use_agent_dir: bool = False,
    hierarchical: bool = False,
    skip_agents_md: bool = False,
    skip_hooks: bool = False,
    force: bool = False,
) -> None:
    repo_root = target_dir.resolve()
    if not repo_root.exists() or not repo_root.is_dir():
        print(f"Error: Target directory '{repo_root}' does not exist.", file=sys.stderr)
        sys.exit(1)

    scaffold_dir = (repo_root / ".agent") if use_agent_dir else repo_root
    scaffold_dir.mkdir(parents=True, exist_ok=True)

    print("\n====================================================================")
    print(f" SDCS v{SPEC_VERSION} Initializer :: 7-Pillar Cognitive Scaffolding")
    print(f" Target Root: {repo_root}")
    print(f" Harness Dir: {scaffold_dir}")
    print(f" Mode:        {'Hierarchical' if hierarchical else 'Flat Cartography'}")
    print("====================================================================\n")

    # 1. Primary Pillars
    write_file(scaffold_dir / "spine.md", TEMPLATE_SPINE, force)
    write_file(scaffold_dir / "wiring.yaml", TEMPLATE_WIRING, force)
    write_file(scaffold_dir / "roadmap.md", TEMPLATE_ROADMAP, force)
    write_file(scaffold_dir / "state.md", TEMPLATE_STATE, force)
    write_file(scaffold_dir / "decisions.md", TEMPLATE_DECISIONS, force)
    write_file(scaffold_dir / "evals.md", TEMPLATE_EVALS, force)

    # 2. Cartography (Pillar 5)
    if hierarchical:
        generate_hierarchical_cartography(repo_root, scaffold_dir, force)
    else:
        flat_map = generate_flat_app_map(repo_root)
        write_file(scaffold_dir / "app_map.md", flat_map, force)

    # 3. Flight Recorder Infrastructure
    sessions_dir = scaffold_dir / "sessions"
    sessions_dir.mkdir(parents=True, exist_ok=True)
    template_session = TEMPLATE_SESSION_HANDOFF.format(timestamp="YYYY-MM-DD HH:MM UTC")
    write_file(sessions_dir / "template.md", template_session, force)

    # 4. Authoring Protocol (/grillme)
    prompts_dir = scaffold_dir / "prompts"
    prompts_dir.mkdir(parents=True, exist_ok=True)
    write_file(prompts_dir / "grillme.md", generate_grillme_md(), force)

    # 5. Behavioral Contract
    if not skip_agents_md:
        write_file(repo_root / "AGENTS.md", TEMPLATE_AGENTS, force)

    # 6. Git Invariant Protection Hook
    if not skip_hooks:
        install_githook(repo_root)

    # Ensure a basic fixture file exists so audit doesn't break
    fixture_dir = repo_root / "tests" / "fixtures"
    fixture_dir.mkdir(parents=True, exist_ok=True)
    init_fixture = fixture_dir / "init.txt"
    if not init_fixture.exists():
        init_fixture.write_text("SDCS Golden Test Fixture Placeholder\n", encoding="utf-8")
        print(f"  + Fixture: {init_fixture}")

    print("\n[OK] Scaffolding complete.")
    if not skip_hooks:
        print("\nTo activate invariant enforcement in your local repository, run:")
        print("  git config core.hooksPath .githooks")
        print("  git config sdcs.mode advisory   # or 'strict'")
    print()


def main():
    parser = argparse.ArgumentParser(
        description="Bootstrap the 7-Pillar Spec-Driven Cognitive Scaffolding (SDCS) Architecture."
    )
    parser.add_argument(
        "--target-dir", default=".", help="Root repository directory (default: current directory)"
    )
    parser.add_argument(
        "--use-agent-dir",
        action="store_true",
        help="Place SDCS pillars inside .agent/ control directory",
    )
    parser.add_argument(
        "--hierarchical",
        action="store_true",
        help="Generate hierarchical multi-tiered cartography maps",
    )
    parser.add_argument("--skip-agents-md", action="store_true", help="Skip generating AGENTS.md")
    parser.add_argument(
        "--skip-hooks",
        action="store_true",
        help="Skip generating .githooks/pre-commit protection hook",
    )
    parser.add_argument("--force", action="store_true", help="Overwrite existing scaffolding files")
    parser.add_argument(
        "--grill",
        action="store_true",
        help="Display the /grillme adversarial spec elicitation prompt and exit",
    )
    parser.add_argument(
        "--milestone",
        type=str,
        default=None,
        help="Target milestone ID (e.g. M-001) for --grill output",
    )

    args = parser.parse_args()

    if args.grill:
        print(generate_grillme_md(args.milestone))
        sys.exit(0)

    init_scaffold(
        target_dir=Path(args.target_dir),
        use_agent_dir=args.use_agent_dir,
        hierarchical=args.hierarchical,
        skip_agents_md=args.skip_agents_md,
        skip_hooks=args.skip_hooks,
        force=args.force,
    )


if __name__ == "__main__":
    main()
