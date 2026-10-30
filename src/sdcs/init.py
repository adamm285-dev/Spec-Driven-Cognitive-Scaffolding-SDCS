"""
sdcs.init - Spec-Driven Cognitive Scaffolding (SDCS) Initializer
Conforming to SPEC-001 v1.9.0

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
  +  MOCKS.md        — Mock Ledger (Gate L)
  +  .githooks/      — Invariant Lock & State Sync Git Hook
"""

import argparse
import os
import stat
import subprocess
import sys
from pathlib import Path

SPEC_VERSION = "1.9.0"

# -----------------------------------------------------------------------------
# Pillar Templates
# -----------------------------------------------------------------------------

TEMPLATE_SPINE = """# Constitutional Invariants (The Law)
<!-- SPEC-001 v1.9.0 Pillar 1 | Mutability: IMMUTABLE (Human-Only) -->

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
- Bypassing pre-commit hooks via `--no-verify` (enforced via agent harness permission boundary).
- Reading `sessions/*.md` flight recorder archives during Turn 1 boot hydration.
"""

TEMPLATE_WIRING = """# Declarative Topology (The Mesh)
# SPEC-001 v1.9.0 Pillar 2 | Mutability: STATIC (Explicit PR)

version: "1.9.0"
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

sandbox:
  protected_paths:
    - ".env*"
    - "*.jks"
    - "*.pem"
    - "*.key"
    - "credentials/**"
  allowed_commands:
    - "pytest"
    - "git"
    - "python"
    - "ruff"
    - "sdcs"
  prohibited_flags:
    - "--no-verify"
    - "-f"
    - "--force"

contracts:
  strict_imports: true
  circular_dependencies: false

# Central Cognitive Warehouse Integration (SPEC-001 v1.6.0)
warehouse:
  source: ""                  # Local path or git URL to central warehouse repository
  cache_dir: "~/.sdcs/warehouse"
  subscriptions:
    tags: []                  # Subscribed tags (e.g., ["telecom", "android", "stripe"])
    severity_floor: "advisory" # critical | high | medium | advisory
  auto_sync: false            # false = use local cache without blocking network calls
"""

TEMPLATE_ROADMAP = """# Macro Acceptance Contract (The North Star)
<!-- SPEC-001 v1.9.0 Pillar 3 | Mutability: BIMODAL ([INTENT] vs [MEASURED]) -->
<!-- Iron Invariant: NO TASK QUEUES. Ephemeral tasks belong exclusively in state.md -->

## Milestone M-001: Initial Operational Capability
* [INTENT]: Scaffold and bootstrap the repository under SPEC-001 v1.9.0 invariants. Verify zero test fixture drift.
* [MEASURED]: Scaffolding complete; initial evals verified via SHA-256 audit. Status: VERIFIED.

<!--
Template for New Milestones:
## Milestone M-XXX: [Descriptive Milestone Name]
* [INTENT]: [Human acceptance criteria: explicit latencies, memory ceilings, error rates]
* [MEASURED]: [Empirical telemetry: test results, benchmark data, git commit hashes]
-->
"""

TEMPLATE_STATE = """# Dynamic Working Memory (The Blackboard)
<!-- SPEC-001 v1.9.0 Pillar 4 | Mutability: HIGH VOLATILITY | Budget: <= 300 Tokens -->
<!-- Read on Turn 1 boot. Strictly pruned after milestone completion. -->

## Current Objective
- Complete repository bootstrapping and verify invariant enforcement hooks.

## Status & Gate Verification
- Gate T: AST topology verified via `sdcs verify`.
- Gate Q: Visible unit tests tracked via `pytest`.
- Gate S: Token budget <= 300 tokens.

## Immediate Next Action
- Inspect pre-hydrated source modules and implement active specification requirements.
"""

TEMPLATE_DECISIONS = """# Negative Episodic Memory (The Graveyard)
<!-- SPEC-001 v1.9.0 Pillar 6 | Mutability: APPEND-ONLY -->
<!-- Mandatory 3-part schema: Claim -> Measurement -> Reopen Condition -->

## REJ-001: Monolithic Session Diary Ingestion
- **The Claim:** Ingesting all past session logs on Turn 1 boot provides comprehensive historical context.
- **The Measurement:** Exhausted 28k tokens of context window within 3 conversational turns; induced severe context drift and hallucinated file boundaries.
- **What Would Reopen It:** LLM architecture with sub-linear attention latency and zero needle-in-a-haystack degradation beyond 1M tokens.
"""

TEMPLATE_EVALS = """# Empirical Standing & Ground Truth (Evals)
<!-- SPEC-001 v1.9.0 Pillar 7 | Mutability: CRYPTOGRAPHIC -->
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

TEMPLATE_MOCKS = """# MOCKS.md: Mock Inventory (Gate L)
<!-- SPEC-001 v1.9.0 Mock Ledger | Mutability: IN-STRIDE (same commit as the mock) -->

