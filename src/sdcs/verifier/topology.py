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


class ImportExtractor(ast.NodeVisitor):
    """Extracts absolute and relative imports with source line coordinates."""

    def __init__(self, current_file: Path, repo_root: Path):
        self.current_file = current_file
        self.repo_root = repo_root
        self.imports: list[tuple[str, int]] = []

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
                base_parts = list(rel_base.parts)
                if node.module:
                    base_parts.append(node.module)
                module_name = ".".join(base_parts)
            except ValueError:
                module_name = node.module or ""
        else:
            module_name = node.module or ""

        if module_name:
            self.imports.append((module_name, node.lineno))
        self.generic_visit(node)


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
            allowed = set(cfg.get("allowed_dependencies", []))
            self.subsystems[name] = SubsystemConfig(
                name=name, path=subsys_path, allowed_dependencies=allowed
            )

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
        mod_path_relative = Path(*module_str.split("."))
        for name, cfg in self.subsystems.items():
            try:
                rel_subsys_path = cfg.path.relative_to(self.repo_root)
            except ValueError:
                rel_subsys_path = cfg.path

            if (
                mod_path_relative == rel_subsys_path
                or rel_subsys_path in mod_path_relative.parents
                or module_str.startswith(f"{name}.")
                or module_str == name
            ):
                return name
        return None

    def audit_file(self, file_path: Path) -> list[ImportViolation]:
        source_subsystem = self.resolve_subsystem_for_file(file_path)
        if not source_subsystem:
            return []

        cfg = self.subsystems[source_subsystem]
        violations: list[ImportViolation] = []

        try:
            tree = ast.parse(file_path.read_text(encoding="utf-8"), filename=str(file_path))
        except (SyntaxError, UnicodeDecodeError):
            return []

        extractor = ImportExtractor(file_path, self.repo_root)
        extractor.visit(tree)

        for module_name, lineno in extractor.imports:
            target_subsystem = self.resolve_subsystem_for_module(module_name)
            if not target_subsystem or target_subsystem == source_subsystem:
                continue
            if target_subsystem not in cfg.allowed_dependencies:
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
        for file_path in self.repo_root.rglob("*.py"):
            if any(
                part.startswith(".") or part in ("venv", ".venv", "build", "dist")
                for part in file_path.parts
            ):
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
    decisions_file = repo_root / "decisions.md"
    if not decisions_file.exists():
        # Check .agent/decisions.md fallback
        agent_decisions = repo_root / ".agent" / "decisions.md"
        if agent_decisions.exists():
            decisions_file = agent_decisions
        else:
            print(
                "[SDCS::DECISIONS] decisions.md not found. Skipping negative memory serialization."
            )
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
    target_wiring = wiring_path or (repo_root / "wiring.yaml")
    if not target_wiring.is_file():
        agent_wiring = repo_root / ".agent" / "wiring.yaml"
        if agent_wiring.is_file():
            target_wiring = agent_wiring
        else:
            print(f"[SDCS::ERROR] wiring.yaml not found at {target_wiring}")
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
