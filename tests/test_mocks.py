"""Tests for Gate L: Mock Ledger Reconciliation (`sdcs verify --mocks`, SPEC-001 v1.9.0 Section 7.21)."""

import os
import subprocess
import sys
from pathlib import Path

from sdcs.init import TEMPLATE_AGENTS, TEMPLATE_MOCKS, TEMPLATE_PRE_COMMIT_HOOK, init_scaffold
from sdcs.verifier.mocks import check_mock_ledger, locate_mock_ledger, run_mock_ledger_audit

ENV = dict(os.environ)
ENV["PYTHONPATH"] = str(Path(__file__).parent.parent / "src")


def _write(root: Path, rel: str, text: str) -> None:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _entry(mid: str, where: str, skip: str = "") -> str:
    fields = {"Where": where, "What it fakes": "x", "Why": "x", "To make it real": "x"}
    lines = [f"### {mid}: example"] + [f"- **{k}:** {v}" for k, v in fields.items() if k != skip]
    return "\n".join(lines) + "\n\n"


def _problems(root: Path) -> str:
    return "\n".join(check_mock_ledger(root).problems)


def test_consistent_polyglot_repo_passes(tmp_path: Path):
    _write(
        tmp_path,
        "app/svc.py",
        "class Svc:\n    def call(self):\n        # MOCK(M-001): fake call\n        return 1\n",
    )
    _write(tmp_path, "web/api.ts", "// MOCK(M-002): fake fetch\nexport async function load() {}\n")
    _write(
        tmp_path,
        "svc/pay.go",
        "package svc\n\n// MOCK(M-003): fake charge\nfunc Charge() error { return nil }\n",
    )
    _write(
        tmp_path,
        "MOCKS.md",
        (
            _entry("M-001", "`app/svc.py::Svc.call`")
            + _entry("M-002", "`web/api.ts::load`")
            + _entry("M-003", "`svc/pay.go::Charge`")
        ),
    )
    report = check_mock_ledger(tmp_path)
    assert report.problems == []
    assert set(report.entries) == {"M-001", "M-002", "M-003"}
    assert run_mock_ledger_audit(tmp_path) == 0


def test_every_kind_of_drift_is_reported(tmp_path: Path):
    _write(
        tmp_path,
        "app/a.py",
        (
            "def real_fn():\n"
            "    # MOCK(M-001): listed and defined\n"
            "    # MOCK(M-002): listed, symbol renamed away\n"
            "    # MOCK(M-009): no ledger entry\n"
            "    # MOCK(M-12): malformed\n"
            "    return 1\n"
        ),
    )
    _write(tmp_path, "app/c.py", "# MOCK(M-001): marker in a file the entry doesn't list\nx = 1\n")
    _write(
        tmp_path,
        "MOCKS.md",
        (
            _entry("M-001", "`app/a.py::real_fn`")
            + _entry("M-002", "`app/a.py::missing_fn`")
            + _entry("M-003", "`app/gone.py::anything`")
            + _entry("M-004", "`app/a.py::real_fn`")
            + _entry("M-005", "`app/a.py::real_fn`", skip="Why")
            + _entry("M-006", "app/a.py real_fn")
            + _entry("M-001", "`app/a.py::real_fn`")
        ),
    )
    problems = _problems(tmp_path)

    assert "M-009: marker in app/a.py has no ledger entry" in problems
    assert "malformed marker MOCK(M-12)" in problems
    assert "M-001: marker in app/c.py, but the entry's 'Where' doesn't list that file" in problems
    assert "M-001: appears more than once" in problems
    assert "M-002: missing_fn is not defined in app/a.py" in problems
    assert "M-003: app/gone.py does not exist" in problems
    assert "M-003: no MOCK(M-003) marker anywhere in the code" in problems
    assert "M-004: lists app/a.py, but that file has no MOCK(M-004) marker" in problems
    assert "M-005: ledger entry is missing 'Why'" in problems
    assert "M-006: 'Where' lists no path::symbol" in problems
    assert run_mock_ledger_audit(tmp_path) == 1


