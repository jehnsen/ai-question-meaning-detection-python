"""
Effortless-Respond API
A FastAPI application for finding saved answers to new questions using AI-driven semantic search.
Batch processing endpoint with 4-step logic and OpenAI embeddings.
"""

from contextlib import asynccontextmanager
from typing import Optional, List, Dict, Any
import time
from datetime import datetime, timedelta, timezone

from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy import create_engine, text, func
from sqlmodel import SQLModel, Field, select, Session, Column
from sqlalchemy import DateTime
from pgvector.sqlalchemy import Vector
from pydantic import BaseModel
import os
from dotenv import load_dotenv
from openai import OpenAI, RateLimitError, APIError

# Load environment variables
load_dotenv()

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/effortless_respond")

# OpenAI configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY environment variable is required")

# Global OpenAI client
openai_client: Optional[OpenAI] = None


# ==================== DATABASE MODELS ====================

class ResponseEntry(SQLModel, table=True):
    """
    Stores canonical answers and their vector embeddings.
    """
    __tablename__ = "responseentry"

    id: Optional[int] = Field(default=None, primary_key=True)
    question_id: str = Field(index=True, unique=True)  # Canonical question ID
    question_text: str  # The text of the question
    answer_text: str  # The saved answer
    evidence: Optional[str] = Field(default=None)  # Associated compliance evidence
    embedding: list[float] = Field(sa_type=Vector(1024))  # 1024-dim OpenAI vector


class QuestionLink(SQLModel, table=True):
    """
    Maps new question IDs to existing answers (saved links).
    """
    __tablename__ = "questionlink"

    id: Optional[int] = Field(default=None, primary_key=True)
    new_question_id: str = Field(index=True, unique=True)  # ID of the new question
    linked_response_id: int = Field(foreign_key="responseentry.id")  # ID of the linked answer


class AnalyticsEvent(SQLModel, table=True):
    """
    Tracks all questionnaire processing events for analytics.
    """
    __tablename__ = "analyticsevent"

    id: Optional[int] = Field(default=None, primary_key=True)
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False, index=True)
    )

    # Event details
    event_type: str = Field(index=True)  # "questionnaire_processed", "question_matched", etc.
    questionnaire_id: Optional[str] = Field(default=None, index=True)  # Batch identifier
    question_id: Optional[str] = Field(default=None, index=True)  # Individual question ID

    # Result details
    status: Optional[str] = Field(default=None, index=True)  # LINKED, CONFIRMATION_REQUIRED, NO_MATCH
    match_method: Optional[str] = Field(default=None)  # "saved_link", "exact_id", "ai_high_conf", "ai_medium_conf"
    similarity_score: Optional[float] = Field(default=None)  # AI similarity score (0-1)

    # Performance metrics
    processing_time_ms: Optional[int] = Field(default=None)  # Processing time in milliseconds

    # Additional context
    canonical_question_id: Optional[str] = Field(default=None)  # Matched canonical question
    vendor_name: Optional[str] = Field(default=None, index=True)  # Vendor being assessed
    industry: Optional[str] = Field(default=None, index=True)  # Vendor industry


class UsageMetrics(SQLModel, table=True):
    """
    Aggregated daily usage metrics for dashboard.
    """
    __tablename__ = "usagemetrics"

    id: Optional[int] = Field(default=None, primary_key=True)
    date: datetime = Field(
        sa_column=Column(DateTime(timezone=True), nullable=False, index=True, unique=True)
    )

    # Volume metrics
    total_questionnaires: int = Field(default=0)
    total_questions: int = Field(default=0)

    # Status breakdown
    linked_count: int = Field(default=0)
    confirmation_required_count: int = Field(default=0)
    no_match_count: int = Field(default=0)

    # Match method breakdown
    saved_link_count: int = Field(default=0)
    exact_id_count: int = Field(default=0)
    ai_high_conf_count: int = Field(default=0)
    ai_medium_conf_count: int = Field(default=0)

    # Performance metrics
    avg_processing_time_ms: Optional[float] = Field(default=None)
    total_processing_time_ms: int = Field(default=0)


# ==================== PYDANTIC MODELS ====================

class Question(BaseModel):
    """Model for a single question in the questionnaire."""
    id: str
    text: str


class QuestionnaireInput(BaseModel):
    """Input model for batch processing questionnaire."""
    questions: list[Question]


class ResponseData(BaseModel):
    """Model for response data."""
    answer_text: str
    evidence: Optional[str]
    canonical_question_text: str


class QuestionResult(BaseModel):
    """Model for a single question result."""
    id: str
    status: str  # "LINKED", "CONFIRMATION_REQUIRED", "NO_MATCH"
    data: Optional[ResponseData] = None


