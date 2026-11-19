"""AI Reviewer Module supporting Google Gemini and OpenAI APIs with intelligent fallbacks."""

import json
import logging
import os
import re
import time
from typing import Any, Dict, List, Optional, Union

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

try:
    import google.generativeai as genai
except ImportError:
    genai = None

try:
    import openai
except ImportError:
    openai = None

try:
    from .prompts import (
        BATCH_REVIEW_PROMPT_TEMPLATE,
        REVIEW_PROMPT_TEMPLATE,
        SYSTEM_PROMPT,
    )
    from .schemas import AIReviewError, AIReviewOutput, FindingInput
except (ImportError, ValueError):
    from prompts import (
        BATCH_REVIEW_PROMPT_TEMPLATE,
        REVIEW_PROMPT_TEMPLATE,
        SYSTEM_PROMPT,
    )
    from schemas import AIReviewError, AIReviewOutput, FindingInput

logger = logging.getLogger(__name__)


class AIReviewer:
    """Main AI Reviewer service supporting Gemini and OpenAI with robust fallbacks."""

    def __init__(
        self,
        provider: Optional[str] = None,
        api_key: Optional[str] = None,
        rate_limit_delay: float = 0.5,
    ) -> None:
        """Initialize AIReviewer with provider configuration and API keys.

        Args:
            provider: 'gemini' or 'openai'. Defaults to AI_PROVIDER env var or 'gemini'.
            api_key: API key for the chosen provider. Defaults to GEMINI_API_KEY/GOOGLE_API_KEY or OPENAI_API_KEY.
            rate_limit_delay: Minimum delay in seconds between consecutive AI requests (default: 0.5s).
        """
        raw_provider = provider or os.getenv("AI_PROVIDER", "gemini")
        self.provider = raw_provider.lower().strip()
        self.rate_limit_delay = rate_limit_delay
        self._last_call_time = 0.0

        # Load API keys based on provider
        if self.provider == "openai":
            self.api_key = api_key or os.getenv("OPENAI_API_KEY", "")
            self._openai_client = None
            if self.api_key and openai is not None:
                try:
                    self._openai_client = openai.OpenAI(api_key=self.api_key)
                except Exception as exc:
                    logger.warning("Failed to initialize OpenAI client: %s", exc)
        else:
            # Default to gemini
            self.provider = "gemini"
            self.api_key = api_key or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY", "")
            self._gemini_model = None
            if self.api_key and genai is not None:
                try:
                    genai.configure(api_key=self.api_key)
                    # Use gemini-1.5-flash (fast and cost-effective)
                    self._gemini_model = genai.GenerativeModel(
                        model_name="gemini-1.5-flash",
                        system_instruction=SYSTEM_PROMPT,
                    )
                except TypeError:
                    # Older google-generativeai may not support system_instruction in constructor
                    try:
                        self._gemini_model = genai.GenerativeModel(model_name="gemini-1.5-flash")
                    except Exception as exc:
                        logger.warning("Failed to initialize Gemini model: %s", exc)
                except Exception as exc:
                    logger.warning("Failed to initialize Gemini model: %s", exc)

    def _apply_rate_limit(self) -> None:
        """Enforce rate limiting delay between consecutive API calls."""
        elapsed = time.time() - self._last_call_time
        if elapsed < self.rate_limit_delay:
            time.sleep(self.rate_limit_delay - elapsed)
        self._last_call_time = time.time()

    def _normalize_finding(
        self,
        finding: Union[Dict[str, Any], FindingInput],
        code_snippet: str = "",
    ) -> FindingInput:
        """Normalize finding input into a FindingInput model."""
        if isinstance(finding, FindingInput):
            item = finding
        elif isinstance(finding, dict):
            # Shallow copy and ensure fields exist
            data = dict(finding)
            if code_snippet and not data.get("code_snippet"):
                data["code_snippet"] = code_snippet
            if "line" in data:
                try:
                    data["line"] = int(data["line"])
                except (ValueError, TypeError):
                    data["line"] = 1
            item = FindingInput(**data)
        else:
            raise ValueError(f"Unsupported finding type: {type(finding)}")

        if code_snippet and not item.code_snippet:
            item.code_snippet = code_snippet
        return item

    def review_finding(
        self,
        finding: Union[Dict[str, Any], FindingInput],
        code_snippet: str = "",
    ) -> Dict[str, Any]:
        """Review an individual code finding and return an AI analysis or fallback.

        Args:
            finding: Finding metadata dictionary or FindingInput instance.
            code_snippet: Optional code snippet string if not included in finding.

        Returns:
            Dictionary matching AIReviewOutput schema or AIReviewError fallback.
        """
        try:
            norm_finding = self._normalize_finding(finding, code_snippet)
            finding_dict = norm_finding.model_dump()
        except Exception as exc:
            logger.error("Invalid finding input schema: %s", exc)
            fallback = self._get_fallback_review(finding if isinstance(finding, dict) else {})
            fallback["error"] = f"Invalid finding input: {exc}"
            return fallback

        # If no API key configured or library missing, immediately use fallback
        if not self.api_key:
            logger.info("AI API key not configured. Using intelligent fallback review.")
            return self._get_fallback_review(finding_dict)

        prompt = REVIEW_PROMPT_TEMPLATE.format(
            file=finding_dict.get("file", "unknown"),
            line=finding_dict.get("line", 1),
            severity=finding_dict.get("severity", "medium"),
            category=finding_dict.get("category", "general"),
            rule=finding_dict.get("rule", "general-rule"),
            message=finding_dict.get("message", "Issue detected"),
            code_snippet=finding_dict.get("code_snippet", "") or "(No snippet provided)",
        )

        try:
            self._apply_rate_limit()

            if self.provider == "openai":
                raw_response = self._call_openai(prompt)
            else:
                raw_response = self._call_gemini(prompt)

            return self._parse_response(raw_response)

        except Exception as exc:
            logger.warning("AI provider (%s) call failed: %s. Using fallback.", self.provider, exc)
            fallback = self._get_fallback_review(finding_dict)
            fallback["error"] = str(exc)
            return fallback

    def review_findings_batch(
        self,
        findings: List[Union[Dict[str, Any], FindingInput]],
        code_snippets: Optional[Dict[str, str]] = None,
    ) -> List[Dict[str, Any]]:
        """Review multiple findings in a batch.

        Args:
            findings: List of finding dictionaries or FindingInput instances.
            code_snippets: Optional mapping of finding IDs/indices to code snippets.

        Returns:
            List of review result dictionaries matching AIReviewOutput.
        """
        if not findings:
            return []

        code_snippets = code_snippets or {}
        normalized_list: List[Dict[str, Any]] = []

        for idx, item in enumerate(findings):
            snippet = ""
            key_idx = str(idx)
            if key_idx in code_snippets:
                snippet = code_snippets[key_idx]
            elif isinstance(item, dict):
                item_id = str(item.get("id", item.get("rule", idx)))
                if item_id in code_snippets:
                    snippet = code_snippets[item_id]

            try:
                norm = self._normalize_finding(item, snippet)
                normalized_list.append(norm.model_dump())
            except Exception:
                normalized_list.append(item if isinstance(item, dict) else {})

        # If no API key or provider unavailable, return individual fallbacks
        if not self.api_key:
            return [self._get_fallback_review(f) for f in normalized_list]

        # Construct batch prompt
        findings_blocks = []
        for idx, f in enumerate(normalized_list):
            block = (
                f"--- Finding ID: {idx} ---\n"
                f"File: {f.get('file', 'unknown')}\n"
                f"Line: {f.get('line', 1)}\n"
                f"Severity: {f.get('severity', 'medium')}\n"
                f"Category: {f.get('category', 'general')}\n"
                f"Rule: {f.get('rule', 'unknown')}\n"
                f"Message: {f.get('message', '')}\n"
                f"Code Snippet:\n{f.get('code_snippet', '') or '(None)'}\n"
            )
            findings_blocks.append(block)

        batch_prompt = BATCH_REVIEW_PROMPT_TEMPLATE.format(
            findings_block="\n".join(findings_blocks)
        )

        try:
            self._apply_rate_limit()

            if self.provider == "openai":
                raw_response = self._call_openai(batch_prompt)
            else:
                raw_response = self._call_gemini(batch_prompt)

            return self._parse_batch_response(raw_response, normalized_list)

        except Exception as exc:
            logger.warning("Batch AI review failed: %s. Falling back to per-finding review.", exc)
            results = []
            for item in normalized_list:
                fb = self._get_fallback_review(item)
                fb["error"] = str(exc)
                results.append(fb)
            return results

    def _call_gemini(self, prompt: str) -> str:
        """Call Google Gemini API using gemini-1.5-flash."""
        if genai is None:
            raise RuntimeError("The 'google-generativeai' package is not installed.")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is not configured.")

        # Ensure model is ready
        if self._gemini_model is None:
            genai.configure(api_key=self.api_key)
            try:
                self._gemini_model = genai.GenerativeModel(
                    model_name="gemini-1.5-flash",
                    system_instruction=SYSTEM_PROMPT,
                )
            except TypeError:
                self._gemini_model = genai.GenerativeModel(model_name="gemini-1.5-flash")

        # In case system_instruction was not supported, prepend it
        effective_prompt = prompt
        if getattr(self._gemini_model, "_system_instruction", None) is None:
            effective_prompt = f"{SYSTEM_PROMPT}\n\n{prompt}"

        response = self._gemini_model.generate_content(effective_prompt)
        if not response or not hasattr(response, "text") or response.text is None:
            raise RuntimeError("Gemini returned an empty or invalid response.")
        return response.text

    def _call_openai(self, prompt: str) -> str:
        """Call OpenAI API using gpt-4o-mini."""
        if openai is None:
            raise RuntimeError("The 'openai' package is not installed.")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY is not configured.")

        if self._openai_client is None:
            self._openai_client = openai.OpenAI(api_key=self.api_key)

        response = self._openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0.2,
        )

        choices = getattr(response, "choices", [])
        if not choices or not choices[0].message.content:
            raise RuntimeError("OpenAI returned an empty response.")
        return choices[0].message.content

    def _parse_response(self, response_text: str) -> Dict[str, Any]:
        """Extract JSON from response, validate with AIReviewOutput, and return dict."""
        cleaned_text = response_text.strip()

        # Handle markdown code blocks e.g. ```json ... ``` or ``` ... ```
        fence_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", cleaned_text, re.IGNORECASE)
        if fence_match:
            cleaned_text = fence_match.group(1).strip()

        # If there are stray leading or trailing characters, extract outer JSON object
        if not (cleaned_text.startswith("{") and cleaned_text.endswith("}")):
            obj_match = re.search(r"\{[\s\S]*\}", cleaned_text)
            if obj_match:
                cleaned_text = obj_match.group(0)

        data = json.loads(cleaned_text)
        if not isinstance(data, dict):
            raise ValueError(f"Expected JSON object in response, got: {type(data)}")

        # Validate with AIReviewOutput Pydantic model
        validated = AIReviewOutput(
            explanation=str(data.get("explanation", "")).strip(),
            impact=str(data.get("impact", "")).strip(),
            suggested_fix=str(data.get("suggested_fix", "")).strip(),
            fixed_code=str(data.get("fixed_code", "")).strip(),
        )
        return validated.model_dump()

    def _parse_batch_response(
        self,
        response_text: str,
        findings: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Parse batch JSON array response into individual review dictionaries."""
        cleaned_text = response_text.strip()

        fence_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", cleaned_text, re.IGNORECASE)
        if fence_match:
            cleaned_text = fence_match.group(1).strip()

        if not (cleaned_text.startswith("[") and cleaned_text.endswith("]")):
            arr_match = re.search(r"\[[\s\S]*\]", cleaned_text)
            if arr_match:
                cleaned_text = arr_match.group(0)

        data_array = json.loads(cleaned_text)
        if not isinstance(data_array, list):
            raise ValueError("Expected JSON array in batch response.")

        # Map results back to findings
        results: List[Dict[str, Any]] = []
        for idx, finding in enumerate(findings):
            matched = None
            if idx < len(data_array):
                matched = data_array[idx]

            # Try to match by finding_id if available
            for candidate in data_array:
                if isinstance(candidate, dict) and str(candidate.get("finding_id")) == str(idx):
                    matched = candidate
                    break

            if isinstance(matched, dict):
                try:
                    review = AIReviewOutput(
                        explanation=str(matched.get("explanation", "")).strip(),
                        impact=str(matched.get("impact", "")).strip(),
                        suggested_fix=str(matched.get("suggested_fix", "")).strip(),
                        fixed_code=str(matched.get("fixed_code", "")).strip(),
                    ).model_dump()
                    results.append(review)
                    continue
                except Exception:
                    pass

            # If matching or parsing failed for this item, use fallback
            results.append(self._get_fallback_review(finding))

        return results

    def _get_fallback_review(self, finding: Dict[str, Any]) -> Dict[str, Any]:
        """Return an intelligent fallback review based on finding category and rule."""
        category = str(finding.get("category", "")).lower().strip()
        rule = str(finding.get("rule", "Unknown rule")).strip()
        message = str(finding.get("message", "Static analysis issue detected.")).strip()
        snippet = str(finding.get("code_snippet", "")).strip()

        if "security" in category:
            explanation = (
                f"Security finding ({rule}): {message} "
                "This issue indicates potentially unsafe handling of data, sensitive credentials, or insecure operations."
            )
            impact = (
                "Unmitigated security vulnerabilities can be exploited to gain unauthorized access, "
                "leak confidential data, execute unauthorized commands, or bypass authentication controls."
            )
            suggested_fix = (
                "Sanitize and validate all untrusted inputs, replace insecure functions with hardened APIs, "
                "and enforce strict authentication and least-privilege authorization policies."
            )
            fixed_code = (
                f"# TODO: Review security issue in rule '{rule}'\n"
                f"# Ensure input sanitization and secure API usage\n{snippet}"
                if snippet else "# Use secure library alternatives and sanitize inputs"
            )

        elif "bug" in category:
            explanation = (
                f"Functional bug identified ({rule}): {message} "
                "This pattern frequently produces unexpected runtime exceptions, null pointer errors, or invalid states."
            )
            impact = (
                "Bugs of this nature can lead to application crashes, data corruption, broken user workflows, "
                "and degraded system reliability."
            )
            suggested_fix = (
                "Inspect boundary conditions, verify variable initialization and null/None checks, "
                "and add automated unit tests asserting proper error handling."
            )
            fixed_code = (
                f"# TODO: Fix potential bug in rule '{rule}'\n{snippet}"
                if snippet else "# Add appropriate guard checks and error handling"
            )

        elif "complexity" in category:
            explanation = (
                f"Complexity warning ({rule}): {message} "
                "The code exhibits excessive cognitive load, nested conditionals, or overly long execution paths."
            )
            impact = (
                "High cyclomatic complexity significantly increases defect probability, slows down onboarding, "
                "and makes future modifications error-prone."
            )
            suggested_fix = (
                "Decompose complex procedures into smaller, focused helper functions adhering to the single responsibility principle."
            )
            fixed_code = (
                f"# TODO: Refactor and extract helper functions for rule '{rule}'\n{snippet}"
                if snippet else "# Break down complex function into smaller single-purpose functions"
            )

        elif "style" in category:
            explanation = (
                f"Style convention discrepancy ({rule}): {message} "
                "The code deviates from standard formatting or project-wide stylistic guidelines."
            )
            impact = (
                "Inconsistent code style impedes readability and increases friction during collaborative peer reviews."
            )
            suggested_fix = (
                "Format code according to project guidelines using automated linters and code formatters."
            )
            fixed_code = snippet if snippet else "# Format according to style guide"

        else:
            explanation = (
                f"Code review advisory ({rule}): {message} "
                "Static analysis flagged this section for manual inspection and improvement."
            )
            impact = (
                "Addressing this issue enhances overall software quality, robustness, and maintainability."
            )
            suggested_fix = (
                "Evaluate the code against best practices and verify with unit tests."
            )
            fixed_code = snippet if snippet else "# Apply recommended refactoring"

        return AIReviewOutput(
            explanation=explanation,
            impact=impact,
            suggested_fix=suggested_fix,
            fixed_code=fixed_code,
        ).model_dump()


def review_finding(finding: Dict[str, Any], code_snippet: str = "") -> Dict[str, Any]:
    """Top-level convenience function to review an individual code finding.

    Args:
        finding: Dictionary containing finding details (file, line, category, severity, rule, message).
        code_snippet: Optional source code snippet associated with the finding.

    Returns:
        Dictionary matching AIReviewOutput schema or AIReviewError fallback.
    """
    reviewer = AIReviewer()
    return reviewer.review_finding(finding=finding, code_snippet=code_snippet)
