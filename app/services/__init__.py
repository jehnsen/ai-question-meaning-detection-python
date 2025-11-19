"""
Services Package for business logic.
"""
from .database import get_session, init_db
from .embedding import init_openai_client, get_embedding, get_batch_embeddings, cosine_similarity
from .question_processor import QuestionProcessor
from .text_utils import normalize_text, fuzzy_match_score, fuzzy_match_partial_score
from .semantic_search import search_similar_questions, search_similar_questions_fallback

__all__ = [
    "get_session",
    "init_db",
    "init_openai_client",
    "get_embedding",
    "get_batch_embeddings",
    "cosine_similarity",
    "QuestionProcessor",
    "normalize_text",
    "fuzzy_match_score",
    "fuzzy_match_partial_score",
    "search_similar_questions",
    "search_similar_questions_fallback",
]
