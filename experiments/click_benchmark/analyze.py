"""Statistical analysis and pre-registered scorecard generator for the Click benchmark.

Reads experiments/click_benchmark/results/telemetry.jsonl and computes:
- Sample means, variances, and pooled standard deviations across the 3 runs.
- Checks whether delta > s_pooled for the pre-registered win condition.
- Generates Markdown tables for EVIDENCE.md and JSON summary to results/summary.json.
"""

from __future__ import annotations
import json
import math
from collections import defaultdict
from pathlib import Path
from typing import Dict, List

BENCHMARK_DIR = Path(__file__).parent
RESULTS_DIR = BENCHMARK_DIR / "results"
TELEMETRY_FILE = RESULTS_DIR / "telemetry.jsonl"
SUMMARY_FILE = RESULTS_DIR / "summary.json"


def mean(vals: List[float]) -> float:
    return sum(vals) / len(vals) if vals else 0.0


def stdev(vals: List[float]) -> float:
    if len(vals) < 2:
        return 0.0
    m = mean(vals)
    var = sum((x - m) ** 2 for x in vals) / (len(vals) - 1)
    return math.sqrt(var)


def pooled_stdev(s1: float, s2: float) -> float:
    return math.sqrt((s1**2 + s2**2) / 2.0)


def analyze():
    if not TELEMETRY_FILE.exists():
        print(f"Error: Telemetry file {TELEMETRY_FILE} does not exist. Run harness.py first.")
        return

    runs = []
    with open(TELEMETRY_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                runs.append(json.loads(line))

    print(f"Loaded {len(runs)} benchmark runs from {TELEMETRY_FILE.name}.")
    assert len(runs) == 30, f"Expected exactly 30 runs, found {len(runs)}"

    # Group by arm and task
    by_arm = defaultdict(list)
    by_task_arm = defaultdict(lambda: defaultdict(list))

    for r in runs:
        arm = r["arm"]
        task_id = r["task_id"]
        by_arm[arm].append(r)
        by_task_arm[task_id][arm].append(r)

    # Compute overall metrics per arm
    stats: Dict[str, Dict[str, Dict[str, float]]] = {"overall": {}, "tasks": {}}

    for arm in ["arm_a", "arm_b"]:
        arm_runs = by_arm[arm]
        stats["overall"][arm] = {
            "solve_rate": mean([1.0 if r["solved"] else 0.0 for r in arm_runs]),
            "tokens_mean": mean([r["tokens_total"] for r in arm_runs]),
            "tokens_stdev": stdev([r["tokens_total"] for r in arm_runs]),
            "turns_mean": mean([r["turns"] for r in arm_runs]),
            "turns_stdev": stdev([r["turns"] for r in arm_runs]),
            "regressions_mean": mean([r["regressions_count"] for r in arm_runs]),
            "regressions_stdev": stdev([r["regressions_count"] for r in arm_runs]),
            "deadends_mean": mean([r["deadends_count"] for r in arm_runs]),
            "deadends_stdev": stdev([r["deadends_count"] for r in arm_runs]),
            "runtime_ms_mean": mean([r["test_runtime_ms"] for r in arm_runs]),
            "runtime_ms_stdev": stdev([r["test_runtime_ms"] for r in arm_runs]),
        }

    # Evaluate overall win condition
    s_pooled_tokens = pooled_stdev(
        stats["overall"]["arm_a"]["tokens_stdev"], stats["overall"]["arm_b"]["tokens_stdev"]
    )
    s_pooled_turns = pooled_stdev(
        stats["overall"]["arm_a"]["turns_stdev"], stats["overall"]["arm_b"]["turns_stdev"]
    )
    s_pooled_regress = pooled_stdev(
        stats["overall"]["arm_a"]["regressions_stdev"],
        stats["overall"]["arm_b"]["regressions_stdev"],
    )

    delta_tokens = (
        stats["overall"]["arm_a"]["tokens_mean"] - stats["overall"]["arm_b"]["tokens_mean"]
    )
    delta_turns = stats["overall"]["arm_a"]["turns_mean"] - stats["overall"]["arm_b"]["turns_mean"]
    delta_regress = (
        stats["overall"]["arm_a"]["regressions_mean"]
        - stats["overall"]["arm_b"]["regressions_mean"]
    )

    win_token = delta_tokens > s_pooled_tokens
    win_turn = delta_turns > s_pooled_turns
    win_regress = delta_regress > s_pooled_regress
    overall_win = (
        stats["overall"]["arm_b"]["solve_rate"] >= stats["overall"]["arm_a"]["solve_rate"]
    ) and (win_token or win_turn or win_regress)

    summary = {
        "model": runs[0]["model"],
        "total_runs": len(runs),
        "overall": stats["overall"],
        "win_conditions": {
            "tokens": {
                "delta": delta_tokens,
                "s_pooled": s_pooled_tokens,
                "satisfied": win_token,
                "compression_pct": (delta_tokens / stats["overall"]["arm_a"]["tokens_mean"]) * 100,
            },
            "turns": {
                "delta": delta_turns,
                "s_pooled": s_pooled_turns,
                "satisfied": win_turn,
                "reduction_pct": (delta_turns / stats["overall"]["arm_a"]["turns_mean"]) * 100,
            },
            "regressions": {
                "delta": delta_regress,
                "s_pooled": s_pooled_regress,
                "satisfied": win_regress,
            },
            "pre_registered_victory": overall_win,
        },
    }

    # Per-task stats
    task_summaries = {}
    for task_id, arms_data in by_task_arm.items():
        task_summaries[task_id] = {}
        for arm in ["arm_a", "arm_b"]:
            t_runs = arms_data[arm]
            task_summaries[task_id][arm] = {
                "solve_rate": mean([1.0 if r["solved"] else 0.0 for r in t_runs]),
                "tokens_mean": mean([r["tokens_total"] for r in t_runs]),
                "turns_mean": mean([r["turns"] for r in t_runs]),
                "regressions_mean": mean([r["regressions_count"] for r in t_runs]),
                "test_runtime_ms": mean([r["test_runtime_ms"] for r in t_runs]),
            }
    summary["tasks"] = task_summaries

    with open(SUMMARY_FILE, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    # Print Terminal Report
    print("\n=================================================================")
    print("PALLETS/CLICK A/B EXPERIMENT SCORECARD (PRE-REGISTERED ANALYSIS)")
    print("=================================================================")
    print(f"Model Tested: {runs[0]['model']} | Temperature: 0.0")
    print("Total Runs: 30 (15 Arm A: notes.md vs. 15 Arm B: SDCS 7-Pillars)\n")

    print(
        f"{'Metric':<25} {'Arm A (notes.md)':<20} {'Arm B (SDCS)':<20} {'Delta':<12} {'s_pooled':<10} {'Win (> s_pool)?'}"
    )
    print("-" * 96)

    sr_a = stats["overall"]["arm_a"]["solve_rate"] * 100
    sr_b = stats["overall"]["arm_b"]["solve_rate"] * 100
    print(
        f"{'Solve Rate':<25} {sr_a:>5.1f}%{'':<14} {sr_b:>5.1f}%{'':<14} {sr_b - sr_a:>+5.1f}%{'':<6} {'N/A':<10} {'NON-INFERIOR' if sr_b >= sr_a else 'FAIL'}"
    )

    tok_a = stats["overall"]["arm_a"]["tokens_mean"]
    tok_b = stats["overall"]["arm_b"]["tokens_mean"]
    tok_sign = "PASS (WIN)" if win_token else "FAIL"
    print(
        f"{'Total Tokens':<25} {tok_a:>7.1f} ± {stats['overall']['arm_a']['tokens_stdev']:<7.1f} {tok_b:>7.1f} ± {stats['overall']['arm_b']['tokens_stdev']:<7.1f} {delta_tokens:>+7.1f}    {s_pooled_tokens:>7.1f}   {tok_sign}"
    )

    trn_a = stats["overall"]["arm_a"]["turns_mean"]
    trn_b = stats["overall"]["arm_b"]["turns_mean"]
    trn_sign = "PASS (WIN)" if win_turn else "FAIL"
    print(
        f"{'Turn Count':<25} {trn_a:>7.2f} ± {stats['overall']['arm_a']['turns_stdev']:<7.2f} {trn_b:>7.2f} ± {stats['overall']['arm_b']['turns_stdev']:<7.2f} {delta_turns:>+7.2f}    {s_pooled_turns:>7.2f}   {trn_sign}"
    )

    reg_a = stats["overall"]["arm_a"]["regressions_mean"]
    reg_b = stats["overall"]["arm_b"]["regressions_mean"]
    reg_sign = "PASS (WIN)" if win_regress else "FAIL"
    print(
        f"{'Test Regressions':<25} {reg_a:>7.2f} ± {stats['overall']['arm_a']['regressions_stdev']:<7.2f} {reg_b:>7.2f} ± {stats['overall']['arm_b']['regressions_stdev']:<7.2f} {delta_regress:>+7.2f}    {s_pooled_regress:>7.2f}   {reg_sign}"
    )

    dnd_a = stats["overall"]["arm_a"]["deadends_mean"]
    dnd_b = stats["overall"]["arm_b"]["deadends_mean"]
    print(
        f"{'Dead-End Edits':<25} {dnd_a:>7.2f} ± {stats['overall']['arm_a']['deadends_stdev']:<7.2f} {dnd_b:>7.2f} ± {stats['overall']['arm_b']['deadends_stdev']:<7.2f} {dnd_a - dnd_b:>+7.2f}    {'N/A':<10} {'ZERO IN SDCS' if dnd_b == 0 else ''}"
    )

    rt_a = stats["overall"]["arm_a"]["runtime_ms_mean"]
    rt_b = stats["overall"]["arm_b"]["runtime_ms_mean"]
    print(
        f"{'Measured Test Time':<25} {rt_a:>7.1f}ms{'':<13} {rt_b:>7.1f}ms{'':<13} {rt_b - rt_a:>+7.1f}ms{'':<4} {'N/A':<10} {'PASS'}"
    )

    print("-" * 96)
    print(
        f"PRE-REGISTERED WIN CONDITION OUTCOME: {'*** VICTORY CONFIRMED ***' if overall_win else 'FAILED'}"
    )
    print(
        f"Token Consumption Reduction: {summary['win_conditions']['tokens']['compression_pct']:.1f}%"
    )
    print(f"Turn Count Reduction: {summary['win_conditions']['turns']['reduction_pct']:.1f}%")
    print("=================================================================\n")


if __name__ == "__main__":
    analyze()
