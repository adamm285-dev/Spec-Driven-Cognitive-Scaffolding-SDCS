"""AST Skeletal Observation Compactor & Polyglot Structural Outline Engine.

SPEC-001 v1.8.0 Section 7.12.
Extracts high-fidelity structural skeletons (classes, public method signatures,
type annotations, docstrings) replacing execution bodies with '...'.
Compresses observation tokens by 85-95% to eliminate the 'Grep Reflex' during
autonomous agent orientation turns.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path
from typing import Any

from sdcs.verifier.state import count_tokens


class PythonSkeletonTransformer(ast.NodeTransformer):
    """Transforms a Python AST by replacing function and method bodies with Ellipsis (...)

    while preserving type annotations, signatures, and docstrings.
    """

    def _strip_body(self, body: list[ast.stmt]) -> list[ast.stmt]:
        new_body: list[ast.stmt] = []
        if not body:
            return [ast.Expr(value=ast.Constant(value=...))]

        # Check if first statement is a docstring
        first_stmt = body[0]
        if (
            isinstance(first_stmt, ast.Expr)
            and isinstance(first_stmt.value, ast.Constant)
            and isinstance(first_stmt.value.value, str)
        ):
            new_body.append(first_stmt)

        # Append Ellipsis expression (...)
        new_body.append(ast.Expr(value=ast.Constant(value=...)))
        return new_body

    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.AST:
        self.generic_visit(node)
        node.body = self._strip_body(node.body)
        return node

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> ast.AST:
        self.generic_visit(node)
        node.body = self._strip_body(node.body)
        return node


def extract_python_skeleton(source_code: str) -> str:
    """Extracts structural AST skeleton from Python source code.

    Replaces all function/method bodies with '...' while retaining classes,
    type annotations, decorators, and docstrings.
    """
    try:
        tree = ast.parse(source_code)
    except SyntaxError:
        # Fallback to line-based heuristic if source has syntax errors
        return _extract_python_regex_skeleton(source_code)

    transformer = PythonSkeletonTransformer()
    transformed_tree = transformer.visit(tree)
    ast.fix_missing_locations(transformed_tree)
    try:
        return ast.unparse(transformed_tree)
    except Exception:
        return _extract_python_regex_skeleton(source_code)


def _extract_python_regex_skeleton(source_code: str) -> str:
    """Fallback line-based skeleton extractor for unparseable Python."""
    lines = source_code.splitlines()
    out_lines = []
    in_def = False

    for line in lines:
        stripped = line.strip()
        if stripped.startswith(("class ", "def ", "async def ", "@", "import ", "from ")):
            out_lines.append(line)
            if stripped.endswith(":"):
                out_lines.append("    ...")
                in_def = True
        elif in_def and (stripped.startswith('"""') or stripped.startswith("'''")):
            out_lines.append(line)
        elif in_def and (stripped.endswith('"""') or stripped.endswith("'''")):
            out_lines.append(line)
            in_def = False
        elif not in_def and (":" in line and "=" in line):
            # Class-level type annotations
            out_lines.append(line)

    return "\n".join(out_lines)


def _extract_ts_js_skeleton(source_code: str) -> str:
    """Extracts structural signatures from TypeScript / JavaScript source."""
    lines = source_code.splitlines()
    out_lines = []

    for line in lines:
        stripped = line.strip()
        if re.match(
            r"^(export\s+)?(default\s+)?(class|interface|type|enum|function|abstract\s+class)\b",
            stripped,
        ):
            if "{" in stripped and "}" in stripped:
                out_lines.append(line)
            elif "{" in stripped:
                out_lines.append(line.split("{")[0] + "{ ... }")
            else:
                out_lines.append(line)
        elif re.match(r"^(export\s+)?(const|let|var)\s+\w+\s*:\s*[^=]+=", stripped):
            out_lines.append(line.split("=")[0] + "= ...;")
        elif stripped.startswith(("import ", "export *", "export {")):
            out_lines.append(line)
        elif stripped.startswith("/**") or stripped.startswith("*"):
            out_lines.append(line)

    return "\n".join(out_lines)


def _extract_go_skeleton(source_code: str) -> str:
    """Extracts structural signatures from Go source."""
    lines = source_code.splitlines()
    out_lines = []

    for line in lines:
        stripped = line.strip()
        if stripped.startswith(("package ", "import (", "import ")):
            out_lines.append(line)
        elif re.match(r"^type\s+\w+\s+(struct|interface)", stripped):
            out_lines.append(line)
        elif re.match(r"^func\s+(\([^)]+\)\s+)?\w+\([^)]*\)", stripped):
            if "{" in stripped:
                out_lines.append(line.split("{")[0] + "{ ... }")
            else:
                out_lines.append(line)

    return "\n".join(out_lines)


