"""SDCS AST Topology Auditor and Negative Memory Gating Engine (Gate T).

Enforces Pillar 2 (wiring.yaml) architectural boundaries and serializes
violations into Pillar 6 (decisions.md) inverted rejection records.
"""

import ast
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import NamedTuple

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None


class ImportViolation(NamedTuple):
    source_file: Path
    source_subsystem: str
    target_subsystem: str
    imported_module: str
    line_number: int


class SubsystemConfig(NamedTuple):
    name: str
    path: Path
    allowed_dependencies: set[str]


POLYGLOT_EXTENSIONS = {
    ".py",
    ".ts",
    ".tsx",
    ".js",
    ".jsx",
    ".kt",
    ".kts",
    ".java",
    ".go",
    ".rs",
}


class ImportExtractor(ast.NodeVisitor):
    """Extracts absolute and relative imports with source line coordinates."""

    def __init__(self, current_file: Path, repo_root: Path):
        self.current_file = current_file
        self.repo_root = repo_root
        self.imports: list[tuple[str, int]] = []

    def _is_module(self, dotted_name: str) -> bool:
        if not dotted_name:
            return False
        mod_parts = dotted_name.split(".")
        candidate_roots = [self.repo_root, self.current_file.parent]
        for src_dir in ("src", "lib"):
            cand = self.repo_root / src_dir
            if cand.is_dir():
                candidate_roots.append(cand)

        for sroot in candidate_roots:
            cand_path = sroot.joinpath(*mod_parts)
            if cand_path.is_file():
                return True
            for ext in POLYGLOT_EXTENSIONS:
                if cand_path.with_suffix(ext).is_file():
                    return True
            if cand_path.is_dir():
                if (cand_path / "__init__.py").is_file():
                    return True
                try:
                    if any(cand_path.glob("*.py")):
                        return True
                except OSError:
                    pass
        return False

    def visit_Import(self, node: ast.Import):
        for alias in node.names:
            self.imports.append((alias.name, node.lineno))
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom):
        if node.level > 0:
            current_dir = self.current_file.parent
            for _ in range(node.level - 1):
                current_dir = current_dir.parent
            try:
                rel_base = current_dir.relative_to(self.repo_root)
                base_parts = [p for p in rel_base.parts if p and p != "."]
                if node.module:
                    base_parts.extend(node.module.split("."))
                module_name = ".".join(base_parts)
            except ValueError:
                module_name = node.module or ""
        else:
            module_name = node.module or ""

        recorded: set[tuple[str, int]] = set()
        for alias in node.names:
            candidate = f"{module_name}.{alias.name}" if module_name else alias.name
            if self._is_module(candidate):
                if (candidate, node.lineno) not in recorded:
                    self.imports.append((candidate, node.lineno))
                    recorded.add((candidate, node.lineno))
            else:
                if module_name and (module_name, node.lineno) not in recorded:
                    self.imports.append((module_name, node.lineno))
                    recorded.add((module_name, node.lineno))

        self.generic_visit(node)


