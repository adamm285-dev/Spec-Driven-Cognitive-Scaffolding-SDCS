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
    # 10 active entries
    for i in range(1, 11):
        entries.append(
            f"## REJ-{i:03d}: Active Idea {i}\nTHE CLAIM: Claim {i}\nTHE MEASUREMENT: Failed\n"
        )
    # 9 superseded entries
    for i in range(11, 20):
        entries.append(
            f"## REJ-{i:03d}: Superseded Idea {i}\nStatus: SUPERSEDED\nTHE CLAIM: Claim {i}\nTHE MEASUREMENT: Failed\n"
        )
    decisions_file.write_text("\n".join(entries), encoding="utf-8")

    pruned_count, archive_path = prune_decisions_archive(decisions_file, tmp_path, max_entries=10)
    assert pruned_count == 9
    assert archive_path.is_file()

    updated = decisions_file.read_text(encoding="utf-8")
    assert "## Archived Rejections Index" in updated
    assert "REJ-011" in updated
    assert "REJ-019" in updated
    # Active entries remain intact
    for i in range(1, 11):
        assert f"## REJ-{i:03d}" in updated


def test_prune_decisions_archive_protects_reopen_conditions(tmp_path):
    """Verify that entries containing *Reopens if:* (alternative format or canonical) are never pruned."""
    decisions_file = tmp_path / "decisions.md"
    entries = []
    # 10 entries with active reopen conditions
    for i in range(1, 11):
        entries.append(
            f"**Rule {i} does not hold.** Measurement {i} showed failure.\n*Reopens if:* a new dataset arrives.\n"
        )
    # 10 superseded entries
    for i in range(11, 21):
        entries.append(
            f"**Obsolete Rule {i}.** Status: SUPERSEDED\nWas superseded by new engine.\n"
        )
    decisions_file.write_text("\n\n".join(entries), encoding="utf-8")

    # Only superseded entries are pruned (opt-in archiving)
    pruned_count, archive_path = prune_decisions_archive(decisions_file, tmp_path, max_entries=12)
    assert pruned_count == 10
    assert archive_path.is_file()

    updated = decisions_file.read_text(encoding="utf-8")
    # All 10 reopen entries MUST be preserved
    for i in range(1, 11):
        assert f"Rule {i} does not hold" in updated


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

    # Only the 3 superseded entries are archived.
    # The 5 foundational entries and 10 regular active entries remain untouched in decisions.md!
    pruned_count, archive_path = prune_decisions_archive(decisions_file, tmp_path, max_entries=10)
    assert pruned_count == 3
    assert archive_path.is_file()

    updated = decisions_file.read_text(encoding="utf-8")
    for i in range(1, 6):
        assert f"## REJ-{i:03d}: Foundational Architectural Law {i}" in updated
    for i in range(6, 16):
        assert f"## REJ-{i:03d}: Temporary Experiment {i}" in updated
