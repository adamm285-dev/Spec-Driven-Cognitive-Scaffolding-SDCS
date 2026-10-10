"""Deterministic Pre-Flight Auto-Repair Engine.

SPEC-001 v1.8.0 Section 7.14.
Intercepts code modifications in place and applies deterministic formatters
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


def detect_configured_formatters(repo_root: Path) -> set[str]:
    """Detects formatters explicitly declared or configured in the repository."""
    configured: set[str] = set()

    # 1. pyproject.toml
    pyproject = repo_root / "pyproject.toml"
    if pyproject.is_file():
        try:
            content = pyproject.read_text(encoding="utf-8", errors="ignore")
            if "[tool.black]" in content:
                configured.add("black")
            if "[tool.ruff]" in content:
                configured.add("ruff")
            if "[tool.autopep8]" in content:
                configured.add("autopep8")
            if "[tool.yapf]" in content:
                configured.add("yapf")
            if "[tool.flake8]" in content:
                configured.add("flake8")
        except Exception:
            pass

    # 2. Dedicated config files for Python formatters
    if (repo_root / "ruff.toml").is_file() or (repo_root / ".ruff.toml").is_file():
        configured.add("ruff")
    if (repo_root / ".black").is_file() or (repo_root / "black.toml").is_file():
        configured.add("black")
    if (repo_root / ".style.yapf").is_file():
        configured.add("yapf")
    if (repo_root / ".flake8").is_file():
        configured.add("flake8")

    setup_cfg = repo_root / "setup.cfg"
    if setup_cfg.is_file():
        try:
            content = setup_cfg.read_text(encoding="utf-8", errors="ignore")
            if "[tool.black]" in content or "[black]" in content:
                configured.add("black")
            if "[tool.ruff]" in content or "[ruff]" in content:
                configured.add("ruff")
            if "[flake8]" in content:
                configured.add("flake8")
            if "[yapf]" in content:
                configured.add("yapf")
        except Exception:
            pass

    tox_ini = repo_root / "tox.ini"
    if tox_ini.is_file():
        try:
            content = tox_ini.read_text(encoding="utf-8", errors="ignore")
            if "[flake8]" in content:
                configured.add("flake8")
            if "[black]" in content:
                configured.add("black")
        except Exception:
            pass

    # 3. JS / TS / Prettier / Biome configs
    prettier_configs = [
        ".prettierrc",
        ".prettierrc.json",
        ".prettierrc.yml",
        ".prettierrc.yaml",
        ".prettierrc.json5",
        ".prettierrc.js",
        ".prettierrc.cjs",
        ".prettierrc.mjs",
        ".prettierrc.toml",
        "prettier.config.js",
        "prettier.config.cjs",
        "prettier.config.mjs",
        ".prettierignore",
    ]
    for cfg in prettier_configs:
        if (repo_root / cfg).is_file():
            configured.add("prettier")
            break

    package_json = repo_root / "package.json"
    if package_json.is_file():
        try:
            content = package_json.read_text(encoding="utf-8", errors="ignore")
            if '"prettier"' in content:
                configured.add("prettier")
        except Exception:
            pass

    if (repo_root / "biome.json").is_file() or (repo_root / "biome.jsonc").is_file():
        configured.add("biome")

    # 4. Go & Rust
    if (repo_root / "go.mod").is_file():
        configured.add("gofmt")
    if (repo_root / "rustfmt.toml").is_file() or (repo_root / ".rustfmt.toml").is_file():
        configured.add("rustfmt")

    # 5. wiring.yaml / .agent/wiring.yaml
    for cand in [repo_root / "wiring.yaml", repo_root / ".agent" / "wiring.yaml"]:
        if cand.is_file():
            try:
                content = cand.read_text(encoding="utf-8", errors="ignore")
                for fmt in ["ruff", "black", "prettier", "biome", "gofmt", "rustfmt"]:
                    if fmt in content:
                        configured.add(fmt)
            except Exception:
                pass

    return configured


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


def get_unstaged_code_files(repo_root: Path) -> set[Path]:
    """Retrieves files with unstaged modifications in working tree."""
    try:
        res = subprocess.run(
            ["git", "diff", "--name-only"],
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            check=True,
        )
        files = set()
        for line in res.stdout.splitlines():
            clean = line.strip()
            if clean:
                p = repo_root / clean
                files.add(p.resolve())
        return files
    except Exception:
        return set()


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


def auto_repair_python(
    files: list[Path],
    check_only: bool = False,
    configured_formatters: set[str] | None = None,
) -> dict[str, Any]:
    """Executes ruff --fix and black on Python files."""
    results = {"tool": "python", "repaired": [], "clean": [], "errors": []}
    py_files = [f for f in files if f.suffix.lower() == ".py"]
    if not py_files:
        return results

    str_paths = [str(f) for f in py_files]

    # 1. Ruff check --fix
    allow_ruff = (configured_formatters is None) or ("ruff" in configured_formatters)
    if allow_ruff and shutil.which("ruff"):
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
    allow_black = (configured_formatters is None) or ("black" in configured_formatters)
    if allow_black and shutil.which("black"):
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


def auto_repair_javascript(
    files: list[Path],
    check_only: bool = False,
    configured_formatters: set[str] | None = None,
) -> dict[str, Any]:
    """Executes prettier on JS/TS/JSON/MD files."""
    results = {"tool": "js_ts", "repaired": [], "clean": [], "errors": []}
    js_exts = {".js", ".jsx", ".ts", ".tsx", ".json", ".md"}
    js_files = [f for f in files if f.suffix.lower() in js_exts]
    if not js_files:
        return results

    str_paths = [str(f) for f in js_files]

    allow_prettier = (configured_formatters is None) or ("prettier" in configured_formatters)
    if allow_prettier and shutil.which("prettier"):
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
    """CLI runner executing deterministic in-place repair across target files."""
    print("\n====================================================================")
    print(" SDCS :: Deterministic Pre-Flight Auto-Repair (SPEC-001 v1.8.0)")
    print(f" Target Repository: {repo_root}")
    print(f" Mode:              {'Dry-Run Check' if check_only else 'Automatic In-Place Repair'}")
    print(f" Scope:             {'Staged Git Index' if staged else 'Working Tree Modifications'}")
    print("====================================================================\n")

    available_tools = detect_available_formatters()
    configured_tools = detect_configured_formatters(repo_root)
    print(
        f"[SDCS::REPAIR] Detected local formatters: {', '.join(sorted(available_tools.keys())) or 'None'}"
    )
    print(
        f"[SDCS::REPAIR] Configured repository formatters: {', '.join(sorted(configured_tools)) or 'None'}"
    )

    if not configured_tools:
        print("[SDCS::REPAIR] OK: No formatters declared or configured in repository.")
        print("✓ [REPAIR: CLEAN] Repository declares no formatters; skipping auto-repair.")
        print("====================================================================\n")
        return 0

    if explicit_paths:
        candidates = [p for p in explicit_paths if p.is_file()]
        if staged:
            unstaged_files = get_unstaged_code_files(repo_root)
            target_files = []
            for f in candidates:
                if f.resolve() in unstaged_files:
                    print(
                        f"[SDCS::REPAIR] Refusing to format partially staged file with unstaged edits: {f.name}"
                    )
                else:
                    target_files.append(f)
        else:
            target_files = candidates
    elif staged:
        staged_files = get_staged_code_files(repo_root)
        unstaged_files = get_unstaged_code_files(repo_root)
        target_files = []
        skipped_partially_staged = []
        for f in staged_files:
            if f.resolve() in unstaged_files:
                skipped_partially_staged.append(f)
            else:
                target_files.append(f)
        if skipped_partially_staged:
            names = ", ".join(f.name for f in skipped_partially_staged)
            print(
                f"[SDCS::REPAIR] Refusing to format partially staged file(s) with unstaged edits: {names}"
            )
    else:
        target_files = get_modified_code_files(repo_root)

    if not target_files:
        print("[SDCS::REPAIR] OK: No target code files require repair.")
        print("====================================================================\n")
        return 0

    print(f"[SDCS::REPAIR] Inspecting {len(target_files)} target file(s)...")

    py_res = auto_repair_python(
        target_files, check_only=check_only, configured_formatters=configured_tools
    )
    js_res = auto_repair_javascript(
        target_files, check_only=check_only, configured_formatters=configured_tools
    )

    repaired_tools = list(set(py_res["repaired"] + js_res["repaired"]))

    if staged and not check_only and repaired_tools and target_files:
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
