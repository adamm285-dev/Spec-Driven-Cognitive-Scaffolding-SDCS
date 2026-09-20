import subprocess
import sys
from pathlib import Path

from sdcs.map import check_cartography, parse_mapped_files, sync_cartography


def test_parse_mapped_files():
    content = """# Repository Cartography (The Compass)

### `root/`
- `AGENTS.md`
- `README.md`

### `src/core/`
- `engine.py` - Core engine
- `utils.py`
"""
    mapped = parse_mapped_files(content)
    assert "AGENTS.md" in mapped
    assert "README.md" in mapped
    assert "src/core/engine.py" in mapped
    assert "src/core/utils.py" in mapped


def test_check_cartography_detects_unmapped_and_orphaned(tmp_path: Path):
    # Setup files on disk
    src_dir = tmp_path / "src"
    src_dir.mkdir(parents=True)
    (src_dir / "app.py").write_text("# app", encoding="utf-8")
    (src_dir / "untracked.py").write_text("# untracked", encoding="utf-8")

    # Map only contains app.py and a deleted file old.py
    map_file = tmp_path / "app_map.md"
    map_content = """# Cartography
### `src/`
- `app.py`
- `old.py`
"""
    map_file.write_text(map_content, encoding="utf-8")

    unmapped, orphaned = check_cartography(tmp_path, map_file)

    assert "src/untracked.py" in unmapped
    assert "src/old.py" in orphaned
    assert "src/app.py" not in unmapped
    assert "src/app.py" not in orphaned


def test_sync_cartography_updates_map(tmp_path: Path):
    src_dir = tmp_path / "src"
    src_dir.mkdir(parents=True)
    (src_dir / "app.py").write_text("# app", encoding="utf-8")
    (src_dir / "new_feature.py").write_text("# new feature", encoding="utf-8")

    map_file = tmp_path / "app_map.md"
    map_content = """# Cartography
### `src/`
- `app.py` - Core application
- `removed.py`
"""
    map_file.write_text(map_content, encoding="utf-8")

    # Execute sync
    success = sync_cartography(tmp_path, map_file)
    assert success is True

    # Re-check cartography: should now be completely clean
    unmapped, orphaned = check_cartography(tmp_path, map_file)
    assert len(unmapped) == 0
    assert len(orphaned) == 0

    updated_content = map_file.read_text(encoding="utf-8")
    assert "app.py" in updated_content
    assert "new_feature.py" in updated_content
    assert "Core application" in updated_content  # Preserved annotation
    assert "removed.py" not in updated_content  # Orphan removed


def test_cli_map_check_and_sync(tmp_path: Path):
    import os

    env = dict(os.environ)
    env["PYTHONPATH"] = str(Path(__file__).parent.parent / "src")

    src_dir = tmp_path / "src"
    src_dir.mkdir(parents=True)
    (src_dir / "module.py").write_text("# mod", encoding="utf-8")

    map_file = tmp_path / "app_map.md"
    map_file.write_text("# Cartography\n", encoding="utf-8")

    # 1. sdcs map --check should exit with code 1 due to unmapped files
    cmd_check = [
        sys.executable,
        "-m",
        "sdcs.cli",
        "map",
        "--check",
        "--repo-root",
        str(tmp_path),
    ]
    res_check = subprocess.run(cmd_check, capture_output=True, text=True, env=env, check=False)
    assert res_check.returncode == 1
    assert "DRIFT: UNMAPPED FILES" in res_check.stdout

    # 2. sdcs map --sync should synchronize app_map.md and exit 0
    cmd_sync = [
        sys.executable,
        "-m",
        "sdcs.cli",
        "map",
        "--sync",
        "--repo-root",
        str(tmp_path),
    ]
    res_sync = subprocess.run(cmd_sync, capture_output=True, text=True, env=env, check=False)
    assert res_sync.returncode == 0
    assert "Cartography synchronized" in res_sync.stdout

    # 3. sdcs map --check should now exit with code 0
    res_clean = subprocess.run(cmd_check, capture_output=True, text=True, env=env, check=False)
    assert res_clean.returncode == 0
    assert "100% in sync" in res_clean.stdout
