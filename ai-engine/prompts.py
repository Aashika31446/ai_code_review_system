"""Prompt templates and system prompts for the AI Review Engine."""

SYSTEM_PROMPT = (
    "You are an expert code reviewer and security analyst. "
    "You analyze code findings and provide clear, actionable explanations. "
    "Always respond with valid JSON."
)

REVIEW_PROMPT_TEMPLATE = """Analyze the following code finding and code snippet. Provide a comprehensive, actionable review in JSON format.

### Finding Details:
- File: {file}
- Line: {line}
- Severity: {severity}
- Category: {category}
- Rule: {rule}
- Message: {message}

### Code Snippet:
```
{code_snippet}
```

### Instructions:
1. Explain the underlying issue clearly in plain English (keep explanation under 150 words).
2. Describe the potential operational or security impact if exploited or left unaddressed (keep impact under 100 words).
3. Provide a clear, textual explanation of the suggested fix.
4. Provide the complete fixed code snippet that safely and correctly resolves the issue.
5. Your response must be strictly valid JSON matching the format below, with no surrounding commentary or unescaped text.

### Required JSON Format:
{{
  "explanation": "Plain-English explanation under 150 words",
  "impact": "Potential impact if exploited or ignored under 100 words",
  "suggested_fix": "Textual suggestion explaining how to fix the issue",
  "fixed_code": "Fixed code snippet resolving the issue"
}}
"""

BATCH_REVIEW_PROMPT_TEMPLATE = """Analyze the following list of code findings and their corresponding snippets. Provide an actionable review for each finding in JSON format.

### Findings to Review:
{findings_block}

### Instructions:
1. Review each finding listed above.
2. For every finding, provide:
   - "finding_id": identifier or index corresponding to the finding
   - "explanation": plain-English explanation of the issue (under 150 words)
   - "impact": potential impact if exploited or ignored (under 100 words)
   - "suggested_fix": textual suggestion on how to fix the issue
   - "fixed_code": the corrected code snippet
3. Respond strictly with a valid JSON array of review objects.
4. Keep the explanation under 150 words and impact under 100 words for each item.

### Required JSON Array Format:
[
  {{
    "finding_id": "0",
    "explanation": "Plain-English explanation under 150 words",
    "impact": "Potential impact if exploited or ignored under 100 words",
    "suggested_fix": "Textual suggestion explaining how to fix the issue",
    "fixed_code": "Fixed code snippet"
  }}
]
"""
