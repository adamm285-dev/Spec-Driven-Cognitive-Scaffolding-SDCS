"""Governed Model Tier Routing & Escalation Engine.

SPEC-001 v1.8.0 Section 7.15.
Implements Workhorse-first (Flash/Haiku) execution loops with 4 Deterministic
Escalation Triggers to Frontier (Pro/Sonnet) tiers and a Sticky Escalation Lock.
Eliminates over-spending on mechanical turns while guaranteeing high reasoning
for architectural changes and stubborn failure loops.
"""

from __future__ import annotations

import ast
import json
import subprocess
from pathlib import Path
from typing import Any

import yaml


def load_routing_config(repo_root: Path) -> dict[str, Any]:
    """Loads routing policy from wiring.yaml or returns defaults."""
    candidates = [repo_root / "wiring.yaml", repo_root / ".agent" / "wiring.yaml"]
    for c in candidates:
        if c.is_file():
            try:
                data = yaml.safe_load(c.read_text(encoding="utf-8")) or {}
                if "routing" in data and isinstance(data["routing"], dict):
                    return data["routing"]
            except Exception:
                pass

    return {
        "workhorse_tier": "flash",
        "frontier_tier": "pro",
        "failure_threshold": 3,
        "escalate_on_ast_change": True,
    }


def is_test_file(file_path: Path) -> bool:
    """Returns True if file_path is a test file or inside a test directory."""
    parts = [p.lower() for p in file_path.parts]
    if any(p in ("tests", "test", "fixtures") for p in parts):
        return True
    name = file_path.name.lower()
    return name.startswith("test_") or name.endswith("_test.py")


def format_ast_args(args_node: ast.arguments) -> str:
    """Formats ast.arguments into a canonical argument signature string including defaults and *args/**kwargs."""
    parts: list[str] = []

    pos_args = list(args_node.posonlyargs) + list(args_node.args)
    num_pos = len(pos_args)
    num_defaults = len(args_node.defaults)
    default_start = num_pos - num_defaults

    pos_parts: list[str] = []
    for idx, a in enumerate(pos_args):
        if idx >= default_start:
            default_expr = args_node.defaults[idx - default_start]
            try:
                def_val = ast.unparse(default_expr)
            except Exception:
                def_val = "..."
            pos_parts.append(f"{a.arg}={def_val}")
        else:
            pos_parts.append(a.arg)

        if args_node.posonlyargs and idx == len(args_node.posonlyargs) - 1:
            pos_parts.append("/")

    parts.extend(pos_parts)

    if args_node.vararg:
        parts.append(f"*{args_node.vararg.arg}")
    elif args_node.kwonlyargs:
        parts.append("*")

    for a, kw_d in zip(args_node.kwonlyargs, args_node.kw_defaults):
        if kw_d is not None:
            try:
                def_val = ast.unparse(kw_d)
            except Exception:
                def_val = "..."
            parts.append(f"{a.arg}={def_val}")
        else:
            parts.append(a.arg)

    if args_node.kwarg:
        parts.append(f"**{args_node.kwarg.arg}")

    return ",".join(parts)


def extract_public_signatures(source_code: str) -> set[str]:
    """Extracts public classes and function signatures from Python source."""
    signatures = set()
    try:
        tree = ast.parse(source_code)
    except Exception:
        return signatures

    for node in tree.body:
        if isinstance(node, ast.ClassDef) and not node.name.startswith("_"):
            if node.name.startswith("Test"):
                continue
            signatures.add(f"class:{node.name}")
            for item in node.body:
                if isinstance(
                    item, (ast.FunctionDef, ast.AsyncFunctionDef)
                ) and not item.name.startswith("_"):
                    if item.name.startswith("test_") or item.name.startswith("test"):
                        continue
                    args_str = format_ast_args(item.args)
                    signatures.add(f"method:{node.name}.{item.name}({args_str})")
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and not node.name.startswith(
            "_"
        ):
            if node.name.startswith("test_") or node.name.startswith("test"):
                continue
            args_str = format_ast_args(node.args)
            signatures.add(f"func:{node.name}({args_str})")

    return signatures


