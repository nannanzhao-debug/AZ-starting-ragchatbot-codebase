"""FastAPI application for the RAG chatbot."""

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from backend.rag_engine import retrieve, generate_response, list_courses

app = FastAPI(title="RAG Course Chatbot")

# Mount static files for the frontend (requires the directory to exist)
app.mount("/static", StaticFiles(directory="static"), name="static")


class QueryRequest(BaseModel):
    question: str
    top_k: int = 3


class QueryResponse(BaseModel):
    answer: str
    sources: list[dict]


@app.get("/")
def root():
    return {"status": "ok", "message": "RAG Course Chatbot API"}


@app.post("/api/query")
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


@app.get("/api/courses")
def courses():
    return {"courses": list_courses()}
