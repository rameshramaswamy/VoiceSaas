from typing import Optional, Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.pydantic_v1 import BaseModel, Field
from app.core.config import settings
import structlog

logger = structlog.get_logger()

# Define the structure we want the LLM to output
class SearchFilters(BaseModel):
    query: str = Field(description="The semantic search concept")
    filter: Dict[str, Any] = Field(description="Pinecone metadata filters", default_factory=dict)

class QueryAnalyzer:
    def __init__(self):
        self.llm = ChatOpenAI(
            api_key=settings.OPENAI_API_KEY, 
            model="gpt-3.5-turbo", 
            temperature=0
        )
        # Using OpenAI Function Calling to enforce JSON structure
        self.structured_llm = self.llm.with_structured_output(SearchFilters)

    async def analyze_query(self, raw_query: str) -> SearchFilters:
        """
        Input: "How much did Acme Corp pay in 2023?"
        Output: { "query": "payment amount", "filter": {"client": "Acme Corp", "year": "2023"} }
        """
        try:
            system = """
            You are a search optimizer. Extract metadata filters from the query.
            Supported metadata fields: 'year', 'client', 'category', 'status'.
            If no filters apply, return empty dict.
            """
            
            result = await self.structured_llm.ainvoke([
                {"role": "system", "content": system},
                {"role": "user", "content": raw_query}
            ])
            
            logger.info("query_analysis", original=raw_query, filters=result.filter)
            return result
        except Exception as e:
            logger.error("query_analysis_failed", error=str(e))
            # Fallback: Search everything
            return SearchFilters(query=raw_query, filter={})