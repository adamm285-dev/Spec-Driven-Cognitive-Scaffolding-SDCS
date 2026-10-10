"""Gate T on the layout and the wiring.yaml this repository actually uses.

Written by the reviewing agent, 2026-09-22 (gate audit, batch 2). Two import violations
planted in SDCS's own source -- decay.py (allowed nothing) importing sdcs.watch, and
skeleton.py importing sdcs.warehouse -- and `sdcs verify --topology` still printed
"PASS: All import edges strictly satisfy declarative boundaries". Two causes, each hiding
the other:

  1. An import resolves to a subsystem only if the dotted name mirrors the path from the
     repo root, or starts with the subsystem's name. So a src/ layout imported by package
     name never resolves, and neither does a module inside a package declared as a
     single-file subsystem (`pkg.billing` for pkg/billing.py). SDCS is both: `sdcs.watch`
     for src/sdcs/watch.py. Every target is None and is skipped; zero edges are checked,
     and zero violations is a PASS. (Flat directories and flat single files work -- they
     are the controls below.)
  2. SDCS's wiring.yaml declares `allowed_imports`; TopologyValidator reads
     `allowed_dependencies`. Every allow-list loads empty. Fix 1 alone and Gate T flags
     every legitimate import in the repo.

Gate T's own tests write `import src.core.utils` -- the path, spelled as a module -- and use
`allowed_dependencies`, so they never met either case.
"""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

from sdcs.verifier.topology import TopologyValidator

REPO = Path(__file__).resolve().parents[1]


def _audit(repo: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "sdcs.cli", "verify", "--topology", "--repo-root", str(repo)],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )


# Each layout: files to write, the walls/billing subsystem paths, and the forbidden import.
# Gate T's own tests write imports as `import src.core.utils` -- a string that mirrors the
# path from the repo root. Real code in a src/ layout imports by package name.
LAYOUTS = {
    # Caught today -- controls, so a fix cannot trade one layout for another.
    "flat_directories": (
        {
            "walls/__init__.py": "",
            "billing/__init__.py": "",
            "billing/api.py": "X = 1\n",
            "walls/crawl.py": "from billing.api import X  # forbidden\n",
        },
        "walls",
        "billing",
    ),
    "flat_files_named_as_subsystems": (
        {"billing.py": "X = 1\n", "walls.py": "from billing import X  # forbidden\n"},
        "walls.py",
        "billing.py",
    ),
    # Missed today. SDCS's own source is both of these at once.
    "src_layout_imported_by_package_name": (
        {
            "src/pkg/__init__.py": "",
            "src/pkg/walls/__init__.py": "",
            "src/pkg/billing/__init__.py": "",
            "src/pkg/billing/api.py": "X = 1\n",
            "src/pkg/walls/crawl.py": "from pkg.billing.api import X  # forbidden\n",
        },
        "src/pkg/walls",
        "src/pkg/billing",
    ),
    "file_subsystems_inside_a_package": (
        {
            "pkg/__init__.py": "",
            "pkg/billing.py": "X = 1\n",
            "pkg/walls.py": "from pkg.billing import X  # forbidden\n",
        },
        "pkg/walls.py",
        "pkg/billing.py",
    ),
    # Added pass 4 -- held out, then missed: a module imported FROM its package. The
    # extractor records the package, not the module named after `import`.
    "from_package_import_module": (
        {
            "pkg/__init__.py": "",
            "pkg/billing.py": "X = 1\n",
            "pkg/walls.py": "from pkg import billing  # forbidden\n",
        },
        "pkg/walls.py",
        "pkg/billing.py",
    ),
    "relative_from_dot_import_module": (
        {
            "pkg/__init__.py": "",
            "pkg/billing.py": "X = 1\n",
            "pkg/walls.py": "from . import billing  # forbidden\n",
        },
        "pkg/walls.py",
        "pkg/billing.py",
    ),
}


@pytest.mark.parametrize("layout", sorted(LAYOUTS))
def test_a_forbidden_import_is_caught(tmp_path: Path, layout: str):
    files, walls_path, billing_path = LAYOUTS[layout]
    for rel, text in files.items():
        (tmp_path / rel).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / rel).write_text(text, encoding="utf-8")
    (tmp_path / "wiring.yaml").write_text(
        "subsystems:\n"
        f"  walls:\n    path: {walls_path}\n    allowed_dependencies: []\n"
        f"  billing:\n    path: {billing_path}\n    allowed_dependencies: []\n",
        encoding="utf-8",
    )
    result = _audit(tmp_path)
    assert (
        result.returncode != 0
    ), f"[{layout}] walls imports billing, which it may not, and Gate T passed"


def test_sdcs_own_allow_lists_are_read():
    """cli declares twelve allowed imports; the validator must see them."""
    validator = TopologyValidator(REPO / "wiring.yaml", REPO)
    assert validator.subsystems[
        "cli"
    ].allowed_dependencies, (
        "wiring.yaml's allow-list for cli loaded empty -- the key it uses is not the key read"
    )


def test_every_module_wiring_yaml_allows_exists():
    """A boundary that names a module that does not exist is a rule about nothing."""
    data = yaml.safe_load((REPO / "wiring.yaml").read_text(encoding="utf-8"))
    named = {
        m
        for cfg in data.get("subsystems", {}).values()
        for key in ("allowed_imports", "allowed_dependencies")
        for m in cfg.get(key, []) or []
    }
    missing = sorted(m for m in named if importlib.util.find_spec(m) is None)
    assert missing == [], f"wiring.yaml allows imports of modules that do not exist: {missing}"
