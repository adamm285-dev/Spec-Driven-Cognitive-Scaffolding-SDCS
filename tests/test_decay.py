import os
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

from sdcs.decay import audit_roadmap_staleness, prune_decisions_archive, run_decay_command

ENV = dict(os.environ)
ENV["PYTHONPATH"] = str(Path(__file__).parent.parent / "src")


def test_audit_roadmap_staleness_fresh_and_stale(tmp_path):
    roadmap_file = tmp_path / "roadmap.md"
    roadmap_file.write_text(
        "## Milestone M-001\n"
        "* [INTENT]: High throughput\n"
        "* [MEASURED]: 500 RPS (Commit `abc1234`)\n"
        "## Milestone M-002\n"
        "* [INTENT]: Low latency\n"
        "* [MEASURED]: 2ms (Commit `def5678`)\n",
        encoding="utf-8",
    )

    def mock_distance(root, commit):
        return 10 if commit == "abc1234" else 65

    with patch("sdcs.decay.get_commit_distance", side_effect=mock_distance):
        stale_count, records = audit_roadmap_staleness(roadmap_file, tmp_path, threshold=50, tag_stale=True)
        assert stale_count == 1
        assert len(records) == 2
        assert records[0]["stale"] is False
        assert records[1]["stale"] is True

        # Verify tag was appended
        updated = roadmap_file.read_text(encoding="utf-8")
        assert "[STALE: 65 commits behind HEAD]" in updated


def test_prune_decisions_archive(tmp_path):
    decisions_file = tmp_path / "decisions.md"
    entries = []
    for i in range(1, 20):
        entries.append(f"## REJ-{i:03d}: Attempted Idea {i}\nTHE CLAIM: Claim {i}\nTHE MEASUREMENT: Failed\nWHAT WOULD REOPEN IT: Fix\n")
    decisions_file.write_text("\n".join(entries), encoding="utf-8")

    pruned_count, archive_path = prune_decisions_archive(decisions_file, tmp_path, max_entries=10)
    assert pruned_count == 9
    assert archive_path.is_file()

    updated = decisions_file.read_text(encoding="utf-8")
    assert "## Archived Rejections Index" in updated
    assert "REJ-001" in updated
    assert "REJ-019" in updated
