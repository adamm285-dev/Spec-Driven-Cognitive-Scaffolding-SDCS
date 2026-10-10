"""SDCS Gate L: Mock Ledger Reconciliation.

Product code that stands in for real behavior (simulated API responses, seeded data,
demo-only keys or endpoints, offline stubs, fallbacks that fake success) must be
declared twice: a `MOCK(M-NNN)` comment marker where the mock lives, and an entry with
the same ID in the mock ledger (MOCKS.md). Gate L fails when the two disagree, so mocks
can't be hidden and the ledger can't drift from the code.

Test doubles are out of scope (Gate Q audits tests); test paths are not scanned.
"""

from __future__ import annotations

import ast
import os
import re
from dataclasses import dataclass, field
from pathlib import Path

LEDGER_NAME = "MOCKS.md"
LEDGER_DIRS = (".", ".agent", "docs")
FIELDS = ("Where", "What it fakes", "Why", "To make it real")

CODE_SUFFIXES = {
    ".py",
    ".js",
    ".jsx",
    ".mjs",
    ".cjs",
    ".ts",
    ".tsx",
    ".vue",
    ".svelte",
    ".go",
    ".rs",
    ".java",
    ".kt",
    ".kts",
    ".scala",
    ".swift",
    ".rb",
    ".php",
    ".cs",
    ".c",
    ".cc",
    ".cpp",
    ".h",
    ".hpp",
    ".m",
    ".dart",
    ".lua",
    ".sh",
    ".bash",
    ".sql",
}
EXCLUDED_DIRS = {
    ".git",
    "node_modules",
    "dist",
    "build",
    "out",
    "target",
    "vendor",
    "third_party",
    "__pycache__",
    ".venv",
    "venv",
    "env",
    ".tox",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    "coverage",
    "htmlcov",
    ".next",
    ".nuxt",
    "sessions",
    # Test doubles belong to Gate Q, not the product mock ledger
    "tests",
    "test",
    "__tests__",
    "spec",
    "specs",
}
TEST_FILE_RE = re.compile(r"(^test_.*|.*_test\.[^.]+$|.*\.(test|spec)\.[^.]+$)")

_COMMENT = r"(?:#|//|--|/\*|\*|<!--)"
MARKER_RE = re.compile(_COMMENT + r"\s*MOCK\((M-\d{3,})\)")
ANY_MARKER_RE = re.compile(_COMMENT + r"\s*MOCK\(([^)]*)\)")
ENTRY_RE = re.compile(r"^###\s+(M-\d{3,})\b", re.MULTILINE)
# Documentation placeholder, never a real marker
PLACEHOLDER_ID = "M-NNN"


@dataclass
class MockLedgerReport:
    ledger_path: Path | None
    entries: dict[str, list[tuple[str, str]]] = field(default_factory=dict)
    markers: dict[str, set[str]] = field(default_factory=dict)
    problems: list[str] = field(default_factory=list)


def locate_mock_ledger(repo_root: Path) -> Path | None:
    """Finds MOCKS.md (any casing) at the repo root, in .agent/ or in docs/."""
    for sub in LEDGER_DIRS:
        folder = repo_root / sub
        if not folder.is_dir():
            continue
        for item in folder.iterdir():
            if item.is_file() and item.name.lower() == LEDGER_NAME.lower():
                return item
    return None


def parse_ledger(text: str) -> tuple[dict[str, list[tuple[str, str]]], list[str]]:
    """Returns ({id: [(path, symbol), ...]}, problems)."""
    entries: dict[str, list[tuple[str, str]]] = {}
    problems: list[str] = []
    headings = list(ENTRY_RE.finditer(text))
    for i, heading in enumerate(headings):
        mid = heading.group(1)
        end = headings[i + 1].start() if i + 1 < len(headings) else len(text)
        body = text[heading.end() : end]
        if mid in entries:
            problems.append(f"{mid}: appears more than once in the ledger")
        fields: dict[str, str] = {}
        for name in FIELDS:
            match = re.search(rf"^\s*-\s*\*\*{re.escape(name)}:\*\*\s*(.+)$", body, re.MULTILINE)
            if match and match.group(1).strip():
                fields[name] = match.group(1)
            else:
                problems.append(f"{mid}: ledger entry is missing '{name}'")
        where: list[tuple[str, str]] = []
        for item in re.findall(r"`([^`]+)`", fields.get("Where", "")):
            if "::" not in item:
                problems.append(f"{mid}: 'Where' item `{item}` is not path::symbol")
                continue
            path, symbol = item.split("::", 1)
            where.append((path.strip(), symbol.strip()))
        if "Where" in fields and not where:
            problems.append(f"{mid}: 'Where' lists no path::symbol")
        entries[mid] = where
    return entries, problems