class QuestionnaireOutput(BaseModel):
    """Output model for batch processing questionnaire."""
    results: list[QuestionResult]


# ==================== ANALYTICS PYDANTIC MODELS ====================

class DashboardOverview(BaseModel):
    """Overview statistics for the analytics dashboard."""
    # Today's metrics
    today_questionnaires: int
    today_questions: int
    today_linked: int
    today_confirmation_required: int
    today_no_match: int

    # All-time metrics
    total_questionnaires: int
    total_questions: int
    total_response_entries: int
    total_question_links: int

    # Match effectiveness
    linked_percentage: float
    confirmation_percentage: float
    no_match_percentage: float

    # Performance
    avg_processing_time_ms: Optional[float]


class MatchMethodBreakdown(BaseModel):
    """Breakdown of how questions are being matched."""
    saved_link: int
    exact_id: int
    ai_high_confidence: int
    ai_medium_confidence: int
    no_match: int

    # Percentages
    saved_link_pct: float
    exact_id_pct: float
    ai_high_confidence_pct: float
    ai_medium_confidence_pct: float
    no_match_pct: float


class TimeSeriesDataPoint(BaseModel):
    """Single data point for time series charts."""
    date: str  # ISO format date
    value: int


class TimeSeriesData(BaseModel):
    """Time series data for trend analysis."""
    dates: List[str]
    questionnaires: List[int]
    questions: List[int]
    linked: List[int]
    confirmation_required: List[int]
    no_match: List[int]


class TopCanonicalQuestion(BaseModel):
    """Most frequently matched canonical question."""
    question_id: str
    question_text: str
    match_count: int
    avg_similarity_score: Optional[float]


class VendorInsight(BaseModel):
    """Analytics grouped by vendor."""
    vendor_name: str
    questionnaire_count: int
    question_count: int
    linked_count: int
    confirmation_required_count: int
    no_match_count: int
    avg_processing_time_ms: Optional[float]


class IndustryInsight(BaseModel):
    """Analytics grouped by industry."""
    industry: str
    vendor_count: int
    questionnaire_count: int
    question_count: int
    avg_linked_percentage: float


# ==================== DATABASE CONNECTION ====================

engine = create_engine(DATABASE_URL, echo=True)


def init_db():
    """Initialize database: create extension and tables."""
    with engine.connect() as conn:
        # Enable pgvector extension
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
        conn.commit()

    # Create all tables
    SQLModel.metadata.create_all(engine)


def get_session():
    """Dependency for database session."""
    with Session(engine) as session:
        yield session


# ==================== AI MODEL HELPERS ====================

def init_openai_client():
    """Initialize the OpenAI client."""
    global openai_client
    print("Initializing OpenAI client...")
    openai_client = OpenAI(api_key=OPENAI_API_KEY)
    print("OpenAI client initialized successfully!")


async def get_embedding(text: str) -> list[float]:
    """
    Generate embedding vector for the given text using OpenAI API.

    Args:
        text: Input text to embed

    Returns:
        1024-dimensional embedding vector from text-embedding-3-small
    """
    if openai_client is None:
        raise RuntimeError("OpenAI client not initialized")

    response = openai_client.embeddings.create(
        input=text,
        model="text-embedding-3-small",
        dimensions=1024  # Request 1024 dimensions
    )

    return response.data[0].embedding


