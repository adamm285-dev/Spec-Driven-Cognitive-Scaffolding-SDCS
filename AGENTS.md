# AGENTS.md :  Operational Harness Protocol
<!-- Conforming to SPEC-001 v1.9.0 -->

## 1. Turn 1 Boot Hydration Order (7 Pillars) & Hot-Path Execution
Scale-Adaptive Boot Context:
- **When `# [PRE-HYDRATED SOURCE FILES]` (or `# [CacheForge Zero-Read Workspace Bundle]`) is present in your prompt:**
  1. The exact verbatim contents of the workspace `.py` files are already in your prompt. Do **NOT** call `list_files` or `read_file` on those files.
  2. Untouched helper methods collapsed to `...` do not need modification; leave collapsed `...` stubs untouched and pass only the exact verbatim target function/class lines as `Target` to `edit_file`.
  3. When implementing a baseline `TASK.md` specification (where `TASK.md` is already on disk), start editing the target `.py` files on Turn 1 using `edit_file`.
  4. Whenever a user message introduces multi-package or mid-session sprint requirements that are NOT in `TASK.md`, your **VERY FIRST tool call** MUST be `edit_file` on `state.md` to lock all newly requested requirements (including exact parameter names, default values, formulas, inequalities, return shapes, and ordering rules) BEFORE editing any `.py` files!
  5. Do not read `spine.md`, `roadmap.md`, `decisions.md`, `evals.md`, `MOCKS.md`, or `app_map.md` on boot. They are on-disk reference manuals consulted only when a gate triggers or when navigating unhydrated directories.
- **When working in a large repository (> 4,000 source tokens) where `# [AST SKELETAL INTERFACES]` and `app_map.md` are hydrated:**
  1. Whenever a user message introduces multi-package or mid-session sprint requirements that are NOT in `TASK.md`, your **VERY FIRST tool call** MUST be `edit_file` on `state.md` to record every requirement's exact parameter names, default values, formulas/inequalities, return types, and target `.py` file paths (using `app_map.md` and `# [AST SKELETAL INTERFACES]`) BEFORE reading or editing any `.py` code files!
  2. Then call `read_file` only on the specific target file you are about to edit (unless already pre-hydrated in `# [CacheForge Zero-Read Workspace Bundle]`), and apply surgical `edit_file` changes.

**Fast resume (Post-Reset / Session 2):** After compaction or a session reset, read `state.md` (`## Current Objective` and `## Immediate Next Action`) first and compare every listed requirement and edge-case rule against the pre-hydrated source files. If any requirement or validation parameter in `state.md` is missing from any target module, use `edit_file` to wire it immediately before running `run_tests` and calling `finish`.

**Flight Recorder Invariant:** Do not read `sessions/*.md` on boot. They are immutable history, not working memory; loading them wastes tokens and pulls in stale context. Query them on demand when debugging (`sdcs session`, `sessions/manifest.jsonl`).

## 2. Working Memory (`state.md` <= 500 Tokens) & Mid-Session Spec Lock
- Keep exactly three headings: `## Current Objective`, `## Status & Gate Verification`, `## Immediate Next Action`. Stay at or under 500 tokens (Gate S) by using concise 1-line bullets per package while preserving exact formulas (`<=` vs `>=`, cap scope, return dict/tuple shapes, and explain-plan ordering).
- **Write new requirements down first (Never summarize completed baseline work).** Whenever a user message introduces multi-package or mid-session sprint requirements:
  1. Your **VERY FIRST tool call** after receiving that message **MUST** be `edit_file` on `state.md`. Write **ONLY the newly requested sprint requirements** (preserving exact parameter names, default values, formulas, inequalities, return shapes, and ordering rules) under `## Current Objective` and list the target `.py` files under `## Immediate Next Action` **BEFORE** reading or editing any `.py` code files.
  2. Then use `edit_file` to implement the newly requested requirements across all affected modules.
- Whenever you change code or the requirements change, update `state.md` (marking completed items `- [x]`) and commit it together with the code, so verified progress is in git history. Make a commit (`commit` or `finish`) your last action before a session ends: anything edited after your final commit, `state.md` included, is lost.

