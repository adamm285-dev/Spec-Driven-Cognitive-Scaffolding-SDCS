"""Gate C-Cache: which files it reads, and what it calls volatile.

Written by the reviewing agent, 2026-09-22 (gate audit, batch 1). On Floorsmith the gate
read one file, AGENTS.md, and printed "Server-side KV cache discount (75-90%) is
preserved". It never reads CLAUDE.md, the instruction file Claude Code loads into every
session. And it judges text by its SHAPE: a static instruction "step 2 of 6" is flagged as
a dynamic step counter, although nothing about it changes between turns. What breaks a
prompt cache is content that CHANGES between requests, which no single read of a file can
see.
"""

from __future__ import annotations

from pathlib import Path

from sdcs.verifier.cache import audit_prefix_invariance, run_cache_invariance_audit


def test_a_static_instruction_is_not_a_step_counter():
    text = "Close-out, step 2 of 6: write the handoff before pruning state.md."
    assert audit_prefix_invariance(text) == []


def test_claude_md_is_audited(tmp_path: Path):
    """A turn counter in CLAUDE.md must be seen -- it is the file Claude Code loads.

    A clean AGENTS.md sits beside it, so the audit has a file to pass and cannot fail for
    the wrong reason (finding nothing at all).
    """
    (tmp_path / "AGENTS.md").write_text("# Agreement\nRender before asserting.\n", encoding="utf-8")
    (tmp_path / "CLAUDE.md").write_text("You are on Turn 3 of 20.\n", encoding="utf-8")
    assert run_cache_invariance_audit(tmp_path) != 0