async def get_batch_embeddings(texts: list[str], max_retries: int = 3) -> list[list[float]]:
    """
    Generate embeddings for multiple texts with automatic chunking and retry logic.

    Features:
    - Automatically splits batches larger than 2048 into chunks
    - Exponential backoff retry for rate limits (3 retries)
    - Preserves order of embeddings

    Args:
        texts: List of text strings to embed
        max_retries: Maximum number of retry attempts for rate limits

    Returns:
        List of 1024-dimensional embedding vectors (same order as input)

    Raises:
        RuntimeError: If OpenAI client not initialized
        RateLimitError: If rate limit persists after all retries
        APIError: If API error occurs
    """
    if openai_client is None:
        raise RuntimeError("OpenAI client not initialized")

    BATCH_SIZE_LIMIT = 2048
    all_embeddings = []

    # Split into chunks if needed
    chunks = []
    if len(texts) > BATCH_SIZE_LIMIT:
        # Split into chunks of 2048
        for i in range(0, len(texts), BATCH_SIZE_LIMIT):
            chunks.append(texts[i:i + BATCH_SIZE_LIMIT])
    else:
        chunks = [texts]

    # Process each chunk with retry logic
    for chunk_idx, chunk in enumerate(chunks):
        retry_count = 0
        last_error = None

        while retry_count <= max_retries:
            try:
                # Attempt batch embedding API call
                batch_response = openai_client.embeddings.create(
                    input=chunk,
                    model="text-embedding-3-small",
                    dimensions=1024
                )

                # Extract embeddings in order
                chunk_embeddings = [item.embedding for item in batch_response.data]
                all_embeddings.extend(chunk_embeddings)

                # Success - break retry loop
                break

            except RateLimitError as e:
                last_error = e
                retry_count += 1

                if retry_count > max_retries:
                    # Max retries reached
                    raise RateLimitError(
                        f"Rate limit exceeded after {max_retries} retries. "
                        f"Chunk {chunk_idx + 1}/{len(chunks)} failed."
                    )

                # Exponential backoff: 2^retry * 1 second
                wait_time = (2 ** retry_count) * 1
                print(f"Rate limit hit. Retry {retry_count}/{max_retries} after {wait_time}s...")
                time.sleep(wait_time)

            except APIError as e:
                # API error - don't retry, raise immediately
                raise APIError(
                    f"OpenAI API error on chunk {chunk_idx + 1}/{len(chunks)}: {str(e)}"
                )

    return all_embeddings


# ==================== ANALYTICS HELPERS ====================

def log_analytics_event(
    session: Session,
    event_type: str,
    questionnaire_id: Optional[str] = None,
    question_id: Optional[str] = None,
    status: Optional[str] = None,
    match_method: Optional[str] = None,
    similarity_score: Optional[float] = None,
    processing_time_ms: Optional[int] = None,
    canonical_question_id: Optional[str] = None,
    vendor_name: Optional[str] = None,
    industry: Optional[str] = None
):
    """
    Log an analytics event to the database.

    Args:
        session: Database session
        event_type: Type of event (e.g., "question_matched", "questionnaire_processed")
        questionnaire_id: Batch/questionnaire identifier
        question_id: Individual question ID
        status: Result status (LINKED, CONFIRMATION_REQUIRED, NO_MATCH)
        match_method: How the match was found (saved_link, exact_id, ai_high_conf, ai_medium_conf)
        similarity_score: AI similarity score (0-1)
        processing_time_ms: Processing time in milliseconds
        canonical_question_id: Matched canonical question ID
        vendor_name: Vendor being assessed
        industry: Vendor industry
    """
    event = AnalyticsEvent(
        event_type=event_type,
        questionnaire_id=questionnaire_id,
        question_id=question_id,
        status=status,
        match_method=match_method,
        similarity_score=similarity_score,
        processing_time_ms=processing_time_ms,
        canonical_question_id=canonical_question_id,
        vendor_name=vendor_name,
        industry=industry
    )
    session.add(event)
    session.commit()


# ==================== APPLICATION LIFESPAN ====================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup and shutdown events."""
    # Startup
    print("Starting application...")
    init_db()
    init_openai_client()
    print("Application ready!")

    yield

    # Shutdown
    print("Shutting down application...")


# ==================== FASTAPI APPLICATION ====================

app = FastAPI(
    title="Effortless-Respond API",
    description="Batch process questionnaires using AI-driven semantic search (OpenAI)",
    version="3.0.0",
    lifespan=lifespan
)


# ==================== API ENDPOINTS ====================

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Welcome to Effortless-Respond API v3.0",
        "docs": "/docs",
        "version": "3.0.0",
        "ai_provider": "OpenAI",
        "embedding_model": "text-embedding-3-small",
        "features": ["batch_processing", "4_step_logic", "auto_linking"]
    }


