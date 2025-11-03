"""
Effortless-Respond API
A FastAPI application for finding saved answers to new questions using AI-driven semantic search.
"""

from contextlib import asynccontextmanager
from typing import Optional, Union, Literal

from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy import create_engine, text
from sqlmodel import SQLModel, Field, select, Session
from pgvector.sqlalchemy import Vector
from sentence_transformers import SentenceTransformer
from pydantic import BaseModel
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/effortless_respond")

# Global AI model variable
model: Optional[SentenceTransformer] = None

# ==================== DATABASE MODELS ====================

class ResponseEntry(SQLModel, table=True):
    """
    Stores canonical answers and their vector embeddings.
    """
    __tablename__ = "responseentry"

    id: Optional[int] = Field(default=None, primary_key=True)
    canonical_question: str = Field(index=True)
    answer: str
    evidence: Optional[str] = Field(default=None)
    embedding: list[float] = Field(sa_type=Vector(768))  # 768 for multi-qa-mpnet-base-dot-v1


class QuestionLink(SQLModel, table=True):
    """
    Maps new question text to existing answers (user-confirmed links).
    """
    __tablename__ = "questionlink"

    id: Optional[int] = Field(default=None, primary_key=True)
    new_question_text: str = Field(index=True, unique=True)
    linked_response_id: int = Field(foreign_key="responseentry.id")


# ==================== PYDANTIC MODELS ====================

class QuestionInput(BaseModel):
    """Input model for processing a question."""
    question_text: str


class LinkRequest(BaseModel):
    """Input model for creating a confirmed link."""
    new_question_text: str
    confirmed_response_id: int


class NewResponseInput(BaseModel):
    """Input model for creating a new response entry."""
    question_text: str
    answer_text: str
    evidence: Optional[str] = None


class ResponseOutput(BaseModel):
    """Output model for a response."""
    # id: int
    answer: str
    evidence: Optional[str]
    canonical_question: str


class ResponseEntryOutput(BaseModel):
    """Output model for ResponseEntry without embedding."""
    id: int
    canonical_question: str
    answer: str
    evidence: Optional[str]


class Suggestion(BaseModel):
    """Model for a suggested response with similarity score."""
    response: ResponseOutput
    similarity_score: float


class LinkedResponse(BaseModel):
    """Response when a linked answer is found."""
    status: Literal["linked"]
    data: ResponseOutput


class ConfirmationRequired(BaseModel):
    """Response when confirmation is required."""
    status: Literal["confirmation_required"]
    suggestions: list[Suggestion]


class NoMatchFound(BaseModel):
    """Response when no match is found."""
    status: Literal["no_match_found"]


# Union type for process response
ProcessResponse = Union[LinkedResponse, ConfirmationRequired, NoMatchFound]


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

def load_ai_model():
    """Load the sentence transformer model."""
    global model
    model_name = 'multi-qa-mpnet-base-dot-v1'  # ('all-MiniLM-L6-v2')
    print(f"Loading AI model: {model_name}")
    model = SentenceTransformer(model_name)
    print("AI model loaded successfully!")


def get_embedding(text: str) -> list[float]:
    """
    Generate embedding vector for the given text.

    Args:
        text: Input text to embed

    Returns:
        384-dimensional embedding vector
    """
    if model is None:
        raise RuntimeError("AI model not loaded")

    embedding = model.encode(text)
    return embedding.tolist()


# ==================== APPLICATION LIFESPAN ====================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup and shutdown events."""
    # Startup
    print("Starting application...")
    init_db()
    load_ai_model()
    print("Application ready!")

    yield

    # Shutdown
    print("Shutting down application...")


# ==================== FASTAPI APPLICATION ====================

app = FastAPI(
    title="Effortless-Respond API",
    description="Find saved answers to new questions using AI-driven semantic search",
    version="1.0.0",
    lifespan=lifespan
)


# ==================== API ENDPOINTS ====================

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Welcome to Effortless-Respond API",
        "docs": "/docs",
        "version": "1.0.0"
    }


