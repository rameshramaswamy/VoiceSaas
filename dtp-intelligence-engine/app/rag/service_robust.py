import structlog
from app.rag.service import IngestionService # Inherit or wrap
from app.core.cache import CacheService
from app.core.resilience import external_api_retry

logger = structlog.get_logger()

class RobustIngestionService(IngestionService):
    
    @external_api_retry
    async def retrieve_context(self, query: str, agent_id: str) -> str:
        """
        Enterprise Retrieval: Cache -> Embed (Retry) -> Vector Search (Retry)
        """
        # 1. Check Cache (Fast Path)
        cached_ctx = await CacheService.get_rag_context(query, agent_id)
        if cached_ctx:
            logger.info("rag_cache_hit", query=query[:20])
            return cached_ctx

        # 2. Embed Query (Protected by Retry)
        # Note: We call the parent method logic here, but broken down for granular control
        logger.info("rag_cache_miss", query=query[:20])
        
        query_vector = await self.embeddings.aembed_query(query)
        
        # 3. Search Pinecone (Protected by Retry)
        matches = await self.vector_store.query_similar(query_vector, namespace=agent_id)
        
        # 4. Construct Context
        context_blocks = [m['metadata']['text'] for m in matches]
        context_str = "\n---\n".join(context_blocks)
        
        # 5. Save to Cache
        if context_str:
            await CacheService.set_rag_context(query, agent_id, context_str)
            
        return context_str