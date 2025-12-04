import uuid
import structlog
from typing import List

# LangChain Utilities for Chunking & Embedding
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings

from app.rag.loaders.pdf import PDFLoader
from app.rag.vectorstore.pinecone import PineconeStore
from app.core.config import settings

logger = structlog.get_logger()

class IngestionService:
    def __init__(self):
        self.vector_store = PineconeStore()
        
        # 1. Embedder (OpenAI text-embedding-3-small is cheap and fast)
        self.embeddings = OpenAIEmbeddings(
            api_key=settings.OPENAI_API_KEY,
            model="text-embedding-3-small" 
        )
        
        # 2. Chunker (Splits text into context-aware pieces)
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            separators=["\n\n", "\n", " ", ""]
        )

    async def ingest_file(self, file_name: str, file_content: bytes, tenant_id: str, agent_id: str):
        """
        Full Pipeline: PDF -> Text -> Chunks -> Embeddings -> Pinecone
        """
        try:
            logger.info("ingest_started", file=file_name, tenant=tenant_id)
            
            # 1. Extract Text
            if file_name.endswith(".pdf"):
                raw_text = PDFLoader.extract_text(file_content)
            else:
                raw_text = file_content.decode("utf-8") # Plain text fallback

            # 2. Chunk Text
            chunks = self.text_splitter.split_text(raw_text)
            logger.info("text_chunked", chunks=len(chunks))

            # 3. Generate Embeddings (Async batching handled by LangChain)
            vectors = await self.embeddings.aembed_documents(chunks)

            # 4. Format for Pinecone
            pinecone_vectors = []
            for i, (chunk_text, vector) in enumerate(zip(chunks, vectors)):
                vector_id = f"{agent_id}_{uuid.uuid4()}"
                pinecone_vectors.append({
                    "id": vector_id,
                    "values": vector,
                    "metadata": {
                        "text": chunk_text,
                        "source": file_name,
                        "agent_id": agent_id,
                        "chunk_index": i
                    }
                })

            # 5. Upsert (Using agent_id as namespace for strict isolation)
            # Alternatively, use tenant_id as namespace and filter by agent_id metadata
            namespace = agent_id 
            await self.vector_store.upsert_vectors(pinecone_vectors, namespace=namespace)
            
            logger.info("ingest_complete", vectors=len(pinecone_vectors))
            return {"status": "success", "chunks": len(pinecone_vectors)}

        except Exception as e:
            logger.error("ingestion_failed", error=str(e))
            raise e

    async def retrieve_context(self, query: str, agent_id: str) -> str:
        """
        RAG Retrieval Step
        """
        # 1. Embed Query
        query_vector = await self.embeddings.aembed_query(query)
        
        # 2. Search Pinecone
        matches = await self.vector_store.query_similar(query_vector, namespace=agent_id)
        
        # 3. Concatenate Context
        context_blocks = [m['metadata']['text'] for m in matches]
        return "\n---\n".join(context_blocks)