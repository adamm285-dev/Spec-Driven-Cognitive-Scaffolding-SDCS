import os
from pathlib import Path
import subprocess
import sys

ENV = dict(os.environ)
ENV["PYTHONPATH"] = str(Path(__file__).parent.parent / "src")


def test_cli_version():
    cmd = [sys.executable, "-m", "sdcs.cli", "--version"]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True, env=ENV)
    assert "sdcs 1.2.0" in result.stdout or "sdcs 1.2.0" in result.stderr


def test_cli_help():
    cmd = [sys.executable, "-m", "sdcs.cli", "--help"]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True, env=ENV)
    assert "init" in result.stdout
    assert "audit" in result.stdout
    assert "grill" in result.stdout


def test_cli_grill():
    cmd = [sys.executable, "-m", "sdcs.cli", "grill"]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True, env=ENV)
    assert "/grillme" in result.stdout
    assert "Adversarial Spec Elicitation Protocol" in result.stdout


def test_cli_grill_milestone():
    cmd = [sys.executable, "-m", "sdcs.cli", "grill", "--milestone", "M-003"]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True, env=ENV)
    assert "Milestone M-003" in result.stdout


def test_cli_audit_help():
    cmd = [sys.executable, "-m", "sdcs.cli", "audit", "--help"]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True, env=ENV)
    assert "--evals-path" in result.stdout
    assert "--repo-root" in result.stdout
    assert "--update-pending" in result.stdout

