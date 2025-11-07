"""
Pydantic schemas for question processing requests and responses.
"""
from typing import Optional
from pydantic import BaseModel


class Question(BaseModel):
    """
    Model for a single question in the questionnaire.

    Attributes:
        id: Unique identifier for the question
        text: The question text
    """
    id: int
    text: str


class QuestionnaireInput(BaseModel):
    """
    Input model for batch processing questionnaire.

    Attributes:
        vendor_id: Which vendor is processing this questionnaire
        questions: List of questions to process
    """
    vendor_id: str
    questions: list[Question]


class ResponseData(BaseModel):
    """
    Model for response data returned with question results.

    Attributes:
        answer_text: The answer text
        evidence: Optional evidence/citation
        canonical_question_text: The original canonical question text
        similarity_score: Cosine similarity score (0-1) if AI search was used
    """
    answer_text: str
    evidence: Optional[str]
    canonical_question_text: str
    similarity_score: Optional[float] = None


class QuestionResult(BaseModel):
    """
    Model for a single question result.

    Attributes:
        id: Question ID (from input)
        status: Processing status - "LINKED", "CONFIRMATION_REQUIRED", or "NO_MATCH"
        data: Response data if match was found, None otherwise
    """
    id: int
    status: str  # "LINKED", "CONFIRMATION_REQUIRED", "NO_MATCH"
    data: Optional[ResponseData] = None


class QuestionnaireOutput(BaseModel):
    """
    Output model for batch processing questionnaire.

    Attributes:
        results: List of results for each question
    """
    results: list[QuestionResult]
