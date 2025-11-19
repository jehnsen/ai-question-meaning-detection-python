"""
Text processing utilities for normalization and fuzzy matching.
"""
import re
import string
from thefuzz import fuzz
from typing import Optional


def normalize_text(text: str) -> str:
    """
    Normalize text for fuzzy matching.

    Normalization steps:
    1. Convert to lowercase
    2. Remove punctuation
    3. Remove extra whitespace
    4. Strip leading/trailing whitespace

    Args:
        text: Input text to normalize

    Returns:
        Normalized text string
    """
    # Convert to lowercase
    text = text.lower()

    # Remove punctuation
    text = text.translate(str.maketrans('', '', string.punctuation))

    # Remove extra whitespace (collapse multiple spaces to one)
    text = re.sub(r'\s+', ' ', text)

    # Strip leading/trailing whitespace
    text = text.strip()

    return text


def fuzzy_match_score(text1: str, text2: str, normalize: bool = True) -> float:
    """
    Calculate fuzzy match score between two text strings.

    Uses Levenshtein distance ratio for string similarity.

    Args:
        text1: First text string
        text2: Second text string
        normalize: Whether to normalize texts before comparison (default: True)

    Returns:
        Similarity score between 0.0 and 1.0 (1.0 = identical)
    """
    if normalize:
        text1 = normalize_text(text1)
        text2 = normalize_text(text2)

    # Use fuzz.ratio which returns 0-100, convert to 0-1
    score = fuzz.ratio(text1, text2) / 100.0

    return score


def fuzzy_match_partial_score(text1: str, text2: str, normalize: bool = True) -> float:
    """
    Calculate partial fuzzy match score (for substring matching).

    Uses partial ratio which is better for cases where one string
    is a substring of the other.

    Args:
        text1: First text string
        text2: Second text string
        normalize: Whether to normalize texts before comparison (default: True)

    Returns:
        Similarity score between 0.0 and 1.0 (1.0 = perfect match/substring)
    """
    if normalize:
        text1 = normalize_text(text1)
        text2 = normalize_text(text2)

    # Use fuzz.partial_ratio which returns 0-100, convert to 0-1
    score = fuzz.partial_ratio(text1, text2) / 100.0

    return score
