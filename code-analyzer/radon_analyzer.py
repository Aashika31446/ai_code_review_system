"""
Radon Python API wrapper for code complexity and maintainability metrics.

Uses radon's Python API to analyze cyclomatic complexity, maintainability index,
and raw line metrics.
"""

from __future__ import annotations

import os
from typing import Any

try:
    from radon.complexity import cc_visit
    from radon.metrics import mi_visit
    from radon.raw import analyze as raw_analyze
    RADON_AVAILABLE = True
except ImportError:
    RADON_AVAILABLE = False


class RadonAnalyzer:
    """Analyzer computing complexity and maintainability via Radon."""

    def __init__(self) -> None:
        pass

    def analyze(self, file_path: str, base_dir: str | None = None) -> list[dict[str, Any]]:
        """
        Analyze a file using Radon API.

        Args:
            file_path: Path to the Python file.
            base_dir: Optional base directory for relative path resolution.

        Returns:
            List of findings conforming to the common finding format.
        """
        if not RADON_AVAILABLE:
            return []

        if not os.path.exists(file_path):
            return []

        rel_file = self._resolve_rel_file(file_path, base_dir)

        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                code = f.read()
        except (FileNotFoundError, PermissionError):
            return []
        except Exception:
            return []

        findings: list[dict[str, Any]] = []

        # 1. Cyclomatic complexity per function/class
        try:
            blocks = cc_visit(code)
            for block in blocks:
                self._check_complexity(block, rel_file, findings)
                for method in getattr(block, "methods", []):
                    self._check_complexity(method, rel_file, findings)
        except (SyntaxError, Exception):
            # Syntax errors are handled by ASTAnalyzer
            pass

        # 2. Maintainability Index per file
        try:
            mi_score = mi_visit(code, multi=False)
            mi_severity = self._map_mi_severity(mi_score)
            if mi_severity:
                findings.append({
                    "file": rel_file,
                    "line": 1,
                    "category": "maintainability",
                    "severity": mi_severity,
                    "rule": "Maintainability Index",
                    "message": f"Low Maintainability Index ({mi_score:.1f}/100).",
                })
        except Exception:
            pass

        # 3. High LOC per file: >300 → low, maintainability
        try:
            raw_res = raw_analyze(code)
            loc = getattr(raw_res, "loc", 0)
            if loc > 300:
                findings.append({
                    "file": rel_file,
                    "line": 1,
                    "category": "maintainability",
                    "severity": "low",
                    "rule": "High LOC",
                    "message": f"File has {loc} lines of code (> 300 LOC).",
                })
        except Exception:
            pass

        return findings

    def _check_complexity(self, block: Any, rel_file: str, findings: list[dict[str, Any]]) -> None:
        """
        Evaluate cyclomatic complexity:
        - CC > 20: critical, complexity
        - CC > 10: high, complexity
        - CC > 5: medium, complexity
        - CC > 2: low, complexity (only if >2)
        """
        cc = getattr(block, "complexity", 0)
        lineno = getattr(block, "lineno", 1)
        name = getattr(block, "name", "block")

        severity = None
        if cc > 20:
            severity = "critical"
        elif cc > 10:
            severity = "high"
        elif cc > 5:
            severity = "medium"
        elif cc > 2:
            severity = "low"

        if severity:
            findings.append({
                "file": rel_file,
                "line": int(lineno),
                "category": "complexity",
                "severity": severity,
                "rule": "Cyclomatic Complexity",
                "message": f"Cyclomatic complexity of '{name}' is {cc}.",
            })

    def _map_mi_severity(self, mi_score: float) -> str | None:
        """
        Maintainability Index thresholds:
        - MI < 10: critical, maintainability
        - MI < 25: high, maintainability
        - MI < 50: medium, maintainability
        """
        if mi_score < 10:
            return "critical"
        if mi_score < 25:
            return "high"
        if mi_score < 50:
            return "medium"
        return None

    def _resolve_rel_file(self, file_path: str, base_dir: str | None = None) -> str:
        """Resolve file path to a relative representation."""
        if base_dir:
            try:
                rel = os.path.relpath(file_path, base_dir)
                return rel.replace("\\", "/")
            except ValueError:
                pass
        return os.path.basename(file_path)
