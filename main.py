"""
AI Integration Service API
A comprehensive FastAPI application for AI-powered services:
- Question matching using semantic search
- Vendor relationship graph analysis (3-7 degree connections)
- AI-powered vendor matching and discovery

This refactored version uses a clean modular architecture:
- app/models: Database models
- app/schemas: Pydantic schemas for API requests/responses
- app/services: Business logic and utilities
- app/api: API route handlers
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.services import init_db, init_openai_client
from app.api import questionnaire_router, responses_router, admin_router, vendors_router, risk_router

# Neo4j imports (optional)
try:
    from app.services.neo4j_service import init_neo4j, close_neo4j, is_neo4j_available
    NEO4J_IMPORTS_OK = True
except ImportError:
    NEO4J_IMPORTS_OK = False


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan: startup and shutdown events.
    """
    # Startup
    print("Starting application...")
    init_db()
    init_openai_client()

    # Try to initialize Neo4j (optional - graceful fallback to MySQL)
    if NEO4J_IMPORTS_OK:
        try:
            init_neo4j()
            if is_neo4j_available():
                print("✅ Neo4j connected - Using graph database for vendor relationships")
            else:
                print("⚠️  Neo4j unavailable - Using MySQL for vendor relationships")
        except Exception as e:
            print(f"⚠️  Neo4j initialization failed: {e}")
            print("   Continuing with MySQL fallback")
    else:
        print("ℹ️  Neo4j driver not installed - Using MySQL for vendor relationships")
        print("   Install with: pip install neo4j")

    print("Application ready!")

    yield

    # Shutdown
    print("Shutting down application...")
    if NEO4J_IMPORTS_OK:
        try:
            close_neo4j()
        except:
            pass


# Create FastAPI application
app = FastAPI(
    title="AI Integration Service API",
    description="Multi-tenant AI services: Question matching, Vendor relationship graph, AI-powered discovery",
    version="5.0.0",
    lifespan=lifespan
)


# Register routers
app.include_router(questionnaire_router)
app.include_router(responses_router)
app.include_router(admin_router)
app.include_router(vendors_router)
app.include_router(risk_router)


@app.get("/")
async def root():
    """
    Root endpoint with API information.
    """
    return {
        "message": "Welcome to AI Integration Service API v5.0",
        "docs": "/docs",
        "version": "5.0.0",
        "architecture": "modular",
        "ai_provider": "OpenAI",
        "embedding_model": "text-embedding-3-small",
        "services": [
            "question_matching",
            "vendor_relationship_graph",
            "vendor_ai_matching",
            "multi_tenant_support"
        ],
        "features": [
            "batch_processing",
            "graph_traversal_3_to_7_degrees",
            "semantic_search",
            "auto_linking",
            "retry_logic"
        ]
    }


@app.get("/health")
async def health_check():
    """
    Health check endpoint.
    """
    return {"status": "healthy", "version": "5.0.0"}


# For backward compatibility, add the old endpoint paths
from typing import Optional
from fastapi import Depends
from sqlmodel import Session
from app.schemas import QuestionnaireInput, BatchCreateInput
from app.services import get_session


@app.post("/process-questionnaire")
async def process_questionnaire_legacy(
    questionnaire: QuestionnaireInput,
    session: Session = Depends(get_session)
):
    """Legacy endpoint - redirects to new path."""
    from app.api.questionnaire import process_questionnaire
    return await process_questionnaire(questionnaire, session)


@app.post("/batch-process-questionnaire")
async def batch_process_questionnaire_legacy(
    questionnaire: QuestionnaireInput,
    session: Session = Depends(get_session)
):
    """Legacy endpoint - redirects to new path."""
    from app.api.questionnaire import batch_process_questionnaire
    return await batch_process_questionnaire(questionnaire, session)


@app.post("/create-response")
async def create_response_legacy(
    vendor_id: str,
    question_id: str,
    question_text: str,
    answer_text: str,
    evidence: Optional[str] = None,
    session: Session = Depends(get_session)
):
    """Legacy endpoint - redirects to new path."""
    from app.api.responses import create_response
    return await create_response(vendor_id, question_id, question_text, answer_text, evidence, session)


@app.post("/batch-create-responses")
async def batch_create_responses_legacy(
    input_data: BatchCreateInput,
    session: Session = Depends(get_session)
):
    """Legacy endpoint - redirects to new path."""
    from app.api.responses import batch_create_responses
    return await batch_create_responses(input_data, session)


@app.get("/responses")
async def list_responses_legacy(
    vendor_id: Optional[str] = None,
    session: Session = Depends(get_session)
):
    """Legacy endpoint - redirects to new path."""
    from app.api.responses import list_responses
    return await list_responses(vendor_id, session)


@app.get("/links")
async def list_links_legacy(session: Session = Depends(get_session)):
    """Legacy endpoint - redirects to new path."""
    from app.api.admin import list_links
    return await list_links(session)


@app.delete("/responses/{response_id}")
async def delete_response_legacy(
    response_id: int,
    session: Session = Depends(get_session)
):
    """Legacy endpoint - redirects to new path."""
    from app.api.responses import delete_response
    return await delete_response(response_id, session)


@app.delete("/links/{link_id}")
async def delete_link_legacy(
    link_id: int,
    session: Session = Depends(get_session)
):
    """Legacy endpoint - redirects to new path."""
    from app.api.admin import delete_link
    return await delete_link(link_id, session)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
