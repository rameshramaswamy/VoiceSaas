import uuid
import structlog
from typing import Dict, List, Any

# Base Services & Utilities
from app.rag.service_robust import RobustIngestionService
from app.rag.loaders.pdf import PDFLoader
from app.rag.security import PIIScrubber
from app.rag.query_analysis import QueryAnalyzer
from app.core.cache import CacheService
from app.core.resilience import external_api_retry

logger = structlog.get_logger()

class EnterpriseIngestionService(RobustIngestionService):
    def __init__(self):
        """
        Initialize the Enterprise RAG Service.
        Inherits Embeddings, Text Splitter, and Vector Store from RobustIngestionService.
        Adds Query Analysis for precision retrieval.
        """
        super().__init__()
        self.query_analyzer = QueryAnalyzer()

    async def ingest_file(self, file_name: str, file_content: bytes, tenant_id: str, agent_id: str):
        """
        Enterprise Ingestion Pipeline:
        1. Extract Text
        2. Scrub PII (Emails, Phones, Credit Cards)
        3. Chunk
        4. Embed
        5. Upsert to Pinecone (with Metadata)
        """
        try:
            logger.info("enterprise_ingest_started", file=file_name, tenant=tenant_id, agent=agent_id)
            
            # 1. Extract Text
            if file_name.lower().endswith(".pdf"):
                raw_text = PDFLoader.extract_text(file_content)
            else:
                # Assume text/plain or markdown
                raw_text = file_content.decode("utf-8", errors="ignore")

            # 2. Security: Scrub PII
            clean_text = PIIScrubber.scrub(raw_text)
            
            if len(clean_text.strip()) == 0:
                logger.warning("ingest_skipped_empty", file=file_name)
                return {"status": "skipped", "reason": "empty_after_scrubbing"}

            # 3. Chunk Text
            chunks = self.text_splitter.split_text(clean_text)
            logger.info("text_chunked", chunks=len(chunks))

            # 4. Generate Embeddings
            # Uses the embeddings model initialized in parent class
            vectors = await self.embeddings.aembed_documents(chunks)

            # 5. Format for Pinecone
            pinecone_vectors = []
            for i, (chunk_text, vector) in enumerate(zip(chunks, vectors)):
                # Unique ID for the vector
                vector_id = f"{agent_id}_{uuid.uuid4()}"
                
                # Metadata for filtering and context reconstruction
                pinecone_vectors.append({
                    "id": vector_id,
                    "values": vector,
                    "metadata": {
                        "text": chunk_text,
                        "source": file_name,
                        "agent_id": agent_id,
                        "tenant_id": tenant_id,
                        "chunk_index": i
                        # Future: Add 'year', 'category' via LLM classification here if needed
                    }
                })

            # 6. Upsert to Vector Store
            # We use agent_id as namespace for strict multi-tenant isolation
            await self.vector_store.upsert_vectors(pinecone_vectors, namespace=agent_id)
            
            logger.info("enterprise_ingest_complete", vectors=len(pinecone_vectors))
            return {"status": "success", "chunks": len(pinecone_vectors)}

        except Exception as e:
            logger.error("enterprise_ingest_failed", error=str(e), file=file_name)
            raise e

    @external_api_retry
    async def retrieve_context(self, query: str, agent_id: str) -> str:
        """
        Enterprise Retrieval Pipeline:
        1. Analyze Query (Extract Filters + Optimize phrasing)
        2. Check Cache (using Optimized Query)
        3. Embed Optimized Query
        4. Vector Search with Metadata Filters
        5. Cache & Return
        """
        try:
            # 1. Analyze Query (Self-Querying)
            # Transforms "pricing for Acme" -> query="pricing", filter={"client": "Acme"}
            analysis = await self.query_analyzer.analyze_query(query)
            optimized_query = analysis.query
            metadata_filters = analysis.filter

            logger.info("retrieval_analysis", original=query, optimized=optimized_query, filters=metadata_filters)

            # 2. Check Cache
            # We cache based on the optimized query to increase hit rate across similar user phrasings
            cached_ctx = await CacheService.get_rag_context(optimized_query, agent_id)
            if cached_ctx:
                logger.info("rag_cache_hit", query=optimized_query[:20])
                return cached_ctx

            # 3. Embed the Optimized Query
            query_vector = await self.embeddings.aembed_query(optimized_query)

            # 4. Search Pinecone with Filters
            # Accessing the underlying Pinecone index directly to support 'filter'
            # (The basic wrapper might not expose filter, so we bypass to the SDK)
            response = self.vector_store.index.query(
                vector=query_vector,
                top_k=4, # Retrieve slightly more context for enterprise
                namespace=agent_id,
                filter=metadata_filters, 
                include_metadata=True
            )
            
            matches = response.get('matches', [])
            
            # 5. Construct Context
            if not matches:
                logger.info("rag_no_matches_found", query=optimized_query)
                return ""

            context_blocks = [m['metadata']['text'] for m in matches]
            context_str = "\n---\n".join(context_blocks)

            # 6. Save to Cache
            if context_str:
                await CacheService.set_rag_context(optimized_query, agent_id, context_str)

            return context_str

        except Exception as e:
            logger.error("enterprise_retrieval_failed", error=str(e), query=query)
            # Fallback: In case of specialized error, return empty string so call doesn't crash
            return ""