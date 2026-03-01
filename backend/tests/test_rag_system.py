"""Integration tests for RAGSystem.query().

Covers direct answers, single-round tool use, two-round sequential tool use,
source retrieval, and session history.
"""

from unittest.mock import MagicMock, patch, PropertyMock

from helpers import make_text_response, make_tool_use_response


SEARCH_TOOL_DEF = {
    "name": "search_course_content",
    "description": "Search course materials",
    "input_schema": {
        "type": "object",
        "properties": {"query": {"type": "string"}},
        "required": ["query"],
    },
}


def _build_rag_system(mock_client):
    """Build a RAGSystem with all heavy dependencies mocked out."""
    with patch("ai_generator.anthropic") as mock_anthropic_mod, \
         patch("rag_system.VectorStore") as MockVS, \
         patch("rag_system.DocumentProcessor"), \
         patch("rag_system.SessionManager") as MockSM:

        mock_anthropic_mod.AnthropicBedrock.return_value = mock_client

        # Minimal config object
        config = MagicMock()
        config.CHUNK_SIZE = 800
        config.CHUNK_OVERLAP = 100
        config.CHROMA_PATH = "/tmp/test_chroma"
        config.EMBEDDING_MODEL = "all-MiniLM-L6-v2"
        config.MAX_RESULTS = 5
        config.AWS_REGION = "us-east-1"
        config.ANTHROPIC_MODEL = "claude-sonnet-4-20250514"
        config.MAX_HISTORY = 2

        # Mock VectorStore instance methods
        mock_vs_instance = MockVS.return_value
        mock_vs_instance.search.return_value = MagicMock(
            documents=["Content about computer use"],
            metadata=[{"course_title": "AI Basics", "lesson_number": 1}],
            distances=[0.2],
            error=None,
            is_empty=MagicMock(return_value=False),
        )
        mock_vs_instance.get_lesson_link.return_value = "https://example.com/1"
        mock_vs_instance.get_course_outline.return_value = None

        # Mock SessionManager
        mock_sm_instance = MockSM.return_value
        mock_sm_instance.get_conversation_history.return_value = None

        from rag_system import RAGSystem
        rag = RAGSystem(config)

    # Replace the client on the already-constructed AIGenerator
    rag.ai_generator.client = mock_client
    return rag


class TestRAGSystemQuery:

    def test_query_general_knowledge(self):
        """No tool use, direct answer returned."""
        mock_client = MagicMock()
        mock_client.messages.create.return_value = make_text_response(
            "Python is a programming language."
        )

        rag = _build_rag_system(mock_client)
        response, sources = rag.query("What is Python?")

        assert response == "Python is a programming language."
        assert mock_client.messages.create.call_count == 1

    def test_query_content_triggers_tool_use(self):
        """Full tool path end-to-end — FAILS before bug fix."""
        mock_client = MagicMock()

        tool_response = make_tool_use_response([
            {"id": "toolu_99", "name": "search_course_content", "input": {"query": "computer use"}},
        ])
        final_response = make_text_response("Computer use lets AI control GUIs.")

        mock_client.messages.create.side_effect = [tool_response, final_response]

        rag = _build_rag_system(mock_client)
        response, sources = rag.query("What is computer use?")

        # Two API calls should have been made
        assert mock_client.messages.create.call_count == 2

        # Second call must include tools (the bug)
        second_call_kwargs = mock_client.messages.create.call_args_list[1][1]
        assert "tools" in second_call_kwargs, (
            "RAG query tool path: second API call missing 'tools' parameter"
        )
        assert response == "Computer use lets AI control GUIs."

    def test_query_returns_sources(self):
        """Source retrieval + reset works after a non-tool query."""
        mock_client = MagicMock()
        mock_client.messages.create.return_value = make_text_response("Answer")

        rag = _build_rag_system(mock_client)

        # Manually populate sources on the search tool to simulate a previous search
        for tool in rag.tool_manager.tools.values():
            if hasattr(tool, "last_sources"):
                tool.last_sources = ["AI Basics - Lesson 1"]

        response, sources = rag.query("question")

        assert sources == ["AI Basics - Lesson 1"]
        # Sources should be reset after retrieval
        assert rag.tool_manager.get_last_sources() == []

    def test_query_with_session_saves_history(self):
        """add_exchange called when session_id is provided."""
        mock_client = MagicMock()
        mock_client.messages.create.return_value = make_text_response("Hi there!")

        rag = _build_rag_system(mock_client)
        rag.query("Hello", session_id="sess_1")

        rag.session_manager.add_exchange.assert_called_once()

    def test_query_without_session_no_history(self):
        """conversation_history=None passed when no session_id."""
        mock_client = MagicMock()
        mock_client.messages.create.return_value = make_text_response("Answer")

        rag = _build_rag_system(mock_client)
        rag.query("question")

        # get_conversation_history should not have been called with a session_id
        rag.session_manager.get_conversation_history.assert_not_called()

    def test_query_two_round_tool_use(self):
        """Two sequential tool rounds end-to-end: outline → search → final answer."""
        mock_client = MagicMock()

        round1 = make_tool_use_response([
            {"id": "toolu_int1", "name": "get_course_outline",
             "input": {"course_name": "MCP"}},
        ])
        round2 = make_tool_use_response([
            {"id": "toolu_int2", "name": "search_course_content",
             "input": {"query": "tool integration", "course_name": "MCP", "lesson_number": 4}},
        ])
        final = make_text_response("Lesson 4 covers tool integration with MCP.")

        mock_client.messages.create.side_effect = [round1, round2, final]

        rag = _build_rag_system(mock_client)
        response, sources = rag.query("What does lesson 4 of the MCP course cover?")

        assert mock_client.messages.create.call_count == 3
        assert response == "Lesson 4 covers tool integration with MCP."
        # Sources come from tool execution — verify they are populated
        assert isinstance(sources, list)
