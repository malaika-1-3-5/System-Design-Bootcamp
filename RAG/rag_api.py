"""
Exposes REST endpoints for the RAG pipeline.
"""

import sys
from pathlib import Path

from fastapi import FastAPI, Query
from pydantic import BaseModel

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent

# Make imports resilient across different launch directories.
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    # Works when launched from repository root (e.g., `uvicorn RAG.rag_api:app`)
    from RAG.lang_chain import RAGPipeline
except ModuleNotFoundError:
    # Works when launched from inside the RAG directory (e.g., `uvicorn rag_api:app`)
    from lang_chain import RAGPipeline

rag = RAGPipeline()

app = FastAPI(
    title=" RAG Pipeline Demo",
    description="Retrieval-Augmented Generation: ask questions, get grounded answers",
    version="1.0.0",
)


class AskRequest(BaseModel):
    question: str
    n_results: int = 3


@app.post("/ask")
def ask_question(req: AskRequest):
    """
    Ask a farming question — the RAG pipeline will:
    1. Find relevant docs from the knowledge base
    2. Use them as context for the LLM
    3. Return a grounded answer with sources
    """
    return rag.query(req.question, n_results=req.n_results)


@app.get("/ask")
def ask_question_get(
    q: str = Query(..., description="Your farming question"),
    n: int = Query(3, description="Number of sources to retrieve"),
):
    """GET version for easy browser testing."""
    return rag.query(q, n_results=n)


@app.get("/documents")
def list_documents():
    """View all documents in the knowledge base."""
    return {
        "count": len(rag.knowledge),
        "documents": rag.knowledge,
    }


@app.get("/search")
def search_only(q: str = Query(...), n: int = Query(3)):
    """Search without LLM — shows just the retrieval step."""
    results = rag.search(q, n_results=n)
    return {"query": q, "results": results}