@app.post("/process-questionnaire", response_model=QuestionnaireOutput)
async def process_questionnaire(
    questionnaire: QuestionnaireInput,
    session: Session = Depends(get_session)
):
    """
    Batch processing endpoint for questionnaires.

    Processes a list of questions and applies 4-step logic to each:
    1. Check if question ID has a saved link in QuestionLink table
    2. Check if question ID has an exact match in ResponseEntry table
    3. Run AI search using embeddings
    4. Apply 3-tier confidence logic (>0.92, 0.80-0.92, <0.80)

    Args:
        questionnaire: Input containing list of questions
        session: Database session

    Returns:
        QuestionnaireOutput with results for each question
    """
    results = []

    for question in questionnaire.questions:
        # Step 1: Check for saved link in QuestionLink table
        link_query = select(QuestionLink).where(QuestionLink.new_question_id == question.id)
        existing_link = session.exec(link_query).first()

        if existing_link:
            # Found saved link, fetch the response
            response_entry = session.get(ResponseEntry, existing_link.linked_response_id)
            if response_entry:
                results.append(QuestionResult(
                    id=question.id,
                    status="LINKED",
                    data=ResponseData(
                        answer_text=response_entry.answer_text,
                        evidence=response_entry.evidence,
                        canonical_question_text=response_entry.question_text
                    )
                ))
                continue  # Move to next question

        # Step 2: Check for exact ID match in ResponseEntry table
        exact_match_query = select(ResponseEntry).where(ResponseEntry.question_id == question.id)
        exact_match = session.exec(exact_match_query).first()

        if exact_match:
            results.append(QuestionResult(
                id=question.id,
                status="LINKED",
                data=ResponseData(
                    answer_text=exact_match.answer_text,
                    evidence=exact_match.evidence,
                    canonical_question_text=exact_match.question_text
                )
            ))
            continue  # Move to next question

        # Step 3: Run AI Search using embeddings
        embedding = await get_embedding(question.text)

        # Query for top 1 closest match using cosine distance
        ai_search_query = (
            select(ResponseEntry)
            .order_by(ResponseEntry.embedding.cosine_distance(embedding))
            .limit(1)
        )
        ai_results = session.exec(ai_search_query).all()

        if not ai_results:
            # No results from AI search
            results.append(QuestionResult(
                id=question.id,
                status="NO_MATCH"
            ))
            continue  # Move to next question

        top_match = ai_results[0]

        # Calculate cosine distance and similarity score
        distance_query = select(
            ResponseEntry.embedding.cosine_distance(embedding)
        ).where(ResponseEntry.id == top_match.id)
        distance = session.exec(distance_query).first()

        # Convert distance to similarity: similarity = 1 - (distance / 2)
        # Cosine distance range: [0, 2], similarity range: [0, 1]
        similarity_score = 1 - (distance / 2) if distance is not None else 0

        # Step 4: Apply 3-Tier Logic
        if similarity_score > 0.92:
            # HIGH CONFIDENCE: Auto-link and return LINKED
            auto_link = QuestionLink(
                new_question_id=question.id,
                linked_response_id=top_match.id
            )
            session.add(auto_link)
            session.commit()

            results.append(QuestionResult(
                id=question.id,
                status="LINKED",
                data=ResponseData(
                    answer_text=top_match.answer_text,
                    evidence=top_match.evidence,
                    canonical_question_text=top_match.question_text
                )
            ))

        elif similarity_score >= 0.80:
            # MEDIUM CONFIDENCE: Ask for confirmation
            results.append(QuestionResult(
                id=question.id,
                status="CONFIRMATION_REQUIRED",
                data=ResponseData(
                    answer_text=top_match.answer_text,
                    evidence=top_match.evidence,
                    canonical_question_text=top_match.question_text
                )
            ))

        else:
            # LOW CONFIDENCE: No match
            results.append(QuestionResult(
                id=question.id,
                status="NO_MATCH"
            ))

    return QuestionnaireOutput(results=results)