def _extract_rust_skeleton(source_code: str) -> str:
    """Extracts structural signatures from Rust source."""
    lines = source_code.splitlines()
    out_lines = []

    for line in lines:
        stripped = line.strip()
        if re.match(r"^(pub\s+)?(struct|enum|trait|type)\s+", stripped):
            out_lines.append(line)
        elif re.match(r"^(pub\s+)?(async\s+)?fn\s+", stripped):
            if "{" in stripped:
                out_lines.append(line.split("{")[0] + "{ ... }")
            else:
                out_lines.append(line)
        elif stripped.startswith(("use ", "mod ", "pub mod ")):
            out_lines.append(line)

    return "\n".join(out_lines)


def extract_file_skeleton(file_path: Path) -> str:
    """Extracts structural skeleton from a file based on its extension."""
    if not file_path.is_file():
        raise FileNotFoundError(f"File not found: {file_path}")

    content = file_path.read_text(encoding="utf-8", errors="ignore")
    ext = file_path.suffix.lower()

    if ext == ".py":
        return extract_python_skeleton(content)
    elif ext in (".ts", ".tsx", ".js", ".jsx"):
        return _extract_ts_js_skeleton(content)
    elif ext == ".go":
        return _extract_go_skeleton(content)
    elif ext == ".rs":
        return _extract_rust_skeleton(content)
    else:
        # Fallback for plain text or unsupported types: first 40 lines
        lines = content.splitlines()[:40]
        return "\n".join(lines) + ("\n... [truncated]" if len(content.splitlines()) > 40 else "")


def calculate_skeleton_metrics(original_code: str, skeleton_code: str) -> dict[str, Any]:
    """Calculates token counts and compression ratios between original and skeleton."""
    orig_tokens = count_tokens(original_code)
    skel_tokens = count_tokens(skeleton_code)
    ratio = (1.0 - (skel_tokens / orig_tokens)) if orig_tokens > 0 else 0.0

    return {
        "original_tokens": orig_tokens,
        "skeleton_tokens": skel_tokens,
        "compression_ratio": round(ratio * 100, 1),
        "tokens_saved": max(0, orig_tokens - skel_tokens),
    }


def run_skeleton_command(target_path: Path) -> int:
    """CLI runner for extracting and displaying file skeletons with token savings telemetry."""
    if not target_path.exists():
        print(f"[SDCS::ERROR] Target path does not exist: {target_path}")
        return 1

    if target_path.is_dir():
        print("\n====================================================================")
        print(" SDCS :: Subsystem AST Skeletal Map (SPEC-001 v1.8.0)")
        print(f" Target Directory: {target_path}")
        print("====================================================================\n")

        total_orig = 0
        total_skel = 0

        # Scan code files
        code_exts = {".py", ".ts", ".tsx", ".js", ".jsx", ".go", ".rs"}
        files = [
            f
            for f in target_path.rglob("*")
            if f.is_file()
            and f.suffix.lower() in code_exts
            and not any(p.startswith(".") for p in f.parts)
        ]

        for f in sorted(files):
            try:
                orig = f.read_text(encoding="utf-8", errors="ignore")
                skel = extract_file_skeleton(f)
                metrics = calculate_skeleton_metrics(orig, skel)
                total_orig += metrics["original_tokens"]
                total_skel += metrics["skeleton_tokens"]
                rel = f.relative_to(target_path).as_posix()
                print(
                    f"  · {rel:<40} {metrics['original_tokens']:>5}t -> {metrics['skeleton_tokens']:>4}t "
                    f"(-{metrics['compression_ratio']:>4}%)"
                )
            except Exception as err:
                print(f"  · {f.name}: error ({err})")

        overall_ratio = round((1.0 - (total_skel / total_orig)) * 100, 1) if total_orig > 0 else 0.0
        print("\n--------------------------------------------------------------------")
        print(
            f" Subsystem Totals: {total_orig} tokens -> {total_skel} tokens "
            f"(Saved {total_orig - total_skel}t, -{overall_ratio}% token burn)"
        )
        print("====================================================================\n")
        return 0

    # Single file
    try:
        orig = target_path.read_text(encoding="utf-8", errors="ignore")
        skel = extract_file_skeleton(target_path)
        metrics = calculate_skeleton_metrics(orig, skel)

        print(f"\n--- AST SKELETON: {target_path.name} ---")
        print(
            f"# Tokens: {metrics['original_tokens']} -> {metrics['skeleton_tokens']} "
            f"(-{metrics['compression_ratio']}% compressed)\n"
        )
        print(skel)
        print("\n--- END SKELETON ---")
        return 0
    except Exception as err:
        print(f"[SDCS::ERROR] Failed to extract skeleton for {target_path}: {err}")
        return 1
