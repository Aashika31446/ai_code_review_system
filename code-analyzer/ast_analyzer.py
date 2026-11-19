"""
AST-based static analyzer for Python source code.

Detects code security issues, bugs, style issues, complexity, and maintainability concerns
using Python's built-in `ast` module.
"""

from __future__ import annotations

import ast
import os
from pathlib import Path
from typing import Any, List, Set, Tuple


class ASTAnalyzer:
    """Analyzes Python source files using the Abstract Syntax Tree."""

    SECRET_EXACT_NAMES = {
        "password",
        "secret",
        "token",
        "key",
        "api_key",
        "apikey",
        "auth_token",
        "access_token",
        "secret_key",
        "private_key",
        "client_secret",
        "db_password",
    }

    SECRET_KEYWORD_PARTS = {
        "password",
        "secret",
        "api_key",
        "apikey",
        "auth_token",
        "access_token",
    }

    SECRET_FALSE_POSITIVES = {
        "primary_key",
        "foreign_key",
        "sort_key",
        "dict_key",
        "key_value",
        "keyboard",
        "keyword",
        "hotkey",
    }

    def __init__(self) -> None:
        pass

    def analyze(self, file_path: str, base_dir: str | None = None) -> list[dict[str, Any]]:
        """
        Analyze a Python file and detect issues.

        Args:
            file_path: Path to the Python file.
            base_dir: Optional base directory for computing relative paths.

        Returns:
            List of findings conforming to the common finding format:
            {
                "file": str,
                "line": int,
                "category": str,
                "severity": str,
                "rule": str,
                "message": str
            }
        """
        rel_file = self._resolve_rel_file(file_path, base_dir)

        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
        except (FileNotFoundError, PermissionError):
            return []
        except Exception:
            return []

        findings: list[dict[str, Any]] = []

        # 9. Very long files (>500 lines)
        source_lines = content.splitlines()
        line_count = len(source_lines)
        if line_count > 500:
            findings.append({
                "file": rel_file,
                "line": 1,
                "category": "maintainability",
                "severity": "low",
                "rule": "Long File",
                "message": f"File is too long ({line_count} lines > 500 lines).",
            })

        # Parse AST, handling syntax errors gracefully
        try:
            tree = ast.parse(content, filename=file_path)
        except SyntaxError as exc:
            findings.append({
                "file": rel_file,
                "line": exc.lineno or 1,
                "category": "bug",
                "severity": "critical",
                "rule": "Syntax Error",
                "message": f"Syntax error: {exc.msg} (line {exc.lineno or 1})",
            })
            return findings

        is_test_file = self._is_test_file(file_path)

        # Collect imported names and referenced identifiers for unused import detection
        imported_entries: list[tuple[str, int, str]] = []  # (identifier_used, lineno, full_display_name)
        used_identifiers: set[str] = set()

        # Check nodes across AST
        for node in ast.walk(tree):
            # 1. Use of eval() or exec()
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                if node.func.id in ("eval", "exec"):
                    findings.append({
                        "file": rel_file,
                        "line": getattr(node, "lineno", 1),
                        "category": "security",
                        "severity": "critical",
                        "rule": "Eval/Exec Usage",
                        "message": f"Use of '{node.func.id}()' detected. Dynamic code execution can allow arbitrary code execution.",
                    })

            # 2. Bare except: clauses (catching all exceptions)
            if isinstance(node, ast.ExceptHandler):
                if node.type is None:
                    findings.append({
                        "file": rel_file,
                        "line": getattr(node, "lineno", 1),
                        "category": "bug",
                        "severity": "medium",
                        "rule": "Bare Except",
                        "message": "Bare 'except:' clause catches all exceptions including SystemExit and KeyboardInterrupt. Use 'except Exception:' instead.",
                    })

            # 3. Hardcoded secrets in assignments
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    var_name = self._get_target_name(target)
                    if var_name and self._is_secret_variable(var_name):
                        if isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
                            findings.append({
                                "file": rel_file,
                                "line": getattr(node, "lineno", 1),
                                "category": "security",
                                "severity": "high",
                                "rule": "Hardcoded Secret",
                                "message": f"Possible hardcoded secret in variable '{var_name}'.",
                            })
            elif isinstance(node, ast.AnnAssign):
                var_name = self._get_target_name(node.target)
                if var_name and self._is_secret_variable(var_name):
                    if node.value and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
                        findings.append({
                            "file": rel_file,
                            "line": getattr(node, "lineno", 1),
                            "category": "security",
                            "severity": "high",
                            "rule": "Hardcoded Secret",
                            "message": f"Possible hardcoded secret in variable '{var_name}'.",
                        })

            # 4. Use of assert statements
            if isinstance(node, ast.Assert):
                findings.append({
                    "file": rel_file,
                    "line": getattr(node, "lineno", 1),
                    "category": "bug",
                    "severity": "low",
                    "rule": "Assert Statement",
                    "message": "Use of 'assert' detected. Asserts are ignored when running Python with -O optimization.",
                })

            # 5. Mutable default arguments
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                # Positional/keyword defaults
                all_defaults = list(node.args.defaults) + [d for d in node.args.kw_defaults if d is not None]
                for default_node in all_defaults:
                    if self._is_mutable_node(default_node):
                        findings.append({
                            "file": rel_file,
                            "line": getattr(default_node, "lineno", node.lineno),
                            "category": "bug",
                            "severity": "medium",
                            "rule": "Mutable Default Argument",
                            "message": f"Mutable default argument detected in function '{node.name}'. Use None as default instead.",
                        })
                        break  # Report once per function

            # 6. Comparison to None using == instead of is
            if isinstance(node, ast.Compare):
                is_comparison_to_none = False
                operator_used = "=="
                for op, comp in zip(node.ops, node.comparators):
                    if isinstance(op, (ast.Eq, ast.NotEq)):
                        if self._is_none_node(node.left) or self._is_none_node(comp):
                            is_comparison_to_none = True
                            operator_used = "==" if isinstance(op, ast.Eq) else "!="
                            break
                if is_comparison_to_none:
                    findings.append({
                        "file": rel_file,
                        "line": getattr(node, "lineno", 1),
                        "category": "style",
                        "severity": "low",
                        "rule": "Comparison to None",
                        "message": f"Comparison to None using '{operator_used}' detected. Use 'is' or 'is not' instead.",
                    })

            # 8. Very long functions (>50 lines)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                end_lineno = getattr(node, "end_lineno", node.lineno)
                func_length = end_lineno - node.lineno + 1
                if func_length > 50:
                    findings.append({
                        "file": rel_file,
                        "line": node.lineno,
                        "category": "maintainability",
                        "severity": "medium",
                        "rule": "Long Function",
                        "message": f"Function '{node.name}' is {func_length} lines long (> 50 lines).",
                    })

            # 10. Use of print() in non-test files
            if not is_test_file and isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                if node.func.id == "print":
                    findings.append({
                        "file": rel_file,
                        "line": getattr(node, "lineno", 1),
                        "category": "style",
                        "severity": "low",
                        "rule": "Print Statement",
                        "message": "Use of 'print()' detected in non-test code. Consider using a structured logger.",
                    })

            # Track imports for 7. Unused imports
            if isinstance(node, ast.Import):
                for alias in node.names:
                    local_ref = alias.asname or alias.name.split(".")[0]
                    imported_entries.append((local_ref, node.lineno, alias.name))
            elif isinstance(node, ast.ImportFrom):
                if node.module != "__future__":
                    for alias in node.names:
                        if alias.name != "*":
                            local_ref = alias.asname or alias.name
                            full_name = f"{node.module}.{alias.name}" if node.module else alias.name
                            imported_entries.append((local_ref, node.lineno, full_name))

            # Collect referenced names
            if isinstance(node, ast.Name) and not isinstance(getattr(node, "ctx", None), ast.Store):
                used_identifiers.add(node.id)

            # Special case: __all__ variable exports
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == "__all__":
                        if isinstance(node.value, (ast.List, ast.Tuple, ast.Set)):
                            for elt in node.value.elts:
                                if isinstance(elt, ast.Constant) and isinstance(elt.value, str):
                                    used_identifiers.add(elt.value)

        # 7. Unused imports check
        for local_ref, lineno, full_name in imported_entries:
            if local_ref not in used_identifiers:
                findings.append({
                    "file": rel_file,
                    "line": lineno,
                    "category": "style",
                    "severity": "low",
                    "rule": "Unused Import",
                    "message": f"Import '{full_name}' is not used.",
                })

        return findings

    def _resolve_rel_file(self, file_path: str, base_dir: str | None = None) -> str:
        """Resolve file path to a relative representation."""
        if base_dir:
            try:
                rel = os.path.relpath(file_path, base_dir)
                return rel.replace("\\", "/")
            except ValueError:
                pass
        return os.path.basename(file_path)

    def _is_test_file(self, file_path: str) -> bool:
        """Determine if a file path is a test file."""
        p = Path(file_path)
        name_lower = p.name.lower()
        parts_lower = [part.lower() for part in p.parts]
        if "tests" in parts_lower or "test" in parts_lower:
            return True
        if name_lower.startswith("test_") or name_lower.endswith("_test.py"):
            return True
        return False

    def _get_target_name(self, target: ast.AST) -> str | None:
        """Extract identifier string from assignment target."""
        if isinstance(target, ast.Name):
            return target.id
        if isinstance(target, ast.Attribute):
            return target.attr
        return None

    def _is_secret_variable(self, name: str) -> bool:
        """Check if variable name resembles a hardcoded secret."""
        lower = name.lower()
        if lower in self.SECRET_FALSE_POSITIVES:
            return False
        if lower in self.SECRET_EXACT_NAMES:
            return True
        # Check underscore-separated components
        tokens = lower.split("_")
        for part in self.SECRET_KEYWORD_PARTS:
            if part in tokens or lower.startswith(f"{part}_") or lower.endswith(f"_{part}"):
                return True
        if lower.endswith("_key") or lower.endswith("_token") or lower.endswith("_secret") or lower.endswith("_password"):
            return True
        return False

    def _is_mutable_node(self, node: ast.AST | None) -> bool:
        """Check if an AST expression represents a mutable literal or constructor call."""
        if node is None:
            return False
        if isinstance(node, (ast.List, ast.Dict, ast.Set)):
            return True
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            if node.func.id in ("list", "dict", "set"):
                return True
        return False

    def _is_none_node(self, node: ast.AST | None) -> bool:
        """Check if node is a None literal."""
        if node is None:
            return False
        if isinstance(node, ast.Constant) and node.value is None:
            return True
        if isinstance(node, ast.Name) and node.id == "None":
            return True
        return False
