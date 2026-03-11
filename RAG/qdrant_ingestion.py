"""
Qdrant ingestion helpers for Concept 6.
"""

import json
from pathlib import Path
from typing import Any

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

# Qdrant ingestion client for encoding and upserting documents.

class QdrantIngestion:

    def __init__(
        self,
        collection_name: str,
        vector_size: int = 384,
        url: str = "http://localhost:6433",
    ):
        self.collection_name = collection_name
        self.vector_size = vector_size
        self.url = url
        self._client: QdrantClient | None = None

    # lazily create and return the Qdrant client
    @property
    def client(self) -> QdrantClient:
      
        if self._client is None:
            self.create_client()
        return self._client

    # create the Qdrant client and collection if it doesn't exist
    def create_client(self) -> QdrantClient:
      
        self._client = QdrantClient(url=self.url)
        self._client.recreate_collection(
            collection_name=self.collection_name,
            vectors_config=VectorParams(
                size=self.vector_size, distance=Distance.COSINE
            ),
        )
        return self._client
    
# ingest documents into the Qdrant collection
    def ingest_documents(
        self,
        encoder: Any,
        docs: list[dict],
    ) -> int:

        if self._client is None:
            self.create_client()
        client = self._client

        if not docs:
            return 0

        contents = [d["content"] for d in docs]
        embeddings = encoder.encode(contents)

        points = [
            PointStruct(
                id=i,
                vector=embedding.tolist(),
                payload={"content": doc["content"], "metadata": doc["metadata"]},
            )
            for i, (doc, embedding) in enumerate(zip(docs, embeddings))
        ]

        client.upsert(
            collection_name=self.collection_name,
            points=points,
        )
        return len(points)

    def load_and_ingest(self, path: Path, encoder: Any) -> int:
       
        with path.open("r", encoding="utf-8") as f:
            docs = json.load(f)
        return self.ingest_documents(encoder=encoder, docs=docs)
