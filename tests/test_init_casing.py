import os
from pathlib import Path

from sdcs.init import init_scaffold, normalize_legacy_casing


def test_normalize_legacy_casing(tmp_path):
    # Create legacy uppercase files
    state_upper = tmp_path / "STATE.md"
    state_upper.write_text("# Old State\n", encoding="utf-8")
    spine_upper = tmp_path / "SPINE.md"
    spine_upper.write_text("# Old Spine\n", encoding="utf-8")

    normalized = normalize_legacy_casing(tmp_path)
    assert len(normalized) == 2
    # Verify canonical lowercase files now exist
    assert (tmp_path / "state.md").is_file()
    assert (tmp_path / "spine.md").is_file()


def test_init_scaffold_with_casing_normalization(tmp_path):
    # Simulate legacy repo with STATE.md
    (tmp_path / "STATE.md").write_text("# Legacy State\n", encoding="utf-8")

    init_scaffold(target_dir=tmp_path, skip_hooks=True)
    assert (tmp_path / "state.md").is_file()
    assert (tmp_path / "spine.md").is_file()
    assert (tmp_path / "wiring.yaml").is_file()
