"""Tests for AIGenerator sequential tool-calling flow.

Covers three scenarios:
- Direct answers (no tool use) — TestAIGeneratorDirectAnswer
- Single-round tool use (1 tool call → follow-up) — TestAIGeneratorToolUse
- Sequential tool use (up to 2 tool rounds) — TestAIGeneratorSequentialToolUse
"""

from unittest.mock import MagicMock, call

from helpers import make_text_response, make_tool_use_response


SAMPLE_TOOLS = [
    {
        "name": "search_course_content",
        "description": "Search course materials",
        "input_schema": {
            "type": "object",
            "properties": {"query": {"type": "string"}},
            "required": ["query"],
        },
    }
]


class TestAIGeneratorDirectAnswer:
    """Tests for the non-tool path (single API call returns text)."""

    def test_direct_answer_no_tool_use(self, ai_generator, mock_anthropic_client):
        """No tool path, single API call returns text."""
        mock_anthropic_client.messages.create.return_value = make_text_response(
            "Paris is the capital of France."
        )

        result = ai_generator.generate_response(query="What is the capital of France?")

        assert result == "Paris is the capital of France."
        assert mock_anthropic_client.messages.create.call_count == 1

    def test_direct_answer_with_tools_available(self, ai_generator, mock_anthropic_client):
        """Tools offered but Claude answers directly (stop_reason != 'tool_use')."""
        mock_anthropic_client.messages.create.return_value = make_text_response(
            "Python is a programming language."
        )

        result = ai_generator.generate_response(
            query="What is Python?",
            tools=SAMPLE_TOOLS,
            tool_manager=MagicMock(),
        )

        assert result == "Python is a programming language."
        assert mock_anthropic_client.messages.create.call_count == 1


class TestAIGeneratorToolUse:
    """Tests for the tool-use path (two API calls)."""

    def test_tool_use_flow_calls_tool_manager(self, ai_generator, mock_anthropic_client):
        """Second API call must include `tools` — currently fails (bug)."""
        tool_response = make_tool_use_response([
            {"id": "toolu_01", "name": "search_course_content", "input": {"query": "computer use"}},
        ])
        final_response = make_text_response("Computer use lets AI control GUIs.")

        mock_anthropic_client.messages.create.side_effect = [tool_response, final_response]

        tm = MagicMock()
        tm.execute_tool.return_value = "Relevant content about computer use."

        result = ai_generator.generate_response(
            query="What is computer use?",
            tools=SAMPLE_TOOLS,
            tool_manager=tm,
        )

        # Tool manager should have been called
        tm.execute_tool.assert_called_once_with("search_course_content", query="computer use")

        # Two API calls should have been made
        assert mock_anthropic_client.messages.create.call_count == 2

        # THE BUG: second call must contain `tools`
        second_call_kwargs = mock_anthropic_client.messages.create.call_args_list[1][1]
        assert "tools" in second_call_kwargs, (
            "Second API call is missing the 'tools' parameter — "
            "the Anthropic API requires it when messages contain tool_use/tool_result blocks"
        )
        assert result == "Computer use lets AI control GUIs."

    def test_tool_use_second_call_includes_tools(self, ai_generator, mock_anthropic_client):
        """Focused assertion: second call kwargs must contain 'tools'."""
        tool_response = make_tool_use_response([
            {"id": "toolu_02", "name": "search_course_content", "input": {"query": "MCP"}},
        ])
        final_response = make_text_response("MCP stands for Model Context Protocol.")

        mock_anthropic_client.messages.create.side_effect = [tool_response, final_response]

        tm = MagicMock()
        tm.execute_tool.return_value = "MCP info"

        ai_generator.generate_response(
            query="What is MCP?",
            tools=SAMPLE_TOOLS,
            tool_manager=tm,
        )

        second_call_kwargs = mock_anthropic_client.messages.create.call_args_list[1][1]
        assert "tools" in second_call_kwargs

    def test_tool_use_second_call_includes_system(self, ai_generator, mock_anthropic_client):
        """system IS included in the follow-up call."""
        tool_response = make_tool_use_response([
            {"id": "toolu_03", "name": "search_course_content", "input": {"query": "RAG"}},
        ])
        final_response = make_text_response("RAG combines retrieval with generation.")

        mock_anthropic_client.messages.create.side_effect = [tool_response, final_response]

        tm = MagicMock()
        tm.execute_tool.return_value = "RAG info"

        ai_generator.generate_response(
            query="What is RAG?",
            tools=SAMPLE_TOOLS,
            tool_manager=tm,
        )

        second_call_kwargs = mock_anthropic_client.messages.create.call_args_list[1][1]
        assert "system" in second_call_kwargs

    def test_tool_use_messages_structure(self, ai_generator, mock_anthropic_client):
        """Message assembly: user → assistant tool_use → user tool_result."""
        tool_response = make_tool_use_response([
            {"id": "toolu_04", "name": "search_course_content", "input": {"query": "embeddings"}},
        ])
        final_response = make_text_response("Embeddings are vector representations.")

        mock_anthropic_client.messages.create.side_effect = [tool_response, final_response]

        tm = MagicMock()
        tm.execute_tool.return_value = "Embedding content"

        ai_generator.generate_response(
            query="What are embeddings?",
            tools=SAMPLE_TOOLS,
            tool_manager=tm,
        )

        second_call_kwargs = mock_anthropic_client.messages.create.call_args_list[1][1]
        messages = second_call_kwargs["messages"]

        # Should be 3 messages: user, assistant (tool_use), user (tool_result)
        assert len(messages) == 3
        assert messages[0]["role"] == "user"
        assert messages[1]["role"] == "assistant"
        assert messages[2]["role"] == "user"

        # Third message should contain tool_result
        tool_result_content = messages[2]["content"]
        assert isinstance(tool_result_content, list)
        assert tool_result_content[0]["type"] == "tool_result"
        assert tool_result_content[0]["tool_use_id"] == "toolu_04"

    def test_conversation_history_in_system(self, ai_generator, mock_anthropic_client):
        """History appended to system prompt correctly."""
        mock_anthropic_client.messages.create.return_value = make_text_response("Sure!")

        ai_generator.generate_response(
            query="Follow up question",
            conversation_history="User: Hi\nAssistant: Hello!",
        )

        call_kwargs = mock_anthropic_client.messages.create.call_args[1]
        assert "Previous conversation:" in call_kwargs["system"]
        assert "User: Hi" in call_kwargs["system"]

    def test_multiple_tool_calls(self, ai_generator, mock_anthropic_client):
        """Multiple tool calls in one response — same missing `tools` bug."""
        tool_response = make_tool_use_response([
            {"id": "toolu_10", "name": "search_course_content", "input": {"query": "topic A"}},
            {"id": "toolu_11", "name": "search_course_content", "input": {"query": "topic B"}},
        ])
        final_response = make_text_response("Combined answer about A and B.")

        mock_anthropic_client.messages.create.side_effect = [tool_response, final_response]

        tm = MagicMock()
        tm.execute_tool.return_value = "Result"

        result = ai_generator.generate_response(
            query="Tell me about A and B",
            tools=SAMPLE_TOOLS,
            tool_manager=tm,
        )

        # Both tools should have been executed
        assert tm.execute_tool.call_count == 2

        # Second API call must include tools
        second_call_kwargs = mock_anthropic_client.messages.create.call_args_list[1][1]
        assert "tools" in second_call_kwargs, (
            "Second API call is missing 'tools' — bug affects multi-tool responses too"
        )
        assert result == "Combined answer about A and B."


