import os
from pathlib import Path
from unittest.mock import patch

from sdcs.decay import audit_roadmap_staleness, prune_decisions_archive

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
        stale_count, records = audit_roadmap_staleness(
            roadmap_file, tmp_path, threshold=50, tag_stale=True
        )
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
        entries.append(
            f"## REJ-{i:03d}: Attempted Idea {i}\nTHE CLAIM: Claim {i}\nTHE MEASUREMENT: Failed\nWHAT WOULD REOPEN IT: Fix\n"
        )
    decisions_file.write_text("\n".join(entries), encoding="utf-8")

    pruned_count, archive_path = prune_decisions_archive(decisions_file, tmp_path, max_entries=10)
    assert pruned_count == 9
    assert archive_path.is_file()

    updated = decisions_file.read_text(encoding="utf-8")
    assert "## Archived Rejections Index" in updated
    assert "REJ-001" in updated
    assert "REJ-019" in updated


def test_prune_decisions_archive_protects_foundational(tmp_path):
    decisions_file = tmp_path / "decisions.md"
    entries = []
    # Create 5 foundational rejections (e.g. REJ-001 to REJ-005)
    for i in range(1, 6):
        entries.append(
            f"## REJ-{i:03d}: Foundational Architectural Law {i}\nStatus: FOUNDATIONAL\nPermanent: true\nTHE CLAIM: Core Law {i}\nTHE MEASUREMENT: Invariant\n"
        )
    # Create 10 regular active rejections (REJ-006 to REJ-015)
    for i in range(6, 16):
        entries.append(
            f"## REJ-{i:03d}: Temporary Experiment {i}\nStatus: ACTIVE\nTHE CLAIM: Experiment {i}\nTHE MEASUREMENT: Failed\n"
        )
    # Create 3 superseded rejections (REJ-016 to REJ-018)
    for i in range(16, 19):
        entries.append(
            f"## REJ-{i:03d}: Obsolete Experiment {i}\nStatus: SUPERSEDED\nTHE CLAIM: Obsolete {i}\nTHE MEASUREMENT: Superseded\n"
        )
    decisions_file.write_text("\n".join(entries), encoding="utf-8")

    # Total 18 entries, max_entries=10 -> excess is 8.
    # The 3 superseded entries and 5 oldest regular entries should be archived.
    # The 5 foundational entries (REJ-001 to REJ-005) MUST remain untouched in decisions.md!
    pruned_count, archive_path = prune_decisions_archive(decisions_file, tmp_path, max_entries=10)
    assert pruned_count == 8
    assert archive_path.is_file()

    updated = decisions_file.read_text(encoding="utf-8")
    for i in range(1, 6):
        assert f"## REJ-{i:03d}: Foundational Architectural Law {i}" in updated
