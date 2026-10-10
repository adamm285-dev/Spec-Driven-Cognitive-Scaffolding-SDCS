# Release Notes: Spec-Driven Cognitive Scaffolding (SDCS) v1.9.0

**Released:** 2026-10-10 · **Spec:** SPEC-001 v1.9.0 · **Replaces:** v1.8.1

v1.9.0 adds **Gate L, the Mock Ledger**: a kinetic gate that makes agents declare every mock they put into product code, in the code and in one ledger, and fails when the two disagree.

---

## 🎯 The Problem: Mocks Found by Forensics

Agents working fast stand in simulated API responses, seeded data, demo-only keys and fallbacks for real behavior, then move on. Nobody records them, so reviewers find them by searching, usually after something has been presented as real. Gate Q already audits *test* doubles; nothing covered mocks in *product* code.

## 🚀 Key Highlights in v1.9.0

### 1. 🧾 Gate L: Mock Ledger Reconciliation (`sdcs verify --mocks`)
- Every product-code mock carries a comment marker, `# MOCK(M-NNN): <what it fakes>` (`// MOCK(M-NNN): ...` in JS/TS, Go, Rust, Java and similar).
- Every marker ID has one entry in `MOCKS.md` (repo root, `.agent/` or `docs/`) with `Where` (`path::symbol`), `What it fakes`, `Why` and `To make it real`.
- The gate rejects markers without entries, entries without markers, entries and markers that list different files, paths that don't exist, symbols that aren't defined (Python via the AST; other languages by declaration patterns), missing fields, duplicate IDs and malformed markers.
- Test paths, vendored and generated code are not scanned. No ledger and no markers passes; markers without a ledger fail.
- Included in `sdcs verify --all` and in the pre-commit hook (strict: reject; advisory: warn).

### 2. 🏗️ `sdcs init` scaffolds the ledger
- New repositories get a `MOCKS.md` template. An existing `MOCKS.md` at the root, in `.agent/` or in `docs/` is never overwritten.
- The `AGENTS.md` template lists Gate L and adds the Mock Ledger Invariant, including the rule that a fallback must never report a failed call as a success (SPEC-001 REQ-GATE-L-06; a policy rule, not something the gate can detect).
- The `AGENTS.md` wording now says the three layers *hold the 7 pillars*, to stop agents reading "three layers" as "three pillars".

### 3. 🩹 Fix: session index command
- `AGENTS.md` and its template told agents to run `sdcs session --sync`, which the CLI rejects. They now say `sdcs session index`.

### 4. 📐 SPEC-001 v1.9.0
- New Section 7.21, Gate L (REQ-GATE-L-01 to 06).

## ✅ Verification
- Framework suite: 235 passed (225 existing plus 10 new Gate L tests).
- `sdcs verify --all` passes on the framework repository, including Gate L.
- Validated against a downstream application repository with 19 declared mocks across Python and TypeScript.

## 📦 Also in this release
The post-1.8.1 work committed in `342492f` (Click benchmark pre-registration harness and kinetic gate remediation; see that commit and `state.md`).

## 📦 Upgrading to v1.9.0
```bash
pip install --upgrade sdcs
sdcs verify --mocks        # passes immediately if you have no mocks declared yet
sdcs init                  # adds MOCKS.md if missing; without --force it never overwrites existing files
```