@app.post("/batch-process-questionnaire", response_model=QuestionnaireOutput)
async def batch_process_questionnaire(
    questionnaire: QuestionnaireInput,
    session: Session = Depends(get_session)
):
    """
    OPTIMIZED batch processing endpoint for large questionnaires.

    Production-ready features:
    - Automatic chunking for batches > 2048 questions
    - Exponential backoff retry logic for rate limits (3 retries: 2s, 4s, 8s)
    - Handles up to unlimited questions (auto-splits into 2048-question chunks)
    - Single API call per chunk instead of N individual calls

    Performance:
    - 500 questions: 1 API call instead of 500 calls (500x faster)
    - 3000 questions: 2 API calls instead of 3000 calls (1500x faster)
    - Resilient to OpenAI rate limits with automatic retry

    Processes a list of questions and applies 4-step logic to each:
    1. Check if question ID has a saved link in QuestionLink table
    2. Check if question ID has an exact match in ResponseEntry table
    3. Run AI search using batch embeddings (OPTIMIZED with retry)
    4. Apply 3-tier confidence logic (>0.92, 0.80-0.92, <0.80)

    Args:
        questionnaire: Input containing list of questions (no size limit)
        session: Database session

    Returns:
        QuestionnaireOutput with results for each question

    Raises:
        RateLimitError: If rate limit persists after 3 retries
        APIError: If OpenAI API error occurs
    """
    results = []
    questions_needing_ai_search = []
    question_index_map = {}  # Maps question index to position in batch

    # Phase 1: Process Steps 1 & 2 for all questions
    for idx, question in enumerate(questionnaire.questions):
        # Step 1: Check for saved link in QuestionLink table
        link_query = select(QuestionLink).where(QuestionLink.new_question_id == question.id)
        existing_link = session.exec(link_query).first()

        if existing_link:
            # Found saved link, fetch the response
            response_entry = session.get(ResponseEntry, existing_link.linked_response_id)
            if response_entry:
                results.append(QuestionResult(
                    id=question.id,
                    status="LINKED",
                    data=ResponseData(
                        answer_text=response_entry.answer_text,
                        evidence=response_entry.evidence,
                        canonical_question_text=response_entry.question_text
                    )
                ))
                continue  # Move to next question

        # Step 2: Check for exact ID match in ResponseEntry table
        exact_match_query = select(ResponseEntry).where(ResponseEntry.question_id == question.id)
        exact_match = session.exec(exact_match_query).first()

        if exact_match:
            results.append(QuestionResult(
                id=question.id,
                status="LINKED",
                data=ResponseData(
                    answer_text=exact_match.answer_text,
                    evidence=exact_match.evidence,
                    canonical_question_text=exact_match.question_text
                )
            ))
            continue  # Move to next question

        # Neither Step 1 nor Step 2 matched - needs AI search
        questions_needing_ai_search.append(question)
        question_index_map[len(questions_needing_ai_search) - 1] = idx

    # Phase 2: Batch generate embeddings for all questions needing AI search
    if questions_needing_ai_search:
        texts_to_embed = [q.text for q in questions_needing_ai_search]

        # OPTIMIZATION: Batch embedding with automatic chunking and retry logic
        # - Handles batches > 2048 by auto-splitting into chunks
        # - Implements exponential backoff for rate limits (3 retries)
        # - Preserves order of embeddings
        embeddings = await get_batch_embeddings(texts_to_embed)

        # Phase 3: Process Steps 3 & 4 for questions needing AI search
        for idx, question in enumerate(questions_needing_ai_search):
            embedding = embeddings[idx]

            # Step 3: Query for top 1 closest match using cosine distance
            ai_search_query = (
                select(ResponseEntry)
                .order_by(ResponseEntry.embedding.cosine_distance(embedding))
                .limit(1)
            )
            ai_results = session.exec(ai_search_query).all()

            if not ai_results:
                # No results from AI search
                results.append(QuestionResult(
                    id=question.id,
                    status="NO_MATCH"
                ))
                continue

            top_match = ai_results[0]

            # Calculate cosine distance and similarity score
            distance_query = select(
                ResponseEntry.embedding.cosine_distance(embedding)
            ).where(ResponseEntry.id == top_match.id)
            distance = session.exec(distance_query).first()

            # Convert distance to similarity
            similarity_score = 1 - (distance / 2) if distance is not None else 0

            # Step 4: Apply 3-Tier Logic
            if similarity_score > 0.92:
                # HIGH CONFIDENCE: Auto-link and return LINKED
                auto_link = QuestionLink(
                    new_question_id=question.id,
                    linked_response_id=top_match.id
                )
                session.add(auto_link)
                session.commit()

                results.append(QuestionResult(
                    id=question.id,
                    status="LINKED",
                    data=ResponseData(
                        answer_text=top_match.answer_text,
                        evidence=top_match.evidence,
                        canonical_question_text=top_match.question_text
                    )
                ))

            elif similarity_score >= 0.80:
                # MEDIUM CONFIDENCE: Ask for confirmation
                results.append(QuestionResult(
                    id=question.id,
                    status="CONFIRMATION_REQUIRED",
                    data=ResponseData(
                        answer_text=top_match.answer_text,
                        evidence=top_match.evidence,
                        canonical_question_text=top_match.question_text
                    )
                ))

            else:
                # LOW CONFIDENCE: No match
                results.append(QuestionResult(
                    id=question.id,
                    status="NO_MATCH"
                ))

    return QuestionnaireOutput(results=results)


# ==================== UTILITY ENDPOINTS ====================

@app.get("/responses")
async def list_responses(session: Session = Depends(get_session)):
    """List all response entries (for debugging/admin purposes)."""
    statement = select(ResponseEntry)
    results = session.exec(statement).all()
    return results


@app.get("/links")
async def list_links(session: Session = Depends(get_session)):
    """List all question links (for debugging/admin purposes)."""
    statement = select(QuestionLink)
    results = session.exec(statement).all()
    return results


