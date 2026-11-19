"""Pydantic schemas for the AI Review Engine."""

from pydantic import BaseModel, ConfigDict, Field


class FindingInput(BaseModel):
    """Schema representing an input finding from static analysis."""
    model_config = ConfigDict(extra="ignore")

    file: str = Field(..., description="File path where the finding occurred")
    line: int = Field(default=1, description="Line number of the finding")
    category: str = Field(..., description="Finding category (e.g., security, bug, complexity, style)")
    severity: str = Field(..., description="Severity level (e.g., high, medium, low, critical)")
    rule: str = Field(..., description="Rule or check identifier that triggered the finding")
    message: str = Field(..., description="Description or message from the scanner")
    code_snippet: str = Field(default="", description="Relevant source code snippet around the finding")


class AIReviewOutput(BaseModel):
    """Schema representing a successful AI-assisted review analysis."""
    model_config = ConfigDict(extra="ignore")

    explanation: str = Field(..., description="Plain-English explanation of the detected issue")
    impact: str = Field(..., description="Potential security, stability, or maintainability impact")
    suggested_fix: str = Field(..., description="Textual description explaining how to fix the issue")
    fixed_code: str = Field(default="", description="Suggested code snippet resolving the issue")


class AIReviewError(BaseModel):
    """Schema representing an error or fallback response when AI is unavailable."""
    model_config = ConfigDict(extra="ignore")

    error: str = Field(..., description="Reason or error message explaining why AI review could not complete")
    explanation: str = Field(default="AI review unavailable", description="Fallback explanation")
    impact: str = Field(default="Unknown", description="Fallback impact description")
    suggested_fix: str = Field(default="Please review manually", description="Fallback fix advice")
    fixed_code: str = Field(default="", description="Fallback fixed code")
