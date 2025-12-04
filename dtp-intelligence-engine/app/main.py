from fastapi import FastAPI
from prometheus_client import make_asgi_app

from app.api.ingestion import router as ingestion_router
from app.api.tools import router as tools_router
from app.core.config import settings

# Dependency Injection
from app.tools.executor_parallel import ParallelToolExecutor
from app.rag.service_enterprise import EnterpriseIngestionService
import app.api.tools
import app.api.ingestion

# Inject Enterprise Services
app.api.tools.executor = ParallelToolExecutor()
app.api.ingestion.ingestion_service = EnterpriseIngestionService()

app = FastAPI(title="DTP Enterprise Intelligence Engine")

metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

app.include_router(ingestion_router, prefix="/api/v1/knowledge", tags=["RAG"])
app.include_router(tools_router, prefix="/api/v1/tools", tags=["Tools"])

@app.get("/health")
def health():
    return {"status": "ok", "mode": "enterprise"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=settings.PORT)