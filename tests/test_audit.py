import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT / "src"))
sys.path.insert(0, str(REPO_ROOT))

from audit_evals_corpus import (
    calculate_normalized_sha256,
    calculate_sha256,
    parse_evals_table,
    run_audit,
)


def test_calculate_sha256():
    with tempfile.NamedTemporaryFile("wb", delete=False) as f:
        f.write(b"hello world\n")
        f_path = Path(f.name)
    try:
        digest = calculate_sha256(f_path)
        assert len(digest) == 64
        # sha256 of "hello world\n"
        assert digest == "a948904f2f0f479b8f8197694b30184b0d2ed1c1cd2a1ec0fb85d299a192a447"
    finally:
        f_path.unlink()


def test_audit_clean_corpus():
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        fixture = root / "fixtures" / "sample.txt"
        fixture.parent.mkdir(parents=True)
        fixture.write_text("sample content", encoding="utf-8")
        hash_8 = calculate_sha256(fixture)[:8]

        evals_content = f"""# Empirical Standing & Ground Truth (Evals)

## 1. Golden Reference Corpus & Diversity
| Asset ID | Path / Scenario | SHA-256 (8-char) | Unique Characteristics | Target Subsystem |
| :--- | :--- | :--- | :--- | :--- |
| `TC-01` | `fixtures/sample.txt` | `{hash_8}` | Test fixture | Engine |

## 2. Baseline Empirical Scorecard
- Pass rate: 100%
"""
        (root / "evals.md").write_text(evals_content, encoding="utf-8")

        result = run_audit(root)
        assert result is True


def test_audit_detects_duplicate_hash():
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        fix1 = root / "fix1.txt"
        fix2 = root / "fix2.txt"
        fix1.write_text("identical content", encoding="utf-8")
        fix2.write_text("identical content", encoding="utf-8")
        hash_8 = calculate_sha256(fix1)[:8]

        evals_content = f"""# Empirical Standing & Ground Truth (Evals)

## 1. Golden Reference Corpus & Diversity
| Asset ID | Path / Scenario | SHA-256 (8-char) | Unique Characteristics | Target Subsystem |
| :--- | :--- | :--- | :--- | :--- |
| `TC-01` | `fix1.txt` | `{hash_8}` | Test fixture 1 | Engine |
| `TC-02` | `fix2.txt` | `{hash_8}` | Test fixture 2 | Engine |
"""
        (root / "evals.md").write_text(evals_content, encoding="utf-8")

        result = run_audit(root)
        assert result is False  # Should fail due to duplicate fixture detection


def test_audit_detects_near_duplicate_whitespace():
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        fix1 = root / "fix1.txt"
        fix2 = root / "fix2.txt"
        # fix2 has identical content but extra trailing spaces and blank lines
        fix1.write_text("important payload data\nline 2", encoding="utf-8")
        fix2.write_text("important payload data   \n\nline 2  \n", encoding="utf-8")

        hash1 = calculate_sha256(fix1)[:8]
        hash2 = calculate_sha256(fix2)[:8]
        assert hash1 != hash2  # Raw hashes differ

        evals_content = f"""# Empirical Standing & Ground Truth (Evals)

## 1. Golden Reference Corpus & Diversity
| Asset ID | Path / Scenario | SHA-256 (8-char) | Unique Characteristics | Target Subsystem |
| :--- | :--- | :--- | :--- | :--- |
| `TC-01` | `fix1.txt` | `{hash1}` | Standard fixture | Engine |
| `TC-02` | `fix2.txt` | `{hash2}` | Padded fixture | Engine |
"""
        (root / "evals.md").write_text(evals_content, encoding="utf-8")

        result = run_audit(root)
        assert result is False  # Fails due to near-duplicate detection


def test_normalization_collides_on_comments_and_whitespace(tmp_path):
    """SPEC-001 §7.4: Asserts comments, blank lines, and whitespace variance
    resolve to identical hashes to prevent trivial Phantom Corpus evasions.
    """
    # 1. Python comment & whitespace padding
    py_clean = tmp_path / "clean.py"
    py_padded = tmp_path / "padded.py"
    py_clean.write_text("def process(item):\n    return item * 2\n", encoding="utf-8")
    py_padded.write_text(
        "def process(item):   \n"
        "    # Injected padding comment\n"
        "    return item * 2   # inline comment\n\n\n",
        encoding="utf-8",
    )
    assert calculate_normalized_sha256(py_clean) == calculate_normalized_sha256(py_padded)

    # 2. C-style / JavaScript comment padding
    js_clean = tmp_path / "clean.js"
    js_padded = tmp_path / "padded.js"
    js_clean.write_text("export const add = (a, b) => a + b;\n", encoding="utf-8")
    js_padded.write_text(
        "// Header comment\n" "export const add = (a, b) => a + b;   // inline logic\n",
        encoding="utf-8",
    )
    assert calculate_normalized_sha256(js_clean) == calculate_normalized_sha256(js_padded)