Every place where product code stands in for real behavior: simulated API responses, seeded or
hardcoded data, demo-only keys or endpoints, offline stubs, and fallbacks that fake success.
Test doubles are out of scope (Gate Q audits tests).

**Markers.** Mark each mock where it lives with a comment carrying its ID: `# MOCK(M-NNN): <what it fakes>`
(`// MOCK(M-NNN): ...` in JS/TS, Go, Rust, Java and similar). `sdcs verify --mocks` fails if a marker has no
entry, an entry has no marker, an entry and its markers list different files, or a listed `path::symbol`
does not exist.

**Format.** One `### M-NNN: title` heading per entry (real IDs use digits, e.g. M-001), then four fields:

- **Where:** one or more backticked `path::symbol` (Python: `function`, `Class`, `Class.method` or a
  module-level name; other languages: a declared function, class, const or method name)
- **What it fakes:** the real behavior this replaces
- **Why:** why the mock exists
- **To make it real:** what replacing it requires

Never reuse an ID. When a mock is removed, delete its markers and its entry together and list the ID
under "Retired IDs".

**Retired IDs:** none
"""

TEMPLATE_AGENTS = """# AGENTS.md — Operational Harness Protocol
<!-- Conforming to SPEC-001 v1.9.0 -->

## 0. What SDCS Is
You will lose your memory. Context resets, compaction, and new sessions erase what you learned. Spec-Driven Cognitive Scaffolding (SDCS) exists so the next agent (often you, an hour from now) can resume exactly where you stopped, without re-exploring the repo or repeating failed attempts.

It does this with a few files, each with one job:
- `state.md`: what is happening right now. The handoff note for the next agent.
- `roadmap.md`: where the project is going. Each milestone states its `[INTENT]` and its `[MEASURED]` result.
- `spine.md`, `wiring.yaml`: the rules and the module boundaries. You may add new modules to `wiring.yaml`; never loosen what is already there.
- `app_map.md`: where things live, so you don't have to search.
- `decisions.md`: what was tried and rejected, so nobody tries it again.
- `evals.md`: what has been verified to work, locked by SHA-256 fixture hashes.
- `sessions/`: past shift logs. A flight recorder, read only when debugging.

Rules you could forget are enforced by `sdcs verify` gates and the pre-commit hook. A rejected commit is the system working, not an obstacle to route around. Your job: do the user's task, and leave these files more accurate than you found them.

When a gate fails, its name tells you what to fix:
- **Gate T** (`sdcs verify --topology`): an import crosses a boundary declared in `wiring.yaml`.
- **Gate M** (`sdcs map --check`): `app_map.md` no longer matches the files on disk.
- **Gate S** (`sdcs verify --state`): `state.md` is over budget or missing a heading.
- **Gate C** (pre-commit hook): the commit touches `spine.md` or `wiring.yaml`. Only a human can approve it, by setting `SDCS_ALLOW_INVARIANT_MUTATION=1`; ask, never set it yourself.
- **Gate L** (`sdcs verify --mocks`): a `MOCK(M-NNN)` marker and its `MOCKS.md` entry disagree.
- **Gate Q** (`sdcs verify --quality`): a test is hollow or mocks the thing it should test.
- The sandbox, secret, environment, cache-prefix, and cycle gates are listed in `sdcs verify --help`. `sdcs verify --all` runs every gate.

## 1. Turn 1 Boot Hydration Order (7 Pillars)
If your prompt already contains `SDCS DETERMINISTIC CONTEXT COMPILER` (the output of `sdcs hydrate`), all 7 pillars, `# [AST SKELETAL INTERFACES]`, and `# [PRE-HYDRATED SOURCE FILES]` are already loaded. Do not re-read those files, on boot or after compaction; start work on Turn 1.

Otherwise, read the pillars in this order, or get them in one call with `sdcs hydrate --profile standard [-s <subsystem>]` (`lite` and `full` profiles also exist):
1. `spine.md`: invariants and forbidden actions (Pillar 1)
2. `roadmap.md`: the active milestone, `[INTENT]` vs `[MEASURED]` (Pillar 3)
3. `app_map.md`: resolve target paths here before searching (Pillar 5)
4. `decisions.md`: rejected approaches (Pillar 6)
5. `evals.md`: the verified baseline (Pillar 7)
6. `state.md`: current working memory (Pillar 4)
7. `wiring.yaml`: subsystem boundaries (Pillar 2)

**Fast resume:** After compaction or a restart, read `state.md` first. Check every requirement recorded in `state.md` against `# [PRE-HYDRATED SOURCE FILES]` (or on disk if not pre-hydrated) to confirm all affected modules are wired and tests pass, then execute any remaining step in `## Immediate Next Action`. Skip the whole-repo survey.

