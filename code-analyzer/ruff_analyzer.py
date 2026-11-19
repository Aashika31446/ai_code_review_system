"""
Ruff subprocess wrapper for static code analysis.

Executes `ruff check --output-format json` on Python files and maps the
diagnostics to the common review finding format.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from typing import Any


class RuffAnalyzer:
    """Analyzer running Ruff via subprocess."""

    def __init__(self) -> None:
        pass

    def analyze(self, file_path: str, base_dir: str | None = None) -> list[dict[str, Any]]:
        """
        Analyze a file using Ruff and return mapped findings.

        Args:
            file_path: Path to the Python file.
            base_dir: Optional base directory for computing relative paths.

        Returns:
            List of findings conforming to the common finding format.
        """
        if not os.path.exists(file_path):
            return []

        rel_file = self._resolve_rel_file(file_path, base_dir)

        # Attempt to run ruff CLI or via python -m ruff
        raw_output = self._run_ruff_subprocess(file_path)
        if raw_output is None:
            # Ruff is not installed or execution failed
            return []

        try:
            items = json.loads(raw_output)
            if not isinstance(items, list):
                return []
        except (json.JSONDecodeError, UnicodeDecodeError):
            return []

        findings: list[dict[str, Any]] = []
        for item in items:
            if not isinstance(item, dict):
                continue

            code = str(item.get("code") or "")
            message = str(item.get("message") or "")
            line = item.get("location", {}).get("row") or item.get("line") or 1

            severity = self._map_severity(code)
            category = self._map_category(code, severity, message)

            findings.append({
                "file": rel_file,
                "line": int(line),
                "category": category,
                "severity": severity,
                "rule": code or "Ruff Finding",
                "message": message,
            })

        return findings

    def _run_ruff_subprocess(self, file_path: str) -> str | None:
        """Execute ruff and return stdout string, or None if unavailable."""
        cmd_candidates = [
            ["ruff", "check", "--output-format", "json", file_path],
            [sys.executable, "-m", "ruff", "check", "--output-format", "json", file_path],
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
                # Ruff exits with 0 on no findings, 1 when findings exist
                if proc.stdout and proc.stdout.strip().startswith("["):
                    return proc.stdout
                if proc.returncode in (0, 1):
                    return proc.stdout
            except (FileNotFoundError, PermissionError, subprocess.SubprocessError):
                continue
            except Exception:
                continue

        return None

    def _map_severity(self, code: str) -> str:
        """
        Map Ruff diagnostic code to standard severity level:
        - E9xx (syntax errors): critical
        - F401 (unused imports): low
        - F811 (redefinition): medium
        - F841 (unused variable): low
        - E501 (line too long): low
        - W6xx (deprecated): medium
        - E711, E712 (comparison): low
        - Bxxx (bugbear): high
        - Sxxx (security): high
        - Default: medium
        """
        if code.startswith("E9"):
            return "critical"
        if code == "F401":
            return "low"
        if code == "F811":
            return "medium"
        if code == "F841":
            return "low"
        if code == "E501":
            return "low"
        if code.startswith("W6"):
            return "medium"
        if code in ("E711", "E712"):
            return "low"
        if code.startswith("B"):
            return "high"
        if code.startswith("S"):
            return "high"
        return "medium"

    def _map_category(self, code: str, severity: str, message: str) -> str:
        """Map code and metadata to common category."""
        if code.startswith("S"):
            return "security"
        if code.startswith("C") or code.startswith("PLR09") or "complexity" in message.lower():
            return "complexity"
        if code.startswith("W6") or code.startswith("PLR"):
            return "maintainability"
        if code.startswith("B") or code.startswith("E9") or code.startswith("F8"):
            return "bug"
        if code.startswith("E") or code.startswith("W") or code in ("F401", "F841"):
            return "style"
        return "bug" if severity in ("critical", "high") else "style"

    def _resolve_rel_file(self, file_path: str, base_dir: str | None = None) -> str:
        """Resolve file path to a relative representation."""
        if base_dir:
            try:
                rel = os.path.relpath(file_path, base_dir)
                return rel.replace("\\", "/")
            except ValueError:
                pass
        return os.path.basename(file_path)
