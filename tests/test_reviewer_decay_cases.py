"""Decay may move a rejection out of the ledger only when someone marked it superseded.

Written by the reviewing agent, 2026-09-22 (second pass). Run on a temporary copy of
Floorsmith's docs/map/decisions.md, decay parsed 34 entries, protected the 20 that carry
`*Reopens if:*`, and archived the other 14. Those 14 have no reopen line mostly BECAUSE
they are permanent: "Dash-train periodicity as an OFFSET exclusion -- never", "The
page-global vote on whether walls exist", "Viewport clustering by plateau". The rule
"protect what has a reopen condition" prunes the strongest rejections first.

The ledgers below reproduce that shape. The ratio is Floorsmith's, 20 marked to 14 not.
"""

from __future__ import annotations

from pathlib import Path

from sdcs.decay import prune_decisions_archive


def _floorsmith_shaped_ledger(marked: int, unmarked: int) -> str:
    lines = ["# Decisions", "", "---", "", "## Wall crawl", ""]
    for k in range(marked):
        lines += [
            f"**Reopenable rule {k}.** Measured {k}.{k}% on one sheet. "
            f"*Reopens if:* a second sheet shows the band.",
            "",
        ]
    for k in range(unmarked):
        lines += [
            f"**Standing rejection {k} -- never.** Destroyed {k + 3} rooms on every sheet.",
            "",
        ]
    return "\n".join(lines)


def test_a_rejection_without_a_reopen_line_is_not_pruned(tmp_path: Path):
    ledger = tmp_path / "decisions.md"
    ledger.write_text(_floorsmith_shaped_ledger(marked=20, unmarked=14), encoding="utf-8")

    prune_decisions_archive(ledger, tmp_path, max_entries=15)

    # Check the BODY, not the title: an archived entry leaves its title behind in the
    # ledger's index table, and a first draft of this test passed on that alone.
    text = ledger.read_text(encoding="utf-8")
    missing = [k for k in range(14) if f"Destroyed {k + 3} rooms on every sheet" not in text]
    assert missing == [], f"decay moved {len(missing)} standing rejections out of the ledger"


def test_a_superseded_rejection_is_archived(tmp_path: Path):
    """The opt-in path still works: marking an entry superseded is what releases it."""
    blocks = [
        f"## REJ-{k:03d}: rule {k}\nTHE CLAIM: c{k}\nTHE MEASUREMENT: m{k}\n"
        f"WHAT WOULD REOPEN IT: r{k}\n"
        for k in range(1, 20)
    ]
    blocks.append(
        "## REJ-020: replaced rule\nStatus: SUPERSEDED\nTHE CLAIM: c\n"
        "THE MEASUREMENT: m\nWHAT WOULD REOPEN IT: r\n"
    )
    ledger = tmp_path / "decisions.md"
    ledger.write_text("# Decisions\n\n" + "\n".join(blocks), encoding="utf-8")

    pruned, _ = prune_decisions_archive(ledger, tmp_path, max_entries=15)

    text = ledger.read_text(encoding="utf-8")
    assert pruned == 1
    assert "## REJ-020" not in text
    assert all(f"## REJ-{k:03d}" in text for k in range(1, 20))
