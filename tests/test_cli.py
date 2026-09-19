import os
import subprocess
import sys
from pathlib import Path

ENV = dict(os.environ)
ENV["PYTHONPATH"] = str(Path(__file__).parent.parent / "src")


def test_cli_version():
    cmd = [sys.executable, "-m", "sdcs.cli", "--version"]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True, env=ENV)
    assert "sdcs 1.3.0" in result.stdout or "sdcs 1.3.0" in result.stderr


def test_cli_help():
    cmd = [sys.executable, "-m", "sdcs.cli", "--help"]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True, env=ENV)
    assert "init" in result.stdout
    assert "audit" in result.stdout
    assert "grill" in result.stdout
    assert "verify" in result.stdout


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


def test_cli_verify_help():
    cmd = [sys.executable, "-m", "sdcs.cli", "verify", "--help"]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True, env=ENV)
    assert "--topology" in result.stdout
    assert "--append-rejections" in result.stdout
    assert "--all" in result.stdout


def test_cli_verify_topology_execution(tmp_path: Path):
    wiring_file = tmp_path / "wiring.yaml"
    wiring_file.write_text(
        'version: "1.2.0"\nsubsystems:\n  core:\n    path: "src/core"\n    allowed_dependencies: []\n',
        encoding="utf-8",
    )
    src_core = tmp_path / "src" / "core"
    src_core.mkdir(parents=True, exist_ok=True)
    (src_core / "utils.py").write_text("x = 1\n", encoding="utf-8")
    cmd = [
        sys.executable,
        "-m",
        "sdcs.cli",
        "verify",
        "--topology",
        "--repo-root",
        str(tmp_path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True, env=ENV)
    assert "PASS: All import edges strictly satisfy declarative boundaries." in result.stdout
