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
from collections.abc import Sequence
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
    # Operational and benchmark scripts are not shipped product code
    "scripts",
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


def _find_markers_with_lines(
    repo_root: Path,
) -> tuple[dict[str, set[str]], dict[str, set[int]], list[str]]:
    """Returns ({id: {repo-relative paths}}, {rel_path: {marker_lines}}, problems)."""
    markers: dict[str, set[str]] = {}
    marker_lines: dict[str, set[int]] = {}
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
                marker_lines.setdefault(rel, set()).add(lineno)
    return markers, marker_lines, problems


def find_markers(repo_root: Path) -> tuple[dict[str, set[str]], list[str]]:
    """Returns ({id: {repo-relative paths}}, problems)."""
    markers, _, problems = _find_markers_with_lines(repo_root)
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
                    elif isinstance(sub, (ast.Assign, ast.AnnAssign)):
                        sub_targets = sub.targets if isinstance(sub, ast.Assign) else [sub.target]
                        for t in sub_targets:
                            if isinstance(t, ast.Name):
                                names.add(f"{node.name}.{t.id}")
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


_META_MOCK_TERMS = (
    "ledger",
    "marker",
    "audit",
    "verifier",
    "verify",
    "locate_mock",
    "check_mock",
    "find_mock",
    "parse_mock",
    "mock_id",
    "mock_call",
    "mock_assertion",
    "mock_patch",
    "mock_abuse",
    "simulate_and_validate",
    "anti_mock",
    "hollow",
)

_FAKE_FALLBACK_IDENT_RE = re.compile(
    r"(?i)^_?(?:mock|simulat(?:e|ed)|fake|dummy|canned|stub(?:bed)?)(?:_[a-z0-9_]+)?$"
)
_FAKE_SUCCESS_COMMENT_RE = re.compile(
    r"(?i)#.*\b(?:fall\s*back\s+to\s+(?:simulat\w*|mock\w*|fake\w*|stub\w*|canned\w*)"
    r"|(?:simulat\w*|mock\w*|fake\w*|canned\w*)\s+fallback"
    r"|return\s+(?:simulat\w*|mock\w*|fake\w*|canned\w*))"
)
_MOCK_DEF_RE = re.compile(
    r"^(?:_?(?:mock|fake|dummy|canned|simulated|stubbed)_[a-zA-Z0-9_]+"
    r"|(?:Mock|Fake|Dummy|Canned|Simulated)[A-Z][a-zA-Z0-9_]*)$"
)
_MOCK_VAR_RE = re.compile(
    r"^_?(?:mock_mode|use_mock|fake_mode|simulate_mode"
    r"|(?:simulated|mock|fake|dummy|canned)_(?:kv_cache|cache|delay|latency|response|data"
    r"|result|completion|stream|chunks|client|db|store|tokens|status|output|payload))$",
    re.IGNORECASE,
)
_MOCK_MODE_PARAMS = {"mock_mode", "use_mock", "fake_mode", "simulate_mode"}
_MOCK_KWARGS = {"mock_mode", "use_mock", "fake_mode", "simulate_mode", "simulate", "fake"}
_SIMULATED_SLEEP_DOC_RE = re.compile(
    r"(?i)\b(?:simulat(?:e|es|ed|ing)\b[^\n]*\b(?:delay|latency|ttft|tool|execution"
    r"|i/o|rpc|wait|network|gemm|kernel|memory|cluster|profiler|telemetry)"
    r"|quick\s+fallback\s+for\s+testing)"
)
_UNDECLARED_MOCK_COMMENT_RE = re.compile(
    r"(?i)^\s*#\s*(?:seed(?:ed)?\s+baseline\b|pre-?seed(?:ed)?\s+"
    r"|simulated\s+(?:radix\s+cache|ttft\s+delay|sse\s+streaming|kv[- ]cache)"
    r"|in-memory\s+mock\s+cache\b"
    r"|quick\s+fallback\s+for\s+testing\b)"
)
_NON_PY_CATCH_RE = re.compile(r"\bcatch\s*(?:\([^)]*\))?\s*\{([^{}]*)\}", re.MULTILINE)
_NON_PY_FAKE_RETURN_RE = re.compile(
    r"\breturn\s+(?:await\s+)?(?:this\.)?(_?(?:mock|simulat(?:e|ed)|fake|dummy|canned)_[a-zA-Z0-9_]+)\s*\("
)
_NON_PY_MOCK_DEF_RE = re.compile(
    r"\b(?:function|func|fn|def)\s+(_?(?:mock|fake|dummy|canned|simulated|stubbed)_[a-zA-Z0-9_]+)\s*\("
)
_BASELINE_RETURN_COMMENT_RE = re.compile(r"(?i)#.*\b(?:benchmark|hardware)\s+baseline\b")
_CREDENTIAL_KEY_RE = re.compile(r"(?i)(?:API_KEY|SECRET_KEY|ACCESS_TOKEN|AUTH_TOKEN)$")
_PLACEHOLDER_TOKEN_RE = re.compile(r"(?i)(?:token|key|mock|demo|placeholder|fake|dummy|proxy)")
_MOCK_ID_LITERAL_RE = re.compile(
    r"\b(?:chatcmpl|call|ch|usr|req)[-_](?:mock|fake|dummy|test)[-_][a-zA-Z0-9_{}]+"
)
_CHART_DATASET_RE = re.compile(
    r"new\s+Chart\s*\([\s\S]*?datasets\s*:\s*\[[\s\S]*?data\s*:\s*\[\s*\d+(?:\.\d+)?\s*,\s*\d+(?:\.\d+)?\s*,\s*\d+(?:\.\d+)?"
)


