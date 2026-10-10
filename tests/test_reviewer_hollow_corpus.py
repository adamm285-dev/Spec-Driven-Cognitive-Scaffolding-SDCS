"""The reviewer's hollow-test corpus, run through Gate Q.

Measured 2026-09-22 against v1.8.1 (e08a789): Gate Q flagged 4 of the 13 hollow tests.
v1.8.1's "100% catch rate" was measured on hollow tests written by the same agent that
wrote the fix, so it could only find the blind spots the author already knew about.
This corpus came from someone else.

The corpus is fixtures/reviewer_hollow_corpus.py.txt -- see its header for why it is not
a .py file, and for the second-pass revision. Every test_H* must be flagged; every test_C*
must not be. test_U* are not asserted: syntax cannot separate them from sound tests.

The controls are what stop H* from being fixed by flagging more. The first pass had too
few, and a gate fitted to it passed 25/25 while flagging five sound Floorsmith tests.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from sdcs.verifier.quality import audit_test_quality_file

CORPUS = Path(__file__).parent / "fixtures" / "reviewer_hollow_corpus.py.txt"


def _corpus_test_names() -> list[str]:
    tree = ast.parse(CORPUS.read_text(encoding="utf-8"))
    return sorted(
        n.name
        for n in ast.walk(tree)
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name.startswith("test_")
    )


HOLLOW = [n for n in _corpus_test_names() if n.startswith("test_H")]
SOUND = [n for n in _corpus_test_names() if n.startswith("test_C")]
UNDECIDABLE = [n for n in _corpus_test_names() if n.startswith("test_U")]


@pytest.fixture(scope="module")
def flagged(tmp_path_factory) -> dict[str, str]:
    target = tmp_path_factory.mktemp("reviewer_corpus") / "test_reviewer_corpus.py"
    target.write_text(CORPUS.read_text(encoding="utf-8"), encoding="utf-8")
    return {v.function_name: v.rule for v in audit_test_quality_file(target)}


def test_the_corpus_carries_both_populations():
    """A yardstick with one population measures nothing."""
    assert len(HOLLOW) == 11
    assert len(SOUND) == 15
    assert len(UNDECIDABLE) == 2


@pytest.mark.parametrize("name", HOLLOW)
def test_gate_q_flags_the_hollow_test(name, flagged):
    assert name in flagged, f"{name} is hollow and Gate Q let it through"


@pytest.mark.parametrize("name", SOUND)
def test_gate_q_passes_the_sound_test(name, flagged):
    assert name not in flagged, f"{name} is sound and Gate Q flagged it: {flagged.get(name)}"
