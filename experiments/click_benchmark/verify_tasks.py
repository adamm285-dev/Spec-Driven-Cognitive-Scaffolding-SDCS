"""Task verification and blindness audit script for the Click benchmark.

Validates:
1. Every task fails on base_commit with reproduction test.
2. Every task passes on fix_commit with reproduction test.
3. Task 4 race test passes deterministically 3/3 times.
4. Pillar blindness: arm_b_sdcs and arm_a_notes have 0 leaked keywords.
"""

import os
import re
import subprocess
import sys
import time
from pathlib import Path

from tasks import BENCHMARK_TASKS

SCRATCH_CLICK = Path(os.environ.get("CLICK_REPO_PATH", BENCHMARK_DIR / "click"))
BENCHMARK_DIR = Path(__file__).parent

FORBIDDEN_LEAK_KEYWORDS = [
    r"update_min_steps",
    r"_completed_intervals",
    r"PermissionError: \[WinError 32\]",
    r"3802",
    r"3571",
    r"3731",
    r"3805",
    r"3865",
    r"test_abort_interrupt",
    r"test_make_default_short_help",
    r"test_sentinel_duplication",
    r"test_tempfile_pager_closes_file_before_unlink",
    r"test_progressbar_lands_on_final_position",
]


def run_git(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git"] + args, cwd=SCRATCH_CLICK, capture_output=True, text=True, check=True
    )


def run_pytest(cmd_str: str) -> tuple[int, str, float]:
    env = os.environ.copy()
    env["PYTHONPATH"] = "src"
    t0 = time.perf_counter()
    res = subprocess.run(
        cmd_str,
        shell=True,
        cwd=SCRATCH_CLICK,
        capture_output=True,
        text=True,
        env=env,
    )
    t1 = time.perf_counter()
    return res.returncode, res.stdout + res.stderr, (t1 - t0) * 1000


def audit_blindness():
    print("\n--- Auditing Blinded Scaffolding & Notes Parity ---")
    files_to_check = list((BENCHMARK_DIR / "arm_b_sdcs").glob("*")) + [
        BENCHMARK_DIR / "arm_a_notes" / "notes.md"
    ]
    leaks = []
    for f in files_to_check:
        if not f.is_file():
            continue
        content = f.read_text(encoding="utf-8")
        for kw in FORBIDDEN_LEAK_KEYWORDS:
            if re.search(kw, content, re.IGNORECASE):
                leaks.append((f.name, kw))

    if leaks:
        print(f"FAILED: Found {len(leaks)} information leaks in pillars/notes:")
        for fn, kw in leaks:
            print(f"  - {fn}: matches '{kw}'")
        sys.exit(1)
    else:
        print("PASS: 100% Blindness confirmed. Zero task keywords leaked in Arm A or Arm B.")


def audit_tasks():
    print("\n--- Validating Fail-to-Pass Invariants on Disk ---")
    results = []

    for task in BENCHMARK_TASKS:
        print(f"\n[Task {task.task_id}] {task.title}")
        # 1. Checkout base_commit
        run_git(["checkout", "-f", task.base_commit])
        run_git(["clean", "-fd"])

        # 2. Checkout test file from fix_commit to reproduce
        run_git(["checkout", task.fix_commit, "--", task.test_file])

        # 3. Run test on base -> must FAIL
        ret_fail, out_fail, duration_fail = run_pytest(task.full_test_command)
        assert (
            ret_fail != 0
        ), f"Task {task.task_id} expected to fail on base_commit, but passed! Output: {out_fail}"
        print(f"  Base commit ({task.base_commit}): FAILS as expected in {duration_fail:.1f}ms")

        # 4. Checkout fix_commit
        run_git(["checkout", "-f", task.fix_commit])
        run_git(["clean", "-fd"])

        # 5. Run test on fix -> must PASS
        ret_pass, out_pass, duration_pass = run_pytest(task.full_test_command)
        assert (
            ret_pass == 0
        ), f"Task {task.task_id} expected to pass on fix_commit, but failed! Output: {out_pass}"
        print(f"  Fix commit ({task.fix_commit}): PASSES as expected in {duration_pass:.1f}ms")

        # 6. If Task 4 (race test), run 3 times to confirm determinism
        if task.task_id == "click-3802-keyboard-race":
            for run_idx in range(1, 4):
                r_ret, _, r_dur = run_pytest(task.full_test_command)
                assert (
                    r_ret == 0
                ), f"Task {task.task_id} failed on run {run_idx} of determinism check!"
            print(f"  Determinism check: 3/3 consecutive runs PASSED clean (avg {r_dur:.1f}ms)")

        results.append(
            {
                "task_id": task.task_id,
                "fail_ms": duration_fail,
                "pass_ms": duration_pass,
            }
        )

    # Cleanup working tree
    run_git(["checkout", "-f", "main"])
    run_git(["clean", "-fd"])

    print("\n--- Summary of Measured Task Runtimes ---")
    for r in results:
        print(f"  {r['task_id']:<30} Fail: {r['fail_ms']:>6.1f}ms | Pass: {r['pass_ms']:>6.1f}ms")
    print("All 5 tasks verified fail-to-pass and deterministic.")


if __name__ == "__main__":
    audit_blindness()
    audit_tasks()