def _is_meta_mock_identifier(name: str) -> bool:
    low = name.lower()
    return any(term in low for term in _META_MOCK_TERMS)


def _iter_non_nested_nodes(root_nodes: Sequence[ast.AST]):
    """Yields AST nodes within root_nodes without crossing into nested function/class defs."""
    stack: list[ast.AST] = list(reversed(root_nodes))
    while stack:
        node = stack.pop()
        yield node
        for child in reversed(list(ast.iter_child_nodes(node))):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                continue
            stack.append(child)


def _check_python_fake_success_handlers(
    rel: str,
    tree: ast.Module,
    lines: list[str],
) -> list[str]:
    """Enforces REQ-GATE-L-06 (No Fake Success): rejects except blocks returning mock/fake success."""
    problems: list[str] = []

    def _scan_scope(body: list[ast.stmt], symbol: str) -> None:
        for node in ast.walk(ast.Module(body=body, type_ignores=[])):
            if not isinstance(node, ast.Try):
                continue
            for handler in node.handlers:
                if any(isinstance(stmt, ast.Raise) for stmt in handler.body):
                    continue
                returns = [
                    n
                    for n in _iter_non_nested_nodes(handler.body)
                    if isinstance(n, (ast.Return, ast.Yield))
                ]
                if not returns:
                    continue
                reported = False
                for ret in returns:
                    val = getattr(ret, "value", None)
                    if val is None:
                        continue
                    for sub in ast.walk(val):
                        ident = None
                        if isinstance(sub, ast.Name):
                            ident = sub.id
                        elif isinstance(sub, ast.Attribute):
                            ident = sub.attr
                        if (
                            ident
                            and _FAKE_FALLBACK_IDENT_RE.match(ident)
                            and not _is_meta_mock_identifier(ident)
                        ):
                            problems.append(
                                f"{rel}:{ret.lineno}: REQ-GATE-L-06 (No Fake Success): "
                                f"except handler in '{symbol}' returns mock/simulated fallback '{ident}' on error"
                            )
                            reported = True
                            break
                    if reported:
                        break
                    if isinstance(val, ast.Dict):
                        for k_node, v_node in zip(val.keys, val.values):
                            if (
                                isinstance(k_node, ast.Constant)
                                and isinstance(k_node.value, str)
                                and isinstance(v_node, ast.Constant)
                            ):
                                k_str = k_node.value.lower()
                                v_val = v_node.value
                                if k_str in ("status", "state") and isinstance(v_val, str):
                                    if v_val.lower() in {
                                        "ok",
                                        "success",
                                        "succeeded",
                                        "healthy",
                                        "online",
                                        "authenticated",
                                        "verified",
                                        "hit",
                                    }:
                                        problems.append(
                                            f"{rel}:{ret.lineno}: REQ-GATE-L-06 (No Fake Success): "
                                            f"except handler in '{symbol}' returns fake success status "
                                            f"({k_node.value}={v_val!r}) on error"
                                        )
                                        reported = True
                                        break
                                elif k_str == "is_simulated" and v_val is True:
                                    problems.append(
                                        f"{rel}:{ret.lineno}: REQ-GATE-L-06 (No Fake Success): "
                                        f"except handler in '{symbol}' returns simulated payload on error"
                                    )
                                    reported = True
                                    break
                    if reported:
                        break
                if not reported:
                    h_start = max(1, handler.lineno)
                    h_end = getattr(handler, "end_lineno", h_start) or h_start
                    for ln in range(h_start, min(len(lines), h_end) + 1):
                        if _FAKE_SUCCESS_COMMENT_RE.search(lines[ln - 1]):
                            problems.append(
                                f"{rel}:{ln}: REQ-GATE-L-06 (No Fake Success): "
                                f"except handler in '{symbol}' falls back to simulated/mock result on error"
                            )
                            break

    for top in tree.body:
        if isinstance(top, (ast.FunctionDef, ast.AsyncFunctionDef)):
            _scan_scope(top.body, top.name)
        elif isinstance(top, ast.ClassDef):
            for sub in top.body:
                if isinstance(sub, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    _scan_scope(sub.body, f"{top.name}.{sub.name}")
    return problems


def _unit_undeclared_reason(
    unit_node: ast.AST,
    bare_name: str,
    span_start: int,
    span_end: int,
    lines: list[str],
    walk_nested: bool = True,
) -> tuple[int, str] | None:
    """Returns (lineno, reason) if an unmarked AST unit contains a product-code mock."""
    if isinstance(unit_node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
        if _MOCK_DEF_RE.match(bare_name) and not _is_meta_mock_identifier(bare_name):
            return (unit_node.lineno, f"mock/simulated definition '{bare_name}'")

    if isinstance(unit_node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        all_args = list(unit_node.args.args) + list(unit_node.args.kwonlyargs)
        for arg in all_args:
            if arg.arg in _MOCK_MODE_PARAMS:
                return (unit_node.lineno, f"mock-mode parameter '{arg.arg}'")

    docstring = (
        ast.get_docstring(unit_node)
        if isinstance(unit_node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
        else None
    ) or ""

    nodes = list(ast.walk(unit_node)) if walk_nested else list(_iter_non_nested_nodes([unit_node]))

    for node in nodes:
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            for t in targets:
                t_name = (
                    t.id
                    if isinstance(t, ast.Name)
                    else (t.attr if isinstance(t, ast.Attribute) else None)
                )
                if t_name and _MOCK_VAR_RE.match(t_name) and not _is_meta_mock_identifier(t_name):
                    return (node.lineno, f"mock/simulated state '{t_name}'")

        elif isinstance(node, ast.Call):
            for kw in node.keywords:
                if (
                    kw.arg in _MOCK_KWARGS
                    and isinstance(kw.value, ast.Constant)
                    and kw.value.value is True
                ):
                    return (node.lineno, f"mock activation '{kw.arg}=True'")

            func_name = ""
            if isinstance(node.func, ast.Attribute):
                func_name = node.func.attr
            elif isinstance(node.func, ast.Name):
                func_name = node.func.id

            if func_name in ("get", "getenv") and len(node.args) >= 2:
                arg0, arg1 = node.args[0], node.args[1]
                if (
                    isinstance(arg0, ast.Constant)
                    and isinstance(arg0.value, str)
                    and isinstance(arg1, ast.Constant)
                    and isinstance(arg1.value, str)
                    and _CREDENTIAL_KEY_RE.search(arg0.value)
                    and _PLACEHOLDER_TOKEN_RE.search(arg1.value)
                ):
                    return (
                        node.lineno,
                        f"placeholder credential fallback '{arg1.value}' for '{arg0.value}'",
                    )

            if func_name == "sleep" and node.args:
                arg0 = node.args[0]
                if isinstance(arg0, ast.Name) and re.search(
                    r"(?i)(?:simulat|mock|fake|dummy)", arg0.id
                ):
                    return (node.lineno, f"simulated delay 'sleep({arg0.id})'")
                win_start = max(span_start, node.lineno - 6)
                window_text = "\n".join(lines[win_start - 1 : node.lineno])
                if _SIMULATED_SLEEP_DOC_RE.search(window_text) or _SIMULATED_SLEEP_DOC_RE.search(
                    docstring
                ):
                    return (node.lineno, "simulated latency/I/O delay via sleep()")

        elif isinstance(node, ast.Dict):
            for k_node, v_node in zip(node.keys, node.values):
                if isinstance(k_node, ast.Constant) and isinstance(k_node.value, str):
                    if (
                        k_node.value == "is_simulated"
                        and isinstance(v_node, ast.Constant)
                        and v_node.value is True
                    ):
                        return (node.lineno, "simulated payload flag 'is_simulated: True'")
                    if (
                        k_node.value == "created"
                        and isinstance(v_node, ast.Constant)
                        and v_node.value == 1700000000
                    ):
                        return (node.lineno, "hardcoded stub timestamp 'created: 1700000000'")
                if isinstance(v_node, ast.Constant) and isinstance(v_node.value, str):
                    if _MOCK_ID_LITERAL_RE.search(v_node.value):
                        return (node.lineno, f"hardcoded mock identifier '{v_node.value}'")

        elif isinstance(node, ast.Constant) and isinstance(node.value, str):
            if _CHART_DATASET_RE.search(node.value) and ".update(" not in node.value:
                return (node.lineno, "hardcoded static Chart.js dataset array")

    c_start = max(1, span_start - 2)
    c_end = min(len(lines), span_end)
    for ln in range(c_start, c_end + 1):
        line = lines[ln - 1]
        if _UNDECLARED_MOCK_COMMENT_RE.search(line):
            return (ln, f"undeclared simulation/seed comment '{line.strip()}'")
        if _BASELINE_RETURN_COMMENT_RE.search(line) and re.search(
            r"\breturn\s+[1-9]\d*(?:\.\d+)?|\breturn\s+0\.\d*[1-9]", line
        ):
            return (ln, f"hardcoded baseline fallback return '{line.strip()}'")

    return None


def _scan_undeclared_and_fake_success(
    repo_root: Path,
    entries: dict[str, list[tuple[str, str]]],
    markers: dict[str, set[str]],
    marker_lines_by_file: dict[str, set[int]],
) -> list[str]:
    """Scans product code for REQ-GATE-L-06 fake-success fallbacks and REQ-GATE-L-01 undeclared mocks."""
    problems: list[str] = []

    for path in _code_files(repo_root):
        rel = path.relative_to(repo_root).as_posix()
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        file_marker_lines = marker_lines_by_file.get(rel, set())
        marked_ids_in_file = {mid for mid, paths in markers.items() if rel in paths}
        declared_symbols: set[str] = set()
        for mid in marked_ids_in_file:
            for w_path, w_sym in entries.get(mid, []):
                if w_path == rel:
                    declared_symbols.add(w_sym)

        if path.suffix.lower() != ".py":
            for m in _NON_PY_CATCH_RE.finditer(text):
                catch_body = m.group(1)
                ret_m = _NON_PY_FAKE_RETURN_RE.search(catch_body)
                if ret_m:
                    lineno = text[: m.start()].count("\n") + 1
                    problems.append(
                        f"{rel}:{lineno}: REQ-GATE-L-06 (No Fake Success): "
                        f"catch block returns mock/simulated fallback '{ret_m.group(1)}' on error"
                    )
            for m in _NON_PY_MOCK_DEF_RE.finditer(text):
                fn_name = m.group(1)
                if _is_meta_mock_identifier(fn_name) or fn_name in declared_symbols:
                    continue
                lineno = text[: m.start()].count("\n") + 1
                if not any((lineno - 6) <= ml <= (lineno + 20) for ml in file_marker_lines):
                    problems.append(
                        f"{rel}:{lineno}: undeclared mock in '{fn_name}' "
                        f"(mock/simulated definition '{fn_name}'); "
                        f"mark with MOCK(M-NNN) and record in {LEDGER_NAME}"
                    )
            continue

        try:
            tree = ast.parse(text)
        except SyntaxError:
            continue

        lines = text.splitlines()

        # 1. REQ-GATE-L-06 (No Fake Success): always enforced, even when declared as a mock
        problems.extend(_check_python_fake_success_handlers(rel, tree, lines))

        # 2. REQ-GATE-L-01 (Declared at the Source): detect unmarked product-code mocks
        def _is_covered(
            symbol: str,
            span_start: int,
            span_end: int,
            class_name: str | None = None,
            class_start: int | None = None,
            is_method: bool = False,
        ) -> bool:
            if symbol in declared_symbols:
                return True
            if class_name and class_name in declared_symbols:
                return True
            lead = 2 if is_method else 6
            for m_line in file_marker_lines:
                if (span_start - lead) <= m_line <= span_end:
                    return True
                if class_start is not None and (class_start - 3) <= m_line <= class_start:
                    return True
            return False

        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                s_start = node.lineno
                s_end = getattr(node, "end_lineno", s_start) or s_start
                if _is_covered(node.name, s_start, s_end):
                    continue
                found = _unit_undeclared_reason(node, node.name, s_start, s_end, lines, True)
                if found:
                    lineno, reason = found
                    problems.append(
                        f"{rel}:{lineno}: undeclared mock in '{node.name}' ({reason}); "
                        f"mark with # MOCK(M-NNN) and record in {LEDGER_NAME}"
                    )

            elif isinstance(node, ast.ClassDef):
                c_start = node.lineno
                c_end = getattr(node, "end_lineno", c_start) or c_start
                methods = [
                    sub
                    for sub in node.body
                    if isinstance(sub, (ast.FunctionDef, ast.AsyncFunctionDef))
                ]
                first_method_line = methods[0].lineno if methods else c_end

                header_end = max(c_start, first_method_line - 2) if methods else c_end
                if not _is_covered(node.name, c_start, header_end, node.name, c_start, False):
                    found = _unit_undeclared_reason(
                        node, node.name, c_start, header_end, lines, False
                    )
                    if found:
                        lineno, reason = found
                        problems.append(
                            f"{rel}:{lineno}: undeclared mock in '{node.name}' ({reason}); "
                            f"mark with # MOCK(M-NNN) and record in {LEDGER_NAME}"
                        )

                for sub in methods:
                    m_sym = f"{node.name}.{sub.name}"
                    m_start = sub.lineno
                    m_end = getattr(sub, "end_lineno", m_start) or m_start
                    if _is_covered(m_sym, m_start, m_end, node.name, c_start, True):
                        continue
                    found = _unit_undeclared_reason(sub, sub.name, m_start, m_end, lines, True)
                    if found:
                        lineno, reason = found
                        problems.append(
                            f"{rel}:{lineno}: undeclared mock in '{m_sym}' ({reason}); "
                            f"mark with # MOCK(M-NNN) and record in {LEDGER_NAME}"
                        )

            elif isinstance(node, (ast.Assign, ast.AnnAssign)):
                targets = node.targets if isinstance(node, ast.Assign) else [node.target]
                names: list[str] = []
                for t in targets:
                    if isinstance(t, ast.Name):
                        names.append(t.id)
                    elif isinstance(t, ast.Attribute) and isinstance(t.value, ast.Name):
                        names.append(t.value.id)
                sym = names[0] if names else "<module>"
                s_start = node.lineno
                s_end = getattr(node, "end_lineno", s_start) or s_start
                if _is_covered(sym, s_start, s_end):
                    continue
                found = _unit_undeclared_reason(node, sym, s_start, s_end, lines, True)
                if found:
                    lineno, reason = found
                    problems.append(
                        f"{rel}:{lineno}: undeclared mock in '{sym}' ({reason}); "
                        f"mark with # MOCK(M-NNN) and record in {LEDGER_NAME}"
                    )

    return problems


def check_mock_ledger(repo_root: Path) -> MockLedgerReport:
    """Reconciles the ledger with the markers in the code and scans for undeclared mocks."""
    repo_root = repo_root.resolve()
    ledger = locate_mock_ledger(repo_root)
    markers, marker_lines_by_file, marker_problems = _find_markers_with_lines(repo_root)
    report = MockLedgerReport(ledger_path=ledger, markers=markers, problems=list(marker_problems))

    entries: dict[str, list[tuple[str, str]]] = {}
    if ledger is None:
        for mid in sorted(markers):
            report.problems.append(
                f"{mid}: marker in {', '.join(sorted(markers[mid]))} but no {LEDGER_NAME} exists"
            )
    else:
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

    report.problems.extend(
        _scan_undeclared_and_fake_success(repo_root, entries, markers, marker_lines_by_file)
    )
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
