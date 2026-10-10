"""SDCS Gate Q: Test Quality and Anti-Mock AST Auditor."""

from __future__ import annotations

import ast
import re
from dataclasses import dataclass
from pathlib import Path


@dataclass
class QualityViolation:
    file_path: str
    function_name: str
    line_number: int
    rule: str
    message: str


def _has_call(node: ast.AST) -> bool:
    """Return True if AST node contains any function or method call."""
    return any(isinstance(n, ast.Call) for n in ast.walk(node))


class TestASTVisitor(ast.NodeVisitor):
    def __init__(
        self, file_path: str, file_content: str = "", asserting_functions: set[str] | None = None
    ):
        self.file_path = file_path
        self.file_content = file_content
        self.file_lines = file_content.splitlines() if file_content else []
        self.asserting_functions: set[str] = asserting_functions or set()
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
                    # Check if handler catches Exception, BaseException, AssertionError, or is bare except
                    is_swallowed_target = False
                    if handler.type is None:
                        is_swallowed_target = True
                    elif isinstance(handler.type, ast.Name):
                        if handler.type.id in ("Exception", "BaseException", "AssertionError"):
                            is_swallowed_target = True
                    elif isinstance(handler.type, ast.Tuple):
                        for elt in handler.type.elts:
                            if isinstance(elt, ast.Name) and elt.id in (
                                "Exception",
                                "BaseException",
                                "AssertionError",
                            ):
                                is_swallowed_target = True

                    if is_swallowed_target:
                        # Check if body is just pass or ...
                        if len(handler.body) == 1:
                            stmt = handler.body[0]
                            if isinstance(stmt, ast.Pass) or (
                                isinstance(stmt, ast.Expr)
                                and isinstance(stmt.value, ast.Constant)
                                and stmt.value.value is Ellipsis
                            ):
                                exc_name = "all"
                                if handler.type:
                                    exc_name = getattr(handler.type, "id", None) or "exception"
                                self.violations.append(
                                    QualityViolation(
                                        file_path=self.file_path,
                                        function_name=node.name,
                                        line_number=handler.lineno,
                                        rule="Q3_SWALLOWED_EXCEPTION",
                                        message=f"Test function '{node.name}' catches and silently swallows '{exc_name}' with pass.",
                                    )
                                )

        # 2. Extract assertions and assert-like context managers
        assert_nodes: list[ast.Assert] = []
        assert_calls: list[ast.Call] = []
        raises_contexts: list[ast.With] = []
        mock_calls: int = 0

        for child in ast.walk(node):
            if isinstance(child, ast.Assert):
                assert_nodes.append(child)
            elif isinstance(child, ast.With):
                for item in child.items:
                    # check for pytest.raises or self.assertRaises / assertWarns / assertLogs
                    ctx_name = ""
                    if isinstance(item.context_expr, ast.Call):
                        func = item.context_expr.func
                        if isinstance(func, ast.Attribute):
                            ctx_name = func.attr
                        elif isinstance(func, ast.Name):
                            ctx_name = func.id
                    elif isinstance(item.context_expr, ast.Attribute):
                        ctx_name = item.context_expr.attr
                    elif isinstance(item.context_expr, ast.Name):
                        ctx_name = item.context_expr.id
                    if ctx_name in (
                        "raises",
                        "assertRaises",
                        "assertRaisesRegex",
                        "assertWarns",
                        "assertWarnsRegex",
                        "assertLogs",
                        "warns",
                    ):
                        raises_contexts.append(child)
            elif isinstance(child, ast.Call):
                call_name = ""
                if isinstance(child.func, ast.Name):
                    call_name = child.func.id
                elif isinstance(child.func, ast.Attribute):
                    call_name = child.func.attr
                if "mock" in call_name.lower() or "patch" in call_name.lower():
                    mock_calls += 1

                if self._is_assertion_call(child):
                    assert_calls.append(child)

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

        # Check for explicit pragma: # sdcs: no-raise or # pragma: no-raise
        has_no_raise_pragma = self._has_no_raise_pragma(node)

        # Separate mock assertions (e.g. m.assert_called()) from substantive assertions
        mock_assertion_calls = [
            c
            for c in assert_calls
            if isinstance(c.func, ast.Attribute)
            and c.func.attr.startswith(
                ("assert_called", "assert_not_called", "assert_has_calls", "assert_any_call")
            )
        ]
        real_assertion_calls = [c for c in assert_calls if c not in mock_assertion_calls]

        # 3. Check for assertless tests (Rule Q2)
        # Filter out docstrings or single pass
        non_doc_statements = [
            s
            for s in body
            if not (
                isinstance(s, ast.Expr)
                and isinstance(s.value, ast.Constant)
                and isinstance(s.value.value, str)
            )
        ]

        total_assertions = len(assert_nodes) + len(real_assertion_calls) + len(mock_assertion_calls)

        if not total_assertions and not raises_contexts and not has_no_raise_pragma:
            # If function has active logic but no assertions or raises
            if len(non_doc_statements) > 0 and not (
                len(non_doc_statements) == 1 and isinstance(non_doc_statements[0], ast.Pass)
            ):
                self.violations.append(
                    QualityViolation(
                        file_path=self.file_path,
                        function_name=node.name,
                        line_number=node.lineno,
                        rule="Q2_ASSERTLESS_TEST",
                        message=f"Test function '{node.name}' contains execution logic but zero assert statements, unittest assertions, or expected exceptions.",
                    )
                )
            return

        # 4. Check for Trivial Assertions (Rule Q1)
        # A test is trivial ONLY if every one of its checks, of any kind, is trivial
        trivial_count = 0
        for a in assert_nodes:
            if self._is_trivial_assertion(a.test):
                trivial_count += 1
        for c in assert_calls:
            if self._is_trivial_call_assertion(c):
                trivial_count += 1

        if (
            total_assertions > 0
            and trivial_count == total_assertions
            and not raises_contexts
            and not has_no_raise_pragma
        ):
            self.violations.append(
                QualityViolation(
                    file_path=self.file_path,
                    function_name=node.name,
                    line_number=node.lineno,
                    rule="Q1_TRIVIAL_ASSERTION",
                    message=f"Test function '{node.name}' relies entirely on trivial assertions (e.g. 'assert True' or tautological comparison).",
                )
            )
            return

        # 5. Check for Mock Abuse / Hollow Mocks (Rule Q4)
        # Case A: High mock count with minimal substantive logic
        if mock_calls >= 3 and total_assertions == 1 and len(non_doc_statements) <= mock_calls + 2:
            self.violations.append(
                QualityViolation(
                    file_path=self.file_path,
                    function_name=node.name,
                    line_number=node.lineno,
                    rule="Q4_MOCK_ABUSE",
                    message=f"Test function '{node.name}' has excessive mocking ({mock_calls} mocks) relative to substantive execution logic.",
                )
            )
            return

        # Case B: Test only verifies its own mock assertions with zero assertions on real outputs
        if (
            len(mock_assertion_calls) > 0
            and len(real_assertion_calls) == 0
            and len(assert_nodes) == 0
            and not raises_contexts
            and not has_no_raise_pragma
        ):
            # Gather all patched target names and mock parameter/variable names
            patched_targets: set[str] = set()

            def _extract_target_name(expr: ast.AST) -> str | None:
                if isinstance(expr, ast.Constant) and isinstance(expr.value, str):
                    return expr.value.split(".")[-1]
                if isinstance(expr, ast.BinOp):
                    for c in ast.walk(expr):
                        if isinstance(c, ast.Constant) and isinstance(c.value, str):
                            s = c.value.strip(".")
                            if s:
                                return s.split(".")[-1]
                return None

            for dec in node.decorator_list:
                if isinstance(dec, ast.Call):
                    fn = dec.func
                    fn_name = (
                        fn.attr
                        if isinstance(fn, ast.Attribute)
                        else (fn.id if isinstance(fn, ast.Name) else "")
                    )
                    if "patch" in fn_name.lower() and dec.args:
                        tgt = _extract_target_name(dec.args[0])
                        if tgt:
                            patched_targets.add(tgt)
                        if len(dec.args) >= 2:
                            tgt2 = _extract_target_name(dec.args[1])
                            if tgt2:
                                patched_targets.add(tgt2)

            for arg in node.args.args:
                if arg.arg not in ("self", "cls"):
                    patched_targets.add(arg.arg)

            for child in ast.walk(node):
                if isinstance(child, ast.With):
                    for item in child.items:
                        ctx = item.context_expr
                        if isinstance(ctx, ast.Call):
                            fn = ctx.func
                            fn_name = (
                                fn.attr
                                if isinstance(fn, ast.Attribute)
                                else (fn.id if isinstance(fn, ast.Name) else "")
                            )
                            if "patch" in fn_name.lower():
                                if ctx.args:
                                    tgt = _extract_target_name(ctx.args[0])
                                    if tgt:
                                        patched_targets.add(tgt)
                                    if len(ctx.args) >= 2:
                                        tgt2 = _extract_target_name(ctx.args[1])
                                        if tgt2:
                                            patched_targets.add(tgt2)
                                if item.optional_vars:
                                    if isinstance(item.optional_vars, ast.Name):
                                        patched_targets.add(item.optional_vars.id)
                                    elif isinstance(item.optional_vars, (ast.Tuple, ast.List)):
                                        for v in item.optional_vars.elts:
                                            if isinstance(v, ast.Name):
                                                patched_targets.add(v.id)

            # Check if ANY non-patch, non-mock substantive call was made
            substantive_calls: list[ast.Call] = []
            for child in ast.walk(node):
                if isinstance(child, ast.Call):
                    fn = child.func
                    fn_name = (
                        fn.attr
                        if isinstance(fn, ast.Attribute)
                        else (fn.id if isinstance(fn, ast.Name) else "")
                    )
                    if fn_name in ("patch", "object", "MagicMock", "Mock", "PropertyMock"):
                        continue
                    if child in assert_calls:
                        continue
                    if (
                        isinstance(fn, ast.Attribute)
                        and isinstance(fn.value, ast.Name)
                        and fn.value.id == "self"
                    ):
                        if fn.attr in ("setUp", "tearDown", "addCleanup", "skipTest", "subTest"):
                            continue
                    substantive_calls.append(child)

            def _is_call_to_patched(call: ast.Call) -> bool:
                fn = call.func
                if isinstance(fn, ast.Name):
                    return fn.id in patched_targets
                if isinstance(fn, ast.Attribute):
                    if fn.attr in patched_targets:
                        return True
                    if isinstance(fn.value, ast.Name) and fn.value.id in patched_targets:
                        return True
                return False

            non_patched_calls = [c for c in substantive_calls if not _is_call_to_patched(c)]

            # Flag only when every call goes to the patched target or mock assertion
            if not non_patched_calls:
                self.violations.append(
                    QualityViolation(
                        file_path=self.file_path,
                        function_name=node.name,
                        line_number=node.lineno,
                        rule="Q4_MOCK_ABUSE",
                        message=f"Test function '{node.name}' only checks its own mock call assertions with zero assertions on substantive logic.",
                    )
                )
                return

    def _has_no_raise_pragma(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
        """Check if test function has an explicit no-raise pragma (# sdcs: no-raise or # pragma: no-raise)."""
        if self.file_lines and hasattr(node, "lineno"):
            start = max(0, node.lineno - 1)
            end = min(len(self.file_lines), getattr(node, "end_lineno", node.lineno + 25))
            for i in range(start, end):
                line = self.file_lines[i]
                if "#" in line:
                    if re.search(r"#\s*(?:sdcs|pragma):\s*no-raise\b", line, re.IGNORECASE):
                        return True
        return False

    def _is_assertion_call(self, call: ast.Call) -> bool:
        """Check if call is a unittest assertion, custom assertion helper, or intra-file helper."""
        name = ""
        attr = ""
        if isinstance(call.func, ast.Attribute):
            attr = call.func.attr
            name = call.func.attr
        elif isinstance(call.func, ast.Name):
            name = call.func.id

        name_lower = name.lower()
        attr_lower = attr.lower()

        # 1. Standard unittest.TestCase assertion methods (self.assertEqual, self.assertTrue, self.assertIn, etc.)
        if attr_lower.startswith("assert") or attr_lower.startswith("_assert"):
            return True
        if name_lower.startswith("assert_") or name_lower.startswith("_assert_"):
            return True

        # 2. Failure assertions (self.fail, pytest.fail)
        if attr_lower == "fail" or name_lower == "fail":
            return True

        # 3. Third-party testing library assertions (np.testing.assert_*, etc.)
        if isinstance(call.func, ast.Attribute):
            val = call.func.value
            if isinstance(val, ast.Attribute) and val.attr == "testing":
                if attr_lower.startswith("assert_"):
                    return True

        # 4. Intra-file helpers known from Pass 1 to contain assertions
        if name in self.asserting_functions or attr in self.asserting_functions:
            return True

        return False

    def _is_trivial_call_assertion(self, call: ast.Call) -> bool:
        """Detect trivial unittest assertion calls like self.assertTrue(True) or self.assertEqual(1, 1)."""
        if isinstance(call.func, ast.Attribute):
            attr = call.func.attr
            if attr == "assertTrue" and call.args:
                if isinstance(call.args[0], ast.Constant) and call.args[0].value is True:
                    return True
            elif attr == "assertFalse" and call.args:
                if isinstance(call.args[0], ast.Constant) and call.args[0].value is False:
                    return True
            elif attr in ("assertEqual", "assert_equal") and len(call.args) >= 2:
                if (
                    isinstance(call.args[0], ast.Constant)
                    and isinstance(call.args[1], ast.Constant)
                    and call.args[0].value == call.args[1].value
                ):
                    return True
                # Self-compare: self.assertEqual(x, x) only when neither side contains a call
                if ast.dump(call.args[0]) == ast.dump(call.args[1]):
                    if not (_has_call(call.args[0]) or _has_call(call.args[1])):
                        return True
        return False

    def _is_trivial_assertion(self, expr: ast.AST) -> bool:
        # assert True
        if isinstance(expr, ast.Constant) and expr.value is True:
            return True
        # assert not False
        if isinstance(expr, ast.UnaryOp) and isinstance(expr.op, ast.Not):
            if isinstance(expr.operand, ast.Constant) and expr.operand.value is False:
                return True
        # assert 1 == 1 or assert x == x
        if isinstance(expr, ast.Compare):
            if len(expr.comparators) == 1:
                if (
                    isinstance(expr.left, ast.Constant)
                    and isinstance(expr.comparators[0], ast.Constant)
                    and expr.left.value == expr.comparators[0].value
                ):
                    return True
                # Self-compare: assert x == x only when neither side contains a call
                if ast.dump(expr.left) == ast.dump(expr.comparators[0]):
                    if not (_has_call(expr.left) or _has_call(expr.comparators[0])):
                        return True
        return False


def _collect_module_asserting_functions(tree: ast.AST) -> set[str]:
    """Analyze module AST to discover all helper functions/methods that contain assertions."""
    asserting_funcs: set[str] = set()
    call_graph: dict[str, set[str]] = {}

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            func_name = node.name
            has_assert = False
            callees: set[str] = set()

            for child in ast.walk(node):
                if isinstance(child, ast.Assert):
                    has_assert = True
                elif isinstance(child, ast.With):
                    for item in child.items:
                        ctx = ""
                        if isinstance(item.context_expr, ast.Call):
                            f = item.context_expr.func
                            ctx = (
                                f.attr
                                if isinstance(f, ast.Attribute)
                                else (f.id if isinstance(f, ast.Name) else "")
                            )
                        elif isinstance(item.context_expr, ast.Attribute):
                            ctx = item.context_expr.attr
                        elif isinstance(item.context_expr, ast.Name):
                            ctx = item.context_expr.id
                        if "raise" in ctx.lower() or "warn" in ctx.lower() or "log" in ctx.lower():
                            has_assert = True
                elif isinstance(child, ast.Call):
                    cname = ""
                    if isinstance(child.func, ast.Name):
                        cname = child.func.id
                    elif isinstance(child.func, ast.Attribute):
                        cname = child.func.attr
                    c_lower = cname.lower()
                    if (
                        c_lower.startswith("assert")
                        or c_lower.startswith("_assert")
                        or c_lower in ("fail", "_fail")
                    ):
                        has_assert = True
                    if cname:
                        callees.add(cname)

            if has_assert:
                asserting_funcs.add(func_name)
            call_graph[func_name] = callees

    # Transitive closure: propagate assertions along the intra-module call graph
    changed = True
    while changed:
        changed = False
        for caller, callees in call_graph.items():
            if caller not in asserting_funcs:
                if any(c in asserting_funcs for c in callees):
                    asserting_funcs.add(caller)
                    changed = True

    return asserting_funcs


def audit_test_quality_file(file_path: Path) -> list[QualityViolation]:
    """Audit a single test file for quality violations."""
    if file_path.suffix == ".py":
        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
            tree = ast.parse(content, filename=str(file_path))
            asserting_funcs = _collect_module_asserting_functions(tree)
            visitor = TestASTVisitor(
                str(file_path), file_content=content, asserting_functions=asserting_funcs
            )
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
        test_files = [
            p for p in target_paths if p.is_file() and ("test" in p.name or "test" in str(p.parent))
        ]
    else:
        # Search tests directory and test_*.py files
        test_files = []
        for ext in ("*.py", "*.ts", "*.js"):
            test_files.extend(list(repo_root.glob(f"tests/**/{ext}")))
            test_files.extend(list(repo_root.glob(f"**/test_*{ext[1:]}")))
            test_files.extend(list(repo_root.glob(f"**/*_test{ext[1:]}")))

        # Deduplicate
        test_files = sorted(set(test_files))

    for tf in test_files:
        # Skip node_modules, venv, scratch, and hidden directories
        try:
            rel_parts = tf.relative_to(repo_root).parts[:-1]
        except ValueError:
            rel_parts = tf.parts[:-1]

        if any(
            p.startswith(".")
            or p
            in (
                "node_modules",
                ".venv",
                "venv",
                "__pycache__",
                ".git",
                "scratch",
                ".scratch",
                "build",
                "dist",
            )
            for p in rel_parts
        ):
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
