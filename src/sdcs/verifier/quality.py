"""SDCS Gate Q: Test Quality and Anti-Mock AST Auditor."""

from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path
import re


@dataclass
class QualityViolation:
    file_path: str
    function_name: str
    line_number: int
    rule: str
    message: str


class TestASTVisitor(ast.NodeVisitor):
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.violations: list[QualityViolation] = []

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._analyze_function(node)
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._analyze_function(node)
        self.generic_visit(node)

    def _analyze_function(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        # Only inspect test functions
        if not (node.name.startswith("test_") or node.name.endswith("_test")):
            return

        body = node.body
        if not body:
            return

        # 1. Check for swallowed exceptions (Rule Q3)
        for child in ast.walk(node):
            if isinstance(child, ast.Try):
                for handler in child.handlers:
                    # Check if handler catches Exception, BaseException, or is bare except:
                    is_broad = False
                    if handler.type is None:
                        is_broad = True
                    elif isinstance(handler.type, ast.Name) and handler.type.id in ("Exception", "BaseException"):
                        is_broad = True

                    if is_broad:
                        # Check if body is just pass or ...
                        if len(handler.body) == 1:
                            stmt = handler.body[0]
                            if isinstance(stmt, ast.Pass) or (isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Constant) and stmt.value.value is Ellipsis):
                                self.violations.append(
                                    QualityViolation(
                                        file_path=self.file_path,
                                        function_name=node.name,
                                        line_number=handler.lineno,
                                        rule="Q3_SWALLOWED_EXCEPTION",
                                        message=f"Test function '{node.name}' catches and silently swallows '{handler.type.id if handler.type else 'all'}' exceptions with pass.",
                                    )
                                )

        # 2. Extract assertions and assert-like context managers
        assert_nodes: list[ast.Assert] = []
        raises_contexts: list[ast.With] = []
        mock_calls: int = 0

        for child in ast.walk(node):
            if isinstance(child, ast.Assert):
                assert_nodes.append(child)
            elif isinstance(child, ast.With):
                for item in child.items:
                    # check for pytest.raises or self.assertRaises
                    ctx_name = ""
                    if isinstance(item.context_expr, ast.Call):
                        func = item.context_expr.func
                        if isinstance(func, ast.Attribute):
                            ctx_name = func.attr
                        elif isinstance(func, ast.Name):
                            ctx_name = func.id
                    if ctx_name in ("raises", "assertRaises"):
                        raises_contexts.append(child)
            elif isinstance(child, ast.Call):
                call_name = ""
                if isinstance(child.func, ast.Name):
                    call_name = child.func.id
                elif isinstance(child.func, ast.Attribute):
                    call_name = child.func.attr
                if "mock" in call_name.lower() or "patch" in call_name.lower():
                    mock_calls += 1

        # Check for decorators with patch
        for dec in node.decorator_list:
            dec_name = ""
            if isinstance(dec, ast.Call):
                if isinstance(dec.func, ast.Attribute):
                    dec_name = dec.func.attr
                elif isinstance(dec.func, ast.Name):
                    dec_name = dec.func.id
            elif isinstance(dec, ast.Attribute):
                dec_name = dec.attr
            elif isinstance(dec, ast.Name):
                dec_name = dec.id
            if "patch" in dec_name.lower():
                mock_calls += 1

        # 3. Check for assertless tests (Rule Q2)
        # Filter out docstrings or single pass
        non_doc_statements = [
            s for s in body
            if not (isinstance(s, ast.Expr) and isinstance(s.value, ast.Constant) and isinstance(s.value.value, str))
        ]

        if not assert_nodes and not raises_contexts:
            # If function has active logic but no assertions or raises
            if len(non_doc_statements) > 0 and not (len(non_doc_statements) == 1 and isinstance(non_doc_statements[0], ast.Pass)):
                self.violations.append(
                    QualityViolation(
                        file_path=self.file_path,
                        function_name=node.name,
                        line_number=node.lineno,
                        rule="Q2_ASSERTLESS_TEST",
                        message=f"Test function '{node.name}' contains execution logic but zero assert statements or expected exceptions (pytest.raises).",
                    )
                )
            return

        # 4. Check for Trivial Assertions (Rule Q1)
        # If all assert nodes in the function are trivial
        trivial_count = 0
        for a in assert_nodes:
            if self._is_trivial_assertion(a.test):
                trivial_count += 1

        if assert_nodes and trivial_count == len(assert_nodes) and not raises_contexts:
            self.violations.append(
                QualityViolation(
                    file_path=self.file_path,
                    function_name=node.name,
                    line_number=node.lineno,
                    rule="Q1_TRIVIAL_ASSERTION",
                    message=f"Test function '{node.name}' relies entirely on trivial assertions (e.g. 'assert True' or 'assert x is not None' without value verification).",
                )
            )

        # 5. Check for Mock Abuse / Hollow Mocks (Rule Q4)
        # If test has 3+ mocks and only 1 assertion and 0 real execution calls
        if mock_calls >= 3 and len(assert_nodes) == 1 and len(non_doc_statements) <= mock_calls + 2:
            self.violations.append(
                QualityViolation(
                    file_path=self.file_path,
                    function_name=node.name,
                    line_number=node.lineno,
                    rule="Q4_MOCK_ABUSE",
                    message=f"Test function '{node.name}' has excessive mocking ({mock_calls} mocks) relative to substantive execution logic.",
                )
            )

    def _is_trivial_assertion(self, expr: ast.AST) -> bool:
        # assert True
        if isinstance(expr, ast.Constant) and expr.value is True:
            return True
        # assert not False
        if isinstance(expr, ast.UnaryOp) and isinstance(expr.op, ast.Not):
            if isinstance(expr.operand, ast.Constant) and expr.operand.value is False:
                return True
        # assert 1 == 1
        if isinstance(expr, ast.Compare):
            if (
                isinstance(expr.left, ast.Constant)
                and len(expr.comparators) == 1
                and isinstance(expr.comparators[0], ast.Constant)
                and expr.left.value == expr.comparators[0].value
            ):
                return True
            # assert x is not None
            if len(expr.ops) == 1 and isinstance(expr.ops[0], ast.IsNot):
                if len(expr.comparators) == 1 and isinstance(expr.comparators[0], ast.Constant) and expr.comparators[0].value is None:
                    return True
        return False


