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


def extract_public_signatures(source_code: str) -> set[str]:
    """Extracts public classes and function signatures from Python source."""
    signatures = set()
    try:
        tree = ast.parse(source_code)
    except Exception:
        return signatures

    for node in tree.body:
        if isinstance(node, ast.ClassDef) and not node.name.startswith("_"):
            signatures.add(f"class:{node.name}")
            for item in node.body:
                if isinstance(
                    item, (ast.FunctionDef, ast.AsyncFunctionDef)
                ) and not item.name.startswith("_"):
                    args = [a.arg for a in item.args.args]
                    signatures.add(f"method:{node.name}.{item.name}({','.join(args)})")
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and not node.name.startswith(
            "_"
        ):
            args = [a.arg for a in node.args.args]
            signatures.add(f"func:{node.name}({','.join(args)})")

    return signatures


def detect_ast_signature_mutation(repo_root: Path, file_path: Path) -> bool:
    """Compares git HEAD version of file to working tree to detect public signature changes."""
    if not file_path.is_file() or file_path.suffix.lower() != ".py":
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
            # New file: if it has public signatures, that's an addition
            curr_code = file_path.read_text(encoding="utf-8", errors="ignore")
            return len(extract_public_signatures(curr_code)) > 0

        head_sigs = extract_public_signatures(res.stdout)
        curr_code = file_path.read_text(encoding="utf-8", errors="ignore")
        curr_sigs = extract_public_signatures(curr_code)

        return head_sigs != curr_sigs
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
