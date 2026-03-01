"""Tests for CourseSearchTool.execute() and ToolManager."""

from unittest.mock import MagicMock

from vector_store import SearchResults
from search_tools import CourseSearchTool, ToolManager


# ---------------------------------------------------------------------------
# CourseSearchTool.execute()
# ---------------------------------------------------------------------------

class TestCourseSearchToolExecute:

    def test_execute_returns_formatted_results(self, mock_vector_store):
        """Correct formatting: [CourseTitle - Lesson N] headers, document text, source links."""
        mock_vector_store.search.return_value = SearchResults(
            documents=["Computer use enables AI to interact with GUIs."],
            metadata=[{"course_title": "AI Basics", "lesson_number": 3}],
            distances=[0.2],
        )
        mock_vector_store.get_lesson_link.return_value = "https://example.com/ai-basics/3"

        tool = CourseSearchTool(mock_vector_store)
        result = tool.execute(query="computer use")

        # Header should include course title and lesson number
        assert "[AI Basics - Lesson 3]" in result
        # Document text should be present
        assert "Computer use enables AI to interact with GUIs." in result
        # Sources should contain an HTML link
        assert len(tool.last_sources) == 1
        assert 'href="https://example.com/ai-basics/3"' in tool.last_sources[0]

    def test_execute_with_course_filter(self, mock_vector_store):
        """course_name param forwarded to VectorStore.search()."""
        tool = CourseSearchTool(mock_vector_store)
        tool.execute(query="agents", course_name="MCP Course")

        _, kwargs = mock_vector_store.search.call_args
        assert kwargs["course_name"] == "MCP Course"

    def test_execute_with_lesson_filter(self, mock_vector_store):
        """lesson_number param forwarded to VectorStore.search()."""
        tool = CourseSearchTool(mock_vector_store)
        tool.execute(query="tools", lesson_number=2)

        _, kwargs = mock_vector_store.search.call_args
        assert kwargs["lesson_number"] == 2

    def test_execute_empty_results(self, mock_vector_store):
        """Returns 'No relevant content found.' on empty SearchResults."""
        mock_vector_store.search.return_value = SearchResults(
            documents=[], metadata=[], distances=[]
        )

        tool = CourseSearchTool(mock_vector_store)
        result = tool.execute(query="nonexistent topic")

        assert result == "No relevant content found."

    def test_execute_empty_results_with_filters(self, mock_vector_store):
        """Includes filter info: "in course 'MCP' in lesson 2"."""
        mock_vector_store.search.return_value = SearchResults(
            documents=[], metadata=[], distances=[]
        )

        tool = CourseSearchTool(mock_vector_store)
        result = tool.execute(query="xyz", course_name="MCP", lesson_number=2)

        assert "in course 'MCP'" in result
        assert "in lesson 2" in result

    def test_execute_error_from_vector_store(self, mock_vector_store):
        """Propagates error string from SearchResults.error."""
        mock_vector_store.search.return_value = SearchResults(
            documents=[], metadata=[], distances=[], error="Connection failed"
        )

        tool = CourseSearchTool(mock_vector_store)
        result = tool.execute(query="anything")

        assert result == "Connection failed"


# ---------------------------------------------------------------------------
# ToolManager
# ---------------------------------------------------------------------------

class TestToolManager:

    def test_tool_manager_register_and_execute(self, mock_vector_store):
        """ToolManager routes execute_tool('search_course_content') correctly."""
        tm = ToolManager()
        search_tool = CourseSearchTool(mock_vector_store)
        tm.register_tool(search_tool)

        result = tm.execute_tool("search_course_content", query="agents")

        mock_vector_store.search.assert_called_once()
        assert isinstance(result, str)

    def test_tool_manager_unknown_tool(self):
        """Returns "Tool 'xyz' not found" for unregistered tools."""
        tm = ToolManager()
        result = tm.execute_tool("xyz")

        assert result == "Tool 'xyz' not found"

    def test_tool_manager_sources_lifecycle(self, mock_vector_store):
        """get_last_sources() populated after search, empty after reset_sources()."""
        mock_vector_store.search.return_value = SearchResults(
            documents=["Some content"],
            metadata=[{"course_title": "AI Basics", "lesson_number": 1}],
            distances=[0.3],
        )
        mock_vector_store.get_lesson_link.return_value = "https://example.com/1"

        tm = ToolManager()
        search_tool = CourseSearchTool(mock_vector_store)
        tm.register_tool(search_tool)

        # Execute a search to populate sources
        tm.execute_tool("search_course_content", query="test")
        sources = tm.get_last_sources()
        assert len(sources) == 1

        # Reset should clear sources
        tm.reset_sources()
        assert tm.get_last_sources() == []
