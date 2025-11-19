"""
Questionnaire processing API routes.
"""
from fastapi import APIRouter, Depends
from sqlmodel import Session
from app.schemas import QuestionnaireInput, QuestionnaireOutput
from app.services import get_session
from app.services.question_processor import QuestionProcessor

router = APIRouter(prefix="/questionnaire", tags=["questionnaire"])


@router.post("/process", response_model=QuestionnaireOutput)
async def process_questionnaire(
    questionnaire: QuestionnaireInput,
    session: Session = Depends(get_session)
):
    """
    Process questionnaire with single question embeddings.

    Processes each question individually through 4-step logic.
    Use /batch-process for better performance with large questionnaires.

    Args:
        questionnaire: Input containing client_id, provider_id and list of questions
        session: Database session

    Returns:
        QuestionnaireOutput with results for each question
    """
    processor = QuestionProcessor(session, questionnaire.client_id, questionnaire.provider_id)
    results = []

    for question in questionnaire.questions:
        result = await processor.process_single_question(question)
        results.append(result)

    return QuestionnaireOutput(results=results)


@router.post("/batch-process", response_model=QuestionnaireOutput)
async def batch_process_questionnaire(
    questionnaire: QuestionnaireInput,
    session: Session = Depends(get_session)
):
    """
    OPTIMIZED batch processing endpoint for large questionnaires.

    Production-ready features:
    - Automatic chunking for batches > 2048 questions
    - Exponential backoff retry logic for rate limits (3 retries: 2s, 4s, 8s)
    - Single API call per chunk instead of N individual calls
    - 60-100× faster for large batches

    Performance:
    - 500 questions: 1 API call instead of 500 calls
    - 3000 questions: 2 API calls instead of 3000 calls

    Args:
        questionnaire: Input containing client_id, provider_id and list of questions
        session: Database session

    Returns:
        QuestionnaireOutput with results for each question

    Raises:
        RateLimitError: If rate limit persists after 3 retries
        APIError: If OpenAI API error occurs
    """
    processor = QuestionProcessor(session, questionnaire.client_id, questionnaire.provider_id)
    results = await processor.process_batch_questions(questionnaire.questions)

    return QuestionnaireOutput(results=results)