@app.post("/create-response")
async def create_response(
    question_id: str,
    question_text: str,
    answer_text: str,
    evidence: Optional[str] = None,
    session: Session = Depends(get_session)
):
    """
    Create a new response entry.

    Args:
        question_id: Unique identifier for the question
        question_text: The question text
        answer_text: The answer text
        evidence: Optional evidence/citation
        session: Database session

    Returns:
        The created ResponseEntry
    """
    # Generate embedding
    embedding = await get_embedding(question_text)

    # Create new response entry
    new_response = ResponseEntry(
        question_id=question_id,
        question_text=question_text,
        answer_text=answer_text,
        evidence=evidence,
        embedding=embedding
    )

    session.add(new_response)
    session.commit()
    session.refresh(new_response)

    return new_response


@app.delete("/responses/{response_id}")
async def delete_response(response_id: int, session: Session = Depends(get_session)):
    """Delete a response entry (for admin purposes)."""
    response_entry = session.get(ResponseEntry, response_id)

    if not response_entry:
        raise HTTPException(status_code=404, detail="Response not found")

    session.delete(response_entry)
    session.commit()

    return {"message": f"Response {response_id} deleted successfully"}


@app.delete("/links/{link_id}")
async def delete_link(link_id: int, session: Session = Depends(get_session)):
    """Delete a question link (for admin purposes)."""
    link = session.get(QuestionLink, link_id)

    if not link:
        raise HTTPException(status_code=404, detail="Link not found")

    session.delete(link)
    session.commit()

    return {"message": f"Link {link_id} deleted successfully"}


# ==================== ANALYTICS ENDPOINTS ====================

@app.get("/analytics/dashboard", response_model=DashboardOverview)
async def get_dashboard_overview(session: Session = Depends(get_session)):
    """
    Get comprehensive dashboard overview statistics.

    Returns high-level metrics including:
    - Today's activity (questionnaires, questions, status breakdown)
    - All-time totals
    - Match effectiveness percentages
    - Average performance metrics

    Perfect for a CEO dashboard or main analytics page.
    """
    # Get today's date range
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)

    # Today's metrics
    today_events = session.exec(
        select(AnalyticsEvent).where(AnalyticsEvent.timestamp >= today_start)
    ).all()

    today_questionnaires = len(set(e.questionnaire_id for e in today_events if e.questionnaire_id))
    today_questions = len([e for e in today_events if e.event_type == "question_matched"])
    today_linked = len([e for e in today_events if e.status == "LINKED"])
    today_confirmation = len([e for e in today_events if e.status == "CONFIRMATION_REQUIRED"])
    today_no_match = len([e for e in today_events if e.status == "NO_MATCH"])

    # All-time metrics
    all_events = session.exec(select(AnalyticsEvent)).all()
    total_questionnaires = len(set(e.questionnaire_id for e in all_events if e.questionnaire_id))
    total_questions = len([e for e in all_events if e.event_type == "question_matched"])

    # Count database entries
    total_response_entries = len(session.exec(select(ResponseEntry)).all())
    total_question_links = len(session.exec(select(QuestionLink)).all())

    # Calculate percentages
    matched_events = [e for e in all_events if e.status in ["LINKED", "CONFIRMATION_REQUIRED", "NO_MATCH"]]
    total_matched = len(matched_events)

    if total_matched > 0:
        linked_pct = (len([e for e in matched_events if e.status == "LINKED"]) / total_matched) * 100
        confirmation_pct = (len([e for e in matched_events if e.status == "CONFIRMATION_REQUIRED"]) / total_matched) * 100
        no_match_pct = (len([e for e in matched_events if e.status == "NO_MATCH"]) / total_matched) * 100
    else:
        linked_pct = confirmation_pct = no_match_pct = 0.0

    # Average processing time
    times = [e.processing_time_ms for e in all_events if e.processing_time_ms is not None]
    avg_time = sum(times) / len(times) if times else None

    return DashboardOverview(
        today_questionnaires=today_questionnaires,
        today_questions=today_questions,
        today_linked=today_linked,
        today_confirmation_required=today_confirmation,
        today_no_match=today_no_match,
        total_questionnaires=total_questionnaires,
        total_questions=total_questions,
        total_response_entries=total_response_entries,
        total_question_links=total_question_links,
        linked_percentage=round(linked_pct, 2),
        confirmation_percentage=round(confirmation_pct, 2),
        no_match_percentage=round(no_match_pct, 2),
        avg_processing_time_ms=round(avg_time, 2) if avg_time else None
    )


