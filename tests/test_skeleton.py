"""Tests for AST Skeletal Observation Compactor (SPEC-001 v1.8.0 Section 7.12)."""

from pathlib import Path

from sdcs.skeleton import (
    calculate_skeleton_metrics,
    extract_file_skeleton,
    extract_python_skeleton,
    run_skeleton_command,
)


def test_extract_python_skeleton_basic():
    code = """
def add(a: int, b: int) -> int:
    \"\"\"Add two numbers.\"\"\"
    temp = a + b
    return temp

class Calculator:
    \"\"\"A simple calculator.\"\"\"
    base: int = 0

    def multiply(self, x: float, y: float) -> float:
        \"\"\"Multiply two floats.\"\"\"
        result = x * y
        return result
"""
    skel = extract_python_skeleton(code)

    assert "def add(a: int, b: int) -> int:" in skel
    assert '"""Add two numbers."""' in skel
    assert "temp = a + b" not in skel
    assert "class Calculator:" in skel
    assert '"""A simple calculator."""' in skel
    assert "def multiply(self, x: float, y: float) -> float:" in skel
    assert "result = x * y" not in skel
    assert "..." in skel


def test_skeleton_metrics_compression():
    orig = "def compute():\n" + "    x = 1\n" * 100
    skel = extract_python_skeleton(orig)
    metrics = calculate_skeleton_metrics(orig, skel)

    assert metrics["original_tokens"] > metrics["skeleton_tokens"]
    assert metrics["compression_ratio"] >= 70.0
    assert metrics["tokens_saved"] > 0


def test_polyglot_skeleton_extraction(tmp_path: Path):
    # TypeScript
    ts_file = tmp_path / "service.ts"
    ts_file.write_text(
        "export interface User {\n  id: string;\n}\n\nexport class UserService {\n"
        "  async getUser(id: string): Promise<User> {\n    return fetch(id);\n  }\n}\n",
        encoding="utf-8",
    )
    skel_ts = extract_file_skeleton(ts_file)
    assert "export interface User" in skel_ts
    assert "export class UserService" in skel_ts

    # Go
    go_file = tmp_path / "main.go"
    go_file.write_text(
        "package main\n\ntype Config struct {\n  Port int\n}\n\nfunc RunServer(c Config) error {\n  return nil\n}\n",
        encoding="utf-8",
    )
    skel_go = extract_file_skeleton(go_file)
    assert "package main" in skel_go
    assert "type Config struct" in skel_go
    assert "func RunServer(c Config) error" in skel_go


def test_run_skeleton_command(tmp_path: Path, capsys):
    test_file = tmp_path / "module.py"
    test_file.write_text(
        "class Worker:\n    def do_work(self) -> None:\n        print('working')\n",
        encoding="utf-8",
    )

    code = run_skeleton_command(test_file)
    assert code == 0
    captured = capsys.readouterr()
    assert "AST SKELETON: module.py" in captured.out
    assert "class Worker:" in captured.out

    # Test directory run
    code_dir = run_skeleton_command(tmp_path)
    assert code_dir == 0
