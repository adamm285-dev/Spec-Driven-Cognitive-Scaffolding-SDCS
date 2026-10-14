# Release Notes: Spec-Driven Cognitive Scaffolding (SDCS) v1.9.1

**Released:** 2026-10-14 · **Spec:** SPEC-001 v1.9.1 · **Replaces:** v1.9.0

v1.9.1 upgrades **Gate L (`sdcs verify --mocks`)** from a reconciliation-only gate into an active **undeclared mock detector (`REQ-GATE-L-01`)** and **static fake-success fallback blocker (`REQ-GATE-L-06`)**, alongside `/grillme` Gate L integration and documentation enhancements.

---

## 🎯 The Problem: Undeclared Mocks on Existing & Unmarked Code

In v1.9.0, Gate L verified bidirectional agreement once a `# MOCK(M-NNN)` tag or `MOCKS.md` entry existed, but relied on the honor system for the initial `# MOCK(M-NNN)` tag and treated `REQ-GATE-L-06` ("No Fake Success") as a policy rule. On an existing repository or when an agent introduced `_mock_completion(...)` or `except HTTPError: return self._mock_completion(...)` without adding `# MOCK(M-NNN)`, `sdcs verify --mocks` passed silently.

## 🚀 Key Highlights in v1.9.1

### 1. 🔍 Active Undeclared Mock Detection (`REQ-GATE-L-01`)
- Statically scans Python AST and polyglot product code for unmarked mocks:
  - **Mock & Simulated Definitions:** Functions, methods, and classes matching `_mock_*`, `mock_*`, `fake_*`, `dummy_*`, `canned_*`, `simulated_*`.
  - **Mock-Mode & Simulated State:** `mock_mode` / `use_mock` parameters, `mock_mode=True` call keyword arguments, and `_simulated_*` / `simulated_delay` / `mock_data` attributes and variables.
  - **Simulated Latency Sleeps:** `time.sleep(...)` / `asyncio.sleep(...)` called with `simulated_*` delay variables or paired with comments/docstrings stating they simulate latency, TTFT, tool execution, or RPC I/O.
  - **Placeholder Credential Fallbacks:** `os.environ.get("..._API_KEY", "<placeholder-token>")`.
  - **Seeded Baselines & Static Stubs:** `# Seed baseline...` / `# Pre-seed...` comments, zero-request `# ... baseline` fallback returns (`return 0.90  # Benchmark baseline`), hardcoded stub epoch timestamps (`created: 1700000000`), and static Chart.js `datasets` arrays without `.update()`.
- Enforces **method-level marker isolation** inside classes so marking `Class.__init__` does not mask an unmarked `Class._mock_response` method on the same class.

### 2. 🛡️ Static Enforcement of `REQ-GATE-L-06` ("No Fake Success")
- Audits Python `ast.ExceptHandler` and polyglot `catch` blocks that return or yield without re-raising.
- Unconditionally rejects exception handlers that return mock/simulated calls (`return await self._mock_completion(...)`), fake-success status dicts (`{"status": "ok" | "success" | "healthy" | "online"}`, `{"is_simulated": True}`), or `# Fall back to simulation` returns—**even when declared with a `# MOCK(M-NNN)` marker**.

### 3. 🎙️ `/grillme` Adversarial Spec Protocol & Documentation Enhancements
- Upgraded `/grillme` (`prompts/grillme.md`, `src/sdcs/init.py`, `sdcs_init.py`) with explicit Gate L (`MOCKS.md`), Gate T (`wiring.yaml`), and Gate Q (`tests/`) interrogation.
- Updated `README.md` with Layer 2 `MOCKS.md` placement and the Greenfield One-Shot Velocity Pattern, and refreshed `media/slides/slide_01.png`.

## ✅ Verification
- Framework suite: **239 passed** (`13/13` Gate L tests in `tests/test_mocks.py`).
- `sdcs verify --all` passes all 10 kinetic gates on the SDCS repository with **0 false positives**.
- Validated against an untouched downstream repository (`CacheForge` `HEAD 5d9fbb0`): catches **20/20 violations** across all 10 undeclared mocks (`M-001`–`M-010`) and `REQ-GATE-L-06`.

## 📦 Upgrading to v1.9.1
```bash
pip install --upgrade sdcs
sdcs verify --mocks
```
