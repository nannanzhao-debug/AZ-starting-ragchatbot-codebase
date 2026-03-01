"""Unit tests for the RAG engine components."""

import pytest

from backend.rag_engine import (
    CourseChunk,
    load_courses,
    retrieve,
    generate_response,
    list_courses,
    COURSE_DATA,
)


class TestLoadCourses:
    def test_loads_single_course(self, sample_courses):
        load_courses(sample_courses[:1])
        assert "ml101" in COURSE_DATA
        assert len(COURSE_DATA) == 1

    def test_loads_multiple_courses(self, sample_courses):
        load_courses(sample_courses)
        assert "ml101" in COURSE_DATA
        assert "dl201" in COURSE_DATA

    def test_clears_previous_data(self, sample_courses):
        load_courses(sample_courses)
        load_courses(sample_courses[:1])
        assert len(COURSE_DATA) == 1

    def test_chunks_long_content(self):
        long_content = " ".join(["word"] * 200)
        load_courses([{"id": "test", "title": "Test", "content": long_content}])
        assert len(COURSE_DATA["test"]) > 1

    def test_empty_content(self):
        load_courses([{"id": "empty", "title": "Empty", "content": ""}])
        assert COURSE_DATA["empty"] == []


class TestRetrieve:
    def test_returns_matching_chunks(self, loaded_courses):
        results = retrieve("neural networks deep learning")
        assert len(results) > 0

    def test_respects_top_k(self, loaded_courses):
        results = retrieve("learning", top_k=1)
        assert len(results) <= 1

    def test_no_matches_returns_empty(self, loaded_courses):
        results = retrieve("xyznonexistent")
        assert results == []

    def test_returns_course_chunks(self, loaded_courses):
        results = retrieve("machine learning")
        for chunk in results:
            assert isinstance(chunk, CourseChunk)
            assert chunk.content


class TestGenerateResponse:
    def test_with_chunks(self):
        chunks = [
            CourseChunk("ml101", "ML Basics", "Supervised learning uses labels", 0),
        ]
        response = generate_response("What is supervised learning?", chunks)
        assert "Supervised learning" in response
        assert "ML Basics" in response

    def test_empty_chunks_returns_fallback(self):
        response = generate_response("anything", [])
        assert "couldn't find" in response.lower()

    def test_includes_query_in_response(self):
        chunks = [
            CourseChunk("ml101", "ML", "content", 0),
        ]
        response = generate_response("test query", chunks)
        assert "test query" in response


class TestListCourses:
    def test_lists_loaded_courses(self, loaded_courses):
        courses = list_courses()
        ids = [c["id"] for c in courses]
        assert "ml101" in ids
        assert "dl201" in ids

    def test_includes_chunk_count(self, loaded_courses):
        courses = list_courses()
        for course in courses:
            assert "num_chunks" in course
            assert course["num_chunks"] > 0

    def test_empty_when_no_courses(self):
        COURSE_DATA.clear()
        assert list_courses() == []
