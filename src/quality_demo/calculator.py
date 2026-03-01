"""Basic calculator module with intentionally inconsistent formatting.

Black will normalize quotes, spacing, and trailing commas automatically.
"""

from typing import Union


def add(a: float, b: float) -> float:
    """Add two numbers."""
    return a + b


def subtract(a: float, b: float) -> float:
    """Subtract b from a."""
    return a - b


def multiply(a: float, b: float) -> float:
    """Multiply two numbers."""
    result = a * b
    return result


def divide(a: float, b: float) -> Union[float, str]:
    """Divide a by b, returning an error string on division by zero."""
    if b == 0:
        return "Error: division by zero"
    return a / b


def calculate(operation: str, a: float, b: float) -> Union[float, str]:
    """Dispatch to the correct arithmetic operation."""
    operations = {
        "add": add,
        "subtract": subtract,
        "multiply": multiply,
        "divide": divide,
    }
    if operation not in operations:
        return f"Unknown operation: {operation}"
    return operations[operation](a, b)