class TestAIGeneratorSequentialToolUse:
    """Tests for multi-round sequential tool calling (up to MAX_TOOL_ROUNDS)."""

    def test_two_sequential_tool_rounds(self, ai_generator, mock_anthropic_client):
        """Two tool rounds → 3 API calls, tool_manager called twice, correct final text."""
        round1 = make_tool_use_response([
            {"id": "toolu_A1", "name": "get_course_outline", "input": {"course_name": "MCP"}},
        ])
        round2 = make_tool_use_response([
            {"id": "toolu_A2", "name": "search_course_content",
             "input": {"query": "lesson 4", "course_name": "MCP", "lesson_number": 4}},
        ])
        final = make_text_response("Lesson 4 covers tool integration.")

        mock_anthropic_client.messages.create.side_effect = [round1, round2, final]

        tm = MagicMock()
        tm.execute_tool.side_effect = ["Outline: Lesson 4 - Tools", "Detailed content about tools"]

        result = ai_generator.generate_response(
            query="What does lesson 4 of the MCP course cover?",
            tools=SAMPLE_TOOLS,
            tool_manager=tm,
        )

        assert mock_anthropic_client.messages.create.call_count == 3
        assert tm.execute_tool.call_count == 2
        assert result == "Lesson 4 covers tool integration."

    def test_two_rounds_messages_structure(self, ai_generator, mock_anthropic_client):
        """Third API call's messages: user → assistant(tool1) → user(result1) → assistant(tool2) → user(result2)."""
        round1 = make_tool_use_response([
            {"id": "toolu_B1", "name": "get_course_outline", "input": {"course_name": "MCP"}},
        ])
        round2 = make_tool_use_response([
            {"id": "toolu_B2", "name": "search_course_content", "input": {"query": "lesson 4"}},
        ])
        final = make_text_response("Answer.")

        mock_anthropic_client.messages.create.side_effect = [round1, round2, final]

        tm = MagicMock()
        tm.execute_tool.side_effect = ["outline", "content"]

        ai_generator.generate_response(
            query="question",
            tools=SAMPLE_TOOLS,
            tool_manager=tm,
        )

        third_call_kwargs = mock_anthropic_client.messages.create.call_args_list[2][1]
        messages = third_call_kwargs["messages"]

        assert len(messages) == 5
        assert messages[0]["role"] == "user"
        assert messages[1]["role"] == "assistant"
        assert messages[2]["role"] == "user"
        assert messages[3]["role"] == "assistant"
        assert messages[4]["role"] == "user"

        # Verify tool_result blocks
        assert messages[2]["content"][0]["type"] == "tool_result"
        assert messages[2]["content"][0]["tool_use_id"] == "toolu_B1"
        assert messages[4]["content"][0]["type"] == "tool_result"
        assert messages[4]["content"][0]["tool_use_id"] == "toolu_B2"

    def test_two_rounds_all_calls_include_tools_and_system(self, ai_generator, mock_anthropic_client):
        """Every API call includes both 'tools' and 'system' in kwargs."""
        round1 = make_tool_use_response([
            {"id": "toolu_C1", "name": "get_course_outline", "input": {"course_name": "MCP"}},
        ])
        round2 = make_tool_use_response([
            {"id": "toolu_C2", "name": "search_course_content", "input": {"query": "lesson 4"}},
        ])
        final = make_text_response("Answer.")

        mock_anthropic_client.messages.create.side_effect = [round1, round2, final]

        tm = MagicMock()
        tm.execute_tool.side_effect = ["outline", "content"]

        ai_generator.generate_response(
            query="question",
            tools=SAMPLE_TOOLS,
            tool_manager=tm,
        )

        for i, call_obj in enumerate(mock_anthropic_client.messages.create.call_args_list):
            kwargs = call_obj[1]
            assert "tools" in kwargs, f"API call {i} missing 'tools'"
            assert "system" in kwargs, f"API call {i} missing 'system'"

    def test_max_rounds_exceeded_returns_text(self, ai_generator, mock_anthropic_client):
        """If Claude wants a 3rd tool call, loop stops: 2 tool executions, 3 API calls."""
        round1 = make_tool_use_response([
            {"id": "toolu_D1", "name": "get_course_outline", "input": {"course_name": "MCP"}},
        ])
        round2 = make_tool_use_response([
            {"id": "toolu_D2", "name": "search_course_content", "input": {"query": "lesson 4"}},
        ])
        # Third response still wants a tool but also has a text preamble
        round3 = make_tool_use_response(
            [{"id": "toolu_D3", "name": "search_course_content", "input": {"query": "more"}}],
            preamble="Let me search for more details.",
        )

        mock_anthropic_client.messages.create.side_effect = [round1, round2, round3]

        tm = MagicMock()
        tm.execute_tool.side_effect = ["outline", "content"]

        result = ai_generator.generate_response(
            query="question",
            tools=SAMPLE_TOOLS,
            tool_manager=tm,
        )

        # Only 2 tool executions (loop ran rounds 0 and 1, broke at round 2)
        assert tm.execute_tool.call_count == 2
        assert mock_anthropic_client.messages.create.call_count == 3
        # Should extract the text preamble from the 3rd response
        assert result == "Let me search for more details."

    def test_single_round_still_works(self, ai_generator, mock_anthropic_client):
        """Regression guard: single tool round → 2 API calls, identical to existing behavior."""
        tool_response = make_tool_use_response([
            {"id": "toolu_E1", "name": "search_course_content", "input": {"query": "RAG"}},
        ])
        final_response = make_text_response("RAG combines retrieval with generation.")

        mock_anthropic_client.messages.create.side_effect = [tool_response, final_response]

        tm = MagicMock()
        tm.execute_tool.return_value = "RAG content"

        result = ai_generator.generate_response(
            query="What is RAG?",
            tools=SAMPLE_TOOLS,
            tool_manager=tm,
        )

        assert mock_anthropic_client.messages.create.call_count == 2
        assert tm.execute_tool.call_count == 1
        assert result == "RAG combines retrieval with generation."

    def test_tool_error_sent_as_error_result(self, ai_generator, mock_anthropic_client):
        """When execute_tool raises, error sent as is_error tool_result; Claude still responds."""
        tool_response = make_tool_use_response([
            {"id": "toolu_F1", "name": "search_course_content", "input": {"query": "broken"}},
        ])
        final_response = make_text_response("Sorry, I encountered an issue searching.")

        mock_anthropic_client.messages.create.side_effect = [tool_response, final_response]

        tm = MagicMock()
        tm.execute_tool.side_effect = Exception("Connection timeout")

        result = ai_generator.generate_response(
            query="Search for broken",
            tools=SAMPLE_TOOLS,
            tool_manager=tm,
        )

        assert mock_anthropic_client.messages.create.call_count == 2

        # Verify the error was sent as a tool_result with is_error
        second_call_kwargs = mock_anthropic_client.messages.create.call_args_list[1][1]
        tool_result_msg = second_call_kwargs["messages"][2]["content"]
        assert tool_result_msg[0]["is_error"] is True
        assert "Connection timeout" in tool_result_msg[0]["content"]

        assert result == "Sorry, I encountered an issue searching."
