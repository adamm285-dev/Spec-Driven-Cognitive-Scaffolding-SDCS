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


def test_unittest_testcase_assertions_pass(tmp_path: Path):
    """Verify standard unittest.TestCase assertions and helpers pass Gate Q without false positives."""
    test_code = """
import unittest

class MyTestCase(unittest.TestCase):
    def test_equality(self):
        result = 20 * 2
        self.assertEqual(result, 40)
        self.assertTrue(result > 30)
        self.assertIn("key", {"key": "value"})
        self.assertIsNotNone(result)

    def test_with_helper(self):
        data = [1, 2, 3]
        check_all_positive(data)

    def test_raises_context(self):
        with self.assertRaises(ZeroDivisionError):
            _ = 1 / 0
"""
    test_file = tmp_path / "test_unittest_suite.py"
    test_file.write_text(test_code, encoding="utf-8")

    violations = audit_test_quality_file(test_file)
    assert len(violations) == 0


def test_unittest_trivial_assertion_rejected(tmp_path: Path):
    """Verify trivial unittest calls like self.assertTrue(True) are rejected."""
    test_code = """
import unittest

class MyTestCase(unittest.TestCase):
    def test_trivial(self):
        self.assertTrue(True)

    def test_trivial_eq(self):
        self.assertEqual(1, 1)
"""
    test_file = tmp_path / "test_unittest_trivial.py"
    test_file.write_text(test_code, encoding="utf-8")

    violations = audit_test_quality_file(test_file)
    assert len(violations) == 2
    assert all(v.rule == "Q1_TRIVIAL_ASSERTION" for v in violations)


def test_helper_in_same_file_with_assertions_passes(tmp_path: Path):
    """Verify that a test calling a helper function in the same file that asserts passes."""
    test_code = """
def _custom_check(val):
    assert val > 0

def test_via_helper():
    x = 42
    _custom_check(x)
"""
    test_file = tmp_path / "test_helper.py"
    test_file.write_text(test_code, encoding="utf-8")

    violations = audit_test_quality_file(test_file)
    assert len(violations) == 0


def test_no_raise_pragma_passes(tmp_path: Path):
    """Verify that tests explicitly declaring no-raise intent pass Gate Q."""
    test_code = """
def test_operation_runs_cleanly():
    # sdcs: no-raise
    result = sum(range(100))

def test_handler_does_not_raise():
    x = 10 * 5
"""
    test_file = tmp_path / "test_norise.py"
    test_file.write_text(test_code, encoding="utf-8")

    violations = audit_test_quality_file(test_file)
    assert len(violations) == 0


def test_self_fail_counts_as_assertion(tmp_path: Path):
    """Verify that self.fail or pytest.fail is treated as an active test assertion."""
    test_code = """
import unittest

class FailureTest(unittest.TestCase):
    def test_unreachable_branch(self):
        try:
            do_something_bad()
            self.fail("Should have raised exception")
        except ExpectedError:
            pass
"""
    test_file = tmp_path / "test_fail.py"
    test_file.write_text(test_code, encoding="utf-8")

    violations = audit_test_quality_file(test_file)
    assert len(violations) == 0


def test_trivial_only_if_all_checks_are_trivial(tmp_path: Path):
    """A test with assert x is not None alongside real assertions must NOT be flagged as trivial."""
    test_code = """
import unittest

class MixedTest(unittest.TestCase):
    def test_mixed_assertions(self):
        data = {"count": 10}
        assert data is not None
        self.assertEqual(data["count"], 10)
        self.assertTrue(data["count"] > 5)
"""
    test_file = tmp_path / "test_mixed.py"
    test_file.write_text(test_code, encoding="utf-8")

    violations = audit_test_quality_file(test_file)
    assert len(violations) == 0
