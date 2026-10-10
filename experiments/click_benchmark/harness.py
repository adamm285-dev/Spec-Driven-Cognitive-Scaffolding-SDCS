"""Execution harness for the Pallets/Click A/B comparative experiment.

SPEC-001 Methodological Invariants:
1. The harness NEVER writes to src/ or applies patches. Patches must be authored
   exclusively by the autonomous agent during its live session.
2. Synthetic numbers or formulaic token/turn generation are strictly forbidden.
3. Requires a live agent session per run (or configured LLM API key / agent runner).
4. Raw conversational transcripts must be saved per run.
5. Token counts must be extracted directly from API usage fields.
6. Test runtimes must be measured directly via time.perf_counter().
"""

from __future__ import annotations
import json
import os
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional

from tasks import BenchmarkTask

BENCHMARK_DIR = Path(__file__).parent
SCRATCH_CLICK = Path(
    r"C:\Users\adamm_000\.gemini\antigravity\brain\8b59efb6-b7b1-42c7-bae3-9c7d5eebfa30\scratch\click"
)
WORKSPACES_DIR = BENCHMARK_DIR / "workspaces"
RESULTS_DIR = BENCHMARK_DIR / "results"
TRANSCRIPTS_DIR = RESULTS_DIR / "transcripts"
TELEMETRY_FILE = RESULTS_DIR / "telemetry.jsonl"


@dataclass
class RunResult:
    run_id: str
    task_id: str
    arm: str
    iteration: int
    model: str
    solved: bool
    reproduction_pass: bool
    full_suite_pass: bool
    turns: int
    tokens_input: int
    tokens_output: int
    tokens_total: int
    regressions_count: int
    deadends_count: int
    test_runtime_ms: float
    patch_diff: str
    transcript_path: str


def run_cmd(args: list[str], cwd: Path, env: Optional[dict] = None) -> tuple[int, str, float]:
    t0 = time.perf_counter()
    res = subprocess.run(
        args,
        cwd=cwd,
        capture_output=True,
        text=True,
        env=env or os.environ.copy(),
    )
    t1 = time.perf_counter()
    return res.returncode, res.stdout + res.stderr, (t1 - t0) * 1000


def run_pytest(test_cmd: str, cwd: Path) -> tuple[int, str, float]:
    env = os.environ.copy()
    env["PYTHONPATH"] = "src"
    t0 = time.perf_counter()
    res = subprocess.run(
        test_cmd,
        shell=True,
        cwd=cwd,
        capture_output=True,
        text=True,
        env=env,
    )
    t1 = time.perf_counter()
    return res.returncode, res.stdout + res.stderr, (t1 - t0) * 1000


def setup_worktree(task: BenchmarkTask, arm: str, run_idx: int) -> Path:
    """Sets up an isolated, clean git worktree for the run.

    Checks out base_commit, injects reproduction test, and injects scaffolding.
    NEVER touches or modifies src/.
    """
    WORKSPACES_DIR.mkdir(parents=True, exist_ok=True)
    wt_name = f"run_{arm}_{task.task_id}_{run_idx}"
    wt_path = WORKSPACES_DIR / wt_name

    if wt_path.exists():
        run_cmd(["git", "worktree", "remove", "--force", str(wt_path)], cwd=SCRATCH_CLICK)
        if wt_path.exists():
            shutil.rmtree(wt_path, ignore_errors=True)

    # Detached worktree at base_commit
    ret, out, _ = run_cmd(
        ["git", "worktree", "add", "-d", str(wt_path), task.base_commit], cwd=SCRATCH_CLICK
    )
    if ret != 0:
        raise RuntimeError(f"Failed to create worktree: {out}")

    # Checkout test file from fix_commit to reproduce the bug
    ret, out, _ = run_cmd(["git", "checkout", task.fix_commit, "--", task.test_file], cwd=wt_path)
    if ret != 0:
        raise RuntimeError(f"Failed to checkout reproduction test: {out}")

    # Inject scaffolding
    if arm == "arm_a":
        notes_src = BENCHMARK_DIR / "arm_a_notes" / "notes.md"
        shutil.copy2(notes_src, wt_path / "notes.md")
    else:
        arm_b_src = BENCHMARK_DIR / "arm_b_sdcs"
        for pillar_file in arm_b_src.glob("*"):
            if pillar_file.is_file():
                shutil.copy2(pillar_file, wt_path / pillar_file.name)

    return wt_path


def teardown_worktree(wt_path: Path):
    if wt_path.exists():
        run_cmd(["git", "worktree", "remove", "--force", str(wt_path)], cwd=SCRATCH_CLICK)
        if wt_path.exists():
            shutil.rmtree(wt_path, ignore_errors=True)


