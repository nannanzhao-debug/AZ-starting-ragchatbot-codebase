"""Shared fixtures for RAG chatbot tests."""

import sys
import os
from unittest.mock import MagicMock, patch

import pytest

# Add backend directory and tests directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.dirname(__file__))

from search_tools import CourseSearchTool, ToolManager
from vector_store import SearchResults


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_vector_store():
    """A MagicMock standing in for VectorStore with sensible defaults."""
    store = MagicMock()

    # Default: return some search results
    store.search.return_value = SearchResults(
        documents=["Chunk about computer use."],
        metadata=[{"course_title": "AI Basics", "lesson_number": 3}],
        distances=[0.25],
    )
    store.get_lesson_link.return_value = "https://example.com/lesson3"
    return store


@pytest.fixture
def tool_manager_with_search(mock_vector_store):
    """A ToolManager with a CourseSearchTool already registered."""
    tm = ToolManager()
    search_tool = CourseSearchTool(mock_vector_store)
    tm.register_tool(search_tool)
    return tm


@pytest.fixture
def mock_anthropic_client():
    """A MagicMock replacing anthropic.AnthropicBedrock."""
    client = MagicMock()
    return client


@pytest.fixture
def ai_generator(mock_anthropic_client):
    """An AIGenerator instance whose Anthropic client is mocked."""
    with patch("ai_generator.anthropic") as mock_module:
        mock_module.AnthropicBedrock.return_value = mock_anthropic_client
        from ai_generator import AIGenerator
        gen = AIGenerator(region="us-east-1", model="claude-sonnet-4-20250514")
    gen.client = mock_anthropic_client
    return gen
