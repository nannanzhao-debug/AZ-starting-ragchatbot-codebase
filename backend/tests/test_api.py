"""API endpoint tests for the RAG chatbot.

These tests use a test-specific FastAPI app (from conftest.py) that mirrors
the production routes but skips the static file mount, which requires a
directory that doesn't exist in the test environment.
"""

import pytest
from httpx import ASGITransport, AsyncClient

from backend.rag_engine import load_courses, COURSE_DATA
from backend.tests.conftest import SAMPLE_COURSES


# ---------------------------------------------------------------------------
# Root endpoint
# ---------------------------------------------------------------------------

class TestRootEndpoint:
    @pytest.mark.anyio
    async def test_root_returns_ok(self, async_client):
        resp = await async_client.get("/")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"

    @pytest.mark.anyio
    async def test_root_contains_message(self, async_client):
        resp = await async_client.get("/")
        assert "message" in resp.json()


# ---------------------------------------------------------------------------
# /api/courses endpoint
# ---------------------------------------------------------------------------

class TestCoursesEndpoint:
    @pytest.mark.anyio
    async def test_courses_empty_when_none_loaded(self, async_client):
        COURSE_DATA.clear()
        resp = await async_client.get("/api/courses")
        assert resp.status_code == 200
        assert resp.json()["courses"] == []

    @pytest.mark.anyio
    async def test_courses_returns_loaded_courses(self, async_client):
        load_courses(SAMPLE_COURSES)
        resp = await async_client.get("/api/courses")
        assert resp.status_code == 200
        courses = resp.json()["courses"]
        ids = [c["id"] for c in courses]
        assert "ml101" in ids
        assert "dl201" in ids
        COURSE_DATA.clear()

    @pytest.mark.anyio
    async def test_courses_include_chunk_count(self, async_client):
        load_courses(SAMPLE_COURSES)
        resp = await async_client.get("/api/courses")
        for course in resp.json()["courses"]:
            assert "num_chunks" in course
        COURSE_DATA.clear()


# ---------------------------------------------------------------------------
# /api/query endpoint
# ---------------------------------------------------------------------------

class TestQueryEndpoint:
    @pytest.mark.anyio
    async def test_query_returns_answer(self, async_client, loaded_courses):
        resp = await async_client.post(
            "/api/query",
            json={"question": "What is machine learning?"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "answer" in data
        assert "sources" in data

    @pytest.mark.anyio
    async def test_query_sources_have_course_id(self, async_client, loaded_courses):
        resp = await async_client.post(
            "/api/query",
            json={"question": "neural networks"},
        )
        for source in resp.json()["sources"]:
            assert "course_id" in source
            assert "title" in source

    @pytest.mark.anyio
    async def test_query_respects_top_k(self, async_client, loaded_courses):
        resp = await async_client.post(
            "/api/query",
            json={"question": "learning", "top_k": 1},
        )
        assert len(resp.json()["sources"]) <= 1

    @pytest.mark.anyio
    async def test_query_no_results(self, async_client, loaded_courses):
        resp = await async_client.post(
            "/api/query",
            json={"question": "xyznonexistent"},
        )
        assert resp.status_code == 200
        assert resp.json()["sources"] == []

    @pytest.mark.anyio
    async def test_query_missing_question_field(self, async_client):
        resp = await async_client.post("/api/query", json={})
        assert resp.status_code == 422

    @pytest.mark.anyio
    async def test_query_whitespace_only_question(self, async_client):
        resp = await async_client.post(
            "/api/query",
            json={"question": "   "},
        )
        assert resp.status_code == 422

    @pytest.mark.anyio
    async def test_query_invalid_content_type(self, async_client):
        resp = await async_client.post(
            "/api/query",
            content="not json",
            headers={"content-type": "text/plain"},
        )
        assert resp.status_code == 422
