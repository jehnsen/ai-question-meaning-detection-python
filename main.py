"""
Effortless-Respond API
A FastAPI application for finding saved answers to new questions using AI-driven semantic search.
Batch processing endpoint with 4-step logic and OpenAI embeddings.
"""

from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy import create_engine, text
from sqlmodel import SQLModel, Field, select, Session
from pgvector.sqlalchemy import Vector
from pydantic import BaseModel
import os
from dotenv import load_dotenv
from openai import OpenAI

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

    Key optimization: Uses OpenAI's batch embedding API to generate embeddings
    for all questions in a SINGLE API call instead of N calls.

    Performance:
    - 500 questions: 1 API call instead of 500 calls
    - Significantly faster for large batches
    - Same 4-step logic as /process-questionnaire

    Processes a list of questions and applies 4-step logic to each:
    1. Check if question ID has a saved link in QuestionLink table
    2. Check if question ID has an exact match in ResponseEntry table
    3. Run AI search using batch embeddings (OPTIMIZED)
    4. Apply 3-tier confidence logic (>0.92, 0.80-0.92, <0.80)

    Args:
        questionnaire: Input containing list of questions
        session: Database session

    Returns:
        QuestionnaireOutput with results for each question
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
        # OPTIMIZATION: Single API call for all embeddings
        if openai_client is None:
            raise RuntimeError("OpenAI client not initialized")

        texts_to_embed = [q.text for q in questions_needing_ai_search]

        # Batch embedding API call (up to 2048 inputs in one call)
        batch_response = openai_client.embeddings.create(
            input=texts_to_embed,
            model="text-embedding-3-small",
            dimensions=1024
        )

        # Extract embeddings in order
        embeddings = [item.embedding for item in batch_response.data]

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


# ==================== MAIN ====================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