def extract_polyglot_imports(file_path: Path, repo_root: Path) -> list[tuple[str, int, bool]]:
    """
    Extracts imports across Python, TypeScript/JS, Kotlin/Java, Go, and Rust.
    Returns: list of (import_specifier, line_number, is_relative_path)
    """
    ext = file_path.suffix.lower()
    imports: list[tuple[str, int, bool]] = []

    try:
        content = file_path.read_text(encoding="utf-8", errors="ignore")
    except (OSError, UnicodeDecodeError):
        return []

    lines = content.splitlines()

    if ext == ".py":
        try:
            tree = ast.parse(content, filename=str(file_path))
            py_extractor = ImportExtractor(file_path, repo_root)
            py_extractor.visit(tree)
            return [(mod, line, False) for mod, line in py_extractor.imports]
        except (SyntaxError, UnicodeDecodeError):
            return []

    elif ext in (".ts", ".tsx", ".js", ".jsx"):
        ts_import_re = re.compile(r"""(?:import|export)\s+(?:.*?from\s+)?['"]([^'"]+)['"]""")
        ts_require_re = re.compile(r"""require\(\s*['"]([^'"]+)['"]\s*\)""")
        for idx, line in enumerate(lines, start=1):
            stripped = line.strip()
            if stripped.startswith(("//", "/*")):
                continue
            for m in ts_import_re.finditer(line):
                spec = m.group(1)
                is_rel = spec.startswith(".")
                imports.append((spec, idx, is_rel))
            for m in ts_require_re.finditer(line):
                spec = m.group(1)
                is_rel = spec.startswith(".")
                imports.append((spec, idx, is_rel))

    elif ext in (".kt", ".kts", ".java"):
        kt_re = re.compile(r"^\s*import\s+([a-zA-Z0-9_.]+(?:\.\*)?)")
        for idx, line in enumerate(lines, start=1):
            m = kt_re.match(line)
            if m:
                spec = m.group(1).rstrip(".*")
                imports.append((spec, idx, False))

    elif ext == ".go":
        in_block = False
        go_single_re = re.compile(r"""^\s*import\s+['"]([^'"]+)['"]""")
        go_block_re = re.compile(r"""^\s*(?:[a-zA-Z0-9_]+\s+)?['"]([^'"]+)['"]""")
        for idx, line in enumerate(lines, start=1):
            trimmed = line.strip()
            if trimmed.startswith("//"):
                continue
            if trimmed.startswith("import ("):
                in_block = True
                continue
            if in_block:
                if trimmed == ")":
                    in_block = False
                    continue
                m = go_block_re.match(line)
                if m:
                    imports.append((m.group(1), idx, False))
            else:
                m = go_single_re.match(line)
                if m:
                    imports.append((m.group(1), idx, False))

    elif ext == ".rs":
        rs_use_re = re.compile(r"^\s*use\s+(?:crate::)?([a-zA-Z0-9_:]+)")
        rs_mod_re = re.compile(r"^\s*mod\s+([a-zA-Z0-9_]+)\s*;")
        for idx, line in enumerate(lines, start=1):
            trimmed = line.strip()
            if trimmed.startswith("//"):
                continue
            m = rs_use_re.match(line)
            if m:
                spec = m.group(1).split("::")[0]
                imports.append((spec, idx, False))
            m2 = rs_mod_re.match(line)
            if m2:
                imports.append((m2.group(1), idx, False))

    return imports


