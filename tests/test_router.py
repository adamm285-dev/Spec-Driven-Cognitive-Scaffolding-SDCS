"""Tests for Governed Model Tier Router & Escalation Engine (SPEC-001 v1.8.0 Section 7.15)."""

from pathlib import Path

from sdcs.router import (
    evaluate_tier_routing,
    extract_public_signatures,
    run_router_command,
)


def test_extract_public_signatures():
    code = """
def public_func(x: int) -> int:
    return x

def _private_func():
    pass

class PublicClass:
    def public_method(self, a: str):
        pass

    def _private_method(self):
        pass
"""
    sigs = extract_public_signatures(code)
    assert "func:public_func(x)" in sigs
    assert "class:PublicClass" in sigs
    assert "method:PublicClass.public_method(self,a)" in sigs
    assert "func:_private_func()" not in sigs


def test_evaluate_tier_routing_default(tmp_path: Path):
    res = evaluate_tier_routing(tmp_path)
    assert res["selected_tier"] == "flash"
    assert res["is_escalated"] is False
    assert res["sticky_lock"] is False


def test_evaluate_tier_routing_planning_trigger(tmp_path: Path):
    res = evaluate_tier_routing(tmp_path, is_planning=True)
    assert res["selected_tier"] == "pro"
    assert res["is_escalated"] is True
    assert any("planning" in r.lower() for r in res["reasons"])


def test_evaluate_tier_routing_repeated_failures(tmp_path: Path):
    res = evaluate_tier_routing(tmp_path, failure_count=3)
    assert res["selected_tier"] == "pro"
    assert res["is_escalated"] is True
    assert any("failed verification 3 times" in r.lower() for r in res["reasons"])


def test_evaluate_tier_routing_schema_error(tmp_path: Path):
    res = evaluate_tier_routing(tmp_path, schema_error=True)
    assert res["selected_tier"] == "pro"
    assert res["is_escalated"] is True


def test_run_router_command(tmp_path: Path, capsys):
    code = run_router_command(tmp_path, failure_count=0)
    assert code == 0
    captured = capsys.readouterr()
    assert "FLASH" in captured.out

    # Escalated run
    code_esc = run_router_command(tmp_path, failure_count=4)
    assert code_esc == 0
    captured_esc = capsys.readouterr()
    assert "PRO" in captured_esc.out
    assert "ESCALATED" in captured_esc.out
