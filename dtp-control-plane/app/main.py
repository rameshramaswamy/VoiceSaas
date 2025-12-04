from fastapi import FastAPI
from fastapi.responses import ORJSONResponse
from app.core.config import settings
from app.core.logging import configure_logging
from app.core.middleware import EnterpriseMiddleware
from app.core.exceptions import add_exception_handlers
from app.core.lifecycle import register_lifecycle_events

# Routes
from app.api.health import router as health_router
from app.modules.tenants.routes import router as tenant_router
from app.modules.agents.routes import router as agent_router

# 1. Configure Logging
configure_logging()

app = FastAPI(
    title=settings.PROJECT_NAME,
    default_response_class=ORJSONResponse,
    docs_url=None if settings.ENV == "production" else "/docs"
)

# 2. Middleware & Exceptions
app.add_middleware(EnterpriseMiddleware)
add_exception_handlers(app)

# 3. Lifecycle (Startup/Shutdown)
register_lifecycle_events(app)

# 4. Routes
app.include_router(health_router, tags=["Health"]) # New Health/Readiness
app.include_router(tenant_router, prefix="/api/v1/tenants", tags=["Tenants"])
app.include_router(agent_router, prefix="/api/v1/agents", tags=["Agents"])