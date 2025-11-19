"""
Effortless-Respond API v5.0 - Intelligent Fallback Chain
A FastAPI application for finding saved answers to new questions using the new 4-step Intelligent Fallback Chain.

New in v5.0:
- Migrated from PostgreSQL/pgvector to MySQL 8+ with native VECTOR support
- Implemented Intelligent Fallback Chain: ID Match → Fuzzy Match → Semantic Search → Confidence Engine
- Added thefuzz library for Levenshtein distance fuzzy matching
- Integrated MySQL VECTOR_COSINE_DISTANCE for semantic search
- Added MatchLog table for analytics tracking
- Enhanced batch processing with cost-optimized fallback logic

Architecture:
- app/models: Database models (SQLModel + MySQL)
- app/schemas: Pydantic schemas for API requests/responses
- app/services: Business logic and utilities
- app/api: API route handlers
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.services import init_db, init_openai_client
from app.api import questionnaire_router, responses_router, admin_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan: startup and shutdown events.
    """
    # Startup
    print("Starting application...")
    init_db()
    init_openai_client()
    print("Application ready!")

    yield

    # Shutdown
    print("Shutting down application...")


# Create FastAPI application
app = FastAPI(
    title="Effortless-Respond API v5.0 - Intelligent Fallback Chain",
    description="Multi-tenant question matching using 4-step Intelligent Fallback Chain with MySQL 8+ VECTOR support",
    version="5.0.0",
    lifespan=lifespan
)


# Register routers
app.include_router(questionnaire_router)
app.include_router(responses_router)
app.include_router(admin_router)


@app.get("/")
async def root():
    """
    Root endpoint with API information.
    """
    return {
        "message": "Welcome to Effortless-Respond API v5.0 - Intelligent Fallback Chain",
        "docs": "/docs",
        "version": "5.0.0",
        "architecture": "modular",
        "database": "MySQL 8+ with native VECTOR support",
        "ai_provider": "OpenAI",
        "embedding_model": "text-embedding-3-small",
        "features": [
            "multi_tenant",
            "intelligent_fallback_chain",
            "id_match",
            "fuzzy_match_levenshtein",
            "semantic_search_mysql_vector",
            "reranker_confidence_engine",
            "batch_processing",
            "auto_linking",
            "match_logging",
            "retry_logic"
        ],
        "fallback_chain": [
            "Step 1: ID Match (saved links + exact ID)",
            "Step 2: Fuzzy Match (Levenshtein distance, threshold 0.90)",
            "Step 3: Semantic Search (AI embeddings via MySQL VECTOR_COSINE_DISTANCE)",
            "Step 4: Re-Ranker + Confidence Engine (thresholds: >0.92 HIGH, >=0.80 MEDIUM, <0.80 LOW)"
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