def test_audit_flags_phantom_corpus_on_padded_duplicates(tmp_path):
    """Verifies run_audit halts with an error when distinct fixture paths
    resolve to identical normalized digests.
    """
    f1 = tmp_path / "fixture_a.py"
    f2 = tmp_path / "fixture_b.py"
    f1.write_text("x = 100\n", encoding="utf-8")
    f2.write_text("x = 100  # disguised duplicate\n\n", encoding="utf-8")

    shared_hash = calculate_normalized_sha256(f1)

    evals_content = f"""# Positive Ground Truth

## Golden Test Corpus
| Fixture ID | Path | SHA-256 Digest | Status |
| :--- | :--- | :--- | :--- |
| `TC-001` | `fixture_a.py` | `{shared_hash}` | active |
| `TC-002` | `fixture_b.py` | `{shared_hash}` | active |
"""
    evals_file = tmp_path / "evals.md"
    evals_file.write_text(evals_content, encoding="utf-8")

    # Audit must detect duplicate normalized digest and fail
    passed = run_audit(evals_file=evals_file, repo_root=tmp_path, update_pending=False)
    assert not passed, "Auditor failed to halt on duplicate normalized fixture digests"


def test_update_pending_replaces_hash_and_preserves_table(tmp_path):
    """Verifies that --update-pending writes computed digests into evals.md
    while keeping markdown table columns intact.
    """
    fixture = tmp_path / "test_artifact.py"
    fixture.write_text("def run():\n    return True\n", encoding="utf-8")
    expected_hash = calculate_normalized_sha256(fixture)

    evals_initial = """# Positive Ground Truth

## Golden Test Corpus
| Fixture ID | Path | SHA-256 Digest | Status |
| :--- | :--- | :--- | :--- |
| `TC-BOOT` | `test_artifact.py` | pending | active |
"""
    evals_file = tmp_path / "evals.md"
    evals_file.write_text(evals_initial, encoding="utf-8")

    # Execute audit with update_pending=True
    passed = run_audit(evals_file=evals_file, repo_root=tmp_path, update_pending=True)
    assert passed, "Audit run failed unexpectedly during pending update"

    updated_content = evals_file.read_text(encoding="utf-8")

    # 1. Assert 'pending' was replaced by computed SHA-256
    assert "pending" not in updated_content
    assert expected_hash in updated_content

    # 2. Assert table remains well-formed and parseable
    parsed = parse_evals_table(updated_content)
    assert len(parsed) == 1
    assert parsed[0].fixture_id == "TC-BOOT"
    assert parsed[0].path_str == "test_artifact.py"
    assert parsed[0].recorded_hash == expected_hash
    assert parsed[0].status == "active"


def test_recalibrate_fixture_single_and_all(tmp_path):
    """SPEC-001 v1.4.0 §7.6: Verifies recalibrate_fixture updates stale hashes
    for a specific fixture ID or all fixtures atomically.
    """
    f1 = tmp_path / "fix1.py"
    f2 = tmp_path / "fix2.py"
    f1.write_text("print('version 1')", encoding="utf-8")
    f2.write_text("print('version 2')", encoding="utf-8")

    stale_hash1 = "0000000000000000000000000000000000000000000000000000000000000000"
    stale_hash2 = "1111111111111111111111111111111111111111111111111111111111111111"

    evals_initial = f"""# Positive Ground Truth

## Golden Test Corpus
| Fixture ID | Path | SHA-256 Digest | Status |
| :--- | :--- | :--- | :--- |
| `TC-01` | `fix1.py` | `{stale_hash1}` | active |
| `TC-02` | `fix2.py` | `{stale_hash2}` | active |
"""
    evals_file = tmp_path / "evals.md"
    evals_file.write_text(evals_initial, encoding="utf-8")

    # 1. Recalibrate only TC-01
    passed = run_audit(evals_file=evals_file, repo_root=tmp_path, recalibrate="TC-01")
    assert passed is True

    updated_1 = evals_file.read_text(encoding="utf-8")
    expected_hash1 = calculate_normalized_sha256(f1)
    assert expected_hash1 in updated_1
    assert stale_hash2 in updated_1  # TC-02 still has stale hash

    # 2. Recalibrate all
    passed_all = run_audit(evals_file=evals_file, repo_root=tmp_path, recalibrate="all")
    assert passed_all is True

    updated_2 = evals_file.read_text(encoding="utf-8")
    expected_hash2 = calculate_normalized_sha256(f2)
    assert expected_hash1 in updated_2
    assert expected_hash2 in updated_2
    assert stale_hash2 not in updated_2

    # Verify audit passes cleanly now
    audit_clean = run_audit(evals_file=evals_file, repo_root=tmp_path)
    assert audit_clean is True