**Flight Recorder Invariant:** Do not read `sessions/*.md` on boot. They are immutable history, not working memory; loading them wastes tokens and pulls in stale context. Query them on demand when debugging (`sdcs session`, `sessions/manifest.jsonl`).

## 2. Working Memory (`state.md`)
- Keep exactly three headings: `## Current Objective`, `## Status & Gate Verification`, `## Immediate Next Action`. Stay at or under 300 tokens (Gate S).
- Record what the next agent can't get elsewhere: the objective, newly added parameter and field names, gate results, modules not yet verified, and the next step. Don't copy `app_map.md` or signature inventories into it.
- **Write new requirements down first.** When a requirement arrives mid-task, add one line for it under `## Current Objective` before you start implementing it, naming the fields, parameters, or behaviors it adds. If the session ends partway through, the next agent still knows the requirement exists; one that never reaches `state.md` is lost.
- Whenever you change code or the requirements change, update `state.md` and commit it together with the code, so verified progress is in git history. Make a commit your last action before a session ends: anything edited after your final commit, `state.md` included, is lost.
- When new requirements arrive, wire every parameter, field, default, and return key through all affected modules.

## Before You Finish
Passing tests are not proof the task is done. Test suites often predate the requirements you were given, so they can pass while those requirements are missing.
Before declaring the task complete:
1. List every requirement recorded in `state.md` under `## Current Objective`.
2. For each one, name the file and the function, field, or parameter that implements it, confirmed by reading the code now, not from memory.
3. A requirement without a location is not done: implement it, then repeat.
If budget remains and anything is unverified, use it.

## 3. Working Rules
- **Navigate from the map:** Find paths in `app_map.md` (`sdcs map -s <subsystem>` gives a focused slice), signatures in `# [AST SKELETAL INTERFACES]`, and source in `# [PRE-HYDRATED SOURCE FILES]` instead of scanning directories or re-reading pre-hydrated files. When source files are not pre-hydrated in your prompt, confirm the real symbols with a targeted read or search before editing.
- **Check boundaries before importing:** Every new `import` must be allowed by `allowed_dependencies` in `wiring.yaml`.
- **Wiring Mutation Invariant:** When you add a subsystem, module, or package, add it to `wiring.yaml` in the same change. Never loosen an existing boundary, add a cycle, or edit `wiring.yaml` to get past a Gate T rejection.
- **Respect the graveyard:** Don't retry an approach or revert a decision recorded in `decisions.md` unless its "WHAT WOULD REOPEN IT" condition is met or a human signs off.
- **No task queue in the roadmap:** Active tasks live in `state.md`.
- **Mock Ledger Invariant (Gate L):** Product code that stands in for real behavior (simulated responses, seeded or hardcoded data, demo-only keys or endpoints, offline stubs) gets a `MOCK(M-NNN)` comment marker and a matching `MOCKS.md` entry in the same commit. Add and remove them together. Never add a fallback that reports a failed call as a success.
- **Verify before reporting done:** Run the tests, typechecks, and `sdcs verify --all`. When you add or change a test fixture, re-record it with `sdcs eval record <Asset-ID>|all` (or `sdcs audit`).

## 4. When to Update the Other Files
Update each one only when its trigger happens:
- `app_map.md`: files or directories were created, moved, or deleted. Run `sdcs map --sync`. Editing existing files needs no update.
- `wiring.yaml`: a new subsystem or module was added. Run `sdcs verify --topology` afterwards.
- `decisions.md`: an approach was tried and rejected. Append an entry that says what would reopen it.
- `evals.md`: golden fixtures were added or modified. Run `sdcs eval record` or `sdcs audit`.
- `roadmap.md` and `sessions/`: a milestone is complete. Update its `[MEASURED]` block and write a handoff log to `sessions/YYYY-MM-DD_<topic>.md` (`sdcs session index`).

## 5. Checkpoint Before Compaction ("prepare for compact")
When told to "prepare for compact", or when your context is nearly full:
1. Run `sdcs verify --topology`.
2. Rewrite `state.md` per Section 2, with a next step precise enough to resume from cold.
3. Apply any Section 4 trigger that fired this session, and write a checkpoint to `sessions/YYYY-MM-DD_<topic>.md` (`sdcs session index`).
4. Reply with a brief confirmation ending in "Ready for compaction."
"""

TEMPLATE_SESSION_HANDOFF = """# Engineering Shift Handoff
<!-- Flight Recorder: Immutable historical log. Do NOT ingest on system boot. -->

## Date & Session
- Timestamp: {timestamp}
- Shift Focus: Repository Initial Scaffolding

