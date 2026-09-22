import os
from unittest.mock import patch

from sdcs.verifier.sandbox import audit_sandbox_staged_files, run_sandbox_audit


def test_sandbox_clean_commit(tmp_path):
    wiring_file = tmp_path / "wiring.yaml"
    wiring_file.write_text(
        "sandbox:\n" "  protected_paths:\n" "    - '.env*'\n" "    - 'secrets/**'\n",
        encoding="utf-8",
    )

    with patch("sdcs.verifier.sandbox.get_staged_files", return_value=["src/main.py", "README.md"]):
        passed, violations = audit_sandbox_staged_files(tmp_path, wiring_file)
        assert passed is True
        assert len(violations) == 0


def test_sandbox_protected_path_violation(tmp_path):
    wiring_file = tmp_path / "wiring.yaml"
    wiring_file.write_text(
        "sandbox:\n" "  protected_paths:\n" "    - '.env*'\n" "    - 'credentials/**'\n",
        encoding="utf-8",
    )

    with patch("sdcs.verifier.sandbox.get_staged_files", return_value=["src/app.py", ".env.local"]):
        passed, violations = audit_sandbox_staged_files(tmp_path, wiring_file)
        assert passed is False
        assert len(violations) == 1
        assert ".env.local" in violations[0]


def test_sandbox_override_env(tmp_path):
    wiring_file = tmp_path / "wiring.yaml"
    wiring_file.write_text(
        "sandbox:\n" "  protected_paths:\n" "    - '.env*'\n",
        encoding="utf-8",
    )

    with patch.dict(os.environ, {"SDCS_ALLOW_SANDBOX_OVERRIDE": "1"}):
        with patch("sdcs.verifier.sandbox.get_staged_files", return_value=[".env"]):
            code = run_sandbox_audit(tmp_path, wiring_file)
            assert code == 0
