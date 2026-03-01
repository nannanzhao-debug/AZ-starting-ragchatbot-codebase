"""RAG engine for course content retrieval and response generation."""

from dataclasses import dataclass


@dataclass
class CourseChunk:
    course_id: str
    title: str
    content: str
    chunk_index: int


# In-memory course store (would be a vector DB in production)
COURSE_DATA: dict[str, list[CourseChunk]] = {}


def load_courses(courses: list[dict]) -> None:
    """Load course data into the in-memory store."""
    COURSE_DATA.clear()
    for course in courses:
        course_id = course["id"]
        chunks = []
        # Split content into chunks of ~200 chars
        content = course.get("content", "")
        words = content.split()
        chunk_text = ""
        chunk_idx = 0
        for word in words:
            if len(chunk_text) + len(word) + 1 > 200:
                chunks.append(CourseChunk(
                    course_id=course_id,
                    title=course["title"],
                    content=chunk_text.strip(),
                    chunk_index=chunk_idx,
                ))
                chunk_text = ""
                chunk_idx += 1
            chunk_text += word + " "
        if chunk_text.strip():
            chunks.append(CourseChunk(
                course_id=course_id,
                title=course["title"],
                content=chunk_text.strip(),
                chunk_index=chunk_idx,
            ))
        COURSE_DATA[course_id] = chunks


def retrieve(query: str, top_k: int = 3) -> list[CourseChunk]:
    """Retrieve the most relevant chunks for a query.

    Uses simple keyword matching. A production system would use
    vector similarity search.
    """
    query_terms = set(query.lower().split())
    scored: list[tuple[float, CourseChunk]] = []

    for chunks in COURSE_DATA.values():
        for chunk in chunks:
            chunk_terms = set(chunk.content.lower().split())
            overlap = len(query_terms & chunk_terms)
            if overlap > 0:
                score = overlap / max(len(query_terms), 1)
                scored.append((score, chunk))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [chunk for _, chunk in scored[:top_k]]


def generate_response(query: str, chunks: list[CourseChunk]) -> str:
    """Generate a response from retrieved chunks.

    In production this would call an LLM. Here we concatenate context.
    """
    if not chunks:
        return "I couldn't find relevant course material for your question."

    context_parts = []
    for chunk in chunks:
        context_parts.append(f"[{chunk.title}]: {chunk.content}")

    context = "\n".join(context_parts)
    return (
        f"Based on the course materials:\n\n{context}\n\n"
        f"This information is relevant to your query: \"{query}\""
    )


def list_courses() -> list[dict]:
    """Return metadata for all loaded courses."""
    courses = []
    seen = set()
    for course_id, chunks in COURSE_DATA.items():
        if course_id not in seen:
            seen.add(course_id)
            courses.append({
                "id": course_id,
                "title": chunks[0].title if chunks else course_id,
                "num_chunks": len(chunks),
            })
    return courses