## Completed Actions
- Initialized SPEC-001 v1.9.0 cognitive scaffolding.
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
  TAMPERED_INVARIANTS=$(git diff --cached --name-only | grep -E '^(spine\\.md|wiring\\.yaml|\\.agent/spine\\.md|\\.agent/wiring\\.yaml|docs/spine\\.md|docs/wiring\\.yaml)$')
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
STATE_TOUCHED=$(git diff --cached --name-only | grep -E '^(state\\.md|\\.agent/state\\.md|docs/state\\.md)$' || true)

if [ "${DIFF_LINES:-0}" -ge 40 ]; then
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

# Resolve Python interpreter for static verification gates (Gate T, Gate M)
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

# 2b. Working Memory Token Budget & Schema Gate (Gate S: state.md <= 350 tokens)
STATE_FILE=""
if [ -f "state.md" ]; then
  STATE_FILE="state.md"
elif [ -f ".agent/state.md" ]; then
  STATE_FILE=".agent/state.md"
elif [ -f "docs/state.md" ]; then
  STATE_FILE="docs/state.md"
fi

if [ -n "$STATE_FILE" ] && [ -n "$STATE_TOUCHED" ]; then
  if [ -n "$PYTHON_BIN" ]; then
    if ! "$PYTHON_BIN" -m sdcs.cli verify --state --max-tokens 350; then
      if [ "$SDCS_MODE" = "strict" ]; then
        echo "===================================================================="
        echo " [SDCS ERROR] GATE S: WORKING MEMORY TOKEN BUDGET EXCEEDED"
        echo "===================================================================="
        echo "state.md exceeds the 350-token budget ceiling or has schema violations."
        echo "Please prune state.md to <= 300 tokens before committing."
        echo "===================================================================="
        exit 1
      else
        echo "--------------------------------------------------------------------"
        echo " [SDCS ADVISORY] Gate S: state.md exceeds 350 tokens or has schema warnings."
        echo "--------------------------------------------------------------------"
      fi
    fi
  fi
fi

# 2c. Declarative Sandbox & Protected Paths Gate (Gate P: wiring.yaml sandbox)
if [ "$SDCS_ALLOW_SANDBOX_OVERRIDE" != "1" ]; then
  if [ -n "$PYTHON_BIN" ]; then
    if ! "$PYTHON_BIN" -m sdcs.cli verify --sandbox; then
      if [ "$SDCS_MODE" = "strict" ]; then
        echo "===================================================================="
        echo " [SDCS ERROR] GATE P: SANDBOX PROTECTED PATH VIOLATION"
        echo "===================================================================="
        echo "Staged files violate sandbox protected_paths declared in wiring.yaml."
        echo "To override: export SDCS_ALLOW_SANDBOX_OVERRIDE=1"
        echo "===================================================================="
        exit 1
      else
        echo "--------------------------------------------------------------------"
        echo " [SDCS ADVISORY] Gate P: Sandbox protected path modification detected."
        echo "--------------------------------------------------------------------"
      fi
    fi
  fi
fi

# 3. Topological Invariant Gate (Gate T: wiring.yaml AST audit)
WIRING_FILE=""
if [ -f "wiring.yaml" ]; then
  WIRING_FILE="wiring.yaml"
elif [ -f ".agent/wiring.yaml" ]; then
  WIRING_FILE=".agent/wiring.yaml"
elif [ -f "docs/wiring.yaml" ]; then
  WIRING_FILE="docs/wiring.yaml"
fi

if [ -n "$WIRING_FILE" ]; then
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

# 4. Cartography Drift Gate (Gate M: app_map.md drift audit)
MAP_FILE=""
if [ -f "app_map.md" ]; then
  MAP_FILE="app_map.md"
elif [ -f ".agent/app_map.md" ]; then
  MAP_FILE=".agent/app_map.md"
elif [ -f "docs/app_map.md" ]; then
  MAP_FILE="docs/app_map.md"
fi

if [ -n "$MAP_FILE" ]; then
  if [ -z "$PYTHON_BIN" ]; then
    echo "⚠️ [SDCS Warning] No functional Python interpreter found to run Gate M verification."
  else
    if ! "$PYTHON_BIN" -m sdcs.cli map --check; then
      if [ "$SDCS_MODE" = "strict" ]; then
        echo "===================================================================="
        echo " [SDCS VIOLATION] GATE M: CARTOGRAPHY DRIFT DETECTED"
        echo "===================================================================="
        echo "One or more files on disk are unmapped in $MAP_FILE or orphaned."
        echo "Run 'sdcs map --sync' to reconcile cartography with disk."
        echo "Stage $MAP_FILE and re-commit:"
        echo "  sdcs map --sync && git add $MAP_FILE"
        echo "===================================================================="
        exit 1
      else
        echo "--------------------------------------------------------------------"
        echo " [SDCS ADVISORY] Gate M: Cartography drift detected."
        echo " Run 'sdcs map --sync' to reconcile $MAP_FILE with disk."
        echo "--------------------------------------------------------------------"
      fi
    fi
  fi