class TopologyValidator:
    """Audits codebase abstract syntax trees against declarative contracts."""

    def __init__(self, wiring_path: Path, repo_root: Path):
        self.repo_root = repo_root.resolve()
        self.subsystems: dict[str, SubsystemConfig] = {}
        self._load_wiring(wiring_path)

    def _load_wiring(self, wiring_path: Path):
        if yaml is None:
            raise ImportError(
                "PyYAML is required for SDCS topology validation. "
                "Install it with: pip install 'sdcs[dev]' or pip install pyyaml"
            )
        with open(wiring_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        raw_subsystems = data.get("subsystems", {})
        for name, cfg in raw_subsystems.items():
            subsys_path = (self.repo_root / cfg["path"]).resolve()
            allowed = set(cfg.get("allowed_dependencies") or []) | set(
                cfg.get("allowed_imports") or []
            )
            self.subsystems[name] = SubsystemConfig(
                name=name, path=subsys_path, allowed_dependencies=allowed
            )

    def _get_subsystem_prefixes(self, name: str, cfg: SubsystemConfig) -> list[str]:
        prefixes = [name]
        try:
            rel = cfg.path.relative_to(self.repo_root)
        except ValueError:
            rel = cfg.path

        if cfg.path.is_file() or rel.suffix in POLYGLOT_EXTENSIONS:
            rel_clean = rel.with_suffix("")
        else:
            rel_clean = rel

        dotted_full = ".".join(rel_clean.parts)
        if dotted_full:
            prefixes.append(dotted_full)

        if rel_clean.parts and rel_clean.parts[0] in ("src", "lib"):
            stripped = ".".join(rel_clean.parts[1:])
            if stripped:
                prefixes.append(stripped)

        return sorted(set(prefixes), key=len, reverse=True)

    def resolve_subsystem_for_file(self, file_path: Path) -> str | None:
        resolved = file_path.resolve()
        matched_name, matched_len = None, -1
        for name, cfg in self.subsystems.items():
            try:
                resolved.relative_to(cfg.path)
                path_len = len(cfg.path.parts)
                if path_len > matched_len:
                    matched_len = path_len
                    matched_name = name
            except ValueError:
                continue
        return matched_name

    def resolve_subsystem_for_module(self, module_str: str) -> str | None:
        # 1. Disk resolution across candidate source roots
        mod_parts = module_str.split(".")
        candidate_roots = [self.repo_root]
        for src_dir in ("src", "lib"):
            cand = self.repo_root / src_dir
            if cand.is_dir():
                candidate_roots.append(cand)

        for sroot in candidate_roots:
            cand_path = sroot.joinpath(*mod_parts)
            for ext in ("", ".py", ".ts", ".js", ".go", ".rs", ".java", ".kt"):
                p = cand_path.with_suffix(ext) if ext else cand_path
                if p.exists():
                    sub = self.resolve_subsystem_for_file(p)
                    if sub:
                        return sub
            if len(mod_parts) > 1:
                parent_path = sroot.joinpath(*mod_parts[:-1])
                for ext in (".py", ".ts", ".js", ".go", ".rs", ".java", ".kt"):
                    p = parent_path.with_suffix(ext)
                    if p.is_file():
                        sub = self.resolve_subsystem_for_file(p)
                        if sub:
                            return sub

        # 2. Candidate prefix matching against declared subsystem paths
        best_match, best_len = None, -1
        for name, cfg in self.subsystems.items():
            prefixes = self._get_subsystem_prefixes(name, cfg)
            for prefix in prefixes:
                if module_str == prefix or module_str.startswith(f"{prefix}."):
                    if len(prefix) > best_len:
                        best_len = len(prefix)
                        best_match = name

        return best_match

    def audit_file(self, file_path: Path) -> list[ImportViolation]:
        source_subsystem = self.resolve_subsystem_for_file(file_path)
        if not source_subsystem:
            return []

        cfg = self.subsystems[source_subsystem]
        violations: list[ImportViolation] = []

        raw_imports = extract_polyglot_imports(file_path, self.repo_root)

        for module_name, lineno, is_relative in raw_imports:
            if is_relative:
                # Relative file reference (e.g. '../other_subsystem/module')
                resolved_target_file = (file_path.parent / module_name).resolve()
                target_subsystem = self.resolve_subsystem_for_file(resolved_target_file)
            else:
                target_subsystem = self.resolve_subsystem_for_module(module_name)

            if not target_subsystem or target_subsystem == source_subsystem:
                continue

            # Verify against allowlist (matching subsystem name or imported module identifier)
            is_allowed = (
                target_subsystem in cfg.allowed_dependencies
                or module_name in cfg.allowed_dependencies
                or any(
                    module_name == a
                    or module_name.startswith(f"{a}.")
                    or self.resolve_subsystem_for_module(a) == target_subsystem
                    for a in cfg.allowed_dependencies
                )
            )

            if not is_allowed:
                violations.append(
                    ImportViolation(
                        source_file=file_path.relative_to(self.repo_root),
                        source_subsystem=source_subsystem,
                        target_subsystem=target_subsystem,
                        imported_module=module_name,
                        line_number=lineno,
                    )
                )
        return violations

    def audit_tree(self) -> list[ImportViolation]:
        violations: list[ImportViolation] = []
        ignored_dirs = {
            "venv",
            ".venv",
            "build",
            "dist",
            "node_modules",
            ".gradle",
            "target",
            "__pycache__",
            ".git",
        }
        for file_path in self.repo_root.rglob("*"):
            if not file_path.is_file():
                continue
            if file_path.suffix.lower() not in POLYGLOT_EXTENSIONS:
                continue
            if any(part.startswith(".") or part in ignored_dirs for part in file_path.parts):
                continue
            violations.extend(self.audit_file(file_path))
        return violations


# ---------------------------------------------------------------------------
# Negative Memory Synchronization (Pillar 6 Serializer)
# ---------------------------------------------------------------------------


def is_violation_duplicate(content: str, violation: ImportViolation) -> bool:
    """Checks whether the violation signature has already been recorded in decisions.md."""
    src_posix = re.escape(violation.source_file.as_posix())
    src_raw = re.escape(str(violation.source_file))
    mod_str = re.escape(violation.imported_module)
    pattern = rf"(?:Target|Violation).*?(?:{src_posix}|{src_raw}).*?{mod_str}"
    return bool(re.search(pattern, content, flags=re.DOTALL))


def get_next_rejection_id(content: str) -> str:
    """Extracts the highest existing monotonic ID across ## and ### headers."""
    existing_ids = [int(m) for m in re.findall(r"#+\s*REJ-(\d+)", content)]
    next_id = (max(existing_ids) + 1) if existing_ids else 1
    return f"REJ-{next_id:03d}"


def format_rejection_entry(
    violation: ImportViolation,
    validator: TopologyValidator,
    rejection_id: str,
) -> str:
    """Formats an AST violation into a strict Inverted ADR schema."""
    allowed = sorted(validator.subsystems[violation.source_subsystem].allowed_dependencies)
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    src_display = violation.source_file.as_posix()

    return f"""## {rejection_id}: Prohibited Import Boundary (`{violation.source_subsystem}` -> `{violation.target_subsystem}`)
- **Date**: {timestamp}
- **Target**: `{src_display}:{violation.line_number}`
- **Status**: REJECTED (AST Topology Invariant Gate T)

**Claim**:
Subsystem `{violation.source_subsystem}` can import `{violation.imported_module}` directly from `{violation.target_subsystem}`.

**Measurement**:
- **Tool**: `sdcs verify --topology` (AST Static Analysis)
- **Violation**: `{src_display}:{violation.line_number}` imports prohibited module `{violation.imported_module}`.
- **Declared Contract**: Allowed dependencies for `{violation.source_subsystem}`: {allowed}.
- **Result**: Automated Gate T pre-commit rejection.

**Reopen Condition**:
1. Decouple via dependency inversion (extract interface/protocol into an allowed layer).
2. Or request human architectural approval to mutate `wiring.yaml` under `{violation.source_subsystem}.allowed_dependencies` via `SDCS_ALLOW_INVARIANT_MUTATION=1`.
"""


def sync_violations_to_decisions(
    violations: list[ImportViolation],
    validator: TopologyValidator,
    repo_root: Path,
) -> int:
    """Persists unique violations to decisions.md without duplicating entries."""
    decisions_file = None
    for c in [
        repo_root / "decisions.md",
        repo_root / ".agent" / "decisions.md",
        repo_root / "docs" / "decisions.md",
        repo_root / "docs" / "map" / "decisions.md",
        repo_root / "DECISIONS.md",
        repo_root / ".agent" / "DECISIONS.md",
        repo_root / "docs" / "DECISIONS.md",
        repo_root / "docs" / "map" / "DECISIONS.md",
    ]:
        if c.is_file():
            decisions_file = c
            break

    if not decisions_file:
        print("[SDCS::DECISIONS] decisions.md not found. Skipping negative memory serialization.")
        return 0

    content = decisions_file.read_text(encoding="utf-8")
    appended_count = 0
    new_entries: list[str] = []

    for v in violations:
        if is_violation_duplicate(content + "\n".join(new_entries), v):
            print(
                f"[SDCS::DECISIONS] Duplicate detected: {v.source_file} -> {v.imported_module}. Skipping append."
            )
            continue

        rej_id = get_next_rejection_id(content + "\n".join(new_entries))
        entry = format_rejection_entry(v, validator, rej_id)
        new_entries.append(entry)
        appended_count += 1

    if new_entries:
        with open(decisions_file, "a", encoding="utf-8") as f:
            f.write("\n\n" + "\n\n".join(new_entries) + "\n")
        print(
            f"[SDCS::DECISIONS] Appended {appended_count} new rejection signature(s) to decisions.md."
        )

    return appended_count


def run_topology_audit(
    repo_root: Path,
    wiring_path: Path | None = None,
    append_rejections: bool = False,
) -> int:
    """CLI orchestrator for Gate T boundary auditing."""
    target_wiring = wiring_path
    if not target_wiring or not Path(target_wiring).is_file():
        target_wiring = None
        for c in [
            repo_root / "wiring.yaml",
            repo_root / ".agent" / "wiring.yaml",
            repo_root / "docs" / "wiring.yaml",
            repo_root / "docs" / "map" / "wiring.yaml",
            repo_root / "wiring.yml",
            repo_root / ".agent" / "wiring.yml",
            repo_root / "docs" / "wiring.yml",
            repo_root / "docs" / "map" / "wiring.yml",
        ]:
            if c.is_file():
                target_wiring = c
                break
        if not target_wiring:
            print(
                f"[SDCS::ERROR] wiring.yaml not found at {wiring_path or (repo_root / 'wiring.yaml')}"
            )
            return 1

    validator = TopologyValidator(target_wiring, repo_root)
    violations = validator.audit_tree()

    print("[SDCS::VERIFY] Running AST Topology Audit against wiring.yaml...")
    if not violations:
        print("[SDCS::VERIFY] PASS: All import edges strictly satisfy declarative boundaries.\n")
        return 0

    print(f"\n[SDCS::FAIL] Detected {len(violations)} architectural boundary violation(s):\n")
    for v in violations:
        print(f"  • {v.source_file}:{v.line_number}")
        print(
            f"    Violation: '{v.source_subsystem}' imports prohibited module '{v.imported_module}' (owned by '{v.target_subsystem}')"
        )
        print(
            f"    Permitted targets: {list(validator.subsystems[v.source_subsystem].allowed_dependencies)}\n"
        )

    if append_rejections:
        sync_violations_to_decisions(violations, validator, repo_root)

    return 1
