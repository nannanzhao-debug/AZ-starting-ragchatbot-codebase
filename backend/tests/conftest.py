"""Shared fixtures for backend tests."""

import pytest
from httpx import ASGITransport, AsyncClient

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
    """Create a FastAPI app for testing without static file mounts.

    The production app in backend/app.py mounts a static files directory
    that doesn't exist in the test environment. This factory builds an
    equivalent app with the same API routes but no static mount.
    """
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
