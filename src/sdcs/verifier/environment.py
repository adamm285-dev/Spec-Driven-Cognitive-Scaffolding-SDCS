"""SDCS Gate E & Diagnostic Doctor Engine: Environment and Toolchain Invariant Lock."""

from __future__ import annotations

import os
import re
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass
class DiagnosticItem:
    category: str
    name: str
    passed: bool
    details: str
    is_warning: bool = False


def _parse_python_version_spec(spec_str: str) -> tuple[str, tuple[int, ...]]:
    """Extract operator and version tuple from a spec string like '>=3.11'."""
    match = re.match(r"([><=!~]+)?\s*(\d+(\.\d+)*)", spec_str.strip())
    if not match:
        return (">=", (3, 10))
    op = match.group(1) or ">="
    ver_parts = tuple(int(x) for x in match.group(2).split("."))
    return op, ver_parts


def _check_python_version(required_spec: str) -> bool:
    """Check if sys.version_info satisfies required_spec (e.g. '>=3.11')."""
    op, req_ver = _parse_python_version_spec(required_spec)
    curr_ver = sys.version_info[: len(req_ver)]

    if op == ">=":
        return curr_ver >= req_ver
    elif op == ">":
        return curr_ver > req_ver
    elif op == "<=":
        return curr_ver <= req_ver
    elif op == "<":
        return curr_ver < req_ver
    elif op in ("==", "="):
        return curr_ver == req_ver
    return True


