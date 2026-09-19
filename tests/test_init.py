import sys
import tempfile
from pathlib import Path

# Ensure src is in sys.path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from sdcs.init import init_scaffold


def test_init_scaffold_root():
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        init_scaffold(target_dir=root)

        expected_files = [
            "wiring.yaml",
            "spine.md",
            "roadmap.md",
            "state.md",
            "app_map.md",
            "decisions.md",
            "evals.md",
            "AGENTS.md",
            "sessions/template.md",
            "prompts/grillme.md",
        ]
        for rel_path in expected_files:
            assert (root / rel_path).is_file(), f"Missing expected file: {rel_path}"

        # Verify content markers
        wiring = (root / "wiring.yaml").read_text(encoding="utf-8")
        assert 'version: "1.2"' in wiring

        spine = (root / "spine.md").read_text(encoding="utf-8")
        assert "Constitutional Invariants" in spine

        roadmap = (root / "roadmap.md").read_text(encoding="utf-8")
        assert "[INTENT]" in roadmap
        assert "[MEASURED]" in roadmap

        decisions = (root / "decisions.md").read_text(encoding="utf-8")
        assert "REJ-001" in decisions
        assert "The Claim" in decisions

        evals = (root / "evals.md").read_text(encoding="utf-8")
        assert "Golden Reference Corpus" in evals

        grillme = (root / "prompts" / "grillme.md").read_text(encoding="utf-8")
        assert "/grillme" in grillme
        assert "[INTENT]" in grillme


def test_init_scaffold_agent_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        init_scaffold(target_dir=root, use_agent_dir=True)

        expected_agent_files = [
            ".agent/wiring.yaml",
            ".agent/spine.md",
            ".agent/roadmap.md",
            ".agent/state.md",
            ".agent/app_map.md",
            ".agent/decisions.md",
            ".agent/evals.md",
            ".agent/sessions/template.md",
            ".agent/prompts/grillme.md",
        ]
        for rel_path in expected_agent_files:
            assert (root / rel_path).is_file(), f"Missing expected file: {rel_path}"

        # AGENTS.md remains in repo root
        assert (root / "AGENTS.md").is_file()


def test_init_scaffold_hierarchical():
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        # Create a dummy subpackage
        pkg = root / "packages" / "auth"
        pkg.mkdir(parents=True)
        (pkg / "__init__.py").write_text("# auth pkg", encoding="utf-8")
        (pkg / "service.py").write_text("class AuthService: pass", encoding="utf-8")

        init_scaffold(target_dir=root, hierarchical=True)

        assert (root / "app_map.md").is_file()
        assert (pkg / "app_map.md").is_file()

        root_map = (root / "app_map.md").read_text(encoding="utf-8")
        assert "Hierarchical Master Index" in root_map
        assert "packages/auth" in root_map

        pkg_map = (pkg / "app_map.md").read_text(encoding="utf-8")
        assert "Cartography: `packages/auth/`" in pkg_map
        assert "service.py" in pkg_map