def test_no_ledger_and_no_markers_passes(tmp_path: Path, capsys):
    _write(tmp_path, "app/main.py", "def main():\n    return 0\n")
    assert check_mock_ledger(tmp_path).problems == []
    assert run_mock_ledger_audit(tmp_path) == 0
    assert "No MOCKS.md and no MOCK markers" in capsys.readouterr().out


def test_markers_without_a_ledger_fail(tmp_path: Path):
    _write(tmp_path, "app/main.py", "# MOCK(M-001): seeded data\nROWS = []\n")
    problems = _problems(tmp_path)
    assert "M-001: marker in app/main.py but no MOCKS.md exists" in problems
    assert run_mock_ledger_audit(tmp_path) == 1


def test_placeholder_is_ignored_and_test_doubles_are_not_scanned(tmp_path: Path):
    _write(tmp_path, "app/doc.py", 'HELP = "mark mocks with # MOCK(M-NNN): <what it fakes>"\n')
    _write(tmp_path, "tests/test_svc.py", "# MOCK(M-777): test double\n")
    _write(tmp_path, "app/svc_test.go", "// MOCK(M-778): go test double\n")
    _write(tmp_path, "web/api.spec.ts", "// MOCK(M-779): spec double\n")
    _write(tmp_path, "node_modules/pkg/index.js", "// MOCK(M-780): third-party code\n")
    report = check_mock_ledger(tmp_path)
    assert report.problems == []
    assert report.markers == {}


def test_ledger_is_found_in_docs_or_agent_dir_any_casing(tmp_path: Path):
    _write(tmp_path, "docs/mocks.md", "")
    assert locate_mock_ledger(tmp_path) == tmp_path / "docs" / "mocks.md"
    other = tmp_path / "other"
    _write(other, ".agent/MOCKS.md", "")
    assert locate_mock_ledger(other) == other / ".agent" / "MOCKS.md"


def test_cli_verify_mocks_exit_codes(tmp_path: Path):
    _write(tmp_path, "app/a.py", "# MOCK(M-001): fake\nX = 1\n")
    cmd = [sys.executable, "-m", "sdcs.cli", "verify", "--mocks", "--repo-root", str(tmp_path)]

    failing = subprocess.run(cmd, capture_output=True, text=True, env=ENV)
    assert failing.returncode == 1
    assert "GATE_L::REJECT" in failing.stdout

    _write(tmp_path, "MOCKS.md", _entry("M-001", "`app/a.py::X`"))
    passing = subprocess.run(cmd, capture_output=True, text=True, env=ENV)
    assert passing.returncode == 0
    assert "GATE_L] OK" in passing.stdout


def test_init_scaffolds_a_ledger_that_passes_gate_l(tmp_path: Path):
    init_scaffold(target_dir=tmp_path, skip_hooks=True)
    ledger = tmp_path / "MOCKS.md"
    assert ledger.read_text(encoding="utf-8").startswith("# MOCKS.md: Mock Inventory (Gate L)")
    assert check_mock_ledger(tmp_path).problems == []


def test_init_keeps_an_existing_ledger(tmp_path: Path):
    existing = "# Existing ledger\n"
    _write(tmp_path, "docs/MOCKS.md", existing)
    init_scaffold(target_dir=tmp_path, skip_hooks=True)
    assert not (tmp_path / "MOCKS.md").exists()
    assert (tmp_path / "docs" / "MOCKS.md").read_text(encoding="utf-8") == existing


def test_templates_wire_in_gate_l():
    assert "sdcs.cli verify --mocks" in TEMPLATE_PRE_COMMIT_HOOK
    assert "GATE L: MOCK LEDGER OUT OF SYNC" in TEMPLATE_PRE_COMMIT_HOOK
    assert "Gate L mock ledger reconciliation (`sdcs verify --mocks`)" in TEMPLATE_AGENTS
    assert "Mock Ledger Invariant (Gate L)" in TEMPLATE_AGENTS
    assert "M-NNN" in TEMPLATE_MOCKS
