"""
Pydantic schemas for answer format.
"""
from typing import Optional
from pydantic import BaseModel, Field


class Answer(BaseModel):
    """
    Answer format schema with type, text, and comment fields.

    This allows for structured answers that can include classification,
    the main answer text, and optional comments/notes.

    Attributes:
        type: Type/classification of the answer (e.g., "text", "boolean", "multiple_choice", etc.)
        text: Main answer text (the actual answer)
        comment: Optional additional comment or note about the answer
    """
    type: str = Field(..., description="Type or classification of the answer")
    text: str = Field(..., description="Main answer text")
    comment: Optional[str] = Field(None, description="Optional additional comment or note")

    class Config:
        json_schema_extra = {
            "example": {
                "type": "text",
                "text": "We comply with GDPR, CCPA, and ISO 27001 standards.",
                "comment": "Updated as of Q4 2024"
            }
        }
