"""
RAG Pipeline with LangChain + Qdrant

Flow:
    1. Load documents into a vector store (Qdrant)
    2. User asks a question
    3. Vector search retrieves relevant documents
    4. LLM generates an answer using those documents as context

Run:

    uvicorn concepts_copy.rag_api:app --reload --port 9006

Test:
    http://localhost:9006/docs
"""

import json
import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv(dotenv_path=Path(__file__).parent / '.env')
KNOWLEDGE_FILE = Path(__file__).parent / 'farming_knowledge_06.json'
PROMPTS_FILE = Path(__file__).parent / 'prompts.json'

from sentence_transformers import SentenceTransformer
from qdrant_ingestion import QdrantIngestion

#Vector Store
class SimpleVectorStore:
    def __init__(self, knowledge_path: Path | None = None):
        self.collection_name = "farming_docs"
        self.ingestion = QdrantIngestion(collection_name=self.collection_name)
        self.encoder = SentenceTransformer("all-MiniLM-L6-v2")
        if knowledge_path:
            self.ingestion.load_and_ingest(knowledge_path, self.encoder)

    def search(self, query: str, n_results: int = 3) -> list:
        """Search for documents similar to the query using semantic similarity."""
        query_vector = self.encoder.encode(query).tolist()
        results = self.ingestion.client.query_points(
            collection_name=self.collection_name,
            query_vector=query_vector,
            limit=n_results,
        )
        return [
            {
                "content": hit.payload["content"],
                "metadata": hit.payload["metadata"],
                "distance": hit.score,
            }
            for hit in results.points
        ]