fi

# 5. Circuit Breaker Gate (Gate Cycles: thrashing & oscillation detection)
if [ -n "$PYTHON_BIN" ]; then
  if ! "$PYTHON_BIN" -m sdcs.cli verify --cycles; then
    if [ "$SDCS_MODE" = "strict" ]; then
      echo "===================================================================="
      echo " [SDCS VIOLATION] CIRCUIT BREAKER TRIPPED: CYCLIC THRASHING DETECTED"
      echo "===================================================================="
      echo "Repeated file oscillation or ping-ponging detected across recent commits."
      echo "Halted to prevent token exhaustion and repository damage."
      echo "===================================================================="
      exit 1
    else
      echo "--------------------------------------------------------------------"
      echo " [SDCS ADVISORY] Circuit breaker warning: file oscillation detected."
      echo "--------------------------------------------------------------------"
    fi
  fi
fi

# 6. Test Quality & Anti-Mock Gate (Gate Q: test assertion audits)
if [ -n "$PYTHON_BIN" ]; then
  if ! "$PYTHON_BIN" -m sdcs.cli verify --quality; then
    if [ "$SDCS_MODE" = "strict" ]; then
      echo "===================================================================="
      echo " [SDCS VIOLATION] GATE Q: TEST QUALITY / ANTI-MOCKING REJECTION"
      echo "===================================================================="
      echo "One or more test files contain hollow tests, assertless tests, or mock abuse."
      echo "Provide substantive assertions before committing."
      echo "===================================================================="
      exit 1
    else
      echo "--------------------------------------------------------------------"
      echo " [SDCS ADVISORY] Gate Q: Test quality warning detected."
      echo "--------------------------------------------------------------------"
    fi
  fi
fi

# 6b. Mock Ledger Gate (Gate L: MOCKS.md vs MOCK markers in product code)
if [ -n "$PYTHON_BIN" ]; then
  if ! "$PYTHON_BIN" -m sdcs.cli verify --mocks; then
    if [ "$SDCS_MODE" = "strict" ]; then
      echo "===================================================================="
      echo " [SDCS VIOLATION] GATE L: MOCK LEDGER OUT OF SYNC"
      echo "===================================================================="
      echo "MOCKS.md and the MOCK markers in the code disagree (see list above)."
      echo "Add or remove the ledger entry or marker in this same commit."
      echo "===================================================================="
      exit 1
    else
      echo "--------------------------------------------------------------------"
      echo " [SDCS ADVISORY] Gate L: Mock ledger out of sync with the code."
      echo "--------------------------------------------------------------------"
    fi
  fi
fi

# 7. Environment Invariant Gate (Gate E: toolchain & runtime checks)
if [ -n "$PYTHON_BIN" ]; then
  if ! "$PYTHON_BIN" -m sdcs.cli verify --env; then
    if [ "$SDCS_MODE" = "strict" ]; then
      echo "===================================================================="
      echo " [SDCS VIOLATION] GATE E: ENVIRONMENT INVARIANT MISMATCH"
      echo "===================================================================="
      echo "Toolchain or runtime environment mismatch detected."
      echo "DO NOT edit application code to circumvent environment errors."
      echo "Fix your local interpreter, tools, or environment variables."
      echo "===================================================================="
      exit 1
    else
      echo "--------------------------------------------------------------------"
      echo " [SDCS ADVISORY] Gate E: Environment mismatch detected."
      echo "--------------------------------------------------------------------"
    fi
  fi
fi

# 8. Secret & PII Sanitization Gate (Gate W: decisions.md and staged files)
if [ -n "$PYTHON_BIN" ]; then
  if ! "$PYTHON_BIN" -m sdcs.cli verify --warehouse; then
    if [ "$SDCS_MODE" = "strict" ]; then
      echo "===================================================================="
      echo " [SDCS VIOLATION] GATE W: SENSITIVE CREDENTIAL OR SECRET DETECTED"
      echo "===================================================================="
      echo "Unscrubbed credentials or secrets detected in negative memory or staged files."
      echo "Scrub sensitive tokens before committing."
      echo "===================================================================="
      exit 1
    else
      echo "--------------------------------------------------------------------"
      echo " [SDCS ADVISORY] Gate W: Sensitive credential pattern detected."
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
<!-- Conforming to SPEC-001 v1.9.0 -->

Act as a relentless Principal Systems Architect. Your objective is to interrogate the human stakeholder, eliminate ambiguity, and extract falsifiable, production-grade requirements to populate `roadmap.md` ([INTENT]), `spine.md` (Constitutional Invariants), `wiring.yaml` (Subsystem Topology), and `MOCKS.md` (Gate L Mock Ledger).

