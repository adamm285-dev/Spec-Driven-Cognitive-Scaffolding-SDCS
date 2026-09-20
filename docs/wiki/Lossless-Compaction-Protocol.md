# Lossless Compaction Protocol ("prepare for compact")

In extended autonomous coding shifts spanning dozens of turns, AI context windows inevitably fill up. Environments like **Claude Code (`/compact`)**, **Cursor** resets, or **Gemini CLI** context rollovers periodically summarize the chat log.

When an un-scaffolded agent undergoes compaction, it suffers from **Compaction Amnesia**: active hypothesis chains, test states, and mental cartography are wiped out. The agent wakes up on post-compact Turn 1 confused, prone to regressions, and repeating measured errors.

SDCS eliminates Compaction Amnesia through the **Mid-Shift Checkpoint Protocol ("prepare for compact")** and the **Wiring Mutation Invariant (Pillar 2)**.

---

## The 4 Operational Dimensions

| Dimension | Specification Contract | Operational Behavior |
| :--- | :--- | :--- |
| **WHY** | **Lossless Memory Persistence** | Guarantees zero context loss. Fine-grained history is externalized to the immutable flight recorder, while active working memory is trimmed to $\le 300$ tokens so Turn 1 hydration is immediate. |
| **WHEN** | **1. Human Trigger:** `"prepare for compact"`<br>**2. Token Saturation (70–80%)**<br>**3. Milestone Completion** | Triggered mid-shift whenever the developer types `"prepare for compact"` before running `/compact`, or when token usage nears context exhaustion. |
| **WHERE** | **Cross-Pillar Synchronization:**<br>• `wiring.yaml` (Pillar 2)<br>• `sessions/*.md` (+1 Flight Recorder)<br>• `state.md` (Pillar 4)<br>• `decisions.md` (Pillar 6)<br>• `app_map.md` (Pillar 5)<br>• `roadmap.md` (Pillar 3) | Checkpoints are written to physical disk files before memory is cleared. |
| **HOW** | **5-Step Mechanical Checklist** | The agent mechanically executes the 5-step checklist and emits an explicit readiness signal before compaction proceeds. |

---

## The 5-Step Checkpoint Execution Checklist

```
[Developer: "prepare for compact" or Token Saturation Nears]
                             │
                             ▼
  1. Topology Audit              ──► Runs `sdcs verify --topology` to audit wiring.yaml
                             │
                             ▼
  2. Flight Recorder Snapshot    ──► Writes immutable log to `sessions/YYYY-MM-DD_<topic>.md`
                             │
                             ▼
  3. Blackboard Pruning          ──► Prunes `state.md` strictly to ≤ 300 tokens
                             │
                             ▼
  4. Episodic Memory Sweeps      ──► Records failed approaches to `decisions.md` & runs `sdcs map --sync`
                             │
                             ▼
  5. Compact Readiness Signal    ──► Emits confirmation: "Ready for compaction."
```

### 1. Topology & Subsystem Audit
Run `sdcs verify --topology` to verify that all imports comply with `wiring.yaml`. If new modules or packages were created during the shift, ensure they are declared in `wiring.yaml`.

### 2. Flight Recorder Checkpoint
Write an immutable checkpoint log to `sessions/YYYY-MM-DD_<topic>.md` capturing:
* Work completed during the shift.
* Current verification status and gate standing.
* Active blockers or open questions.
* Immediate post-compact next steps.
* Update `sessions/manifest.jsonl` via `sdcs session index`.

### 3. Blackboard Pruning (`state.md`)
Aggressively prune and overwrite `state.md` strictly to $\le 300$ tokens containing only:
```markdown
## Current Objective
[Concise active milestone goal]

## Status & Gate Verification
[Passing gates: Gate T, Gate M, Gate C, Gate A, Gate E]

## Immediate Next Action (Post-Compact)
[Next exact file to edit or test to run]
```

### 4. Episodic Memory Sweeps
* Log any rejected approaches or failed experiments to `decisions.md`.
* Synchronize `app_map.md` if files were created, moved, or deleted (`sdcs map --sync`).
* Update `roadmap.md` `[MEASURED]` blocks if milestones or acceptance criteria were met.

### 5. Readiness Signal
Output a brief confirmation:
> *"All 7 pillars and the flight recorder are synchronized. Ready for compaction."*

The developer then triggers `/compact` or restarts the session. On post-compact Turn 1, the agent reads the clean $\le 300$-token `state.md` and resumes engineering with zero amnesia.
