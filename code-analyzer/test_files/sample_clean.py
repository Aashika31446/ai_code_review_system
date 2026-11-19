"""
Sample clean Python module demonstrating best practices and clean code structure.
"""

from __future__ import annotations

import logging
from typing import Sequence

logger = logging.getLogger(__name__)


def calculate_average(numbers: Sequence[float] | None = None) -> float:
    """Calculate the arithmetic mean of a sequence of numbers."""
    if numbers is None:
        return 0.0
    if not numbers:
        return 0.0
    return sum(numbers) / len(numbers)


def validate_username(username: str) -> bool:
    """Validate username criteria."""
    if not username:
        return False
    return username.isalnum() and 3 <= len(username) <= 30


def divide_values(numerator: float, denominator: float) -> float | None:
    """Safely divide two numbers handling ZeroDivisionError."""
    try:
        return numerator / denominator
    except ZeroDivisionError:
        logger.warning("Attempted division by zero.")
        return None
    except Exception as exc:
        logger.error("Unexpected error during division: %s", exc)
        return None