def get_environment_config(repo_root: Path) -> dict[str, Any]:
    """Load environment configuration from wiring.yaml or fallback pyproject.toml."""
    config: dict[str, Any] = {
        "python": ">=3.10",
        "required_tools": ["git"],
        "required_env_vars": [],
    }

    wiring_path = repo_root / "wiring.yaml"
    if wiring_path.exists():
        try:
            with open(wiring_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
                if "environment" in data and isinstance(data["environment"], dict):
                    env_block = data["environment"]
                    if "python" in env_block:
                        config["python"] = str(env_block["python"])
                    if "required_tools" in env_block and isinstance(
                        env_block["required_tools"], list
                    ):
                        config["required_tools"] = env_block["required_tools"]
                    if "required_env_vars" in env_block and isinstance(
                        env_block["required_env_vars"], list
                    ):
                        config["required_env_vars"] = env_block["required_env_vars"]
        except Exception:
            pass

    # Fallback / augment from pyproject.toml if present
    pyproject_path = repo_root / "pyproject.toml"
    if pyproject_path.exists() and config["python"] == ">=3.10":
        try:
            content = pyproject_path.read_text(encoding="utf-8", errors="ignore")
            match = re.search(r'requires-python\s*=\s*"([^"]+)"', content)
            if match:
                config["python"] = match.group(1)
        except Exception:
            pass

    return config


def run_diagnostics(repo_root: Path = Path(".")) -> list[DiagnosticItem]:
    """Perform a comprehensive health check across environment, toolchains, and pillars."""
    items: list[DiagnosticItem] = []
    env_cfg = get_environment_config(repo_root)

    # 1. Python runtime
    req_py = env_cfg.get("python", ">=3.10")
    curr_py_str = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    py_ok = _check_python_version(req_py)
    items.append(
        DiagnosticItem(
            category="Toolchain",
            name="Python Interpreter",
            passed=py_ok,
            details=f"Current: {curr_py_str} (Required: {req_py})",
        )
    )

    # 2. Required CLI tools
    for tool in env_cfg.get("required_tools", []):
        path = shutil.which(tool)
        items.append(
            DiagnosticItem(
                category="Toolchain",
                name=f"Tool: {tool}",
                passed=path is not None,
                details=f"Path: {path}" if path else "NOT FOUND on system PATH",
            )
        )

    # 3. Required Environment Variables
    for env_var in env_cfg.get("required_env_vars", []):
        is_set = env_var in os.environ and bool(os.environ[env_var].strip())
        items.append(
            DiagnosticItem(
                category="Environment",
                name=f"Env Var: {env_var}",
                passed=is_set,
                details="Present in environment" if is_set else "MISSING or empty",
            )
        )

    # 4. Cognitive Pillars Integrity
    pillars = [
        ("spine.md", "Pillar 1: Invariant Spine"),
        ("wiring.yaml", "Pillar 2: Declarative Wiring"),
        ("roadmap.md", "Pillar 3: Teleological Roadmap"),
        ("state.md", "Pillar 4: Dynamic Working State"),
        ("app_map.md", "Pillar 5: Repository Cartography"),
        ("decisions.md", "Pillar 6: Episodic Negative Memory"),
        ("evals.md", "Pillar 7: Empirical Evals Baseline"),
    ]

    for filename, label in pillars:
        p = repo_root / filename
        exists = p.exists()
        items.append(
            DiagnosticItem(
                category="Cognitive Pillars",
                name=label,
                passed=exists,
                details=f"Found ({p.stat().st_size} bytes)" if exists else "NOT FOUND on disk",
                is_warning=not exists and filename in ("evals.md", "roadmap.md"),
            )
        )

    # 5. Pre-commit hooks check
    githooks_dir = repo_root / ".githooks" / "pre-commit"
    git_hooks_dir = repo_root / ".git" / "hooks" / "pre-commit"
    hook_present = githooks_dir.exists() or git_hooks_dir.exists()
    items.append(
        DiagnosticItem(
            category="Kinetic Enforcement",
            name="Git Pre-Commit Hook",
            passed=hook_present,
            details=(
                "Hook active on disk"
                if hook_present
                else "Hook missing; run 'sdcs init' or install .githooks/pre-commit"
            ),
            is_warning=False,
        )
    )

    return items


def verify_environment(repo_root: Path = Path(".")) -> tuple[bool, list[str]]:
    """Gate E: Verify runtime and toolchain invariants.

    Returns:
    - (passed, list_of_error_messages)
    """
    items = run_diagnostics(repo_root)
    errors: list[str] = []

    for item in items:
        # Only fail on Toolchain and Environment items (pillars are audited by other gates)
        if item.category in ("Toolchain", "Environment") and not item.passed:
            errors.append(f"[{item.name}] {item.details}")

    return len(errors) == 0, errors


def run_env_audit(repo_root: Path = Path(".")) -> int:
    """CLI entrypoint for Gate E environment verification."""
    passed, errors = verify_environment(repo_root)
    if passed:
        print("[SDCS::GATE_E] OK: Toolchain and environment invariants verified.")
        return 0

    print("[SDCS::GATE_E::REJECT] Toolchain or environment mismatch detected:")
    for err in errors:
        print(f"  - {err}")
    print("[SDCS::GATE_E::GUIDANCE] DO NOT edit application code to circumvent environment errors.")
    print("                        Fix local interpreter, tools, or environment variables first.")
    return 1


def run_doctor_report(repo_root: Path = Path(".")) -> int:
    """CLI entrypoint for 'sdcs doctor' comprehensive system diagnostics."""
    items = run_diagnostics(repo_root)

    print("=" * 65)
    print("              SDCS DOCTOR: SYSTEM HEALTH & INTEGRITY")
    print("=" * 65)

    current_cat = ""
    failures = 0
    warnings = 0

    for it in items:
        if it.category != current_cat:
            current_cat = it.category
            print(f"\n[{current_cat}]")

        if it.passed:
            status = "[PASS]"
        elif it.is_warning:
            status = "[WARN]"
            warnings += 1
        else:
            status = "[FAIL]"
            failures += 1

        print(f"  {status:<7} {it.name:<32} {it.details}")

    print("\n" + "=" * 65)
    if failures == 0:
        print("  [SUCCESS] All systems operational. Cognitive scaffolding healthy.")
        print("=" * 65)
        return 0
    else:
        print(f"  [ATTENTION] Found {failures} failure(s) and {warnings} warning(s).")
        print("=" * 65)
        return 1