## RULES
1. **Zero Tolerance for Vague Adjectives:** Reject subjective words like "fast", "scalable", "clean", "intuitive", "robust", or "secure". Demand concrete behavior.
2. **Demand Exact Numerical Ceilings & Floors:** Require exact empirical thresholds (e.g., p99 latency <= 50ms, RPS >= 500, memory ceiling <= 384MB, branch coverage >= 90%).
3. **Probe Hidden Failure Modes & Blast Radii:** Interrogate edge cases, network partitions, corrupted payloads, concurrency spikes, race conditions, and error recovery.
4. **Enforce Boundary & Topological Integrity (Gate T):** Interrogate which subsystems in `wiring.yaml` own each responsibility. Prohibit unplanned cross-boundary couplings or circular dependencies.
5. **Interrogate Mock Dependencies & Stand-Ins (Gate L):**
   - Identify external services, APIs, databases, or hardware dependencies up front.
   - If real dependencies are unavailable, demand explicit declaration of permissible product mocks.
   - Require every potential mock to have: Where (`path::symbol`), What it fakes, Why, and concrete criteria for "To make it real".
   - Establish whether the milestone acceptance contract requires 0 standing mocks (`sdcs verify --mocks` clean with empty ledger) before completion.
6. **Consult the Rejection Graveyard (decisions.md):** Verify the proposed approach does not resurrect dead ends already measured and rejected in `decisions.md`. Demand what empirical condition has changed if revisiting past trade-offs.
7. **Anchor to Positive Ground Truth (evals.md & Gate Q):** Demand the specific golden reference test fixture and ensure acceptance tests verify non-trivial behavior without hollow asserts (`assert True`) or swallowed exceptions.
8. **Enforce Falsifiable Acceptance Formatting:** Interrogate until the milestone acceptance criteria can be written verbatim as:
   * `* [INTENT]: Concrete, non-negotiable production criteria with exact floors, ceilings, and mock limits.`
   * `* [MEASURED]: Verifiable test/benchmark assertion (e.g. Commit <hash>, 41.2ms p99 at 500 RPS, Gate L 0 mocks, Gate Q PASS). Gate PASSED/PENDING.`

## INTERVIEW WORKFLOW
1. **Scoping:** Ask the user for the primary objective of {target_text}.
2. **Assumption & Boundary Attack:** Identify the single biggest unstated assumption, missing boundary, or external dependency.
3. **Failure & Mock Interrogation:**
   - Challenge the assumption with a concrete edge case failure scenario.
   - Ask: "How will this handle external system unavailability? Will you permit temporary mocks under Gate L (`MOCKS.md`), and what is the exact criterion to make them real?"
4. **Tolerance Hardening:** Demand the exact numerical thresholds, memory ceilings, and test fixtures required for production acceptance.
5. **Contract Synthesis:** Once hardened, output the finalized markdown block ready to be committed directly into `roadmap.md` (and updates for `spine.md` or `wiring.yaml` if invariants mutate).
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
    """Index files grouped by directory, filtering noisy runtime artifacts and respecting gitignore."""
    if (root / ".git").exists():
        try:
            res = subprocess.run(
                ["git", "ls-files", "--cached", "--others", "--exclude-standard"],
                cwd=root,
                capture_output=True,
                text=True,
                check=False,
            )
            if res.returncode == 0:
                tree: dict[str, list[str]] = {}
                for raw_path in res.stdout.splitlines():
                    path_str = raw_path.strip().replace("\\", "/")
                    if not path_str:
                        continue
                    parts = path_str.split("/")
                    if any(
                        part in EXCLUDE_DIRS or part.endswith(".egg-info") for part in parts[:-1]
                    ):
                        continue
                    fname = parts[-1]
                    if fname.endswith((".pyc", ".pyo", ".so", ".DS_Store", "Thumbs.db")):
                        continue
                    if len(parts) == 1:
                        rel_dir = "root"
                    else:
                        rel_dir = "/".join(parts[:-1])
                    tree.setdefault(rel_dir, []).append(fname)
                for file_list in tree.values():
                    file_list.sort()
                return dict(sorted(tree.items()))
        except (subprocess.SubprocessError, OSError):
            pass

    tree = {}
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
        "<!-- SPEC-001 v1.9.0 Pillar 5 | Flat Cartography -->",
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
        "<!-- SPEC-001 v1.9.0 Pillar 5 | Hierarchical Master Index -->",
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


CANONICAL_PAGES = [
    "spine.md",
    "wiring.yaml",
    "roadmap.md",
    "state.md",
    "decisions.md",
    "evals.md",
    "app_map.md",
]


