import os
import subprocess
import sys
from pathlib import Path

from sdcs.verifier.state import audit_state_tokens, count_tokens, parse_state_sections


def test_count_tokens():
    text = "Hello world from SDCS working memory."
    tokens = count_tokens(text)
    assert tokens > 0
    assert tokens >= len(text.split())


def test_parse_state_sections():
    content = """# Title
Preamble text here.

## Current Objective
Implement M-006 GPU Cache.

## Status & Gate Verification
- Gate T: Passed
- Gate A: In progress

## Immediate Next Action (Post-Compact)
Run integration tests.
"""
    sections = parse_state_sections(content)
    assert "__preamble__" in sections
    assert "Current Objective" in sections
    assert "Status & Gate Verification" in sections
    assert "Immediate Next Action (Post-Compact)" in sections


def test_audit_state_tokens_within_budget(tmp_path: Path):
    state_file = tmp_path / "state.md"
    content = """## Current Objective
Complete Milestone M-004.

## Status & Gate Verification
- Invariant verification: clean.
- Unit tests: 100% passing.

## Immediate Next Action (Post-Compact)
Ship PyPI package.
"""
    state_file.write_text(content, encoding="utf-8")

    passed, total_tokens, section_tokens, warnings = audit_state_tokens(state_file, max_tokens=350)
    assert passed is True
    assert total_tokens < 100
    assert len(warnings) == 0
    assert "Current Objective" in section_tokens


def test_audit_state_tokens_exceeds_budget(tmp_path: Path):
    state_file = tmp_path / "state.md"
    # Create large state content
    long_prose = " ".join(["token-word-item"] * 400)
    content = f"""## Current Objective
{long_prose}

## Status & Gate Verification
Status details here.

## Immediate Next Action (Post-Compact)
Next steps.
"""
    state_file.write_text(content, encoding="utf-8")

    passed, total_tokens, _section_tokens, warnings = audit_state_tokens(state_file, max_tokens=300)
    assert passed is False
    assert total_tokens > 300
    assert any("budget exceeded" in w.lower() for w in warnings)


def test_cli_verify_state(tmp_path: Path):
    env = dict(os.environ)
    env["PYTHONPATH"] = str(Path(__file__).parent.parent / "src")

    state_file = tmp_path / "state.md"
    state_file.write_text(
        "## Current Objective\nGoal\n\n## Status & Gate Verification\nPass\n\n## Immediate Next Action\nNext\n",
        encoding="utf-8",
    )

    cmd = [
        sys.executable,
        "-m",
        "sdcs.cli",
        "verify",
        "--state",
        "--repo-root",
        str(tmp_path),
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, env=env, check=False)
    assert res.returncode == 0
    assert "working memory is disciplined and within budget" in res.stdout

    # Now test failure with tight budget of 5 tokens
    cmd_tight = [
        sys.executable,
        "-m",
        "sdcs.cli",
        "verify",
        "--state",
        "--max-tokens",
        "5",
        "--repo-root",
        str(tmp_path),
    ]
    res_tight = subprocess.run(cmd_tight, capture_output=True, text=True, env=env, check=False)
    assert res_tight.returncode == 1
    assert "Working memory bloat detected" in res_tight.stdout
