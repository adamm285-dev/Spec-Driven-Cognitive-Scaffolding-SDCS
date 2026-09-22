"""Tests for Gate Q: Test Quality and Anti-Mock AST Auditor."""

from pathlib import Path
from sdcs.verifier.quality import (
    audit_test_quality_file,
    run_quality_audit,
)


def test_clean_substantive_test_passes(tmp_path: Path):
    """Substantive test with real assertions and logic passes Gate Q."""
    test_code = """
def test_addition():
    x = 10 + 20
    assert x == 30
    assert x > 0

def test_exception():
    import pytest
    with pytest.raises(ValueError):
        raise ValueError("boom")
"""
    test_file = tmp_path / "test_math.py"
    test_file.write_text(test_code, encoding="utf-8")

    violations = audit_test_quality_file(test_file)
    assert len(violations) == 0


def test_q1_trivial_assertions_rejected(tmp_path: Path):
    """Trivial assertions like 'assert True' or 'assert x is not None' are rejected."""
    test_code = """
def test_trivial_true():
    result = "something"
    assert True

def test_trivial_not_none():
    data = {"key": "val"}
    assert data is not None
"""
    test_file = tmp_path / "test_trivial.py"
    test_file.write_text(test_code, encoding="utf-8")

    violations = audit_test_quality_file(test_file)
    rules = [v.rule for v in violations]
    assert "Q1_TRIVIAL_ASSERTION" in rules
    assert len(violations) == 2


def test_q2_assertless_test_rejected(tmp_path: Path):
    """A test that executes code but has zero assertions is rejected."""
    test_code = """
def test_silent_runner():
    x = [i * 2 for i in range(10)]
    y = sum(x)
    print("Computed:", y)
"""
    test_file = tmp_path / "test_silent.py"
    test_file.write_text(test_code, encoding="utf-8")

    violations = audit_test_quality_file(test_file)
    assert len(violations) == 1
    assert violations[0].rule == "Q2_ASSERTLESS_TEST"
    assert "test_silent_runner" in violations[0].function_name


def test_q3_swallowed_exception_rejected(tmp_path: Path):
    """A test that wraps logic in try/except Exception: pass is rejected."""
    test_code = """
def test_swallow_error():
    try:
        raise RuntimeError("flaky failure")
    except Exception:
        pass
    assert True
"""
    test_file = tmp_path / "test_swallow.py"
    test_file.write_text(test_code, encoding="utf-8")

    violations = audit_test_quality_file(test_file)
    rules = [v.rule for v in violations]
    assert "Q3_SWALLOWED_EXCEPTION" in rules


def test_q4_mock_abuse_rejected(tmp_path: Path):
    """A test that over-mocks without substantive execution is rejected."""
    test_code = """
from unittest.mock import patch, MagicMock

@patch("os.path.exists")
@patch("shutil.rmtree")
@patch("subprocess.run")
def test_overmocked(mock_sub, mock_rm, mock_exists):
    mock_exists.return_value = True
    assert True
"""
    test_file = tmp_path / "test_mocking.py"
    test_file.write_text(test_code, encoding="utf-8")

    violations = audit_test_quality_file(test_file)
    rules = [v.rule for v in violations]
    assert "Q4_MOCK_ABUSE" in rules or "Q1_TRIVIAL_ASSERTION" in rules


def test_js_ts_test_quality(tmp_path: Path):
    """Verify JavaScript/TypeScript test heuristics."""
    ts_code = """
describe('suite', () => {
    it('should work', () => {
        expect(true).toBe(true);
    });
});
"""
    ts_file = tmp_path / "suite.test.ts"
    ts_file.write_text(ts_code, encoding="utf-8")

    violations = audit_test_quality_file(ts_file)
    assert len(violations) == 1
    assert violations[0].rule == "Q1_TRIVIAL_ASSERTION"


def test_run_quality_audit_exit_code(tmp_path: Path):
    """Verify CLI audit returns 1 on violations and 0 on clean code."""
    # Bad test
    bad_file = tmp_path / "test_bad.py"
    bad_file.write_text("def test_foo():\n    assert True\n", encoding="utf-8")
    assert run_quality_audit(repo_root=tmp_path, target_paths=[bad_file]) == 1

    # Good test
    good_file = tmp_path / "test_good.py"
    good_file.write_text("def test_bar():\n    assert 2 + 2 == 4\n", encoding="utf-8")
    assert run_quality_audit(repo_root=tmp_path, target_paths=[good_file]) == 0
