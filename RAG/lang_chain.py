"""RAG pipeline primitives used by the FastAPI service."""

from __future__ import annotations

import json
import os
from pathlib import Path

from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from sentence_transformers import SentenceTransformer

try:
    from RAG.qdrant_ingestion import QdrantIngestion
except ModuleNotFoundError:
    from qdrant_ingestion import QdrantIngestion

BASE_DIR = Path(__file__).parent
ENV_PATH = BASE_DIR / ".env"
KNOWLEDGE_FILE = BASE_DIR / "farming_knowledge.json"
PROMPTS_FILE = BASE_DIR / "prompts.json"

load_dotenv(ENV_PATH)


class SimpleVectorStore:
    def __init__(self, knowledge_path: Path | None = None):
        self.collection_name = "farming_docs"
        self.ingestion = QdrantIngestion(collection_name=self.collection_name)
        self.encoder = SentenceTransformer("all-MiniLM-L6-v2")
        if knowledge_path and knowledge_path.exists():
            self.ingestion.load_and_ingest(knowledge_path, self.encoder)

    def search(self, query: str, n_results: int = 3) -> list[dict]:
        query_vector = self.encoder.encode(query).tolist()
        results = self.ingestion.client.query_points(
            collection_name=self.collection_name,
            query_vector=query_vector,
            limit=n_results,
        )
        return [
            {
                "content": hit.payload.get("content", ""),
                "metadata": hit.payload.get("metadata", {}),
                "distance": hit.score,
            }
            for hit in results.points
        ]


class RAGPipeline:
    def __init__(self):
        self.knowledge = self._load_knowledge(KNOWLEDGE_FILE)
        self.prompts = self._load_prompts(PROMPTS_FILE)
        self.vectorstore: SimpleVectorStore | None = None
        self.client = self._build_llm_client()

    def _get_vectorstore(self) -> SimpleVectorStore:
        if self.vectorstore is None:
            self.vectorstore = SimpleVectorStore(knowledge_path=KNOWLEDGE_FILE)
        return self.vectorstore

    def search(self, question: str, n_results: int = 3) -> list[dict]:
        return self._get_vectorstore().search(question, n_results=n_results)

    def _load_knowledge(self, path: Path) -> list[dict]:
        if not path.exists():
            return []
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)

    def _load_prompts(self, path: Path) -> dict:
        default_prompts = {
            "system": "You are a helpful agricultural advisor.",
            "template": "Context:\n{context}\n\nQuestion: {question}\nAnswer:",
        }
        if not path.exists():
            return default_prompts

        try:
            with path.open("r", encoding="utf-8") as f:
                data = json.load(f)
            return {
                "system": data.get("system", default_prompts["system"]),
                "template": data.get("template", default_prompts["template"]),
            }
        except Exception:
            return default_prompts

    def _build_llm_client(self) -> ChatOpenAI | None:
        api_key = os.getenv("OPENAI_API_KEY")
        base_url = os.getenv("OPENAI_BASE_URL")
        model = os.getenv("OPENAI_MODEL")

        if not api_key or not model:
            return None

        kwargs = {
            "api_key": api_key,
            "model": model,
            "temperature": 0.2,
        }
        if base_url:
            kwargs["base_url"] = base_url

        return ChatOpenAI(**kwargs)

    def query(self, question: str, n_results: int = 3) -> dict:
        search_results = self.search(question, n_results=n_results)
        context = "\n\n".join([item["content"] for item in search_results])

        if self.client is None:
            return {
                "question": question,
                "answer": "LLM is not configured. Set OPENAI_API_KEY and OPENAI_MODEL.",
                "sources": search_results,
            }

        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", self.prompts["system"]),
                ("human", self.prompts["template"]),
            ]
        )
        message = prompt.invoke({"context": context, "question": question})

        try:
            response = self.client.invoke(message)
            answer = response.content
        except Exception as exc:
            answer = f"LLM request failed: {exc}"

        return {
            "question": question,
            "answer": answer,
            "sources": search_results,
        }