def normalize_legacy_casing(target_dir: Path) -> list[tuple[str, str]]:
    """
    Detects legacy uppercase or mixed-case SDCS filenames (e.g. STATE.md, SPINE.md)
    and normalizes them to canonical lowercase to prevent Windows NTFS case-insensitivity
    collisions and git index phantom duplicates.
    """
    if not target_dir.is_dir():
        return []

    normalized = []
    canonical_map = {name.lower(): name for name in CANONICAL_PAGES}

    for item in list(target_dir.iterdir()):
        if not item.is_file():
            continue
        lower_name = item.name.lower()
        if lower_name in canonical_map:
            canonical_name = canonical_map[lower_name]
            if item.name != canonical_name:
                temp_file = item.parent / f".sdcs_norm_{item.name}.tmp"
                target_file = item.parent / canonical_name
                try:
                    git_res = subprocess.run(
                        ["git", "mv", "-f", item.name, temp_file.name],
                        cwd=str(target_dir),
                        capture_output=True,
                        text=True,
                    )
                    if git_res.returncode == 0:
                        subprocess.run(
                            ["git", "mv", "-f", temp_file.name, canonical_name],
                            cwd=str(target_dir),
                            capture_output=True,
                            text=True,
                        )
                    else:
                        item.rename(temp_file)
                        temp_file.rename(target_file)
                    normalized.append((item.name, canonical_name))
                    print(f"  * Normalized casing: {item.name} -> {canonical_name}")
                except Exception as ex:
                    print(
                        f"  ⚠️ Warning: Failed to normalize casing for {item.name}: {ex}",
                        file=sys.stderr,
                    )
    return normalized


def write_file(path: Path, content: str, force: bool = False):
    if path.parent.exists():
        for sibling in path.parent.iterdir():
            if (
                sibling.is_file()
                and sibling.name.lower() == path.name.lower()
                and sibling.name != path.name
            ):
                temp_file = sibling.parent / f".sdcs_norm_{sibling.name}.tmp"
                try:
                    sibling.rename(temp_file)
                    temp_file.rename(path)
                    print(f"  * Normalized casing: {sibling.name} -> {path.name}")
                except Exception:
                    pass
                break

    if path.exists() and not force:
        print(f"  · Exists:  {path} (skipping)")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.strip() + "\n", encoding="utf-8")
    print(f"  + Created: {path}")


def find_existing_pillar(repo_root: Path, filename: str) -> Path | None:
    """Finds if a pillar file already exists anywhere in the repository outside test/transient dirs."""
    name_lower = filename.lower()
    priority_subdirs = [
        Path("."),
        Path(".agent"),
        Path("docs"),
        Path("docs/map"),
        Path("docs/architecture"),
        Path("docs/spec"),
        Path("docs/specs"),
    ]
    for pdir in priority_subdirs:
        cand = repo_root / pdir / filename
        if cand.is_file():
            return cand
        cand_dir = repo_root / pdir
        if cand_dir.is_dir():
            for child in cand_dir.iterdir():
                if child.is_file() and child.name.lower() == name_lower:
                    return child

    for dirpath, dirnames, filenames_in_dir in os.walk(repo_root):
        dirnames[:] = [
            d for d in dirnames if d not in EXCLUDE_DIRS and d not in ("tests", "fixtures", "test")
        ]
        for f in filenames_in_dir:
            if f.lower() == name_lower:
                return Path(dirpath) / f

    return None


def write_pillar_file(
    scaffold_dir: Path,
    repo_root: Path,
    filename: str,
    content: str,
    force: bool = False,
):
    target = scaffold_dir / filename
    if not force:
        existing = find_existing_pillar(repo_root, filename)
        if existing:
            if existing.resolve() == target.resolve():
                print(f"  · Exists:  {existing} (skipping)")
            else:
                try:
                    rel = existing.relative_to(repo_root)
                except ValueError:
                    rel = existing
                print(f"  · Exists elsewhere: {rel} (skipping root {filename})")
            return
    write_file(target, content, force=force)


