"""Unit tests for the AI Code Review Engine."""

import importlib
import json
import os
import sys
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Ensure ai-engine directory is in sys.path for direct imports
AI_ENGINE_DIR = Path(__file__).resolve().parent.parent / "ai-engine"
if str(AI_ENGINE_DIR) not in sys.path:
    sys.path.insert(0, str(AI_ENGINE_DIR))

from ai_reviewer import AIReviewer, review_finding
from prompts import (
    BATCH_REVIEW_PROMPT_TEMPLATE,
    REVIEW_PROMPT_TEMPLATE,
    SYSTEM_PROMPT,
)
from schemas import AIReviewError, AIReviewOutput, FindingInput


@pytest.fixture
def sample_finding():
    """Standard security finding fixture."""
    return {
        "file": "app/auth.py",
        "line": 42,
        "category": "security",
        "severity": "high",
        "rule": "sql-injection",
        "message": "User input directly concatenated into SQL query string.",
        "code_snippet": "query = f\"SELECT * FROM users WHERE id = '{user_id}'\"\ncursor.execute(query)",
    }


def test_fallback_review_when_no_api_key(sample_finding, monkeypatch):
    """Test that reviewer provides intelligent fallback when no API key is set."""
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    reviewer = AIReviewer(provider="gemini", api_key="")
    result = reviewer.review_finding(sample_finding)

    assert isinstance(result, dict)
    assert "explanation" in result
    assert "impact" in result
    assert "suggested_fix" in result
    assert "fixed_code" in result

    # Validate against Pydantic schema
    validated = AIReviewOutput(**result)
    assert validated.explanation
    assert "security" in validated.explanation.lower() or "sql-injection" in validated.explanation.lower()
    assert "exploit" in validated.impact.lower() or "unauthorized" in validated.impact.lower()

    # Test category-specific fallbacks
    categories = [
        ("bug", "bug"),
        ("complexity", "complexity"),
        ("style", "style"),
    ]
    for cat, keyword in categories:
        finding = dict(sample_finding)
        finding["category"] = cat
        res = reviewer.review_finding(finding)
        assert keyword in res["explanation"].lower() or keyword in res["impact"].lower()


def test_parse_valid_json_response():
    """Test parsing a clean, raw JSON string from LLM."""
    reviewer = AIReviewer(api_key="dummy_key")
    raw_json = json.dumps({
        "explanation": "Direct string interpolation in SQL queries allows SQL injection attacks.",
        "impact": "Attackers can bypass authentication and extract or modify sensitive records.",
        "suggested_fix": "Use parameterized queries or prepared statements instead of format strings.",
        "fixed_code": "cursor.execute('SELECT * FROM users WHERE id = %s', (user_id,))",
    })

    parsed = reviewer._parse_response(raw_json)

    assert isinstance(parsed, dict)
    assert parsed["explanation"] == "Direct string interpolation in SQL queries allows SQL injection attacks."
    assert "authentication" in parsed["impact"]
    assert "parameterized" in parsed["suggested_fix"].lower()
    assert "cursor.execute" in parsed["fixed_code"]

    # Verify Pydantic schema validation
    output_model = AIReviewOutput(**parsed)
    assert output_model.explanation == parsed["explanation"]


def test_parse_json_in_markdown_block():
    """Test parsing JSON enclosed within markdown code fences (```json and ```)."""
    reviewer = AIReviewer(api_key="dummy_key")

    markdown_payload = """
Here is the review result:
```json
{
  "explanation": "Hardcoded secret key found in source code.",
  "impact": "Anyone with read access to the repo can decrypt user sessions.",
  "suggested_fix": "Read the secret key from an environment variable.",
  "fixed_code": "secret_key = os.environ.get('SECRET_KEY')"
}
```
"""
    parsed = reviewer._parse_response(markdown_payload)
    assert parsed["explanation"] == "Hardcoded secret key found in source code."
    assert "environment variable" in parsed["suggested_fix"]
    assert parsed["fixed_code"] == "secret_key = os.environ.get('SECRET_KEY')"

    # Test without language tag in fence
    plain_fence_payload = """
```
{
  "explanation": "Resource leak: file handler not closed.",
  "impact": "File descriptor exhaustion leading to application failure.",
  "suggested_fix": "Use a context manager ('with' statement).",
  "fixed_code": "with open(path, 'r') as f:\\n    data = f.read()"
}
```
"""
    parsed_plain = reviewer._parse_response(plain_fence_payload)
    assert parsed_plain["explanation"] == "Resource leak: file handler not closed."
    assert "context manager" in parsed_plain["suggested_fix"]


def test_review_finding_returns_valid_schema(sample_finding):
    """Test that top-level review_finding and instance method return a valid schema."""
    # Test top-level helper function
    top_level_result = review_finding(sample_finding)
    assert isinstance(top_level_result, dict)
    model = AIReviewOutput(**top_level_result)
    assert model.explanation
    assert model.impact
    assert model.suggested_fix

    # Test instance with code snippet passed separately
    reviewer = AIReviewer(api_key="")
    finding_no_snippet = dict(sample_finding)
    finding_no_snippet["code_snippet"] = ""

    instance_result = reviewer.review_finding(
        finding_no_snippet,
        code_snippet="password = 'admin123'",
    )
    assert isinstance(instance_result, dict)
    instance_model = AIReviewOutput(**instance_result)
    assert instance_model.explanation
    assert instance_model.suggested_fix