## Before You Finish
Passing tests are not proof the task is done, because test suites often predate newly added requirements.
Before calling `finish`:
1. Check your active context to ensure every initial and mid-session requirement is implemented across all affected modules and recorded in `state.md` under `## Current Objective`.
2. Do NOT call `read_file` to re-read files that are already in your context or that you just edited.
3. Once all requirements are implemented, `state.md` is updated (marking completed items `- [x]`), and tests pass (run `sdcs check` or `pytest -q`), call `finish` (or `commit`) immediately.

## Critical Commit Invariant
Uncommitted changes are permanently deleted (`git reset --hard`) when a session ends!
Whenever you receive "This session is ending. Commit your work now", you MUST call `commit` or `finish` immediately. Never spend your final turns on additional edits without committing.

## 0. What SDCS Is (7-Pillar Architecture & Gate Reference)
You will lose your memory. Context resets, compaction, and new sessions erase what you learned. Spec-Driven Cognitive Scaffolding (SDCS) exists so the next agent (often you, an hour from now) can resume exactly where you stopped, without re-exploring the repo or repeating failed attempts.

It does this with 7 Pillars, each with one job:
- `state.md`: what is happening right now. The handoff note for the next agent.
- `roadmap.md`: where the project is going. Each milestone states its `[INTENT]` and its `[MEASURED]` result.
- `spine.md`, `wiring.yaml`: the rules and the module boundaries. You may add new modules to `wiring.yaml`; never loosen what is already there.
- `app_map.md`: where things live, so you don't have to search.
- `decisions.md`: what was tried and rejected, so nobody tries it again.
- `evals.md`: what has been verified to work, locked by SHA-256 fixture hashes.
- `sessions/`: past shift logs. A flight recorder, read only when debugging.

When a gate fails, its name tells you what to fix:
- **Gate T** (`sdcs verify --topology`): an import crosses a boundary declared in `wiring.yaml`.
- **Gate M** (`sdcs map --check`): `app_map.md` no longer matches the files on disk.
- **Gate S** (`sdcs verify --state`): `state.md` is over budget or missing a heading.
- **Gate C** (pre-commit hook): the commit touches `spine.md` or `wiring.yaml`. Only a human can approve it, by setting `SDCS_ALLOW_INVARIANT_MUTATION=1`; ask, never set it yourself.
- **Gate L** (`sdcs verify --mocks`): a `MOCK(M-NNN)` marker and its `MOCKS.md` entry disagree.
- **Gate Q** (`sdcs verify --quality`): a test is hollow or mocks the thing it should test.
- The sandbox, secret, environment, cache-prefix, and cycle gates are listed in `sdcs verify --help`. `sdcs verify --all` runs every gate.

## 3. Working Rules
- **Navigate from the map:** Find paths in `app_map.md` (`sdcs map -s <subsystem>` gives a focused slice), signatures in `# [AST SKELETAL INTERFACES]`, and source in `# [PRE-HYDRATED SOURCE FILES]` instead of scanning directories or re-reading pre-hydrated files.
- **Check boundaries before importing:** Every new `import` must be allowed by `allowed_dependencies` in `wiring.yaml`.
- **Wiring Mutation Invariant:** When you add a subsystem, module, or package, add it to `wiring.yaml` in the same change. Never loosen an existing boundary, add a cycle, or edit `wiring.yaml` to get past a Gate T rejection.
- **Respect the graveyard:** Don't retry an approach or revert a decision recorded in `decisions.md` unless its "WHAT WOULD REOPEN IT" condition is met or a human signs off.
- **No task queue in the roadmap:** Active tasks live in `state.md`.
- **Mock Ledger Invariant (Gate L):** Product code that stands in for real behavior (simulated responses, seeded or hardcoded data, demo-only keys or endpoints, offline stubs) gets a `MOCK(M-NNN)` comment marker and a matching `MOCKS.md` entry in the same commit. Add and remove them together. Never add a fallback that reports a failed call as a success.
- **Verify before reporting done:** Run `sdcs check` (which runs `pytest -q`, syncs `app_map.md` and `evals.md` SHA-256 hashes, and verifies all SDCS gates in a single 3-line receipt) or `sdcs verify --all`.

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
