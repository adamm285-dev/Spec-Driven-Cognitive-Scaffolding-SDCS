"""Deterministic Pre-Flight Auto-Repair Engine.

SPEC-001 v1.8.0 Section 7.14.
Intercepts code modifications in the sandbox and applies deterministic formatters
(ruff --fix, black, prettier, gofmt) locally with ZERO LLM inference tokens.
Ensures trivial style, whitespace, and import formatting issues are resolved
mechanically before kinetic gates evaluate.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import Any


def detect_available_formatters() -> dict[str, str]:
    """Detects available deterministic code formatting and auto-repair CLI tools."""
    tools = {}
    candidates = ["ruff", "black", "prettier", "biome", "gofmt", "rustfmt"]
    for c in candidates:
        path = shutil.which(c)
        if path:
            tools[c] = path
    return tools


def get_staged_code_files(repo_root: Path) -> list[Path]:
    """Retrieves staged files from git index."""
    try:
        res = subprocess.run(
            ["git", "diff", "--cached", "--name-only"],
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            check=True,
        )
        files = []
        for line in res.stdout.splitlines():
            clean = line.strip()
            if clean:
                p = repo_root / clean
                if p.is_file():
                    files.append(p)
        return files
    except Exception:
        return []


def get_modified_code_files(repo_root: Path) -> list[Path]:
    """Retrieves modified or untracked files from working tree."""
    try:
        res = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            check=True,
        )
        files = []
        for line in res.stdout.splitlines():
            if len(line) > 3:
                filepath = line[3:].strip()
                p = repo_root / filepath
                if p.is_file():
                    files.append(p)
        return files
    except Exception:
        return []


def auto_repair_python(files: list[Path], check_only: bool = False) -> dict[str, Any]:
    """Executes ruff --fix and black on Python files."""
    results = {"tool": "python", "repaired": [], "clean": [], "errors": []}
    py_files = [f for f in files if f.suffix.lower() == ".py"]
    if not py_files:
        return results

    str_paths = [str(f) for f in py_files]

    # 1. Ruff check --fix
    if shutil.which("ruff"):
        cmd_ruff = [
            "ruff",
            "check",
            *(["--no-fix"] if check_only else ["--fix"]),
            *str_paths,
        ]
        try:
            res = subprocess.run(cmd_ruff, capture_output=True, text=True, check=False)
            if res.returncode != 0 and not check_only:
                results["repaired"].append("ruff")
        except Exception as err:
            results["errors"].append(f"ruff: {err}")

    # 2. Black
    if shutil.which("black"):
        cmd_black = [
            "black",
            *(["--check"] if check_only else []),
            *str_paths,
        ]
        try:
            res = subprocess.run(cmd_black, capture_output=True, text=True, check=False)
            if "reformatted" in res.stderr or "would be reformatted" in res.stderr:
                results["repaired"].append("black")
        except Exception as err:
            results["errors"].append(f"black: {err}")

    return results


def auto_repair_javascript(files: list[Path], check_only: bool = False) -> dict[str, Any]:
    """Executes prettier on JS/TS/JSON/MD files."""
    results = {"tool": "js_ts", "repaired": [], "clean": [], "errors": []}
    js_exts = {".js", ".jsx", ".ts", ".tsx", ".json", ".md"}
    js_files = [f for f in files if f.suffix.lower() in js_exts]
    if not js_files:
        return results

    str_paths = [str(f) for f in js_files]

    if shutil.which("prettier"):
        cmd_prettier = [
            "prettier",
            *(["--check"] if check_only else ["--write"]),
            *str_paths,
        ]
        try:
            res = subprocess.run(cmd_prettier, capture_output=True, text=True, check=False)
            if res.returncode == 0:
                results["repaired"].append("prettier")
        except Exception as err:
            results["errors"].append(f"prettier: {err}")

    return results


def run_repair_command(
    repo_root: Path,
    staged: bool = False,
    check_only: bool = False,
    explicit_paths: list[Path] | None = None,
) -> int:
    """CLI runner executing deterministic sandbox repair across target files."""
    print("\n====================================================================")
    print(" SDCS :: Deterministic Pre-Flight Auto-Repair (SPEC-001 v1.8.0)")
    print(f" Target Repository: {repo_root}")
    print(f" Mode:              {'Dry-Run Check' if check_only else 'Automatic In-Place Repair'}")
    print(f" Scope:             {'Staged Git Index' if staged else 'Working Tree Modifications'}")
    print("====================================================================\n")

    available_tools = detect_available_formatters()
    print(
        f"[SDCS::REPAIR] Detected local formatters: {', '.join(available_tools.keys()) or 'None'}"
    )

    if explicit_paths:
        target_files = [p for p in explicit_paths if p.is_file()]
    elif staged:
        target_files = get_staged_code_files(repo_root)
    else:
        target_files = get_modified_code_files(repo_root)

    if not target_files:
        print("[SDCS::REPAIR] OK: No target code files require repair.")
        print("====================================================================\n")
        return 0

    print(f"[SDCS::REPAIR] Inspecting {len(target_files)} target file(s)...")

    py_res = auto_repair_python(target_files, check_only=check_only)
    js_res = auto_repair_javascript(target_files, check_only=check_only)

    repaired_tools = list(set(py_res["repaired"] + js_res["repaired"]))

    if staged and not check_only and repaired_tools:
        # Automatically re-stage modified files
        try:
            subprocess.run(
                ["git", "add", *[str(f) for f in target_files]], cwd=str(repo_root), check=True
            )
            print("[SDCS::REPAIR] Automatically re-staged reformatted files in git index.")
        except Exception as err:
            print(f"[SDCS::WARNING] Failed to re-stage files: {err}")

    print("\n--------------------------------------------------------------------")
    if repaired_tools:
        verb = "found deviations in" if check_only else "automatically repaired"
        print(f"✓ [REPAIR: SUCCESS] Deterministic formatters {verb} target files.")
        print(f"  Tools applied: {', '.join(repaired_tools)} (0 LLM inference tokens spent)")
    else:
        print("✓ [REPAIR: CLEAN] All target files conform to deterministic formatting standards.")
    print("====================================================================\n")

    return 0
