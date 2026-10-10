"""Task definitions for the Click A/B comparative benchmark.

Every task represents an actual post-July 2026 bug fix from pallets/click,
verified fail-to-pass and deterministic.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class BenchmarkTask:
    task_id: str
    issue_number: int
    date: str
    base_commit: str
    fix_commit: str
    files_to_modify: List[str]
    test_file: str
    test_filter: str
    title: str
    problem_statement: str
    full_test_command: str


BENCHMARK_TASKS: List[BenchmarkTask] = [
    BenchmarkTask(
        task_id="click-3571-progressbar-pos",
        issue_number=3571,
        date="2026-08-15",
        base_commit="8b44edf",
        fix_commit="f316d5c",
        files_to_modify=["src/click/_termui_impl.py"],
        test_file="tests/test_termui.py",
        test_filter="test_progressbar_lands_on_final_position",
        title="Settles progress bar on its final position",
        problem_statement=(
            "When using click.progressbar with show_pos=True and update_min_steps set to a "
            "value that does not evenly divide the total length (e.g. length 20 with "
            "update_min_steps=7), the progress bar display freezes at the last completed interval "
            "(e.g. 14/20) and never renders the final position (20/20). Remaining completed "
            "intervals below the threshold stay pending and are never applied. When render_finish() "
            "runs, any pending completed intervals must be stepped and rendered so the progress bar "
            "lands on its true final position."
        ),
        full_test_command="pytest -o pythonpath=src tests/test_termui.py -k test_progressbar_lands_on_final_position",
    ),
    BenchmarkTask(
        task_id="click-3731-pager-windows",
        issue_number=3731,
        date="2026-08-16",
        base_commit="150d107",
        fix_commit="1f9cd54",
        files_to_modify=["src/click/_termui_impl.py"],
        test_file="tests/test_termui.py",
        test_filter="test_tempfile_pager_closes_file_before_unlink",
        title="Close the pager temp file before unlinking it",
        problem_statement=(
            "In click._termui_impl._tempfilepager(), when an exception is raised while writing "
            "to the pager, execution skips the normal f.close() call and enters the finally block "
            "which immediately executes os.unlink(f.name). On Windows, operating systems refuse "
            "to delete a file that is still held open by the process, raising PermissionError: "
            "[WinError 32]. This secondary cleanup failure masks the original user exception. "
            "The temp file handle must be closed before calling os.unlink() so cleanup succeeds."
        ),
        full_test_command="pytest -o pythonpath=src tests/test_termui.py -k test_tempfile_pager_closes_file_before_unlink",
    ),
    BenchmarkTask(
        task_id="click-3805-sentinel-pickle",
        issue_number=3805,
        date="2026-08-29",
        base_commit="420c8fb",
        fix_commit="f58ca3e",
        files_to_modify=["src/click/_utils.py"],
        test_file="tests/test_utils/test_sentinel.py",
        test_filter="test_sentinel_duplication_preserves_identity or test_parameter_duplication",
        title="Fix copy, deepcopy and pickle of Sentinel members",
        problem_statement=(
            "Members of the Sentinel enum (such as UNSET and FLAG_NEEDS_VALUE in click._utils) "
            "and objects that store them as default values (such as click.Option or click.Parameter) "
            "cannot be copied with copy.copy(), copy.deepcopy(), or serialized with pickle. "
            "Python's default Enum reduction attempts to look up members by value: (cls, (member.value,)), "
            "which fails on bare object() values with ValueError: <object> is not a valid Sentinel. "
            "Sentinel members must preserve singleton identity across copy, deepcopy, and pickle reduction."
        ),
        full_test_command="pytest -o pythonpath=src tests/test_utils/test_sentinel.py",
    ),
    BenchmarkTask(
        task_id="click-3802-keyboard-race",
        issue_number=3802,
        date="2026-08-31",
        base_commit="08a7bc6",
        fix_commit="fc518e4",
        files_to_modify=["src/click/core.py"],
        test_file="tests/test_abort_interrupt.py",
        test_filter="",
        title="Fix race condition on KeyboardInterrupt arriving in Command.main()",
        problem_statement=(
            "In Command.main(), if a KeyboardInterrupt or EOFError arrives while the command is "
            "already reporting an abort or an error (for example during echo() or when writing to stderr), "
            "the second interrupt escapes unhandled as a raw Python traceback because reporting logic "
            "ran outside the try block catching interrupts. In standalone mode, the intended exit "
            "code should win and the process should exit cleanly with sys.exit(exit_code) even if "
            "an interrupt interrupts the message, while in non-standalone mode the interrupt should "
            "propagate to the caller."
        ),
        full_test_command="pytest -o pythonpath=src tests/test_abort_interrupt.py",
    ),
    BenchmarkTask(
        task_id="click-3865-shorthelp-abbr",
        issue_number=3865,
        date="2026-09-11",
        base_commit="6d5bac5",
        fix_commit="f67c2bb",
        files_to_modify=["src/click/utils.py"],
        test_file="tests/test_utils/test_make_default_short_help.py",
        test_filter="test_make_default_short_help",
        title="Fix short help abbreviation inside sentence",
        problem_statement=(
            "In click.utils._make_default_short_help(), command help descriptions are truncated "
            "at the first period to extract the leading sentence for short help. However, when the "
            "first sentence contains an abbreviation like 'vs.' or 'e.g.' where the next word "
            "begins with a lowercase letter, the function prematurely truncates the text mid-sentence. "
            "A period must only terminate the sentence if it closes the text or if the subsequent "
            "word does not start with a lowercase letter."
        ),
        full_test_command="pytest -o pythonpath=src tests/test_utils/test_make_default_short_help.py",
    ),
]
