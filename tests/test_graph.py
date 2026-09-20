import os
import subprocess
import sys
from pathlib import Path

from sdcs.graph import generate_ascii_graph, generate_mermaid_graph


def test_generate_mermaid_graph():
    subsystems = {
        "core": {"path": "src/core", "allowed_dependencies": []},
        "engine": {"path": "src/engine", "allowed_dependencies": ["core"]},
        "api": {"path": "src/api", "allowed_dependencies": ["engine", "core"]},
    }

    mermaid = generate_mermaid_graph(subsystems)
    assert "```mermaid" in mermaid
    assert "flowchart TD" in mermaid
    assert 'core["core<br/><code>src/core</code>"]' in mermaid
    assert "engine --> core" in mermaid
    assert "api --> engine" in mermaid
    assert "api --> core" in mermaid


def test_generate_ascii_graph():
    subsystems = {
        "core": {"path": "src/core", "allowed_dependencies": []},
        "engine": {"path": "src/engine", "allowed_dependencies": ["core"]},
        "api": {"path": "src/api", "allowed_dependencies": ["engine", "core"]},
    }

    ascii_dag = generate_ascii_graph(subsystems)
    assert "SDCS Declarative Topology DAG" in ascii_dag
    assert "[api] (src/api)" in ascii_dag
    assert "[engine] (src/engine)" in ascii_dag
    assert "[core] (src/core)" in ascii_dag
    assert "└──> (leaf: zero outbound subsystem dependencies)" in ascii_dag


def test_cli_graph(tmp_path: Path):
    env = dict(os.environ)
    env["PYTHONPATH"] = str(Path(__file__).parent.parent / "src")

    wiring_file = tmp_path / "wiring.yaml"
    wiring_content = """version: "1.4.0"
subsystems:
  leaf:
    path: "src/leaf"
    allowed_dependencies: []
  consumer:
    path: "src/consumer"
    allowed_dependencies:
      - leaf
"""
    wiring_file.write_text(wiring_content, encoding="utf-8")

    # 1. ASCII output
    cmd_ascii = [
        sys.executable,
        "-m",
        "sdcs.cli",
        "graph",
        "--format",
        "ascii",
        "--repo-root",
        str(tmp_path),
    ]
    res_ascii = subprocess.run(cmd_ascii, capture_output=True, text=True, env=env, check=False)
    assert res_ascii.returncode == 0
    assert "[consumer] (src/consumer)" in res_ascii.stdout
    assert "└──> [leaf]" in res_ascii.stdout

    # 2. Mermaid output saved to file
    out_file = tmp_path / "diagram.mmd"
    cmd_mermaid = [
        sys.executable,
        "-m",
        "sdcs.cli",
        "graph",
        "--format",
        "mermaid",
        "--output",
        str(out_file),
        "--repo-root",
        str(tmp_path),
    ]
    res_mermaid = subprocess.run(cmd_mermaid, capture_output=True, text=True, env=env, check=False)
    assert res_mermaid.returncode == 0
    assert out_file.is_file()
    saved_diagram = out_file.read_text(encoding="utf-8")
    assert "consumer --> leaf" in saved_diagram