def install_githook(root: Path, force: bool = False) -> bool:
    """Installs the invariant protection pre-commit hook into .githooks/."""
    hook_dir = root / ".githooks"
    hook_dir.mkdir(parents=True, exist_ok=True)
    hook_file = hook_dir / "pre-commit"

    if hook_file.exists() and not force:
        print(f"  · Exists:  {hook_file} (skipped; use --force to overwrite)")
        return False

    hook_file.write_text(TEMPLATE_PRE_COMMIT_HOOK, encoding="utf-8")
    try:
        st = hook_file.stat()
        hook_file.chmod(st.st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    except OSError:
        pass
    print(f"  + Hook:    {hook_file} (executable set)")
    return True


def is_hooks_path_set(repo_root: Path) -> bool:
    """Checks if git core.hooksPath is already configured to .githooks."""
    try:
        res = subprocess.run(
            ["git", "config", "core.hooksPath"],
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            check=False,
        )
        return res.returncode == 0 and res.stdout.strip() in (".githooks", ".githooks/")
    except Exception:
        return False


def init_scaffold(
    target_dir: Path = Path("."),
    use_agent_dir: bool = False,
    use_docs_dir: bool = False,
    hierarchical: bool = False,
    skip_agents_md: bool = False,
    skip_hooks: bool = False,
    force: bool = False,
) -> None:
    repo_root = target_dir.resolve()
    if not repo_root.exists() or not repo_root.is_dir():
        print(f"Error: Target directory '{repo_root}' does not exist.", file=sys.stderr)
        sys.exit(1)

    if use_docs_dir:
        scaffold_dir = repo_root / "docs"
    elif use_agent_dir:
        scaffold_dir = repo_root / ".agent"
    else:
        scaffold_dir = repo_root
    scaffold_dir.mkdir(parents=True, exist_ok=True)

    print("\n====================================================================")
    print(f" SDCS v{SPEC_VERSION} Initializer :: 7-Pillar Cognitive Scaffolding")
    print(f" Target Root: {repo_root}")
    print(f" Harness Dir: {scaffold_dir}")
    print(f" Mode:        {'Hierarchical' if hierarchical else 'Flat Cartography'}")
    print("====================================================================\n")

    # Normalize existing legacy casing (STATE.md -> state.md) before writing
    normalize_legacy_casing(scaffold_dir)
    if use_agent_dir:
        normalize_legacy_casing(repo_root)

    # 1. Primary Pillars (preserve files if already existing elsewhere in repo)
    write_pillar_file(scaffold_dir, repo_root, "spine.md", TEMPLATE_SPINE, force)
    write_pillar_file(scaffold_dir, repo_root, "wiring.yaml", TEMPLATE_WIRING, force)
    write_pillar_file(scaffold_dir, repo_root, "roadmap.md", TEMPLATE_ROADMAP, force)
    write_pillar_file(scaffold_dir, repo_root, "state.md", TEMPLATE_STATE, force)
    write_pillar_file(scaffold_dir, repo_root, "decisions.md", TEMPLATE_DECISIONS, force)
    write_pillar_file(scaffold_dir, repo_root, "evals.md", TEMPLATE_EVALS, force)
    write_pillar_file(scaffold_dir, repo_root, "MOCKS.md", TEMPLATE_MOCKS, force)

    # 2. Flight Recorder Infrastructure
    sessions_dir = scaffold_dir / "sessions"
    sessions_dir.mkdir(parents=True, exist_ok=True)
    template_session = TEMPLATE_SESSION_HANDOFF.format(timestamp="YYYY-MM-DD HH:MM UTC")
    write_file(sessions_dir / "template.md", template_session, force)

    # 3. Authoring Protocol (/grillme)
    prompts_dir = scaffold_dir / "prompts"
    prompts_dir.mkdir(parents=True, exist_ok=True)
    write_file(prompts_dir / "grillme.md", generate_grillme_md(), force)

    # 4. Behavioral Contract
    if not skip_agents_md:
        write_file(repo_root / "AGENTS.md", TEMPLATE_AGENTS, force)

    # 5. Git Invariant Protection Hook
    hook_installed = False
    if not skip_hooks:
        hook_installed = install_githook(repo_root, force=force)

    # Ensure a basic fixture file exists so audit doesn't break
    fixture_dir = repo_root / "tests" / "fixtures"
    fixture_dir.mkdir(parents=True, exist_ok=True)
    init_fixture = fixture_dir / "init.txt"
    if not init_fixture.exists():
        init_fixture.write_text("SDCS Golden Test Fixture Placeholder\n", encoding="utf-8")
        print(f"  + Fixture: {init_fixture}")

    # 6. Cartography (Pillar 5) - Generated after all scaffolding files exist
    if hierarchical:
        generate_hierarchical_cartography(repo_root, scaffold_dir, force)
    else:
        flat_map = generate_flat_app_map(repo_root)
        write_pillar_file(scaffold_dir, repo_root, "app_map.md", flat_map, force)

    print("\n[OK] Scaffolding complete.")
    if not skip_hooks and hook_installed:
        if not is_hooks_path_set(repo_root):
            print("\nTo activate invariant enforcement in your local repository, run:")
            print("  git config core.hooksPath .githooks")
            print("  git config sdcs.mode advisory   # or 'strict'")
        else:
            print("\nInvariant enforcement pre-commit hook active (core.hooksPath = .githooks).")
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
        "--use-docs-dir",
        action="store_true",
        help="Place SDCS pillars inside docs/ directory",
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
        use_docs_dir=args.use_docs_dir,
        hierarchical=args.hierarchical,
        skip_agents_md=args.skip_agents_md,
        skip_hooks=args.skip_hooks,
        force=args.force,
    )


if __name__ == "__main__":
    main()
