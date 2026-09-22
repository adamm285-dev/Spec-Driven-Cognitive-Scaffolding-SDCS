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
        version=f"sdcs {__version__} (SPEC-001 v{__version__})",
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
        help="Store scaffolding files inside .agent/ directory instead of repo root",
    )
    init_parser.add_argument(
        "--hierarchical",
        action="store_true",
        help="Initialize hierarchical scaffolding across detected subpackages/modules",
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
        "action_or_id",
        nargs="?",
        default=None,
        help="Optional action 'record' or fixture ID to recalibrate directly",
    )
    audit_parser.add_argument(
        "extra_id",
        nargs="?",
        default=None,
        help="Fixture ID when using 'record <ID>'",
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

    # Subcommand: eval (First-class positive episodic memory & recalibration)
    eval_parser = subparsers.add_parser(
        "eval",
        help="Positive episodic memory and empirical standing engine (Pillar 7: evals.md)",
    )
    eval_subparsers = eval_parser.add_subparsers(dest="eval_action")

    # eval record
    eval_record_parser = eval_subparsers.add_parser(
        "record",
        help="Recalibrate one fixture ID or 'all' with newly computed SHA-256 digests in evals.md",
    )
    eval_record_parser.add_argument(
        "fixture_id",
        nargs="?",
        default="all",
        help="Fixture ID to record (e.g. TC-001) or 'all' (default: all)",
    )
    eval_record_parser.add_argument(
        "--evals-path",
        default=None,
        help="Path to evals.md file (default: auto-detect)",
    )
    eval_record_parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path("."),
        help="Path to repository root (default: current directory)",
    )

    # eval audit
    eval_audit_parser = eval_subparsers.add_parser(
        "audit",
        help="Audit ground truth references in evals.md for reachability, hashes, and diversity",
    )
    eval_audit_parser.add_argument(
        "--evals-path",
        default=None,
        help="Path to evals.md file (default: auto-detect)",
    )
    eval_audit_parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path("."),
        help="Path to repository root (default: current directory)",
    )
    eval_audit_parser.add_argument(
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
        "--subsystem",
        "-s",
        type=str,
        default=None,
        help="Filter and display cartography for a specific subsystem or directory prefix",
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
        "--sandbox",
        action="store_true",
        help="Audit staged files against wiring.yaml declarative sandbox protected_paths",
    )
    verify_parser.add_argument(
        "--warehouse",
        action="store_true",
        help="Audit negative memory and warehouse records against Gate W secret/PII filters",
    )
    verify_parser.add_argument(
        "--cycles",
        action="store_true",
        help="Detect cyclic file oscillations and thrashing loops (Circuit Breaker)",
    )
    verify_parser.add_argument(
        "--quality",
        action="store_true",
        help="Audit test files for hollow tests and anti-mocking violations (Gate Q)",
    )
    verify_parser.add_argument(
        "--env",
        action="store_true",
        help="Audit toolchain and runtime invariants (Gate E)",
    )
    verify_parser.add_argument(
        "--all",
        action="store_true",
        help="Execute all verification checks (topology, state, sandbox, warehouse, cycles, quality, env, and evals)",
    )

    # Subcommand: hydrate
    hydrate_parser = subparsers.add_parser(
        "hydrate",
        help="Deterministic context compiler: stream pre-budgeted single-pass payload to stdout",
    )
    hydrate_parser.add_argument(
        "--profile",
        "-p",
        choices=["lite", "standard", "full"],
        default="standard",
        help="Operational scale profile (lite ~400t, standard ~1500t, full ~3500t)",
    )
    hydrate_parser.add_argument(
        "--subsystem",
        "-s",
        type=str,
        default=None,
        help="Filter context, cartography, and rejections for a specific subsystem",
    )
    hydrate_parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path("."),
        help="Path to repository root (default: current directory)",
    )

    # Subcommand: decay
    decay_parser = subparsers.add_parser(
        "decay",
        help="Automated staleness decay and decisions graveyard pruning engine",
    )
    decay_parser.add_argument(
        "--check",
        action="store_true",
        help="Check telemetry staleness and decisions count (default)",
    )
    decay_parser.add_argument(
        "--prune",
        action="store_true",
        help="Automatically archive superseded rejections exceeding active ceiling",
    )
    decay_parser.add_argument(
        "--tag-stale",
        action="store_true",
        help="Automatically tag stale [MEASURED] entries in roadmap.md",
    )
    decay_parser.add_argument(
        "--commit-threshold",
        type=int,
        default=50,
        help="Maximum commits before telemetry is tagged [STALE] (default: 50)",
    )
    decay_parser.add_argument(
        "--max-entries",
        type=int,
        default=15,
        help="Maximum active entries allowed in decisions.md (default: 15)",
    )
    decay_parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path("."),
        help="Path to repository root (default: current directory)",
    )

    # Subcommand: state
    state_parser = subparsers.add_parser(
        "state",
        help="Dynamic working memory blackboard management & subagent lifecycle",
    )
    state_subparsers = state_parser.add_subparsers(dest="state_action")

    # state fork <worker-id>
    state_fork_parser = state_subparsers.add_parser(
        "fork",
        help="Fork an ephemeral scoped blackboard (state.<worker_id>.md) for a subagent",
    )
    state_fork_parser.add_argument(
        "worker_id",
        help="Unique subagent or parallel worker identifier",
    )
    state_fork_parser.add_argument(
        "--objective",
        "-o",
        type=str,
        default=None,
        help="Specific subtask objective to assign to the worker blackboard",
    )
    state_fork_parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path("."),
        help="Path to repository root (default: current directory)",
    )

    # state rollup <worker-id>
    state_rollup_parser = state_subparsers.add_parser(
        "rollup",
        help="Rollup a subagent blackboard into root state.md and cleanup ephemeral slice",
    )
    state_rollup_parser.add_argument(
        "worker_id",
        help="Worker identifier to rollup into root state.md",
    )
    state_rollup_parser.add_argument(
        "--keep-file",
        action="store_true",
        help="Do not delete the ephemeral subagent file after rollup",
    )
    state_rollup_parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path("."),
        help="Path to repository root (default: current directory)",
    )

    # Subcommand: warehouse
    warehouse_parser = subparsers.add_parser(
        "warehouse",
        help="Central Cognitive Warehouse & Fleet Federation engine (SPEC-001 v1.6.0)",
    )
    warehouse_subparsers = warehouse_parser.add_subparsers(dest="warehouse_action")

    # warehouse sync
    wh_sync_parser = warehouse_subparsers.add_parser(
        "sync",
        help="Synchronize global vendor traps and rejections into local cache",
    )
    wh_sync_parser.add_argument(
        "--source",
        type=str,
        default=None,
        help="Source directory or remote git repository URL",
    )
    wh_sync_parser.add_argument(
        "--cache-dir",
        type=Path,
        default=None,
        help="Target local cache directory override",
    )
    wh_sync_parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path("."),
        help="Path to repository root (default: current directory)",
    )

    # warehouse publish <identifier>
    wh_pub_parser = warehouse_subparsers.add_parser(
        "publish",
        help="Promote a local rejection or record to the central warehouse with Gate W scrubbing",
    )
    wh_pub_parser.add_argument(
        "identifier",
        help="Rejection ID in decisions.md (e.g., REJ-001) or path to record file",
    )
    wh_pub_parser.add_argument(
        "--target",
        type=Path,
        default=None,
        help="Path to warehouse repository or directory",
    )
    wh_pub_parser.add_argument(
        "--no-scrub",
        action="store_true",
        help="Disable automatic Gate W redaction of secrets and PII",
    )
    wh_pub_parser.add_argument(
        "--force",
        action="store_true",
        help="Force publication even if Gate W detects unscrubbed secrets",
    )
    wh_pub_parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path("."),
        help="Path to repository root (default: current directory)",
    )

    # warehouse list
    wh_list_parser = warehouse_subparsers.add_parser(
        "list",
        help="List cached warehouse records and inspect subscribed traps",
    )
    wh_list_parser.add_argument(
        "--tag",
        "-t",
        type=str,
        default=None,
        help="Filter records by tag",
    )
    wh_list_parser.add_argument(
        "--json",
        action="store_true",
        help="Output records in JSON format",
    )
    wh_list_parser.add_argument(
        "--cache-dir",
        type=Path,
        default=None,
        help="Target local cache directory override",
    )
    wh_list_parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path("."),
        help="Path to repository root (default: current directory)",
    )

    # Subcommand: doctor
    doctor_parser = subparsers.add_parser(
        "doctor",
        help="Comprehensive system diagnostics for toolchain, environment, and 7 cognitive pillars",
    )
    doctor_parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path("."),
        help="Path to repository root (default: current directory)",
    )

    # Subcommand: watch
    watch_parser = subparsers.add_parser(
        "watch",
        help="Launch the real-time Living Office HUD and background telemetry server",
    )
    watch_parser.add_argument(
        "--port",
        "-p",
        type=int,
        default=8765,
        help="Port to bind the HTTP HUD server (default: 8765)",
    )
    watch_parser.add_argument(
        "--host",
        type=str,
        default="127.0.0.1",
        help="Host address to bind (default: 127.0.0.1)",
    )
    watch_parser.add_argument(
        "--no-browser",
        action="store_true",
        help="Do not automatically open the web HUD in the default browser",
    )
    watch_parser.add_argument(
        "--poll-interval",
        type=float,
        default=1.0,
        help="File watcher polling interval in seconds (default: 1.0)",
    )
    watch_parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path("."),
        help="Path to repository root (default: current directory)",
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
        recalibrate_target = args.recalibrate
        if args.action_or_id:
            if args.action_or_id == "record":
                recalibrate_target = args.extra_id or "all"
            elif not recalibrate_target:
                recalibrate_target = args.action_or_id

        passed = run_audit(
            evals_file=evals_file,
            repo_root=repo_root,
            update_pending=args.update_pending,
            recalibrate=recalibrate_target,
        )
        sys.exit(0 if passed else 1)
    elif args.command == "eval":
        repo_root = args.repo_root.resolve()
        evals_file = locate_evals_file(repo_root, getattr(args, "evals_path", None))
        if getattr(args, "eval_action", None) == "record":
            fid = getattr(args, "fixture_id", "all") or "all"
            passed = run_audit(
                evals_file=evals_file,
                repo_root=repo_root,
                recalibrate=fid,
            )
            sys.exit(0 if passed else 1)
        elif getattr(args, "eval_action", None) == "audit":
            passed = run_audit(
                evals_file=evals_file,
                repo_root=repo_root,
                update_pending=getattr(args, "update_pending", False),
            )
            sys.exit(0 if passed else 1)
        else:
            # Default to audit
            passed = run_audit(
                evals_file=evals_file,
                repo_root=repo_root,
                update_pending=False,
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
            subsystem=args.subsystem,
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

        any_specific_check = (
            args.topology
            or args.state
            or getattr(args, "sandbox", False)
            or getattr(args, "warehouse", False)
            or getattr(args, "cycles", False)
            or getattr(args, "quality", False)
            or getattr(args, "env", False)
            or args.all
        )
        run_topology = args.topology or args.all or (not any_specific_check)
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

        # 3. Execute sandbox audit if requested
        if getattr(args, "sandbox", False):
            from sdcs.verifier.sandbox import run_sandbox_audit

            sandbox_code = run_sandbox_audit(
                repo_root=repo_root,
                wiring_path=args.wiring_path,
            )
            if sandbox_code != 0:
                exit_code = sandbox_code

        # 4. Execute Gate W warehouse screening if requested
        if getattr(args, "warehouse", False):
            from sdcs.warehouse import (
                locate_warehouse_cache,
                locate_warehouse_config,
                run_gate_w_audit,
            )

            print("====================================================================")
            print(" SDCS :: Gate W Secret & PII Sanitization Audit (SPEC-001 v1.6.0)")
            print("====================================================================")
            has_violations = False
            files_to_check = []
            for dec in [repo_root / "decisions.md", repo_root / ".agent" / "decisions.md"]:
                if dec.is_file():
                    files_to_check.append(dec)
            wh_cfg = locate_warehouse_config(repo_root)
            wh_cache = locate_warehouse_cache(repo_root, wh_cfg)
            if wh_cache.is_dir():
                files_to_check.extend(wh_cache.glob("*.md"))

            for f in files_to_check:
                content = f.read_text(encoding="utf-8", errors="ignore")
                clean, violations = run_gate_w_audit(content)
                if not clean:
                    has_violations = True
                    print(f"🛑 [GATE W VIOLATION] Sensitive data in {f.name}:")
                    for v in violations:
                        print(f"   {v}")

            if has_violations:
                print("\n[FAIL] Gate W detected unscrubbed credentials or PII.")
                exit_code = 1
            else:
                print(
                    "✓ [STATUS: CLEAN] Zero sensitive credentials or PII detected in negative memory."
                )

        # 5. Execute Circuit Breaker cycle detection if requested
        if getattr(args, "cycles", False) or args.all:
            from sdcs.verifier.cycles import run_cycle_audit

            cycle_code = run_cycle_audit(repo_root=repo_root)
            if cycle_code != 0:
                exit_code = cycle_code

        # 6. Execute Gate Q test quality audit if requested
        if getattr(args, "quality", False) or args.all:
            from sdcs.verifier.quality import run_quality_audit

            quality_code = run_quality_audit(repo_root=repo_root)
            if quality_code != 0:
                exit_code = quality_code

        # 7. Execute Gate E environment audit if requested
        if getattr(args, "env", False) or args.all:
            from sdcs.verifier.environment import run_env_audit

            env_code = run_env_audit(repo_root=repo_root)
            if env_code != 0:
                exit_code = env_code

        # 8. If --all is requested, also run the evals audit
        if run_evals:
            evals_file = locate_evals_file(repo_root)
            if evals_file and evals_file.is_file():
                evals_passed = run_audit(evals_file=evals_file, repo_root=repo_root)
                if not evals_passed:
                    exit_code = 1

        sys.exit(exit_code)

    elif args.command == "hydrate":
        from sdcs.hydrate import run_hydrate_command

        repo_root = args.repo_root.resolve()
        code = run_hydrate_command(
            repo_root=repo_root,
            profile=args.profile,
            subsystem=args.subsystem,
        )
        sys.exit(code)
    elif args.command == "decay":
        from sdcs.decay import run_decay_command

        repo_root = args.repo_root.resolve()
        code = run_decay_command(
            repo_root=repo_root,
            commit_threshold=args.commit_threshold,
            max_entries=args.max_entries,
            prune=args.prune,
            tag_stale=args.tag_stale,
        )
        sys.exit(code)
    elif args.command == "state":
        repo_root = args.repo_root.resolve()
        if getattr(args, "state_action", None) == "fork":
            from sdcs.verifier.state import fork_subagent_state

            p = fork_subagent_state(
                repo_root=repo_root,
                worker_id=args.worker_id,
                subtask_objective=args.objective,
            )
            print(f"✓ [FORKED] Ephemeral subagent blackboard created: {p}")
            sys.exit(0)
        elif getattr(args, "state_action", None) == "rollup":
            from sdcs.verifier.state import rollup_subagent_state

            success, msg = rollup_subagent_state(
                repo_root=repo_root,
                worker_id=args.worker_id,
                delete_after_rollup=not args.keep_file,
            )
            print(f"{'✓' if success else '🛑'} {msg}")
            sys.exit(0 if success else 1)
        else:
            state_parser.print_help()
            sys.exit(0)
    elif args.command == "warehouse":
        repo_root = args.repo_root.resolve()
        from sdcs.warehouse import (
            compile_tier1_index,
            load_cached_records,
            locate_warehouse_cache,
            locate_warehouse_config,
            publish_record,
            sync_warehouse,
        )

        cfg = locate_warehouse_config(repo_root)
        cache_dir = locate_warehouse_cache(repo_root, cfg, args.cache_dir)

        if getattr(args, "warehouse_action", None) == "sync":
            source = args.source or cfg.get("source")
            if not source:
                print(
                    "Error: No warehouse source provided and none configured in wiring.yaml.",
                    file=sys.stderr,
                )
                sys.exit(1)
            success, msg, _count = sync_warehouse(source, cache_dir)
            print(f"{'✓' if success else '⚠️'} {msg}")
            sys.exit(0 if success else 1)

        elif getattr(args, "warehouse_action", None) == "publish":
            target = args.target
            if not target:
                src_val = cfg.get("source")
                if src_val and Path(src_val).is_dir():
                    target = Path(src_val)
                else:
                    target = cache_dir

            success, msg, scrubbed = publish_record(
                identifier=args.identifier,
                repo_root=repo_root,
                warehouse_target=target,
                scrub=not args.no_scrub,
                force=args.force,
            )
            if scrubbed:
                print(f"ℹ️ [Gate W Scrubbed {len(scrubbed)} sensitive item(s)]:")
                for item in scrubbed:
                    print(f"   - {item}")
            print(f"{'✓' if success else '🛑'} {msg}")
            sys.exit(0 if success else 1)

        elif getattr(args, "warehouse_action", None) == "list":
            records = load_cached_records(cache_dir)
            if args.tag:
                records = [r for r in records if args.tag.lower().lstrip("#") in r.get("tags", [])]

            if args.json:
                import json

                clean_recs = [{k: v for k, v in r.items() if k != "raw_content"} for r in records]
                print(json.dumps(clean_recs, indent=2))
            else:
                print("====================================================================")
                print(f" SDCS Warehouse Cache ({len(records)} records in {cache_dir})")
                print("====================================================================")
                table, _ = compile_tier1_index(records, max_tokens=1000)
                if table:
                    print(table)
                else:
                    print("No cached warehouse records found.")
            sys.exit(0)
        else:
            warehouse_parser.print_help()
            sys.exit(0)
    elif args.command == "doctor":
        from sdcs.verifier.environment import run_doctor_report

        code = run_doctor_report(repo_root=args.repo_root.resolve())
        sys.exit(code)
    elif args.command == "watch":
        from sdcs.watch import run_watch_server

        run_watch_server(
            repo_root=args.repo_root.resolve(),
            port=args.port,
            host=args.host,
            open_browser=not args.no_browser,
            poll_interval=args.poll_interval,
        )
        sys.exit(0)
    else:
        parser.print_help()
        sys.exit(0)


if __name__ == "__main__":
    main()