@app.get("/analytics/match-methods", response_model=MatchMethodBreakdown)
async def get_match_method_breakdown(session: Session = Depends(get_session)):
    """
    Get breakdown of how questions are being matched.

    Shows distribution across:
    - Saved links (previously linked questions)
    - Exact ID matches (canonical question IDs)
    - AI high confidence matches (>92% similarity, auto-linked)
    - AI medium confidence matches (80-92% similarity, needs confirmation)
    - No matches (<80% similarity)

    Useful for understanding system efficiency and AI performance.
    """
    events = session.exec(
        select(AnalyticsEvent).where(AnalyticsEvent.event_type == "question_matched")
    ).all()

    saved_link = len([e for e in events if e.match_method == "saved_link"])
    exact_id = len([e for e in events if e.match_method == "exact_id"])
    ai_high_conf = len([e for e in events if e.match_method == "ai_high_conf"])
    ai_medium_conf = len([e for e in events if e.match_method == "ai_medium_conf"])
    no_match = len([e for e in events if e.status == "NO_MATCH"])

    total = len(events) if events else 1  # Avoid division by zero

    return MatchMethodBreakdown(
        saved_link=saved_link,
        exact_id=exact_id,
        ai_high_confidence=ai_high_conf,
        ai_medium_confidence=ai_medium_conf,
        no_match=no_match,
        saved_link_pct=round((saved_link / total) * 100, 2),
        exact_id_pct=round((exact_id / total) * 100, 2),
        ai_high_confidence_pct=round((ai_high_conf / total) * 100, 2),
        ai_medium_confidence_pct=round((ai_medium_conf / total) * 100, 2),
        no_match_pct=round((no_match / total) * 100, 2)
    )


@app.get("/analytics/time-series")
async def get_time_series_data(
    days: int = 30,
    session: Session = Depends(get_session)
) -> TimeSeriesData:
    """
    Get time-series data for trend analysis.

    Args:
        days: Number of days to include (default: 30)

    Returns:
        Time-series data with daily counts for:
        - Questionnaires processed
        - Questions processed
        - Questions linked
        - Questions requiring confirmation
        - Questions with no match

    Perfect for line charts showing usage trends over time.
    """
    # Calculate date range
    end_date = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    start_date = end_date - timedelta(days=days-1)

    # Get all events in range
    events = session.exec(
        select(AnalyticsEvent).where(AnalyticsEvent.timestamp >= start_date)
    ).all()

    # Initialize data structures
    dates = []
    questionnaires = []
    questions = []
    linked = []
    confirmation_required = []
    no_match = []

    # Process each day
    for day_offset in range(days):
        current_date = start_date + timedelta(days=day_offset)
        next_date = current_date + timedelta(days=1)

        # Filter events for this day
        day_events = [e for e in events if current_date <= e.timestamp < next_date]

        dates.append(current_date.strftime("%Y-%m-%d"))
        questionnaires.append(len(set(e.questionnaire_id for e in day_events if e.questionnaire_id)))
        questions.append(len([e for e in day_events if e.event_type == "question_matched"]))
        linked.append(len([e for e in day_events if e.status == "LINKED"]))
        confirmation_required.append(len([e for e in day_events if e.status == "CONFIRMATION_REQUIRED"]))
        no_match.append(len([e for e in day_events if e.status == "NO_MATCH"]))

    return TimeSeriesData(
        dates=dates,
        questionnaires=questionnaires,
        questions=questions,
        linked=linked,
        confirmation_required=confirmation_required,
        no_match=no_match
    )


@app.get("/analytics/top-questions")
async def get_top_canonical_questions(
    limit: int = 10,
    session: Session = Depends(get_session)
) -> List[TopCanonicalQuestion]:
    """
    Get the most frequently matched canonical questions.

    Args:
        limit: Number of top questions to return (default: 10)

    Returns:
        List of top canonical questions with:
        - Question ID and text
        - Number of times matched
        - Average similarity score

    Useful for identifying which canonical answers are most reusable.
    """
    events = session.exec(
        select(AnalyticsEvent)
        .where(AnalyticsEvent.canonical_question_id.isnot(None))
        .where(AnalyticsEvent.status.in_(["LINKED", "CONFIRMATION_REQUIRED"]))
    ).all()

    # Group by canonical question ID
    question_stats: Dict[str, Dict[str, Any]] = {}

    for event in events:
        qid = event.canonical_question_id
        if qid not in question_stats:
            question_stats[qid] = {
                "count": 0,
                "similarity_scores": []
            }

        question_stats[qid]["count"] += 1
        if event.similarity_score is not None:
            question_stats[qid]["similarity_scores"].append(event.similarity_score)

    # Get question text from database
    results = []
    for qid, stats in sorted(question_stats.items(), key=lambda x: x[1]["count"], reverse=True)[:limit]:
        # Find the question text
        response_entry = session.exec(
            select(ResponseEntry).where(ResponseEntry.question_id == qid)
        ).first()

        if response_entry:
            avg_score = None
            if stats["similarity_scores"]:
                avg_score = round(sum(stats["similarity_scores"]) / len(stats["similarity_scores"]), 4)

            results.append(TopCanonicalQuestion(
                question_id=qid,
                question_text=response_entry.question_text,
                match_count=stats["count"],
                avg_similarity_score=avg_score
            ))

    return results