def test_batch_review_fallback(sample_finding):
    """Test batch review when AI is offline, ensuring all items get fallbacks."""
    reviewer = AIReviewer(api_key="")
    findings = [
        dict(sample_finding, rule="rule-1", category="security"),
        dict(sample_finding, rule="rule-2", category="bug"),
        dict(sample_finding, rule="rule-3", category="complexity"),
    ]

    results = reviewer.review_findings_batch(findings)
    assert len(results) == 3
    for res in results:
        assert isinstance(res, dict)
        validated = AIReviewOutput(**res)
        assert validated.explanation
        assert validated.suggested_fix


def test_batch_review_parsing():
    """Test parsing batch response from LLM."""
    reviewer = AIReviewer(api_key="dummy_key")
    raw_batch = """
```json
[
  {
    "finding_id": "0",
    "explanation": "Insecure hash function MD5 used.",
    "impact": "Susceptible to collision attacks.",
    "suggested_fix": "Use SHA-256 or bcrypt instead.",
    "fixed_code": "hashlib.sha256(data).hexdigest()"
  },
  {
    "finding_id": "1",
    "explanation": "Unused import detected.",
    "impact": "Clutters namespace and increases startup time.",
    "suggested_fix": "Remove unused import.",
    "fixed_code": ""
  }
]
```
"""
    findings = [
        {"file": "a.py", "line": 1, "category": "security", "rule": "md5", "message": "Insecure MD5"},
        {"file": "b.py", "line": 2, "category": "style", "rule": "unused-import", "message": "Unused"},
    ]
    parsed = reviewer._parse_batch_response(raw_batch, findings)
    assert len(parsed) == 2
    assert parsed[0]["explanation"] == "Insecure hash function MD5 used."
    assert parsed[1]["explanation"] == "Unused import detected."


def test_prompt_formatting(sample_finding):
    """Test that prompt templates format correctly without formatting errors."""
    prompt = REVIEW_PROMPT_TEMPLATE.format(
        file=sample_finding["file"],
        line=sample_finding["line"],
        severity=sample_finding["severity"],
        category=sample_finding["category"],
        rule=sample_finding["rule"],
        message=sample_finding["message"],
        code_snippet=sample_finding["code_snippet"],
    )
    assert sample_finding["file"] in prompt
    assert sample_finding["rule"] in prompt
    assert "Required JSON Format:" in prompt
    assert SYSTEM_PROMPT


def test_rate_limiting_enforcement():
    """Test that rate limiter enforces minimum delay between calls."""
    reviewer = AIReviewer(rate_limit_delay=0.1)
    reviewer._apply_rate_limit()

    start_time = time.time()
    reviewer._apply_rate_limit()
    elapsed = time.time() - start_time

    assert elapsed >= 0.08  # Tolerant check for 0.1s delay


def test_package_import():
    """Test that package can be imported via importlib."""
    parent_dir = str(AI_ENGINE_DIR.parent)
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)

    pkg = importlib.import_module("ai-engine")
    assert hasattr(pkg, "AIReviewer")
    assert hasattr(pkg, "FindingInput")
    assert hasattr(pkg, "AIReviewOutput")
    assert hasattr(pkg, "AIReviewError")
    assert hasattr(pkg, "review_finding")


def test_call_gemini_mocked(sample_finding):
    """Test full review workflow with mocked Gemini API response."""
    reviewer = AIReviewer(provider="gemini", api_key="valid_gemini_key")

    mock_gemini_response = MagicMock()
    mock_gemini_response.text = json.dumps({
        "explanation": "Gemini: Potential SQL injection found.",
        "impact": "Data compromise risk.",
        "suggested_fix": "Use parameterized queries.",
        "fixed_code": "cursor.execute(query, (user_id,))",
    })

    with patch.object(reviewer, "_call_gemini", return_value=mock_gemini_response.text):
        result = reviewer.review_finding(sample_finding)

        assert result["explanation"] == "Gemini: Potential SQL injection found."
        assert result["impact"] == "Data compromise risk."
        assert "cursor.execute" in result["fixed_code"]


def test_call_openai_mocked(sample_finding):
    """Test full review workflow with mocked OpenAI API response."""
    reviewer = AIReviewer(provider="openai", api_key="valid_openai_key")

    mock_openai_response = json.dumps({
        "explanation": "OpenAI: Insecure direct query interpolation.",
        "impact": "High risk of database breach.",
        "suggested_fix": "Parameterize input values.",
        "fixed_code": "cursor.execute('SELECT * FROM users WHERE id = %s', (user_id,))",
    })

    with patch.object(reviewer, "_call_openai", return_value=mock_openai_response):
        result = reviewer.review_finding(sample_finding)

        assert result["explanation"] == "OpenAI: Insecure direct query interpolation."
        assert result["impact"] == "High risk of database breach."
        assert "cursor.execute" in result["fixed_code"]


def test_call_api_failure_recovers_with_fallback(sample_finding):
    """Test that when an API call raises an exception, the system recovers with fallback without crashing."""
    reviewer = AIReviewer(provider="gemini", api_key="valid_gemini_key")

    with patch.object(reviewer, "_call_gemini", side_effect=Exception("API connection timeout")):
        result = reviewer.review_finding(sample_finding)

        assert isinstance(result, dict)
        assert "explanation" in result
        assert "impact" in result
        assert "suggested_fix" in result
        # Check that error is recorded and scan did not crash
        assert "error" in result
        assert "API connection timeout" in result["error"]

