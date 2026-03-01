"""Shared fixtures for RAG chatbot tests."""

import sys
import os
from unittest.mock import MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

# Add backend directory and tests directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.dirname(__file__))

from search_tools import CourseSearchTool, ToolManager
from vector_store import SearchResults


# ---------------------------------------------------------------------------
# Fixtures from testing_feature (simple RAG engine tests)
# ---------------------------------------------------------------------------

from backend.rag_engine import load_courses, COURSE_DATA


@pytest.fixture(params=["asyncio"])
def anyio_backend(request):
    """Run async tests with asyncio only (trio is not installed)."""
    return request.param


SAMPLE_COURSES = [
    {
        "id": "ml101",
        "title": "Introduction to Machine Learning",
        "content": (
            "Machine learning is a subset of artificial intelligence that enables "
            "systems to learn from data. Supervised learning uses labeled datasets "
            "to train models that can make predictions. Common algorithms include "
            "linear regression, decision trees, and support vector machines."
        ),
    },
    {
        "id": "dl201",
        "title": "Deep Learning Fundamentals",
        "content": (
            "Deep learning uses neural networks with multiple layers to model "
            "complex patterns. Convolutional neural networks excel at image "
            "recognition tasks. Recurrent neural networks handle sequential data "
            "like text and time series."
        ),
    },
]


@pytest.fixture
def sample_courses():
    """Raw course data for testing."""
    return SAMPLE_COURSES.copy()


@pytest.fixture
def loaded_courses():
    """Load sample courses into the RAG engine and clean up after."""
    load_courses(SAMPLE_COURSES)
    yield SAMPLE_COURSES
    COURSE_DATA.clear()


def _create_test_app():
    """Create a FastAPI app for testing without static file mounts."""
    from fastapi import FastAPI, HTTPException
    from pydantic import BaseModel
    from backend.rag_engine import retrieve, generate_response, list_courses

    test_app = FastAPI(title="RAG Course Chatbot (test)")

    class QueryRequest(BaseModel):
        question: str
        top_k: int = 3

    class QueryResponse(BaseModel):
        answer: str
        sources: list[dict]

    @test_app.get("/")
    def root():
        return {"status": "ok", "message": "RAG Course Chatbot API"}

    @test_app.post("/api/query")
    def query(request: QueryRequest) -> QueryResponse:
        if not request.question.strip():
            raise HTTPException(status_code=422, detail="Question cannot be empty")
        chunks = retrieve(request.question, top_k=request.top_k)
        answer = generate_response(request.question, chunks)
        sources = [
            {"course_id": c.course_id, "title": c.title, "chunk_index": c.chunk_index}
            for c in chunks
        ]
        return QueryResponse(answer=answer, sources=sources)

    @test_app.get("/api/courses")
    def courses():
        return {"courses": list_courses()}

    return test_app


@pytest.fixture
def test_app():
    """FastAPI test app without static file mounts."""
    return _create_test_app()


@pytest.fixture
async def async_client(test_app):
    """Async HTTP client wired to the test app."""
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


# ---------------------------------------------------------------------------
# Fixtures from main branch (production RAG system tests)
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
