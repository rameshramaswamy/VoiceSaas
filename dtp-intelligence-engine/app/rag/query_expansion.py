import structlog
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from app.core.config import settings

logger = structlog.get_logger()

class QueryExpander:
    def __init__(self):
        self.llm = ChatOpenAI(
            api_key=settings.OPENAI_API_KEY, 
            model="gpt-3.5-turbo", # Fast & cheap model for this task
            temperature=0
        )
        
        self.prompt = ChatPromptTemplate.from_template(
            """You are a helpful assistant that optimizes voice search queries for a vector database.
            
            User's raw spoken query: "{query}"
            
            Task: Rewrite this query to be a complete, grammatically correct sentence that captures the specific intent. 
            Do not add new facts, just expand the phrasing to improve retrieval.
            
            Optimized Query:"""
        )
        
        self.chain = self.prompt | self.llm | StrOutputParser()

    async def expand_query(self, raw_query: str) -> str:
        """
        Transforms 'pricing?' -> 'What is the pricing structure and cost?'
        """
        # Optimization: Don't expand if query is already long
        if len(raw_query.split()) > 5:
            return raw_query

        try:
            expanded = await self.chain.ainvoke({"query": raw_query})
            logger.info("query_expanded", original=raw_query, expanded=expanded)
            return expanded
        except Exception as e:
            logger.error("expansion_failed", error=str(e))
            return raw_query # Fallback to original