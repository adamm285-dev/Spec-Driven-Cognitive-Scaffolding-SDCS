"""
sdcs.cli - Unified CLI Router for Spec-Driven Cognitive Scaffolding (SPEC-001 v1.2)
"""

import argparse
import sys
from pathlib import Path

from sdcs import __version__
from sdcs.audit import locate_evals_file, run_audit
from sdcs.init import init_scaffold


def main():
    parser = argparse.ArgumentParser(
        prog="sdcs",
        description=f"Spec-Driven Cognitive Scaffolding (SDCS v{__version__}) CLI",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"sdcs {__version__} (SPEC-001 v1.2)",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # Subcommand: init
    init_parser = subparsers.add_parser(
        "init",
        help="Initialize 7-pillar SDCS cognitive scaffolding in a repository",
    )
    init_parser.add_argument(
        "--target-dir",
        type=Path,
        default=Path("."),
        help="Target repository root path (default: current directory)",
    )
    init_parser.add_argument(
        "--use-agent-dir",
        action="store_true",
        help="Store scaffolding files inside a '.agent/' subdirectory instead of root",
    )
    init_parser.add_argument(
        "--hierarchical",
        action="store_true",
        help="Generate hierarchical multi-tiered cartography maps",
    )
    init_parser.add_argument(
        "--skip-agents-md",
        action="store_true",
        help="Skip generating AGENTS.md behavioral prompting file",
    )
    init_parser.add_argument(
        "--skip-hooks",
        action="store_true",
        help="Skip generating .githooks/pre-commit protection hook",
    )
    init_parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing scaffolding files if present",
    )

    # Subcommand: audit
    audit_parser = subparsers.add_parser(
        "audit",
        help="Audit ground truth references in evals.md for reachability, hashes, and diversity",
    )
    audit_parser.add_argument(
        "--evals-path",
        default=None,
        help="Path to evals.md file",
    )
    audit_parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path("."),
        help="Path to repository root (default: current directory)",
    )
    audit_parser.add_argument(
        "--update-pending",
        action="store_true",
        help="Automatically replace 'pending' entries in evals.md with computed hashes",
    )

    # Subcommand: grill
    grill_parser = subparsers.add_parser(
        "grill",
        help="Display the /grillme adversarial spec elicitation prompt for authoring roadmap.md",
    )
    grill_parser.add_argument(
        "--milestone",
        type=str,
        default=None,
        help="Target milestone ID (e.g. M-001) to contextualize prompt",
    )

    # Subcommand: verify
    verify_parser = subparsers.add_parser(
        "verify",
        help="Run specification, invariant, and topological verification checks",
    )
    verify_parser.add_argument(
        "--topology",
        action="store_true",
        help="Audit codebase AST against wiring.yaml boundary contracts",
    )
    verify_parser.add_argument(
        "--append-rejections",
        action="store_true",
        help="Automatically persist unique boundary violations into decisions.md",
    )
    verify_parser.add_argument(
        "--wiring-path",
        type=Path,
        default=None,
        help="Path to wiring.yaml file (default: auto-detect)",
    )
    verify_parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path("."),
        help="Path to repository root (default: current directory)",
    )
    verify_parser.add_argument(
        "--all",
        action="store_true",
        help="Execute all verification checks (topology and evals)",
    )

    args = parser.parse_args()

    if args.command == "init":
        init_scaffold(
            target_dir=args.target_dir,
            use_agent_dir=args.use_agent_dir,
            hierarchical=args.hierarchical,
            skip_agents_md=args.skip_agents_md,
            skip_hooks=args.skip_hooks,
            force=args.force,
        )
    elif args.command == "audit":
        repo_root = args.repo_root.resolve()
        evals_file = locate_evals_file(repo_root, args.evals_path)
        passed = run_audit(
            evals_file=evals_file, repo_root=repo_root, update_pending=args.update_pending
        )
        sys.exit(0 if passed else 1)
    elif args.command == "grill":
        from sdcs.init import generate_grillme_md

        print(generate_grillme_md(args.milestone))
    elif args.command == "verify":
        from sdcs.verifier.topology import run_topology_audit

        repo_root = args.repo_root.resolve()
        exit_code = 0

        # Execute topology audit if requested, if --all is set, or as default verify action
        if args.topology or args.all or not any([args.topology, args.all]):
            code = run_topology_audit(
                repo_root=repo_root,
                wiring_path=args.wiring_path,
                append_rejections=args.append_rejections,
            )
            if code != 0:
                exit_code = code

        # If --all is requested, also run the evals audit
        if args.all:
            evals_file = locate_evals_file(repo_root)
            if evals_file and evals_file.is_file():
                evals_passed = run_audit(evals_file=evals_file, repo_root=repo_root)
                if not evals_passed:
                    exit_code = 1

        sys.exit(exit_code)
    else:
        parser.print_help()
        sys.exit(0)


if __name__ == "__main__":
    main()
