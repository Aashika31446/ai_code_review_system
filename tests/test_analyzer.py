"""
Unit tests for the Python Code Analysis Engine.

Validates ASTAnalyzer, RuffAnalyzer, BanditAnalyzer, RadonAnalyzer, and CodeScanner.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
import pytest

# Ensure analyzer modules can be imported directly
current_dir = Path(__file__).resolve().parent
package_dir = current_dir.parent / "code-analyzer"
if str(package_dir) not in sys.path:
    sys.path.insert(0, str(package_dir))

from ast_analyzer import ASTAnalyzer
from ruff_analyzer import RuffAnalyzer
from bandit_analyzer import BanditAnalyzer
from radon_analyzer import RadonAnalyzer
from scanner import CodeScanner, scan_directory

VULNERABLE_FILE = str(package_dir / "test_files" / "sample_vulnerable.py")
CLEAN_FILE = str(package_dir / "test_files" / "sample_clean.py")
TEST_FILES_DIR = str(package_dir / "test_files")


def test_ast_analyzer_detects_eval():
    """Verify ASTAnalyzer detects eval() call with critical severity."""
    analyzer = ASTAnalyzer()
    findings = analyzer.analyze(VULNERABLE_FILE)
    eval_findings = [
        f for f in findings
        if f["category"] == "security" and f["severity"] == "critical" and "eval" in f["message"].lower()
    ]
    assert len(eval_findings) >= 1
    assert eval_findings[0]["rule"] == "Eval/Exec Usage"
    assert eval_findings[0]["line"] >= 1


def test_ast_analyzer_detects_hardcoded_password():
    """Verify ASTAnalyzer detects hardcoded password/secret assignments."""
    analyzer = ASTAnalyzer()
    findings = analyzer.analyze(VULNERABLE_FILE)
    secret_findings = [
        f for f in findings
        if f["category"] == "security" and f["severity"] == "high" and f["rule"] == "Hardcoded Secret"
    ]
    assert len(secret_findings) >= 1
    pw_matches = [f for f in secret_findings if "password" in f["message"].lower()]
    assert len(pw_matches) >= 1


def test_ast_analyzer_detects_bare_except():
    """Verify ASTAnalyzer detects bare except: clauses."""
    analyzer = ASTAnalyzer()
    findings = analyzer.analyze(VULNERABLE_FILE)
    bare_excepts = [
        f for f in findings
        if f["category"] == "bug" and f["severity"] == "medium" and f["rule"] == "Bare Except"
    ]
    assert len(bare_excepts) >= 1
    assert "bare 'except:'" in bare_excepts[0]["message"].lower()


def test_ast_analyzer_detects_mutable_default():
    """Verify ASTAnalyzer detects mutable default arguments."""
    analyzer = ASTAnalyzer()
    findings = analyzer.analyze(VULNERABLE_FILE)
    mutable_defaults = [f for f in findings if f["rule"] == "Mutable Default Argument"]
    assert len(mutable_defaults) >= 1
    assert mutable_defaults[0]["category"] == "bug"
    assert mutable_defaults[0]["severity"] == "medium"


def test_ast_analyzer_detects_comparison_to_none():
    """Verify ASTAnalyzer detects '== None' comparisons."""
    analyzer = ASTAnalyzer()
    findings = analyzer.analyze(VULNERABLE_FILE)
    none_comparisons = [f for f in findings if f["rule"] == "Comparison to None"]
    assert len(none_comparisons) >= 1
    assert none_comparisons[0]["category"] == "style"
    assert none_comparisons[0]["severity"] == "low"


def test_ast_analyzer_detects_unused_import():
    """Verify ASTAnalyzer detects unused imports."""
    analyzer = ASTAnalyzer()
    findings = analyzer.analyze(VULNERABLE_FILE)
    unused_imports = [f for f in findings if f["rule"] == "Unused Import"]
    assert len(unused_imports) >= 1
    assert unused_imports[0]["category"] == "style"
    assert unused_imports[0]["severity"] == "low"


def test_ast_analyzer_detects_long_function():
    """Verify ASTAnalyzer detects functions exceeding 50 lines."""
    analyzer = ASTAnalyzer()
    findings = analyzer.analyze(VULNERABLE_FILE)
    long_functions = [f for f in findings if f["rule"] == "Long Function"]
    assert len(long_functions) >= 1
    assert "process_data_pipeline" in long_functions[0]["message"]
    assert long_functions[0]["severity"] == "medium"


def test_ast_analyzer_handles_syntax_error(tmp_path):
    """Verify ASTAnalyzer catches SyntaxError and returns a critical finding."""
    bad_syntax_file = tmp_path / "broken.py"
    bad_syntax_file.write_text("def broken_syntax(:\n    pass\n")

    analyzer = ASTAnalyzer()
    findings = analyzer.analyze(str(bad_syntax_file))
    assert len(findings) == 1
    assert findings[0]["rule"] == "Syntax Error"
    assert findings[0]["severity"] == "critical"
    assert findings[0]["category"] == "bug"


def test_scanner_returns_list():
    """Verify CodeScanner.scan_file returns a list."""
    scanner = CodeScanner()
    findings = scanner.scan_file(VULNERABLE_FILE)
    assert isinstance(findings, list)
    assert len(findings) > 0


def test_finding_format_is_valid():
    """Verify every finding conforms strictly to the common finding format."""
    valid_categories = {"security", "bug", "style", "complexity", "maintainability"}
    valid_severities = {"critical", "high", "medium", "low"}

    scanner = CodeScanner()
    findings = scanner.scan_file(VULNERABLE_FILE)

    assert len(findings) > 0
    for finding in findings:
        assert isinstance(finding, dict), f"Finding must be dict: {finding}"
        assert "file" in finding and isinstance(finding["file"], str) and finding["file"]
        assert "line" in finding and isinstance(finding["line"], int) and finding["line"] >= 1
        assert "category" in finding and finding["category"] in valid_categories, (
            f"Invalid category: {finding.get('category')}"
        )
        assert "severity" in finding and finding["severity"] in valid_severities, (
            f"Invalid severity: {finding.get('severity')}"
        )
        assert "rule" in finding and isinstance(finding["rule"], str) and finding["rule"]
        assert "message" in finding and isinstance(finding["message"], str) and finding["message"]


def test_scan_directory():
    """Verify directory scanning finds Python files and aggregates findings."""
    scanner = CodeScanner()
    findings = scanner.scan_directory(TEST_FILES_DIR)
    assert isinstance(findings, list)
    assert len(findings) > 0

    wrapper_findings = scan_directory(TEST_FILES_DIR)
    assert isinstance(wrapper_findings, list)
    assert len(wrapper_findings) == len(findings)


def test_analyzers_handle_missing_file_gracefully():
    """Verify all analyzers handle FileNotFoundError and PermissionError without crashing."""
    non_existent = "non_existent_file_path_xyz.py"
    ast_an = ASTAnalyzer()
    ruff_an = RuffAnalyzer()
    bandit_an = BanditAnalyzer()
    radon_an = RadonAnalyzer()
    scanner = CodeScanner()

    assert ast_an.analyze(non_existent) == []
    assert ruff_an.analyze(non_existent) == []
    assert bandit_an.analyze(non_existent) == []
    assert radon_an.analyze(non_existent) == []
    assert scanner.scan_file(non_existent) == []
    assert scanner.scan_directory("non_existent_directory_xyz") == []


def test_code_snippet_extraction():
    """Verify code snippet retrieval with context lines and marker."""
    scanner = CodeScanner()
    snippet = scanner.get_code_snippet(VULNERABLE_FILE, line_num=15, context=2)
    assert isinstance(snippet, str)
    assert len(snippet) > 0
    assert ">   15 |" in snippet
    assert "14 |" in snippet
    assert "16 |" in snippet


def test_clean_file_has_minimal_findings():
    """Verify sample_clean.py produces minimal/no severe findings."""
    scanner = CodeScanner()
    findings = scanner.scan_file(CLEAN_FILE)
    critical_or_high = [f for f in findings if f["severity"] in ("critical", "high")]
    assert len(critical_or_high) == 0
