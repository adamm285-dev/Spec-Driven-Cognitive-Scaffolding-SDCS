import json
import os
import subprocess
import sys
from pathlib import Path

from sdcs.session import build_manifest, parse_session_file, query_manifest


def test_parse_session_file(tmp_path: Path):
    session_file = tmp_path / "2026-09-19_gpu_cache.md"
    content = """# Engineering Shift Handoff

## Date & Session
- Timestamp: 2026-09-19T14:30:00Z
- Shift Focus: GPU Cache Hardware Integration
- Verdict: PASS

## Completed Actions
- Built CUDA kernel bridge.
- Validated PyTorch tensor cache.
- Passed all Gate T boundary checks.
"""
    session_file.write_text(content, encoding="utf-8")

    rec = parse_session_file(session_file)
    assert rec["file"] == "sessions/2026-09-19_gpu_cache.md"
    assert rec["timestamp"] == "2026-09-19T14:30:00Z"
    assert "GPU Cache" in rec["topic"]
    assert rec["verdict"] == "PASS"
    assert "CUDA kernel bridge" in rec["summary"]


def test_build_and_query_manifest(tmp_path: Path):
    sessions_dir = tmp_path / "sessions"
    sessions_dir.mkdir()

    # Create 2 session logs and 1 template
    s1 = sessions_dir / "2026-09-18_scaffolding.md"
    s1.write_text(
        "# Shift\n- Timestamp: 2026-09-18\n- Topic: Project Bootstrapping\n## Completed Actions\n- Created pillars.\n",
        encoding="utf-8",
    )

    s2 = sessions_dir / "2026-09-19_evals.md"
    s2.write_text(
        "# Shift\n- Timestamp: 2026-09-19\n- Topic: Evals Corpus Hardening\n## Completed Actions\n- Added normalized hashing.\n",
        encoding="utf-8",
    )

    tmpl = sessions_dir / "template.md"
    tmpl.write_text("# Template\n", encoding="utf-8")

    manifest = build_manifest(sessions_dir)
    assert manifest.is_file()

    # Template must be excluded
    all_recs = query_manifest(sessions_dir)
    assert len(all_recs) == 2
    filenames = [r["file"] for r in all_recs]
    assert "sessions/template.md" not in filenames

    # Query filtering
    filtered = query_manifest(sessions_dir, query_str="Corpus")
    assert len(filtered) == 1
    assert "evals" in filtered[0]["file"]


def test_cli_session(tmp_path: Path):
    env = dict(os.environ)
    env["PYTHONPATH"] = str(Path(__file__).parent.parent / "src")

    sessions_dir = tmp_path / "sessions"
    sessions_dir.mkdir()
    s1 = sessions_dir / "2026-09-19_release.md"
    s1.write_text(
        "# Shift\n- Timestamp: 2026-09-19\n- Topic: Release v1.4.0\n- Verdict: READY\n## Actions\n- Tested end to end\n",
        encoding="utf-8",
    )

    # 1. sdcs session index
    cmd_index = [
        sys.executable,
        "-m",
        "sdcs.cli",
        "session",
        "index",
        "--repo-root",
        str(tmp_path),
    ]
    res_index = subprocess.run(cmd_index, capture_output=True, text=True, env=env, check=False)
    assert res_index.returncode == 0
    assert "Indexed 1 session log(s)" in res_index.stdout

    # 2. sdcs session list
    cmd_list = [
        sys.executable,
        "-m",
        "sdcs.cli",
        "session",
        "list",
        "--repo-root",
        str(tmp_path),
    ]
    res_list = subprocess.run(cmd_list, capture_output=True, text=True, env=env, check=False)
    assert res_list.returncode == 0
    assert "Release v1.4.0" in res_list.stdout
    assert "READY" in res_list.stdout

    # 3. sdcs session list --json
    cmd_json = [
        sys.executable,
        "-m",
        "sdcs.cli",
        "session",
        "list",
        "--json",
        "--repo-root",
        str(tmp_path),
    ]
    res_json = subprocess.run(cmd_json, capture_output=True, text=True, env=env, check=False)
    assert res_json.returncode == 0
    data = json.loads(res_json.stdout)
    assert len(data) == 1
    assert data[0]["verdict"] == "READY"