def generate_agent_prompt(task: BenchmarkTask, arm: str) -> str:
    """Generates the initial prompt for the autonomous agent."""
    if arm == "arm_a":
        return (
            f"You are an AI coding assistant solving an issue in pallets/click.\n"
            f"Issue #{task.issue_number}: {task.title}\n\n"
            f"Problem Description:\n{task.problem_statement}\n\n"
            f"Please inspect the codebase, refer to `notes.md` for architectural conventions and "
            f"testing instructions, and apply the minimal code change to resolve the issue.\n"
            f"Verify your fix by running: {task.full_test_command}\n"
            f"Ensure zero regressions on the existing test suite.\n"
        )
    else:
        return (
            f"You are an AI coding assistant operating under Spec-Driven Cognitive Scaffolding (SDCS / SPEC-001 v1.8.1).\n"
            f"Issue #{task.issue_number}: {task.title}\n\n"
            f"Problem Description:\n{task.problem_statement}\n\n"
            f"Follow the Turn 1 boot hydration sequence and 4-phase autonomous execution cycle in `AGENTS.md`.\n"
            f"Consult `app_map.md` to locate relevant modules. Check `decisions.md` before making architectural decisions.\n"
            f"Respect subsystem boundaries declared in `wiring.yaml`.\n"
            f"Maintain `state.md` strictly within <= 350 tokens.\n"
            f"Verify your fix by running: {task.full_test_command}\n"
            f"Verify zero regressions against the baseline scorecard in `evals.md`.\n"
        )


def execute_agent_run(
    task: BenchmarkTask,
    arm: str,
    run_idx: int,
    agent_runner: Callable[[str, Path], dict],
    model_name: str = "gemini-2.5-pro",
) -> RunResult:
    """Executes a real agent run against an isolated worktree.

    agent_runner: Callable[[prompt, workspace_path], dict]
      Must invoke the autonomous agent and return:
      {
        "turns": int,
        "tokens_input": int (from API usage),
        "tokens_output": int (from API usage),
        "transcript": list[dict],
        "deadends_count": int,
      }
    """
    run_id = f"run_{arm}_{task.task_id}_{run_idx}"
    print(f"\n--- Setting up {run_id} ---")

    wt_path = setup_worktree(task, arm, run_idx)
    TRANSCRIPTS_DIR.mkdir(parents=True, exist_ok=True)
    transcript_file = TRANSCRIPTS_DIR / f"{run_id}.jsonl"

    try:
        # 1. Verify reproduction test fails before agent edits
        ret_initial, out_initial, _ = run_pytest(task.full_test_command, wt_path)
        if ret_initial == 0:
            raise RuntimeError(f"Reproduction test passed before any edits: {out_initial}")

        # 2. Formulate prompt
        prompt = generate_agent_prompt(task, arm)

        # 3. Invoke real agent session
        print(f"  Dispatching task to agent ({model_name})...")
        t_agent_start = time.perf_counter()
        agent_data = agent_runner(prompt, wt_path)
        t_agent_elapsed = time.perf_counter() - t_agent_start
        print(
            f"  Agent session completed in {t_agent_elapsed:.2f}s across {agent_data['turns']} turns."
        )

        # 4. Save raw transcript
        with open(transcript_file, "w", encoding="utf-8") as f_tr:
            for turn in agent_data.get("transcript", []):
                f_tr.write(json.dumps(turn) + "\n")

        # 5. Extract patch authored by agent
        ret_diff, patch_diff, _ = run_cmd(["git", "diff", "src/"], cwd=wt_path)
        if not patch_diff.strip():
            print("  WARNING: Agent produced no changes to src/!")

        # 6. Measure reproduction test after agent patch
        ret_post, out_post, dur_test_ms = run_pytest(task.full_test_command, wt_path)
        reproduction_pass = ret_post == 0

        # 7. Check full test suite for regressions
        ret_full, out_full, _ = run_pytest("pytest -o pythonpath=src -q", wt_path)
        full_suite_pass = ret_full == 0

        # Count regressions if full suite failed
        regressions = 0
        if not full_suite_pass:
            for line in out_full.splitlines():
                if line.startswith("FAILED ") and task.test_file not in line:
                    regressions += 1

        solved = reproduction_pass and (regressions == 0)

        return RunResult(
            run_id=run_id,
            task_id=task.task_id,
            arm=arm,
            iteration=run_idx,
            model=model_name,
            solved=solved,
            reproduction_pass=reproduction_pass,
            full_suite_pass=full_suite_pass,
            turns=agent_data["turns"],
            tokens_input=agent_data["tokens_input"],
            tokens_output=agent_data["tokens_output"],
            tokens_total=agent_data["tokens_input"] + agent_data["tokens_output"],
            regressions_count=regressions,
            deadends_count=agent_data.get("deadends_count", 0),
            test_runtime_ms=dur_test_ms,
            patch_diff=patch_diff,
            transcript_path=str(transcript_file.relative_to(BENCHMARK_DIR)),
        )

    finally:
        teardown_worktree(wt_path)


def main():
    """Entrypoint for executing the benchmark.

    Requires a live agent runner. Synthetic runs are physically rejected.
    """
    has_gemini_key = bool(os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY"))
    if not has_gemini_key:
        print("\n" + "=" * 70)
        print("ERROR: NO LIVE MODEL API CREDENTIALS CONFIGURED.")
        print("=" * 70)
        print("Per SDCS SPEC-001 methodological invariants:")
        print("  1. Synthetic, formulaic, or simulated numbers are strictly forbidden.")
        print("  2. Every run requires an actual autonomous agent session.")
        print("  3. Token counts must be extracted from real API usage fields.")
        print("  4. Patches must be authored exclusively by the agent in the workspace.")
        print("\nTo run this pilot, provide GEMINI_API_KEY or an external agent runner")
        print("callable to execute_agent_run().")
        print("=" * 70 + "\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
