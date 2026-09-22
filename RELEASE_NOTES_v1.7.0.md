# Release Notes: Spec-Driven Cognitive Scaffolding (SDCS) v1.7.0

> **Release Tag**: `v1.7.0`  
> **Date**: September 22, 2026  
> **Conforms To**: SPEC-001 v1.7.0  
> **PyPI**: `pip install --upgrade sdcs`  
> **Test Telemetry**: 101/101 Passed (100% Green in Pytest)  

---

## 🏢 The Furnished Office Metaphor: Why SDCS?

> **The Bot** is the *Brain* without arms (LLM reasoning & inference).  
> **The Harness** is the Brain's *arms & hands* (execution loop, shell access, tool calling).  
> **Skills** are the *tools held in the hands* (linters, APIs, test runners, git).  
> **SDCS** is the **Furnished Office** (the constitutional rules on the wall, the floor plan, the central whiteboard, the rejection graveyard, the kinetic bouncer, and the central warehouse).

Without the furnished office, an autonomous agent worker is dropped into an empty, pitch-black room with a box of tools and no lighting. It blindly runs frantic `find` and `grep` loops (burning 2,000 tokens before writing a single line of code), invents non-existent file paths, and repeatedly attempts yesterday's measured failures.

**SDCS v1.7.0 furnishes the office with deterministic cybernetic lighting:**

---

## 🚀 Key Highlights in v1.7.0

### 1. 🎮 The Living Pixel Office HUD (`sdcs watch`)
A zero-dependency local HTTP and Server-Sent Events (SSE) server bridging real-time repository telemetry to an animated **16-bit isometric pixel-art HUD** (conforming to the Grok Bot / Clanker Town indie game aesthetic):
- **Interactive Room Hotspots**:
  - **Dev Desk**: Live worker speech bubble showing active objective, immediate next action, and token budget.
  - **Server Room / Kinetic Bouncer**: Real-time status for all 8 kinetic enforcement gates.
  - **Central Whiteboard**: Live `state.md` token density gauge ($\le 350$ tokens) and raw blackboard view.
  - **Negative Memory Graveyard**: Active dead-end counter and rejection summaries from `decisions.md`.
  - **Central Warehouse**: Federated cognitive trap count and Gate W secret sanitization status.
  - **Empirical Evals**: Test fixture pass ratio and SHA-256 fixture locks.
- **60 FPS Animated Sprite Engine**: Bot characters physically walk, bob, and pathfind across the office floor using click-to-move, toolbar dispatch, or autonomous wander routines.
- **Reactive Event Streaming**: Streams live telemetry over Server-Sent Events (`GET /api/events`) whenever `state.md`, `evals.md`, `decisions.md`, or `sessions/manifest.jsonl` are touched during autonomous coding turns.
- **Zero External Dependencies**: Built entirely on Python's standard library `http.server.ThreadingHTTPServer`.

```bash
# Launch the living office HUD (opens http://127.0.0.1:8765)
sdcs watch

# Run in headless or CI environments on a custom port
sdcs watch --no-browser --port 8765
```

---

### 2. ⚡ The Autonomous Safety Triad
Closes the critical behavioral and operational blind spots of frontier autonomous coding agents:
1. **The Circuit Breaker (`sdcs verify --cycles` / `src/sdcs/verifier/cycles.py`)**:
   - Static transition-graph analyzer tracking touched file sets across consecutive commits and turns.
   - Detects period-2 alternating thrashing loops ($A \to B \to A \to B$) and isolated single-file thrashing, halting the agent before tokens are burned on infinite edit loops.
2. **Gate Q (Test Quality & Anti-Mock AST Auditor, `sdcs verify --quality`)**:
   - Statically inspects test ASTs to reject "hollow tests":
     - `assert True`, `assert not False`, `assert x is not None`
     - Assertless test functions
     - Swallowed test failures (`try...except Exception: pass`)
     - Mock abuse exceeding assertions without invoking the target unit.
3. **Gate E & System Diagnostic Doctor (`sdcs doctor` & `sdcs verify --env`)**:
   - Locks runtime interpreter versions, CLI tools (`git`, `pytest`), and required environment variables declared in `wiring.yaml` or `pyproject.toml`.
   - Prevents agents from refactoring working application code when failures stem from local environment drift.
   - Provides a comprehensive diagnostic health report for human architects.

---

### 3. 🛡️ The Full 8-Gate Kinetic Enforcement Suite
In SDCS v1.7.0, all 8 kinetic gates and the Circuit Breaker are wired into `.githooks/pre-commit` and `sdcs verify --all`:

| Tier | Gate | Name | Command | Physical Failure Prevented |
| :--- | :--- | :--- | :--- | :--- |
| **Spatial** | **Gate C** | Constitutional Immutability | Pre-commit | Unauthorized mutation of `spine.md` or `wiring.yaml`. |
| **Spatial** | **Gate T** | Topological Invariant Gate | `sdcs verify --topology` | Prohibited AST cross-subsystem imports violating `wiring.yaml`. |
| **Spatial** | **Gate P** | Blast-Radius Sandbox Guard | `sdcs verify --sandbox` | Staging modifications within declared `protected_paths`. |
| **Spatial** | **Gate M** | Cartography Drift Gate | `sdcs map --check` | Commits with untracked new files or orphaned paths in `app_map.md`. |
| **Cognitive**| **Gate S** | Working Memory Budget Gate | `sdcs verify --state` | Context window amnesia (`state.md` > 350 tokens) & subagent lifecycle. |
| **Fleet** | **Gate W** | Secret & PII Sanitizer | `sdcs warehouse publish` | Leaking API keys, tokens, emails, or IPs to central warehouse. |
| **Quality** | **Gate Q** | Test Quality & Anti-Mock Gate | `sdcs verify --quality` | Hollow tests, trivial asserts, or swallowed exceptions. |
| **Toolchain**| **Gate E** | Toolchain & Environment Gate | `sdcs doctor` / `--env` | Blaming valid application code on tool or interpreter drift. |
| **Circuit** | **Breaker**| The Circuit Breaker | `sdcs verify --cycles` | Alternating period-2 file thrashing and token burn loops. |

---

### 4. 🧠 Organizational Memory & Context Compilation
- **Single-Pass Deterministic Context Compiler (`sdcs hydrate`)**: Compiles pre-budgeted context payloads (Lite ~400t, Standard ~1500t, Full ~3500t) eliminating the "Grep Reflex" on boot.
- **Central Cognitive Warehouse (`sdcs warehouse`)**: Cross-project organizational memory engine federating rejections, traps, and failure modes across agent fleets with automated Gate W secret sanitization.
- **Parallel Worker Ephemeral Blackboards (`sdcs state fork/rollup`)**: Scoped subagent blackboards (`state.<worker_id>.md`) with deterministic parent rollup.
- **Automated Staleness Decay (`sdcs decay`)**: Scans commit distance in `roadmap.md` and tags stale telemetry; automatically archives dead-end rejections exceeding active limits.

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

# Launch real-time Living Office HUD
sdcs watch
```

### Full Verification
```bash
# Run comprehensive diagnostic report
sdcs doctor

# Run all 8 kinetic gates and circuit breaker
sdcs verify --all
```

---

## 📊 Empirical Test Telemetry
- **Test Suite**: 101/101 PASSED (100% green in pytest)
- **Gate S**: 296 / 350 tokens (disciplined)
- **Gate M**: 100% CLEAN cartography
- **Distribution Integrity**: `twine check` PASSED on both `.whl` and `.tar.gz`
