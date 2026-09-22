"""
sdcs.verifier.sandbox - Declarative Blast-Radius & Sandbox Verification Engine (Gate P / SPEC-001 v1.5.0)

Enforces Pillar 2 (wiring.yaml) declarative sandboxing rules, preventing uncontracted
modifications to sensitive files (.env, credentials, keystores) and unauthorized commands.
"""

import fnmatch
import os
import subprocess
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None


def locate_wiring_file(repo_root: Path, custom_path: Path | None = None) -> Path | None:
    if custom_path and custom_path.is_file():
        return custom_path
    for c in [repo_root / "wiring.yaml", repo_root / ".agent" / "wiring.yaml"]:
        if c.is_file():
            return c
    return None


def load_sandbox_config(wiring_file: Path) -> dict:
    """Loads the 'sandbox' block from wiring.yaml."""
    if yaml is None or not wiring_file.is_file():
        return {}
    try:
        data = yaml.safe_load(wiring_file.read_text(encoding="utf-8")) or {}
        return data.get("sandbox", {})
    except Exception:
        return {}


def get_staged_files(repo_root: Path) -> list[str]:
    """Retrieves list of staged files in git."""
    try:
        res = subprocess.run(
            ["git", "diff", "--cached", "--name-only"],
            cwd=str(repo_root),
            capture_output=True,
            text=True,
        )
        if res.returncode == 0:
            return [line.strip() for line in res.stdout.splitlines() if line.strip()]
    except (subprocess.SubprocessError, OSError):
        pass
    return []


def audit_sandbox_staged_files(
    repo_root: Path,
    wiring_path: Path | None = None,
) -> tuple[bool, list[str]]:
    """
    Audits staged files against sandbox.protected_paths in wiring.yaml.
    Returns: (passed, list_of_violations)
    """
    wiring_file = locate_wiring_file(repo_root, wiring_path)
    if not wiring_file:
        return True, []

    sandbox_cfg = load_sandbox_config(wiring_file)
    protected_patterns = sandbox_cfg.get("protected_paths", [])
    if not protected_patterns:
        # Default safety fallbacks if sandbox not explicitly configured
        protected_patterns = [".env*", "*.jks", "*.pem", "*.key", "credentials/**"]

    staged_files = get_staged_files(repo_root)
    violations = []

    for file_path in staged_files:
        norm_path = file_path.replace("\\", "/")
        file_name = Path(norm_path).name
        for pattern in protected_patterns:
            norm_pattern = pattern.replace("\\", "/")
            if fnmatch.fnmatch(norm_path, norm_pattern) or fnmatch.fnmatch(file_name, norm_pattern):
                violations.append(f"{file_path} (matches protected pattern '{pattern}')")
                break

    passed = len(violations) == 0
    return passed, violations


def run_sandbox_audit(
    repo_root: Path,
    wiring_path: Path | None = None,
) -> int:
    """CLI execution entrypoint for Gate P sandbox audit."""
    print("====================================================================")
    print(" SDCS :: Declarative Sandbox & Protected Paths Auditor (Gate P)")
    print(f" Target Repository: {repo_root}")
    print("====================================================================\n")

    if os.environ.get("SDCS_ALLOW_SANDBOX_OVERRIDE") == "1":
        print("💡 [SDCS ADVISORY] SDCS_ALLOW_SANDBOX_OVERRIDE=1 detected. Sandbox checks bypassed.")
        return 0

    passed, violations = audit_sandbox_staged_files(repo_root, wiring_path)

    if passed:
        print("✓ [GATE P: PASSED] No protected assets staged in commit.")
        return 0
    else:
        print("🛑 [GATE P: FAILED] Staged files violate declarative sandbox protected_paths:")
        for v in violations:
            print(f"   - {v}")
        print(
            "\nAutonomous agents are strictly prohibited from staging credentials or protected assets."
        )
        print("To override as a human operator: export SDCS_ALLOW_SANDBOX_OVERRIDE=1")
        return 1