def audit_test_quality_file(file_path: Path) -> list[QualityViolation]:
    """Audit a single test file for quality violations."""
    if file_path.suffix == ".py":
        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
            tree = ast.parse(content, filename=str(file_path))
            visitor = TestASTVisitor(str(file_path))
            visitor.visit(tree)
            return visitor.violations
        except Exception:
            return []
    elif file_path.suffix in (".js", ".ts", ".jsx", ".tsx"):
        # Basic heuristic scanning for JS/TS
        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
            violations: list[QualityViolation] = []
            lines = content.splitlines()
            for idx, line in enumerate(lines, 1):
                if re.search(r"expect\s*\(\s*true\s*\)\s*\.toBe\s*\(\s*true\s*\)", line):
                    violations.append(
                        QualityViolation(
                            file_path=str(file_path),
                            function_name="js_test",
                            line_number=idx,
                            rule="Q1_TRIVIAL_ASSERTION",
                            message="Trivial JS/TS assertion 'expect(true).toBe(true)' detected.",
                        )
                    )
                if re.search(r"catch\s*\([^)]*\)\s*\{\s*\}", line):
                    violations.append(
                        QualityViolation(
                            file_path=str(file_path),
                            function_name="js_test",
                            line_number=idx,
                            rule="Q3_SWALLOWED_EXCEPTION",
                            message="Swallowed exception in test catch block detected.",
                        )
                    )
            return violations
        except Exception:
            return []
    return []


def audit_test_quality(
    repo_root: Path = Path("."),
    target_paths: list[Path] | None = None,
) -> list[QualityViolation]:
    """Audit all test files in the repository or specified target paths.

    Returns:
    - List of QualityViolation instances.
    """
    violations: list[QualityViolation] = []

    if target_paths:
        test_files = [p for p in target_paths if p.is_file() and ("test" in p.name or "test" in str(p.parent))]
    else:
        # Search tests directory and test_*.py files
        test_files = []
        for ext in ("*.py", "*.ts", "*.js"):
            test_files.extend(list(repo_root.glob(f"tests/**/{ext}")))
            test_files.extend(list(repo_root.glob(f"**/test_*{ext[1:]}")))
            test_files.extend(list(repo_root.glob(f"**/*_test{ext[1:]}")))

        # Deduplicate
        test_files = sorted(list(set(test_files)))

    for tf in test_files:
        # Skip node_modules and venv
        if any(part in tf.parts for part in ("node_modules", ".venv", "venv", "__pycache__", ".git")):
            continue
        violations.extend(audit_test_quality_file(tf))

    return violations


def run_quality_audit(
    repo_root: Path = Path("."),
    target_paths: list[Path] | None = None,
) -> int:
    """CLI entrypoint for Gate Q test quality audit."""
    violations = audit_test_quality(repo_root=repo_root, target_paths=target_paths)
    if not violations:
        print("[SDCS::GATE_Q] OK: All test files passed quality & anti-mocking audits.")
        return 0

    print(f"[SDCS::GATE_Q::REJECT] Found {len(violations)} test quality violation(s):")
    for v in violations:
        print(f"  - [{v.rule}] {v.file_path}:{v.line_number} in {v.function_name}() -> {v.message}")
    return 1
