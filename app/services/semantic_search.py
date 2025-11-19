"""
Semantic search service using MySQL 8+ native vector functions.
"""
from typing import List, Tuple
from sqlmodel import Session, text
from app.models import ResponseEntry


class SemanticSearchResult:
    """Result from semantic search."""
    def __init__(self, response: ResponseEntry, similarity_score: float):
        self.response = response
        self.similarity_score = similarity_score


async def search_similar_questions(
    session: Session,
    provider_id: str,
    query_embedding: List[float],
    top_k: int = 5
) -> List[SemanticSearchResult]:
    """
    Search for similar questions using MySQL's VECTOR_COSINE_DISTANCE function.

    This function uses MySQL 8.0.40+ native vector support for efficient
    similarity search. The lower the distance, the more similar the vectors.

    Args:
        session: Database session
        provider_id: Provider/vendor identifier for multi-tenant filtering
        query_embedding: Query vector embedding (1024 dimensions)
        top_k: Number of top results to return (default: 5)

    Returns:
        List of SemanticSearchResult objects ordered by similarity (best first)
    """
    # Convert embedding to JSON string for MySQL
    import json
    embedding_json = json.dumps(query_embedding)

    # MySQL query using VECTOR_COSINE_DISTANCE
    # Note: MySQL's VECTOR_COSINE_DISTANCE returns distance (lower = more similar)
    # We'll convert it to similarity score (higher = more similar) by doing (1 - distance)
    query = text("""
        SELECT
            id,
            provider_id,
            question_id,
            question_text,
            answer,
            evidence,
            embedding,
            VECTOR_COSINE_DISTANCE(embedding, CAST(:embedding AS VECTOR)) AS distance_score
        FROM
            responseentry
        WHERE
            provider_id = :provider_id
        ORDER BY
            distance_score ASC
        LIMIT :top_k
    """)

    # Execute query
    result = session.execute(
        query,
        {
            "embedding": embedding_json,
            "provider_id": provider_id,
            "top_k": top_k
        }
    )

    # Process results
    search_results = []
    for row in result:
        # Reconstruct ResponseEntry from row
        response = ResponseEntry(
            id=row.id,
            provider_id=row.provider_id,
            question_id=row.question_id,
            question_text=row.question_text,
            answer=json.loads(row.answer) if isinstance(row.answer, str) else row.answer,
            evidence=row.evidence,
            embedding=json.loads(row.embedding) if isinstance(row.embedding, str) else row.embedding
        )

        # Convert distance to similarity (1 - distance)
        # MySQL cosine distance is in [0, 2], where 0 = identical
        # We convert to similarity score in [0, 1], where 1 = identical
        similarity_score = 1.0 - (row.distance_score / 2.0)

        search_results.append(SemanticSearchResult(response, similarity_score))

    return search_results


async def search_similar_questions_fallback(
    session: Session,
    provider_id: str,
    query_embedding: List[float],
    top_k: int = 5
) -> List[SemanticSearchResult]:
    """
    Fallback semantic search using Python-based cosine similarity.

    This is a fallback for MySQL versions that don't support VECTOR_COSINE_DISTANCE.
    It loads all vectors into memory and computes similarity in Python.

    Args:
        session: Database session
        provider_id: Provider/vendor identifier for multi-tenant filtering
        query_embedding: Query vector embedding (1024 dimensions)
        top_k: Number of top results to return (default: 5)

    Returns:
        List of SemanticSearchResult objects ordered by similarity (best first)
    """
    from sqlmodel import select
    from .embedding import cosine_similarity

    # Load all responses for the provider
    statement = select(ResponseEntry).where(ResponseEntry.provider_id == provider_id)
    all_responses = session.exec(statement).all()

    if not all_responses:
        return []

    # Calculate similarities in Python
    similarities = [
        (response, cosine_similarity(query_embedding, response.embedding))
        for response in all_responses
    ]

    # Sort by similarity (descending) and take top_k
    similarities.sort(key=lambda x: x[1], reverse=True)
    top_results = similarities[:top_k]

    # Convert to SemanticSearchResult objects
    search_results = [
        SemanticSearchResult(response, score)
        for response, score in top_results
    ]

    return search_results
