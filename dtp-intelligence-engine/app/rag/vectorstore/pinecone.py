from pinecone import Pinecone
from typing import List, Dict
from app.core.config import settings
import structlog

logger = structlog.get_logger()

class PineconeStore:
    def __init__(self):
        self.pc = Pinecone(api_key=settings.PINECONE_API_KEY)
        self.index = self.pc.Index(settings.PINECONE_INDEX_NAME)

    async def upsert_vectors(self, vectors: List[Dict], namespace: str):
        """
        Uploads vectors to specific tenant namespace.
        vectors format: [{'id': '1', 'values': [0.1, ...], 'metadata': {...}}]
        """
        try:
            # Pinecone upsert is synchronous in the python client, 
            # but fast enough for small batches.
            # Upsert in batches of 100 to avoid limits
            batch_size = 100
            for i in range(0, len(vectors), batch_size):
                batch = vectors[i:i + batch_size]
                self.index.upsert(vectors=batch, namespace=namespace)
            
            logger.info("vectors_upserted", count=len(vectors), namespace=namespace)
        except Exception as e:
            logger.error("pinecone_upsert_error", error=str(e))
            raise e

    async def query_similar(self, vector: List[float], namespace: str, top_k: int = 3) -> List[Dict]:
        """
        Retrieves context relevant to the vector query.
        """
        try:
            response = self.index.query(
                vector=vector,
                top_k=top_k,
                namespace=namespace,
                include_metadata=True
            )
            return response['matches']
        except Exception as e:
            logger.error("pinecone_query_error", error=str(e))
            return []