import os
from pathlib import Path

from sdcs.verifier.topology import TopologyValidator, extract_polyglot_imports


def test_extract_polyglot_imports_ts(tmp_path):
    ts_file = tmp_path / "index.ts"
    ts_file.write_text(
        "import { AuthService } from '../auth/service';\n"
        "import React from 'react';\n"
        "const logger = require('./logger');\n",
        encoding="utf-8",
    )
    imports = extract_polyglot_imports(ts_file, tmp_path)
    specs = [spec for spec, _, _ in imports]
    assert "../auth/service" in specs
    assert "react" in specs
    assert "./logger" in specs


def test_extract_polyglot_imports_kotlin(tmp_path):
    kt_file = tmp_path / "MainActivity.kt"
    kt_file.write_text(
        "package com.app.ui\n\n"
        "import com.app.core.NetworkClient\n"
        "import com.app.core.model.*\n",
        encoding="utf-8",
    )
    imports = extract_polyglot_imports(kt_file, tmp_path)
    specs = [spec for spec, _, _ in imports]
    assert "com.app.core.NetworkClient" in specs
    assert "com.app.core.model" in specs


def test_polyglot_boundary_violation(tmp_path):
    wiring_file = tmp_path / "wiring.yaml"
    wiring_file.write_text(
        "version: '1.5'\n"
        "subsystems:\n"
        "  core:\n"
        "    path: 'src/core'\n"
        "    allowed_dependencies: []\n"
        "  ui:\n"
        "    path: 'src/ui'\n"
        "    allowed_dependencies: []\n",
        encoding="utf-8",
    )

    core_dir = tmp_path / "src" / "core"
    core_dir.mkdir(parents=True)
    ui_dir = tmp_path / "src" / "ui"
    ui_dir.mkdir(parents=True)

    # UI illegally imports core in TypeScript
    ts_ui = ui_dir / "Screen.ts"
    ts_ui.write_text("import { CoreEngine } from '../core/engine';\n", encoding="utf-8")

    validator = TopologyValidator(wiring_file, tmp_path)
    violations = validator.audit_tree()
    assert len(violations) == 1
    assert violations[0].source_subsystem == "ui"
    assert violations[0].target_subsystem == "core"
