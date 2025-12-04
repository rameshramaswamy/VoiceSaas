from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks
from app.rag.service_robust import RobustIngestionService
from app.rag.query_expansion import QueryExpander
import structlog

logger = structlog.get_logger()

router = APIRouter()
ingestion_service = RobustIngestionService()
query_expander = QueryExpander()

# Helper for Background Task
async def background_ingest(file_name: str, file_content: bytes, tenant_id: str, agent_id: str):
    try:
        await ingestion_service.ingest_file(file_name, file_content, tenant_id, agent_id)
        logger.info("background_ingest_success", agent_id=agent_id)
    except Exception as e:
        logger.error("background_ingest_failed", error=str(e))

@router.post("/ingest")
async def ingest_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    tenant_id: str = Form(...),
    agent_id: str = Form(...)
):
    """
    Non-blocking Ingestion Endpoint.
    """
    # 1. Read content into memory (fast)
    content = await file.read()
    
    # 2. Validate
    if file.content_type not in ["application/pdf", "text/plain"]:
        raise HTTPException(status_code=400, detail="Unsupported file type")
    
    # 3. Queue Background Task
    background_tasks.add_task(
        background_ingest, 
        file.filename, 
        content, 
        tenant_id, 
        agent_id
    )
    
    return {"status": "accepted", "message": "Ingestion started in background"}

@router.post("/retrieve")
async def retrieve_context(
    query: str = Form(...),
    agent_id: str = Form(...)
):
    """
    Retrieval with Query Expansion.
    """
    # 1. Optimize Query
    optimized_query = await query_expander.expand_query(query)
    
    # 2. Retrieve (with Cache & Retry from Phase 4.0)
    context = await ingestion_service.retrieve_context(optimized_query, agent_id)
    
    return {
        "original_query": query,
        "optimized_query": optimized_query,
        "context": context
    }