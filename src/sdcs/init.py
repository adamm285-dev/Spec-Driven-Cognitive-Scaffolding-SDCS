"""
sdcs.init - Spec-Driven Cognitive Scaffolding (SDCS) Initializer
Conforming to SPEC-001 v1.3.0

Scaffolds the complete 7-pillar deterministic cognitive harness:
  1. spine.md        — Constitutional Invariants
  2. wiring.yaml     — Declarative Topology
  3. roadmap.md      — Macro Acceptance Contract ([INTENT] vs [MEASURED])
  4. state.md        — Dynamic Working Memory (~300 token budget)
  5. app_map.md      — Repository Cartography (Hierarchical or Flat)
  6. decisions.md    — Negative Episodic Memory (Rejection Graveyard)
  7. evals.md        — Positive Ground Truth & Standing
  +  sessions/*.md   — Flight Recorder Shift Logs
  +  prompts/        — Authoring Protocols (/grillme)
  +  AGENTS.md       — Operational Hydration Contract
  +  .githooks/      — Invariant Lock & State Sync Git Hook
"""

import argparse
import os
import stat
import sys
from pathlib import Path

SPEC_VERSION = "1.3.0"

# -----------------------------------------------------------------------------
# Pillar Templates
# -----------------------------------------------------------------------------

TEMPLATE_SPINE = """# Constitutional Invariants (The Law)
<!-- SPEC-001 v1.2.0 Pillar 1 | Mutability: IMMUTABLE (Human-Only) -->

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
# SPEC-001 v1.2.0 Pillar 2 | Mutability: STATIC (Explicit PR)

version: "1.2"
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
<!-- SPEC-001 v1.2.0 Pillar 3 | Mutability: BIMODAL ([INTENT] vs [MEASURED]) -->
<!-- Iron Invariant: NO TASK QUEUES. Ephemeral tasks belong exclusively in state.md -->

## Milestone M-001: Initial Operational Capability
* [INTENT]: Scaffold and bootstrap the repository under SPEC-001 v1.2.0 invariants. Verify zero test fixture drift.
* [MEASURED]: Scaffolding complete; initial evals verified via SHA-256 audit. Status: VERIFIED.

<!--
Template for New Milestones:
## Milestone M-XXX: [Descriptive Milestone Name]
* [INTENT]: [Human acceptance criteria: explicit latencies, memory ceilings, error rates]
* [MEASURED]: [Empirical telemetry: test results, benchmark data, git commit hashes]
-->
"""

TEMPLATE_STATE = """# Dynamic Working Memory (The Blackboard)
<!-- SPEC-001 v1.2.0 Pillar 4 | Mutability: HIGH VOLATILITY | Budget: ~300 Tokens -->
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
<!-- SPEC-001 v1.2.0 Pillar 6 | Mutability: APPEND-ONLY -->
<!-- Mandatory 3-part schema: Claim -> Measurement -> Reopen Condition -->

## REJ-001: Monolithic Session Diary Ingestion
- **The Claim:** Ingesting all past session logs on Turn 1 boot provides comprehensive historical context.
- **The Measurement:** Exhausted 28k tokens of context window within 3 conversational turns; induced severe context drift and hallucinated file boundaries.
- **What Would Reopen It:** LLM architecture with sub-linear attention latency and zero needle-in-a-haystack degradation beyond 1M tokens.
"""

TEMPLATE_EVALS = """# Empirical Standing & Ground Truth (Evals)
<!-- SPEC-001 v1.2.0 Pillar 7 | Mutability: CRYPTOGRAPHIC -->
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
<!-- Conforming to SPEC-001 v1.2.0 -->

## Turn 1 Boot Hydration Order
On Turn 1 of any task, you MUST hydrate state in this exact sequence:
1. `spine.md`        -> Invariants & forbidden actions
2. `roadmap.md`      -> Active milestone [INTENT] vs [MEASURED]
3. `app_map.md`      -> Repository cartography (resolve target paths first)
4. `decisions.md`    -> Negative memory (rejected hypotheses)
5. `evals.md`        -> Verified empirical baseline
6. `state.md`        -> Turn-by-turn active working memory

CRITICAL INVARIANT: NEVER inspect or hydrate `sessions/*.md` on boot.

## Close-Out Protocol
Before completing your shift:
1. Prune and overwrite `state.md` (~300 token budget).
2. Update `roadmap.md` [MEASURED] blocks with real test telemetry.
3. If an attempted optimization failed, log it to `decisions.md`.
4. Emit an immutable handoff log to `sessions/YYYY-MM-DD_<topic>.md`.
"""

TEMPLATE_SESSION_HANDOFF = """# Engineering Shift Handoff
<!-- Flight Recorder: Immutable historical log. Do NOT ingest on system boot. -->

## Date & Session
- Timestamp: {timestamp}
- Shift Focus: Repository Initial Scaffolding

## Completed Actions
- Initialized SPEC-001 v1.2.0 cognitive scaffolding.
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
# 3. Topological Invariant Gate (Gate T: wiring.yaml AST audit)
WIRING_FILE=""
if [ -f "wiring.yaml" ]; then
  WIRING_FILE="wiring.yaml"
elif [ -f ".agent/wiring.yaml" ]; then
  WIRING_FILE=".agent/wiring.yaml"
fi

if [ -n "$WIRING_FILE" ]; then
  PYTHON_BIN="python3"
  if ! command -v python3 &> /dev/null; then
    PYTHON_BIN="python"
  fi

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
        "<!-- SPEC-001 v1.2.0 Pillar 5 | Flat Cartography -->",
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
        "<!-- SPEC-001 v1.2.0 Pillar 5 | Hierarchical Master Index -->",
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
