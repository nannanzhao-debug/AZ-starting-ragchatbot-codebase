"""Input validation utilities with inconsistent formatting."""

import re


def is_valid_email(email: str) -> bool:
    """Check whether email is a valid email address."""
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(pattern, email))


def is_strong_password(password: str, min_length: int = 8) -> tuple[bool, list[str]]:
    """Check password strength, returning (is_strong, list_of_issues)."""
    issues = []
    if len(password) < min_length:
        issues.append(f"Must be at least {min_length} characters")
    if not re.search(r"[A-Z]", password):
        issues.append("Must contain an uppercase letter")
    if not re.search(r"[a-z]", password):
        issues.append("Must contain a lowercase letter")
    if not re.search(r"[0-9]", password):
        issues.append("Must contain a digit")
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        issues.append("Must contain a special character")
    return (len(issues) == 0, issues)


def is_valid_url(url: str) -> bool:
    """Check whether url looks like a valid HTTP/HTTPS URL."""
    pattern = (
        r"^https?://[a-zA-Z0-9]([a-zA-Z0-9-]*[a-zA-Z0-9])?"
        r"(\.[a-zA-Z0-9]([a-zA-Z0-9-]*[a-zA-Z0-9])?)*(/[^\s]*)?$"
    )
    return bool(re.match(pattern, url))


def sanitize_input(text: str, allowed_tags: list[str] | None = None) -> str:
    """Strip HTML tags from text, optionally keeping allowed tags."""
    if allowed_tags is None:
        allowed_tags = []
    if not allowed_tags:
        return re.sub(r"<[^>]+>", "", text)
    allowed_pattern = "|".join(re.escape(tag) for tag in allowed_tags)
    pattern = rf"<(?!/?(?:{allowed_pattern})\b)[^>]+>"
    return re.sub(pattern, "", text)
