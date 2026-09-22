"""Tests for Deterministic Pre-Flight Auto-Repair Engine (SPEC-001 v1.8.0 Section 7.14)."""

from pathlib import Path

from sdcs.repair import (
    auto_repair_javascript,
    auto_repair_python,
    detect_available_formatters,
    run_repair_command,
)


def test_detect_available_formatters():
    tools = detect_available_formatters()
    assert isinstance(tools, dict)
    # Check that it detects at least one standard tool in dev env (e.g. ruff or black)
    assert any(t in tools for t in ("ruff", "black", "python"))


def test_auto_repair_python(tmp_path: Path):
    f = tmp_path / "messy.py"
    f.write_text("import sys\nimport os\ndef test():\n    x=1+2\n    return x\n", encoding="utf-8")

    res = auto_repair_python([f], check_only=False)
    assert res["tool"] == "python"
    assert isinstance(res["repaired"], list)


def test_auto_repair_javascript(tmp_path: Path):
    f = tmp_path / "script.js"
    f.write_text("const x = { a: 1, b: 2 };\n", encoding="utf-8")

    res = auto_repair_javascript([f], check_only=True)
    assert res["tool"] == "js_ts"


def test_run_repair_command(tmp_path: Path, capsys):
    f = tmp_path / "test.py"
    f.write_text("def hello():\n    pass\n", encoding="utf-8")

    code = run_repair_command(tmp_path, explicit_paths=[f], check_only=True)
    assert code == 0
    captured = capsys.readouterr()
    assert "SDCS :: Deterministic Pre-Flight Auto-Repair" in captured.out
