"""
OpenAI embedding service for generating and comparing vector embeddings.
"""
import os
import time
import numpy as np
from typing import Optional
from openai import OpenAI, RateLimitError, APIError
from dotenv import load_dotenv

# Load environment variables
load_dotenv(override=True)

# OpenAI configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY environment variable is required")

# Global OpenAI client
openai_client: Optional[OpenAI] = None


def init_openai_client():
    """
    Initialize the OpenAI client.
    """
    global openai_client
    print("Initializing OpenAI client...")
    openai_client = OpenAI(api_key=OPENAI_API_KEY)
    print("OpenAI client initialized successfully!")


def cosine_similarity(vec1: list[float], vec2: list[float]) -> float:
    """
    Calculate cosine similarity between two vectors.

    MySQL doesn't have native vector operations, so we compute
    similarity in Python using NumPy.

    Args:
        vec1: First vector
        vec2: Second vector

    Returns:
        Similarity score between 0 and 1 (1 = identical, 0 = orthogonal)
    """
    v1 = np.array(vec1)
    v2 = np.array(vec2)

    dot_product = np.dot(v1, v2)
    norm_v1 = np.linalg.norm(v1)
    norm_v2 = np.linalg.norm(v2)

    if norm_v1 == 0 or norm_v2 == 0:
        return 0.0

    return float(dot_product / (norm_v1 * norm_v2))


async def get_embedding(text: str) -> list[float]:
    """
    Generate embedding vector for the given text using OpenAI API.

    Args:
        text: Input text to embed

    Returns:
        1024-dimensional embedding vector from text-embedding-3-small

    Raises:
        RuntimeError: If OpenAI client not initialized
    """
    if openai_client is None:
        raise RuntimeError("OpenAI client not initialized")

    response = openai_client.embeddings.create(
        input=text,
        model="text-embedding-3-small",
        dimensions=1024
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
