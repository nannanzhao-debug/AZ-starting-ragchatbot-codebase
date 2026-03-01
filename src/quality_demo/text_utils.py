"""Text utility functions with inconsistent formatting for black to fix."""

import re
from collections import Counter


def word_count(text: str) -> dict[str, int]:
    """Count word frequencies in text."""
    words = text.lower().split()
    return dict(Counter(words))


def slugify(text: str) -> str:
    """Convert text to a URL-friendly slug."""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text)
    text = re.sub(r"^-+|-+$", "", text)
    return text


def truncate(text: str, max_length: int = 80, suffix: str = "...") -> str:
    """Truncate text to max_length, appending suffix if truncated."""
    if len(text) <= max_length:
        return text
    return text[: max_length - len(suffix)] + suffix


def extract_emails(text: str) -> list[str]:
    """Extract all email addresses from text."""
    pattern = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
    return re.findall(pattern, text)


def format_name(first: str, last: str, style: str = "full") -> str:
    """Format a name in the given style."""
    styles = {
        "full": f"{first} {last}",
        "last_first": f"{last}, {first}",
        "initials": f"{first[0]}.{last[0]}.",
        "formal": f"Mr./Ms. {last}",
    }
    if style not in styles:
        raise ValueError(
            f"Unknown style: {style}. Choose from: {', '.join(styles.keys())}"
        )
    return styles[style]