@app.get("/analytics/vendors")
async def get_vendor_insights(
    limit: int = 20,
    session: Session = Depends(get_session)
) -> List[VendorInsight]:
    """
    Get analytics grouped by vendor.

    Args:
        limit: Number of vendors to return (default: 20)

    Returns:
        List of vendor insights with:
        - Questionnaire and question counts
        - Status breakdown (linked, confirmation, no match)
        - Average processing time

    Useful for understanding which vendors have been assessed most
    and how well their questionnaires are being matched.
    """
    events = session.exec(
        select(AnalyticsEvent).where(AnalyticsEvent.vendor_name.isnot(None))
    ).all()

    # Group by vendor
    vendor_stats: Dict[str, Dict[str, Any]] = {}

    for event in events:
        vendor = event.vendor_name
        if vendor not in vendor_stats:
            vendor_stats[vendor] = {
                "questionnaires": set(),
                "questions": 0,
                "linked": 0,
                "confirmation": 0,
                "no_match": 0,
                "processing_times": []
            }

        if event.questionnaire_id:
            vendor_stats[vendor]["questionnaires"].add(event.questionnaire_id)

        if event.event_type == "question_matched":
            vendor_stats[vendor]["questions"] += 1

            if event.status == "LINKED":
                vendor_stats[vendor]["linked"] += 1
            elif event.status == "CONFIRMATION_REQUIRED":
                vendor_stats[vendor]["confirmation"] += 1
            elif event.status == "NO_MATCH":
                vendor_stats[vendor]["no_match"] += 1

        if event.processing_time_ms:
            vendor_stats[vendor]["processing_times"].append(event.processing_time_ms)

    # Convert to response models
    results = []
    for vendor, stats in sorted(vendor_stats.items(), key=lambda x: x[1]["questions"], reverse=True)[:limit]:
        avg_time = None
        if stats["processing_times"]:
            avg_time = round(sum(stats["processing_times"]) / len(stats["processing_times"]), 2)

        results.append(VendorInsight(
            vendor_name=vendor,
            questionnaire_count=len(stats["questionnaires"]),
            question_count=stats["questions"],
            linked_count=stats["linked"],
            confirmation_required_count=stats["confirmation"],
            no_match_count=stats["no_match"],
            avg_processing_time_ms=avg_time
        ))

    return results


@app.get("/analytics/industries")
async def get_industry_insights(
    session: Session = Depends(get_session)
) -> List[IndustryInsight]:
    """
    Get analytics grouped by industry.

    Returns:
        List of industry insights with:
        - Number of vendors assessed per industry
        - Questionnaire and question counts
        - Average linked percentage (match effectiveness)

    Useful for understanding which industries are being assessed
    and comparing match effectiveness across industries.
    """
    events = session.exec(
        select(AnalyticsEvent).where(AnalyticsEvent.industry.isnot(None))
    ).all()

    # Group by industry
    industry_stats: Dict[str, Dict[str, Any]] = {}

    for event in events:
        industry = event.industry
        if industry not in industry_stats:
            industry_stats[industry] = {
                "vendors": set(),
                "questionnaires": set(),
                "questions": 0,
                "linked": 0
            }

        if event.vendor_name:
            industry_stats[industry]["vendors"].add(event.vendor_name)

        if event.questionnaire_id:
            industry_stats[industry]["questionnaires"].add(event.questionnaire_id)

        if event.event_type == "question_matched":
            industry_stats[industry]["questions"] += 1

            if event.status == "LINKED":
                industry_stats[industry]["linked"] += 1

    # Convert to response models
    results = []
    for industry, stats in sorted(industry_stats.items(), key=lambda x: x[1]["questions"], reverse=True):
        linked_pct = 0.0
        if stats["questions"] > 0:
            linked_pct = round((stats["linked"] / stats["questions"]) * 100, 2)

        results.append(IndustryInsight(
            industry=industry,
            vendor_count=len(stats["vendors"]),
            questionnaire_count=len(stats["questionnaires"]),
            question_count=stats["questions"],
            avg_linked_percentage=linked_pct
        ))

    return results


# ==================== MAIN ====================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
