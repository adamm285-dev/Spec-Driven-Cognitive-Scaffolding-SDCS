"""
sdcs.cli - Unified CLI Router for Spec-Driven Cognitive Scaffolding (SPEC-001 v1.4.0)
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
        version=f"sdcs {__version__} (SPEC-001 v1.4.0)",
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
    audit_parser.add_argument(
        "--recalibrate",
        metavar="FIXTURE_ID",
        default=None,
        help="Recalibrate one fixture ID or 'all' with newly computed SHA-256 digests in evals.md",
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

    # Subcommand: map
    map_parser = subparsers.add_parser(
        "map",
        help="Audit repository cartography against disk and synchronize app_map.md",
    )
    map_parser.add_argument(
        "--check",
        action="store_true",
        help="Check for cartography drift and return non-zero exit code if unmapped or orphaned files exist",
    )
    map_parser.add_argument(
        "--sync",
        action="store_true",
        help="Synchronize app_map.md with current disk state, appending new files and pruning orphans",
    )
    map_parser.add_argument(
        "--map-path",
        default=None,
        help="Path to app_map.md file (default: auto-detect)",
    )
    map_parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path("."),
        help="Path to repository root (default: current directory)",
    )

    # Subcommand: session
    session_parser = subparsers.add_parser(
        "session",
        help="Structured flight recorder indexing and querying for sessions/*.md",
    )
    session_parser.add_argument(
        "action",
        nargs="?",
        default="list",
        choices=["list", "index"],
        help="Action to perform: 'list' (default) or 'index' (rebuild manifest.jsonl)",
    )
    session_parser.add_argument(
        "--query",
        "-q",
        type=str,
        default=None,
        help="Filter session records by keyword (topic, date, verdict, summary)",
    )
    session_parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON",
    )
    session_parser.add_argument(
        "--sessions-dir",
        default=None,
        help="Path to sessions/ directory (default: auto-detect)",
    )
    session_parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path("."),
        help="Path to repository root (default: current directory)",
    )

    # Subcommand: graph
    graph_parser = subparsers.add_parser(
        "graph",
        help="Visualize declarative subsystem topology as Mermaid diagrams or ASCII DAGs",
    )
    graph_parser.add_argument(
        "--format",
        "-f",
        choices=["ascii", "mermaid"],
        default="ascii",
        help="Output format: 'ascii' (default) or 'mermaid'",
    )
    graph_parser.add_argument(
        "--output",
        "-o",
        type=Path,
        default=None,
        help="File path to save the generated diagram (default: stdout)",
    )
    graph_parser.add_argument(
        "--wiring-path",
        type=Path,
        default=None,
        help="Path to wiring.yaml file (default: auto-detect)",
    )
    graph_parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path("."),
        help="Path to repository root (default: current directory)",
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
        "--state",
        action="store_true",
        help="Audit state.md working memory token budget and canonical section schema",
    )
    verify_parser.add_argument(
        "--max-tokens",
        type=int,
        default=350,
        help="Maximum allowed token budget for state.md (default: 350)",
    )
    verify_parser.add_argument(
        "--state-path",
        default=None,
        help="Path to state.md file (default: auto-detect)",
    )
    verify_parser.add_argument(
        "--all",
        action="store_true",
        help="Execute all verification checks (topology, state, and evals)",
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
            evals_file=evals_file,
            repo_root=repo_root,
            update_pending=args.update_pending,
            recalibrate=args.recalibrate,
        )
        sys.exit(0 if passed else 1)
    elif args.command == "grill":
        from sdcs.init import generate_grillme_md

        print(generate_grillme_md(args.milestone))
    elif args.command == "map":
        from sdcs.map import run_map_command

        repo_root = args.repo_root.resolve()
        code = run_map_command(
            repo_root=repo_root,
            map_path=args.map_path,
            check=args.check,
            sync=args.sync,
        )
        sys.exit(code)
    elif args.command == "session":
        from sdcs.session import run_session_command

        repo_root = args.repo_root.resolve()
        code = run_session_command(
            repo_root=repo_root,
            action=args.action,
            query_str=args.query,
            sessions_dir=args.sessions_dir,
            as_json=args.json,
        )
        sys.exit(code)
    elif args.command == "graph":
        from sdcs.graph import run_graph_command

        repo_root = args.repo_root.resolve()
        code = run_graph_command(
            repo_root=repo_root,
            wiring_path=args.wiring_path,
            graph_format=args.format,
            output_path=args.output,
        )
        sys.exit(code)
    elif args.command == "verify":
        from sdcs.verifier.topology import run_topology_audit

        repo_root = args.repo_root.resolve()
        exit_code = 0

        run_topology = (
            args.topology or args.all or (not args.topology and not args.state and not args.all)
        )
        run_state = args.state or args.all
        run_evals = args.all

        # 1. Execute topology audit
        if run_topology:
            code = run_topology_audit(
                repo_root=repo_root,
                wiring_path=args.wiring_path,
                append_rejections=args.append_rejections,
            )
            if code != 0:
                exit_code = code

        # 2. Execute working memory token audit
        if run_state:
            from sdcs.verifier.state import run_state_audit

            state_code = run_state_audit(
                repo_root=repo_root,
                state_path=args.state_path,
                max_tokens=args.max_tokens,
            )
            if state_code != 0:
                exit_code = state_code

        # 3. If --all is requested, also run the evals audit
        if run_evals:
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
