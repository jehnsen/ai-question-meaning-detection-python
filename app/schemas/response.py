"""
Pydantic schemas for canonical response creation.
"""
from typing import Optional
from pydantic import BaseModel


class CanonicalResponseInput(BaseModel):
    """
    Input for a single canonical response.

    Attributes:
        question_id: Unique identifier for the question (within vendor)
        question_text: The question text
        answer_text: The answer text
        evidence: Optional evidence/citation
    """
    question_id: str
    question_text: str
    answer_text: str
    evidence: Optional[str] = None


class BatchCreateInput(BaseModel):
    """
    Input model for batch creating canonical responses.

    Attributes:
        vendor_id: Which vendor owns these responses
        responses: List of canonical responses to create
    """
    vendor_id: str
    responses: list[CanonicalResponseInput]


class BatchCreateResponse(BaseModel):
    """
    Response model for a single batch create operation.

    Attributes:
        question_id: The question ID that was created
        question_text: The question text
        status: Creation status (typically "created")
    """
    question_id: str
    question_text: str
    status: str


class BatchCreateOutput(BaseModel):
    """
    Output model for batch create canonical responses.

    Attributes:
        message: Success message
        count: Number of responses created
        responses: List of created responses with their status
    """
    message: str
    count: int
    responses: list[BatchCreateResponse]
