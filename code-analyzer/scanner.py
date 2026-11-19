"""
Unified code scanner orchestrating AST, Ruff, Bandit, and Radon analyzers.

Provides file and directory scanning, finding deduplication, severity sorting,
and source code snippet extraction.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

try:
    from .ast_analyzer import ASTAnalyzer
    from .ruff_analyzer import RuffAnalyzer
    from .bandit_analyzer import BanditAnalyzer
    from .radon_analyzer import RadonAnalyzer
except ImportError:
    from ast_analyzer import ASTAnalyzer
    from ruff_analyzer import RuffAnalyzer
    from bandit_analyzer import BanditAnalyzer
    from radon_analyzer import RadonAnalyzer


class CodeScanner:
    """Unified code scanner orchestrating all analysis engines."""

    SEVERITY_ORDER: dict[str, int] = {
        "critical": 0,
        "high": 1,
        "medium": 2,
        "low": 3,
    }

    def __init__(
        self,
        ast_analyzer: ASTAnalyzer | None = None,
        ruff_analyzer: RuffAnalyzer | None = None,
        bandit_analyzer: BanditAnalyzer | None = None,
        radon_analyzer: RadonAnalyzer | None = None,
    ) -> None:
        self.ast_analyzer = ast_analyzer or ASTAnalyzer()
        self.ruff_analyzer = ruff_analyzer or RuffAnalyzer()
        self.bandit_analyzer = bandit_analyzer or BanditAnalyzer()
        self.radon_analyzer = radon_analyzer or RadonAnalyzer()

    def scan_file(self, file_path: str, base_dir: str = "") -> list[dict[str, Any]]:
        """
        Run all analyzers on one file, deduplicate and sort findings.

        Args:
            file_path: Path to the target Python file.
            base_dir: Optional base directory to compute relative paths.

        Returns:
            List of unique findings sorted by severity, file, and line.
        """
        if not os.path.exists(file_path):
            return []

        effective_base = base_dir if base_dir else None
        all_findings: list[dict[str, Any]] = []

        # 1. AST Analysis
        try:
            ast_findings = self.ast_analyzer.analyze(file_path, base_dir=effective_base)
            all_findings.extend(ast_findings)
        except (FileNotFoundError, PermissionError):
            return []
        except Exception:
            pass

        # 2. Ruff Analysis
        try:
            ruff_findings = self.ruff_analyzer.analyze(file_path, base_dir=effective_base)
            all_findings.extend(ruff_findings)
        except (FileNotFoundError, PermissionError):
            return []
        except Exception:
            pass

        # 3. Bandit Analysis
        try:
            bandit_findings = self.bandit_analyzer.analyze(file_path, base_dir=effective_base)
            all_findings.extend(bandit_findings)
        except (FileNotFoundError, PermissionError):
            return []
        except Exception:
            pass

        # 4. Radon Analysis
        try:
            radon_findings = self.radon_analyzer.analyze(file_path, base_dir=effective_base)
            all_findings.extend(radon_findings)
        except (FileNotFoundError, PermissionError):
            return []
        except Exception:
            pass

        return self._deduplicate_and_sort(all_findings)

    def scan_directory(self, directory: str) -> list[dict[str, Any]]:
        """
        Find all .py files recursively and scan each.

        Args:
            directory: Directory to search and scan.

        Returns:
            Deduplicated and sorted list of findings across all files.
        """
        if not os.path.exists(directory):
            return []

        py_files: list[str] = []
        try:
            for root, _, files in os.walk(directory):
                for file in sorted(files):
                    if file.endswith(".py"):
                        py_files.append(os.path.join(root, file))
        except (FileNotFoundError, PermissionError):
            return []

        py_files.sort()
        all_findings: list[dict[str, Any]] = []

        for py_file in py_files:
            file_findings = self.scan_file(py_file, base_dir=directory)
            all_findings.extend(file_findings)

        return self._deduplicate_and_sort(all_findings)

    def get_code_snippet(self, file_path: str, line_num: int, context: int = 3) -> str:
        """
        Return source code lines around a given line number.

        Args:
            file_path: Path to the source file.
            line_num: 1-indexed target line number.
            context: Number of context lines before and after.

        Returns:
            Formatted snippet string with line numbers and focus indicator.
        """
        if not os.path.exists(file_path):
            return ""

        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                lines = f.readlines()
        except (FileNotFoundError, PermissionError, OSError):
            return ""

        total_lines = len(lines)
        if total_lines == 0:
            return ""

        start = max(1, line_num - context)
        end = min(total_lines, line_num + context)

        snippet_lines: list[str] = []
        for i in range(start, end + 1):
            marker = ">" if i == line_num else " "
            content = lines[i - 1].rstrip("\r\n")
            snippet_lines.append(f"{marker} {i:4d} | {content}")

        return "\n".join(snippet_lines)

    def _deduplicate_and_sort(self, findings: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """
        Deduplicate findings by (file, line, rule) and sort by severity (critical first),
        then file, then line.
        """
        dedup_map: dict[tuple[str, int, str], dict[str, Any]] = {}

        for finding in findings:
            file_key = str(finding.get("file", "")).replace("\\", "/")
            line_key = int(finding.get("line") or 1)
            rule_key = str(finding.get("rule", "")).strip().lower()
            key = (file_key, line_key, rule_key)

            if key not in dedup_map:
                dedup_map[key] = finding
            else:
                # Prefer finding with higher severity (lower weight)
                existing_sev = self.SEVERITY_ORDER.get(str(dedup_map[key].get("severity", "")).lower(), 99)
                new_sev = self.SEVERITY_ORDER.get(str(finding.get("severity", "")).lower(), 99)
                if new_sev < existing_sev:
                    dedup_map[key] = finding

        def sort_key(item: dict[str, Any]) -> tuple[int, str, int]:
            sev_rank = self.SEVERITY_ORDER.get(str(item.get("severity", "")).lower(), 99)
            file_name = str(item.get("file", ""))
            line_num = int(item.get("line") or 1)
            return (sev_rank, file_name, line_num)

        return sorted(dedup_map.values(), key=sort_key)


def scan_directory(path: str) -> list[dict[str, Any]]:
    """
    Convenience wrapper to scan a directory using CodeScanner.

    Args:
        path: Path of the directory to scan.

    Returns:
        Deduplicated, sorted list of code review findings.
    """
    scanner = CodeScanner()
    return scanner.scan_directory(path)