def _code_files(repo_root: Path):
    for dirpath, dirnames, filenames in os.walk(repo_root):
        dirnames[:] = [d for d in dirnames if d not in EXCLUDED_DIRS and not d.startswith(".")]
        for name in filenames:
            path = Path(dirpath) / name
            if path.suffix.lower() in CODE_SUFFIXES and not TEST_FILE_RE.match(name):
                yield path


def find_markers(repo_root: Path) -> tuple[dict[str, set[str]], list[str]]:
    """Returns ({id: {repo-relative paths}}, problems)."""
    markers: dict[str, set[str]] = {}
    problems: list[str] = []
    for path in _code_files(repo_root):
        rel = path.relative_to(repo_root).as_posix()
        try:
            lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError as exc:
            problems.append(f"{rel}: could not be read ({exc})")
            continue
        for lineno, line in enumerate(lines, 1):
            for raw in ANY_MARKER_RE.findall(line):
                if raw != PLACEHOLDER_ID and not re.fullmatch(r"M-\d{3,}", raw):
                    problems.append(
                        f"{rel}:{lineno}: malformed marker MOCK({raw}); use MOCK(M-NNN)"
                    )
            for mid in MARKER_RE.findall(line):
                markers.setdefault(mid, set()).add(rel)
    return markers, problems


def _python_symbols(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    names: set[str] = set()
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names.add(node.name)
            if isinstance(node, ast.ClassDef):
                for sub in node.body:
                    if isinstance(sub, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        names.add(f"{node.name}.{sub.name}")
        elif isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            names.update(t.id for t in targets if isinstance(t, ast.Name))
    return names


_DEFINITION_KEYWORDS = (
    r"(?:function|const|let|var|class|def|func|fn|type|interface|struct|enum|trait|val|object)"
)


def symbol_defined(path: Path, symbol: str) -> bool:
    """Python is checked exactly via the AST; other languages by declaration patterns."""
    if path.suffix.lower() == ".py":
        try:
            return symbol in _python_symbols(path)
        except SyntaxError:
            return False
    name = re.escape(symbol.split(".")[-1])
    text = path.read_text(encoding="utf-8", errors="replace")
    declared = re.search(rf"\b{_DEFINITION_KEYWORDS}\s+{name}\b", text)
    method = re.search(
        rf"^\s*(?:(?:public|private|protected|static|async|override|final)\s+)*{name}\s*\(",
        text,
        re.MULTILINE,
    )
    return bool(declared or method)


def check_mock_ledger(repo_root: Path) -> MockLedgerReport:
    """Reconciles the ledger with the markers in the code."""
    repo_root = repo_root.resolve()
    ledger = locate_mock_ledger(repo_root)
    markers, marker_problems = find_markers(repo_root)
    report = MockLedgerReport(ledger_path=ledger, markers=markers, problems=list(marker_problems))

    if ledger is None:
        for mid in sorted(markers):
            report.problems.append(
                f"{mid}: marker in {', '.join(sorted(markers[mid]))} but no {LEDGER_NAME} exists"
            )
        return report

    entries, ledger_problems = parse_ledger(ledger.read_text(encoding="utf-8"))
    report.entries = entries
    report.problems.extend(ledger_problems)

    for mid in sorted(set(markers) - set(entries)):
        report.problems.append(
            f"{mid}: marker in {', '.join(sorted(markers[mid]))} has no ledger entry"
        )

    for mid, where in sorted(entries.items()):
        marked = markers.get(mid, set())
        listed = {path for path, _ in where}
        if not marked:
            report.problems.append(f"{mid}: no MOCK({mid}) marker anywhere in the code")
        for path in sorted(listed - marked):
            if (repo_root / path).is_file():
                report.problems.append(
                    f"{mid}: lists {path}, but that file has no MOCK({mid}) marker"
                )
        for path in sorted(marked - listed):
            report.problems.append(
                f"{mid}: marker in {path}, but the entry's 'Where' doesn't list that file"
            )
        for path, symbol in where:
            target = repo_root / path
            if not target.is_file():
                report.problems.append(f"{mid}: {path} does not exist")
            elif not symbol_defined(target, symbol):
                report.problems.append(f"{mid}: {symbol} is not defined in {path}")
    return report


def run_mock_ledger_audit(repo_root: Path) -> int:
    """CLI entry for `sdcs verify --mocks`. Returns 0 when the ledger and code agree."""
    report = check_mock_ledger(repo_root)
    if report.problems:
        print(f"[SDCS::GATE_L::REJECT] Found {len(report.problems)} mock ledger problem(s):")
        for problem in report.problems:
            print(f"  - {problem}")
        return 1
    if report.ledger_path is None:
        print(f"[SDCS::GATE_L] OK: No {LEDGER_NAME} and no MOCK markers in the code.")
    else:
        rel = report.ledger_path.relative_to(repo_root.resolve()).as_posix()
        count = sum(len(v) for v in report.markers.values())
        print(
            f"[SDCS::GATE_L] OK: {rel} matches the code ({len(report.entries)} mock(s), {count} marker file reference(s))."
        )
    return 0
