"""
Bandit subprocess wrapper for Python security scanning.

Executes `bandit -f json -q <file>` and maps security findings to the common
review finding format.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from typing import Any


class BanditAnalyzer:
    """Analyzer running Bandit security checks via subprocess."""

    def __init__(self) -> None:
        pass

    def analyze(self, file_path: str, base_dir: str | None = None) -> list[dict[str, Any]]:
        """
        Analyze a file using Bandit and return mapped security findings.

        Args:
            file_path: Path to the Python file.
            base_dir: Optional base directory for computing relative paths.

        Returns:
            List of findings conforming to the common finding format.
        """
        if not os.path.exists(file_path):
            return []

        rel_file = self._resolve_rel_file(file_path, base_dir)

        raw_output = self._run_bandit_subprocess(file_path)
        if not raw_output:
            return []

        try:
            data = json.loads(raw_output)
            if not isinstance(data, dict):
                return []
        except (json.JSONDecodeError, UnicodeDecodeError):
            return []

        results = data.get("results", [])
        if not isinstance(results, list):
            return []

        findings: list[dict[str, Any]] = []
        for res in results:
            if not isinstance(res, dict):
                continue

            test_id = str(res.get("test_id", "")).strip()
            test_name = str(res.get("test_name", "")).strip()
            issue_text = str(res.get("issue_text", "")).strip()
            line = res.get("line_number") or 1

            category = self._map_category(test_id)
            severity = self._map_severity(str(res.get("issue_severity", "")))

            rule_display = test_name.replace("_", " ").title() if test_name else (test_id or "Bandit Finding")

            findings.append({
                "file": rel_file,
                "line": int(line),
                "category": category,
                "severity": severity,
                "rule": rule_display,
                "message": issue_text or f"Security issue detected by Bandit ({test_id}).",
            })

        return findings

    def _run_bandit_subprocess(self, file_path: str) -> str | None:
        """Execute bandit and return stdout JSON string, or None if failed/absent."""
        cmd_candidates = [
            ["bandit", "-f", "json", "-q", file_path],
            [sys.executable, "-m", "bandit", "-f", "json", "-q", file_path],
        ]

        for cmd in cmd_candidates:
            try:
                proc = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    check=False,
                    timeout=30,
                )
                if proc.stdout and "results" in proc.stdout:
                    return proc.stdout
                if proc.returncode in (0, 1) and proc.stdout.strip():
                    return proc.stdout
            except (FileNotFoundError, PermissionError, subprocess.SubprocessError):
                continue
            except Exception:
                continue

        return None

    def _map_category(self, test_id: str) -> str:
        """
        Map category based on bandit test_id prefix:
        - B1xx: injection → security
        - B2xx: misc → bug
        - B3xx: blacklist calls → security
        - B4xx: blacklist imports → security
        - B5xx: crypto → security
        - B6xx: injection → security
        - B7xx: xml → security
        """
        prefix = test_id[:2].upper()
        if prefix == "B1":
            return "security"
        if prefix == "B2":
            return "bug"
        if prefix in ("B3", "B4", "B5", "B6", "B7"):
            return "security"
        return "security"

    def _map_severity(self, issue_severity: str) -> str:
        """
        Set severity: HIGH→critical, MEDIUM→high, LOW→medium
        """
        sev = issue_severity.upper().strip()
        if sev == "HIGH":
            return "critical"
        if sev == "MEDIUM":
            return "high"
        if sev == "LOW":
            return "medium"
        return "medium"

    def _resolve_rel_file(self, file_path: str, base_dir: str | None = None) -> str:
        """Resolve file path to a relative representation."""
        if base_dir:
            try:
                rel = os.path.relpath(file_path, base_dir)
                return rel.replace("\\", "/")
            except ValueError:
                pass
        return os.path.basename(file_path)
