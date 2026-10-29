# AGENTS.md — Operational Harness Protocol
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

**Fast resume:** After compaction or a restart, read `state.md` first. If `## Immediate Next Action` names an unfinished step, check that its target files exist and recent tests still pass, then do that step. Skip the whole-repo survey.

**Flight Recorder Invariant:** Do not read `sessions/*.md` on boot. They are immutable history, not working memory; loading them wastes tokens and pulls in stale context. Query them on demand when debugging (`sdcs session`, `sessions/manifest.jsonl`).

## 2. Working Memory (`state.md`)
- Keep exactly three headings: `## Current Objective`, `## Status & Gate Verification`, `## Immediate Next Action`. Stay at or under 300 tokens (Gate S).
- Record what the next agent can't get elsewhere: the objective, newly added parameter and field names, gate results, modules not yet verified, and the next step. Don't copy `app_map.md` or signature inventories into it.
- Whenever you change code or the requirements change, update `state.md` and commit it together with the code, so verified progress is in git history.
- Passing tests don't prove a task is done. Existing suites often cover only the original spec, not requirements added mid-session. When new requirements arrive, wire every parameter, field, default, and return key through all affected modules. After a resume, check each requirement recorded in `state.md` against the source before calling the task complete.

## 3. Working Rules
- **Navigate from the map:** Find paths in `app_map.md` (`sdcs map -s <subsystem>` gives a focused slice) and signatures in `# [AST SKELETAL INTERFACES]` instead of scanning directories. Confirm the real symbols with a targeted search before editing; the map can be stale.
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