@app.post("/process-question", response_model=ProcessResponse)
async def process_question(
    question_input: QuestionInput,
    session: Session = Depends(get_session)
):
    """
    Main endpoint to process a new question.

    Logic flow:
    1. Check for existing user-confirmed link (AC #3)
    2. If no link, run AI search for similar questions (AC #1)
    3. Return suggestions if found (AC #2)
    4. Return no match if threshold not met

    Args:
        question_input: The question to process
        session: Database session

    Returns:
        ProcessResponse with status and relevant data
    """
    question_text = question_input.question_text.strip()

    # Step 1: Check for existing link (AC #3)
    statement = select(QuestionLink).where(QuestionLink.new_question_text == question_text)
    existing_link = session.exec(statement).first()

    if existing_link:
        # Found existing link, fetch the response
        response_entry = session.get(ResponseEntry, existing_link.linked_response_id)

        if response_entry:
            return LinkedResponse(
                status="linked",
                data=ResponseOutput(
                    # id=response_entry.id,
                    answer=response_entry.answer,
                    evidence=response_entry.evidence,
                    canonical_question=response_entry.canonical_question
                )
            )

    # Step 2: Run AI Search (AC #1)
    # Note: The multi-qa-mpnet-base-dot-v1 model handles abbreviations well
    # so we don't need explicit abbreviation expansion
    embedding = get_embedding(question_text)

    # Query for top 3 closest matches using cosine distance
    # Note: pgvector's cosine_distance returns 0 for identical vectors, 2 for opposite
    # We convert to similarity: similarity = 1 - (distance / 2)
    statement = (
        select(ResponseEntry)
        .order_by(ResponseEntry.embedding.cosine_distance(embedding))
        .limit(3)
    )

    results = session.exec(statement).all()

    # Step 3: Filter by similarity threshold and create suggestions (AC #2)
    SIMILARITY_THRESHOLD = 0.80  # Lowered from 0.80 to catch more question variations
    suggestions = []

    for response_entry in results:
        # Calculate cosine distance
        distance_query = select(
            ResponseEntry.embedding.cosine_distance(embedding)
        ).where(ResponseEntry.id == response_entry.id)

        distance = session.exec(distance_query).first()

        # Convert distance to similarity score
        # Cosine distance range: [0, 2], where 0 = identical, 2 = opposite
        # Similarity = 1 - (distance / 2), range: [0, 1]
        similarity_score = 1 - (distance / 2) if distance is not None else 0

        if similarity_score >= SIMILARITY_THRESHOLD:
            suggestions.append(
                Suggestion(
                    response=ResponseOutput(
                        # id=response_entry.id,
                        answer=response_entry.answer,
                        evidence=response_entry.evidence,
                        canonical_question=response_entry.canonical_question
                    ),
                    similarity_score=round(similarity_score, 4)
                )
            )

    # Step 4: Return results
    if suggestions:
        return ConfirmationRequired(
            status="confirmation_required",
            suggestions=suggestions
        )
    else:
        return NoMatchFound(status="no_match_found")


@app.post("/create-link", response_model=QuestionLink)
async def create_link(
    link_request: LinkRequest,
    session: Session = Depends(get_session)
):
    """
    Create a user-confirmed link between a new question and an existing response.

    This is called after the user confirms one of the suggestions.

    Args:
        link_request: The link details
        session: Database session

    Returns:
        The created QuestionLink
    """
    # Verify that the response exists
    response_entry = session.get(ResponseEntry, link_request.confirmed_response_id)

    if not response_entry:
        raise HTTPException(
            status_code=404,
            detail=f"Response with id {link_request.confirmed_response_id} not found"
        )

    # Check if link already exists
    statement = select(QuestionLink).where(
        QuestionLink.new_question_text == link_request.new_question_text
    )
    existing_link = session.exec(statement).first()

    if existing_link:
        raise HTTPException(
            status_code=400,
            detail=f"Link already exists for question: {link_request.new_question_text}"
        )

    # Create new link
    new_link = QuestionLink(
        new_question_text=link_request.new_question_text,
        linked_response_id=link_request.confirmed_response_id
    )

    session.add(new_link)
    session.commit()
    session.refresh(new_link)

    return new_link


@app.post("/create-new-response", response_model=ResponseEntryOutput)
async def create_new_response(
    response_input: NewResponseInput,
    session: Session = Depends(get_session)
):
    """
    Create a new response entry with a new answer.

    This is called after the system returns "no_match_found" and the user provides
    a new, original answer.

    Args:
        response_input: The new response details
        session: Database session

    Returns:
        The created ResponseEntry
    """
    # Generate embedding for the question
    embedding = get_embedding(response_input.question_text)

    # Create new response entry
    new_response = ResponseEntry(
        canonical_question=response_input.question_text,
        answer=response_input.answer_text,
        evidence=response_input.evidence,
        embedding=embedding
    )

    session.add(new_response)
    session.commit()
    session.refresh(new_response)

    return ResponseEntryOutput(
        id=new_response.id,
        canonical_question=new_response.canonical_question,
        answer=new_response.answer,
        evidence=new_response.evidence
    )


# ==================== UTILITY ENDPOINTS ====================

@app.get("/responses", response_model=list[ResponseEntryOutput])
async def list_responses(session: Session = Depends(get_session)):
    """List all response entries (for debugging/admin purposes)."""
    statement = select(ResponseEntry)
    results = session.exec(statement).all()
    return [
        ResponseEntryOutput(
            id=r.id,
            canonical_question=r.canonical_question,
            answer=r.answer,
            evidence=r.evidence
        )
        for r in results
    ]


@app.get("/links", response_model=list[QuestionLink])
async def list_links(session: Session = Depends(get_session)):
    """List all question links (for debugging/admin purposes)."""
    statement = select(QuestionLink)
    results = session.exec(statement).all()
    return results


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
