"""
Pydantic schemas for question processing requests and responses.
"""
from typing import Optional, Union
from pydantic import BaseModel
from .answer import Answer


class Question(BaseModel):
    """
    Model for a single question in the questionnaire.

    Attributes:
        id: Unique identifier for the question (can be int or str)
        text: The question text
    """
    id: Union[int, str]
    text: str


class QuestionnaireInput(BaseModel):
    """
    Input model for batch processing questionnaire.

    Attributes:
        client_id: Client identifier
        provider_id: Provider/vendor identifier
        questions: List of questions to process
    """
    client_id: str
    provider_id: str
    questions: list[Question]


class ResponseData(BaseModel):
    """
    Model for response data returned with question results.

    Attributes:
        answer: Answer object containing type, text, and optional comment
        evidence: Optional evidence/citation
        canonical_question_text: The original canonical question text
        similarity_score: Cosine similarity score (0-1) if AI search was used
    """
    answer: Answer
    evidence: Optional[str]
    canonical_question_text: str
    similarity_score: Optional[float] = None


class QuestionResult(BaseModel):
    """
    Model for a single question result.

    Attributes:
        id: Question ID (from input, can be int or str)
        status: Processing status - "LINKED", "CONFIRMATION_REQUIRED", or "NO_MATCH"
        data: Response data if match was found, None otherwise
    """
    id: Union[int, str]
    status: str  # "LINKED", "CONFIRMATION_REQUIRED", "NO_MATCH"
    data: Optional[ResponseData] = None


class QuestionnaireOutput(BaseModel):
    """
    Output model for batch processing questionnaire.

    Attributes:
        results: List of results for each question
    """
    results: list[QuestionResult]