def detect_ast_signature_mutation(repo_root: Path, file_path: Path) -> bool:
    """Compares git HEAD version of file to working tree to detect public signature changes."""
    if not file_path.is_file() or file_path.suffix.lower() != ".py":
        return False
    if is_test_file(file_path):
        return False

    try:
        rel = file_path.relative_to(repo_root).as_posix()
        res = subprocess.run(
            ["git", "show", f"HEAD:{rel}"],
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            check=False,
        )
        if res.returncode != 0:
            # New file: additions break no existing callers
            return False

        head_sigs = extract_public_signatures(res.stdout)
        curr_code = file_path.read_text(encoding="utf-8", errors="ignore")
        curr_sigs = extract_public_signatures(curr_code)

        # Map symbol identifiers to their declared signatures
        head_map: dict[str, set[str]] = {}
        for s in head_sigs:
            sym = s.split("(", 1)[0]
            head_map.setdefault(sym, set()).add(s)

        curr_map: dict[str, set[str]] = {}
        for s in curr_sigs:
            sym = s.split("(", 1)[0]
            curr_map.setdefault(sym, set()).add(s)

        # Escalate only if an existing public symbol was altered or removed
        for sym, head_set in head_map.items():
            if sym not in curr_map:
                return True
            if not head_set.issubset(curr_map[sym]):
                return True

        return False
    except Exception:
        return False


def evaluate_tier_routing(
    repo_root: Path,
    target_file: Path | None = None,
    failure_count: int = 0,
    is_planning: bool = False,
    schema_error: bool = False,
) -> dict[str, Any]:
    """Evaluates the 4 deterministic escalation triggers to select Workhorse vs Frontier tier."""
    cfg = load_routing_config(repo_root)
    workhorse = cfg.get("workhorse_tier", "flash")
    frontier = cfg.get("frontier_tier", "pro")
    failure_threshold = cfg.get("failure_threshold", 3)
    check_ast = cfg.get("escalate_on_ast_change", True)

    escalated = False
    reasons = []

    # Trigger 1: Planning / Decomposition Phase
    if is_planning:
        escalated = True
        reasons.append("Trigger 1: Initial planning & architectural decomposition phase")

    # Trigger 2: Repeated Gate Failures
    if failure_count >= failure_threshold:
        escalated = True
        reasons.append(
            f"Trigger 2: Target failed verification {failure_count} times (>= threshold {failure_threshold})"
        )

    # Trigger 3: AST Public Signature Mutation
    if check_ast and target_file and target_file.is_file():
        if detect_ast_signature_mutation(repo_root, target_file):
            escalated = True
            reasons.append(
                f"Trigger 3: AST public signature mutation detected in {target_file.name}"
            )

    # Trigger 4: Schema / Structured Validation Failure
    if schema_error:
        escalated = True
        reasons.append("Trigger 4: Structural JSON / Schema validation error occurred")

    selected_tier = frontier if escalated else workhorse
    lock_recommended = escalated and target_file is not None

    return {
        "selected_tier": selected_tier,
        "is_escalated": escalated,
        "workhorse_model": workhorse,
        "frontier_model": frontier,
        "reasons": reasons,
        "sticky_lock": lock_recommended,
        "target_file": str(target_file) if target_file else None,
    }


def run_router_command(
    repo_root: Path,
    target_file: Path | None = None,
    failure_count: int = 0,
    is_planning: bool = False,
    schema_error: bool = False,
    json_output: bool = False,
) -> int:
    """CLI runner evaluating governed tier routing."""
    res = evaluate_tier_routing(
        repo_root,
        target_file=target_file,
        failure_count=failure_count,
        is_planning=is_planning,
        schema_error=schema_error,
    )

    if json_output:
        print(json.dumps(res, indent=2))
        return 0

    print("\n====================================================================")
    print(" SDCS :: Governed Model Tier Router (SPEC-001 v1.8.0)")
    print(f" Target Repository: {repo_root}")
    print(f" Target File:       {target_file.name if target_file else 'None (Session Global)'}")
    print("====================================================================\n")

    tier_label = f"[{res['selected_tier'].upper()}]"
    if res["is_escalated"]:
        print(f"🚀 Recommended Tier: {tier_label} ({res['frontier_model']}) -- ESCALATED")
        print("   Active Triggers:")
        for r in res["reasons"]:
            print(f"     · {r}")
        if res["sticky_lock"]:
            print("   🔒 Sticky Lock: Hold Frontier tier until target file passes all gates.")
    else:
        print(f"⚡ Recommended Tier: {tier_label} ({res['workhorse_model']}) -- DEFAULT WORKHORSE")
        print("   No escalation triggers active. Operating at 90% cost savings.")

    print("\n====================================================================\n")
    return 0
