"""Shared helper functions for building mock Anthropic responses."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from unittest.mock import MagicMock


@dataclass
class _TextBlock:
    type: str = "text"
    text: str = ""


@dataclass
class _ToolUseBlock:
    type: str = "tool_use"
    id: str = "toolu_01"
    name: str = ""
    input: Dict[str, Any] = field(default_factory=dict)


def make_text_response(text: str, stop_reason: str = "end_turn"):
    """Build a mock Anthropic response that contains only a text block."""
    resp = MagicMock()
    resp.stop_reason = stop_reason
    resp.content = [_TextBlock(text=text)]
    return resp


def make_tool_use_response(
    tool_calls: List[Dict[str, Any]],
    *,
    preamble: Optional[str] = None,
    stop_reason: str = "tool_use",
):
    """Build a mock Anthropic response that requests one or more tool calls.

    Each item in *tool_calls* should be a dict with keys:
        id, name, input
    """
    blocks = []
    if preamble:
        blocks.append(_TextBlock(text=preamble))
    for tc in tool_calls:
        blocks.append(_ToolUseBlock(
            id=tc["id"],
            name=tc["name"],
            input=tc["input"],
        ))
    resp = MagicMock()
    resp.stop_reason = stop_reason
    resp.content = blocks
    return resp
