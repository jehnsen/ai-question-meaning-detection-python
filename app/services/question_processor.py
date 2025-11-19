"""
Question processing service implementing the new 4-step Intelligent Fallback Chain.

Step 1: ID Match - Check for exact ID match
Step 2: Fuzzy Match - Use text normalization and Levenshtein distance
Step 3: Semantic Search - Use AI embeddings (costs money)
Step 4: Re-Ranker + Confidence Engine - Apply confidence thresholds
"""
from datetime import datetime
from sqlmodel import Session, select
from app.models import ResponseEntry, QuestionLink, MatchLog
from app.schemas import Question, QuestionResult, ResponseData, Answer
from .embedding import get_embedding, get_batch_embeddings
from .text_utils import fuzzy_match_score
from .semantic_search import search_similar_questions, search_similar_questions_fallback


class QuestionProcessor:
    """
    Service for processing questions using the 4-step Intelligent Fallback Chain:
    1. ID Match - Check for saved link or exact ID match
    2. Fuzzy Match - Normalize text and use Levenshtein distance
    3. Semantic Search - Use AI embeddings (expensive)
    4. Re-Ranker + Confidence Engine - Apply 3-tier thresholds
    """

    # Confidence thresholds
    HIGH_CONFIDENCE_THRESHOLD = 0.92
    MEDIUM_CONFIDENCE_THRESHOLD = 0.80
    FUZZY_MATCH_THRESHOLD = 0.90

    def __init__(self, session: Session, client_id: str, provider_id: str, use_mysql_vector: bool = True):
        """
        Initialize question processor for a specific provider.

        Args:
            session: Database session
            client_id: Client identifier (not used in data model, kept for API compatibility)
            provider_id: Provider/vendor identifier for multi-tenant filtering
            use_mysql_vector: Whether to use MySQL native VECTOR_COSINE_DISTANCE (default: True)
        """
        self.session = session
        self.client_id = client_id  # Kept for potential future use
        self.provider_id = provider_id
        self.use_mysql_vector = use_mysql_vector

    async def process_single_question(self, question: Question) -> QuestionResult:
        """
        Process a single question through the 4-step Intelligent Fallback Chain.

        Args:
            question: Question to process

        Returns:
            QuestionResult with status and data
        """
        # Step 1: ID Match
        result = await self._step1_id_match(question)
        if result:
            return result

        # Step 2: Fuzzy Match
        result = await self._step2_fuzzy_match(question)
        if result:
            return result

        # Step 3: Semantic Search
        embedding = await get_embedding(question.text)
        result = await self._step3_semantic_search(question, embedding)
        if result:
            return result

        # No match found
        return await self._log_and_return(
            question_id=question.id,
            match_method="NONE",
            confidence_score=0.0,
            final_status="NO_MATCH",
            response_data=None
        )

    async def process_batch_questions(self, questions: list[Question]) -> list[QuestionResult]:
        """
        Process multiple questions with optimized batch embedding.

        Implements the 4-step chain with batch optimization:
        - Steps 1 & 2 processed individually (no AI cost)
        - Step 3 uses batch embedding for efficiency

        Args:
            questions: List of questions to process

        Returns:
            List of QuestionResult objects
        """
        results = []
        questions_needing_semantic_search = []
        question_indices = {}  # Map question to its original index

        # Phase 1: Process Steps 1 & 2 (no AI cost)
        for idx, question in enumerate(questions):
            # Step 1: ID Match
            result = await self._step1_id_match(question)
            if result:
                results.append(result)
                continue

            # Step 2: Fuzzy Match
            result = await self._step2_fuzzy_match(question)
            if result:
                results.append(result)
                continue

            # Need semantic search
            questions_needing_semantic_search.append(question)
            question_indices[id(question)] = len(results)
            results.append(None)  # Placeholder

        # Phase 2: Batch semantic search for remaining questions
        if questions_needing_semantic_search:
            texts_to_embed = [q.text for q in questions_needing_semantic_search]
            embeddings = await get_batch_embeddings(texts_to_embed)

            for idx, question in enumerate(questions_needing_semantic_search):
                embedding = embeddings[idx]
                result = await self._step3_semantic_search(question, embedding)

                # Replace placeholder with result
                original_idx = question_indices[id(question)]
                results[original_idx] = result

        return results

    async def _step1_id_match(self, question: Question) -> QuestionResult | None:
        """
        Step 1: Check for saved link or exact ID match.

        Returns:
            QuestionResult if match found, None otherwise
        """
        # Check for saved link
        link_query = select(QuestionLink).where(
            QuestionLink.provider_id == self.provider_id,
            QuestionLink.new_question_id == str(question.id)
        )
        existing_link = self.session.exec(link_query).first()

        if existing_link:
            response_entry = self.session.get(ResponseEntry, existing_link.linked_response_id)
            if response_entry:
                return await self._log_and_return(
                    question_id=question.id,
                    match_method="ID",
                    confidence_score=1.0,
                    final_status="LINKED",
                    response_data=ResponseData(
                        answer=Answer(**response_entry.answer),
                        evidence=response_entry.evidence,
                        canonical_question_text=response_entry.question_text,
                        similarity_score=1.0
                    )
                )

        # Check for exact ID match
        exact_match_query = select(ResponseEntry).where(
            ResponseEntry.provider_id == self.provider_id,
            ResponseEntry.question_id == str(question.id)
        )
        exact_match = self.session.exec(exact_match_query).first()

        if exact_match:
            return await self._log_and_return(
                question_id=question.id,
                match_method="ID",
                confidence_score=1.0,
                final_status="LINKED",
                response_data=ResponseData(
                    answer=Answer(**exact_match.answer),
                    evidence=exact_match.evidence,
                    canonical_question_text=exact_match.question_text,
                    similarity_score=1.0
                )
            )

        return None

    async def _step2_fuzzy_match(self, question: Question) -> QuestionResult | None:
        """
        Step 2: Normalize text and perform fuzzy matching using Levenshtein distance.

        This is a low-cost check that happens before calling the AI API.

        Returns:
            QuestionResult if fuzzy match found, None otherwise
        """
        # Load all responses for this client-vendor pair
        statement = select(ResponseEntry).where(ResponseEntry.provider_id == self.provider_id)
        all_responses = self.session.exec(statement).all()

        if not all_responses:
            return None

        # Find best fuzzy match
        best_match = None
        best_score = 0.0

        for response in all_responses:
            score = fuzzy_match_score(question.text, response.question_text)
            if score > best_score:
                best_score = score
                best_match = response

        # Check if score exceeds threshold
        if best_score >= self.FUZZY_MATCH_THRESHOLD:
            return await self._log_and_return(
                question_id=question.id,
                match_method="FUZZY",
                confidence_score=best_score,
                final_status="LINKED",
                response_data=ResponseData(
                    answer=Answer(**best_match.answer),
                    evidence=best_match.evidence,
                    canonical_question_text=best_match.question_text,
                    similarity_score=best_score
                )
            )

        return None

    async def _step3_semantic_search(
        self,
        question: Question,
        embedding: list[float]
    ) -> QuestionResult:
        """
        Step 3 & 4: Semantic search + Re-Ranker + Confidence Engine.

        Uses AI embeddings to find similar questions, then applies confidence logic.

        Args:
            question: Question to process
            embedding: Pre-computed embedding vector

        Returns:
            QuestionResult with appropriate status
        """
        # Perform semantic search (top 5)
        try:
            if self.use_mysql_vector:
                search_results = await search_similar_questions(
                    self.session, self.provider_id, embedding, top_k=5
                )
            else:
                search_results = await search_similar_questions_fallback(
                    self.session, self.provider_id, embedding, top_k=5
                )
        except Exception as e:
            # Fallback to Python-based similarity if MySQL vector fails
            print(f"MySQL vector search failed, using fallback: {e}")
            search_results = await search_similar_questions_fallback(
                self.session, self.provider_id, embedding, top_k=5
            )

        if not search_results:
            return await self._log_and_return(
                question_id=question.id,
                match_method="SEMANTIC",
                confidence_score=0.0,
                final_status="NO_MATCH",
                response_data=None
            )

        # Step 4: Re-Ranker (for now, just use the top match)
        top_match = search_results[0]
        similarity_score = top_match.similarity_score

        # Step 4: Confidence Engine - Apply 3-tier logic
        if similarity_score > self.HIGH_CONFIDENCE_THRESHOLD:
            # HIGH CONFIDENCE: Auto-link
            auto_link = QuestionLink(
                provider_id=self.provider_id,
                new_question_id=str(question.id),
                linked_response_id=top_match.response.id
            )
            self.session.add(auto_link)
            self.session.commit()

            return await self._log_and_return(
                question_id=question.id,
                match_method="SEMANTIC",
                confidence_score=similarity_score,
                final_status="LINKED",
                response_data=ResponseData(
                    answer=Answer(**top_match.response.answer),
                    evidence=top_match.response.evidence,
                    canonical_question_text=top_match.response.question_text,
                    similarity_score=similarity_score
                )
            )

        elif similarity_score >= self.MEDIUM_CONFIDENCE_THRESHOLD:
            # MEDIUM CONFIDENCE: Confirmation required
            return await self._log_and_return(
                question_id=question.id,
                match_method="SEMANTIC",
                confidence_score=similarity_score,
                final_status="CONFIRMATION_REQUIRED",
                response_data=ResponseData(
                    answer=Answer(**top_match.response.answer),
                    evidence=top_match.response.evidence,
                    canonical_question_text=top_match.response.question_text,
                    similarity_score=similarity_score
                )
            )

        else:
            # LOW CONFIDENCE: No match
            return await self._log_and_return(
                question_id=question.id,
                match_method="SEMANTIC",
                confidence_score=similarity_score,
                final_status="NO_MATCH",
                response_data=None
            )

    async def _log_and_return(
        self,
        question_id,  # Union[int, str]
        match_method: str,
        confidence_score: float,
        final_status: str,
        response_data: ResponseData | None
    ) -> QuestionResult:
        """
        Log the match result to MatchLog table and return QuestionResult.

        Args:
            question_id: ID of the question (can be int or str)
            match_method: Method used ("ID", "FUZZY", "SEMANTIC", "NONE")
            confidence_score: Confidence score (0.0 to 1.0)
            final_status: Final status ("LINKED", "CONFIRMATION_REQUIRED", "NO_MATCH")
            response_data: Response data if match found

        Returns:
            QuestionResult object
        """
        # Create log entry
        log_entry = MatchLog(
            question_id=str(question_id),  # Convert to string for storage
            match_method=match_method,
            confidence_score=confidence_score,
            final_status=final_status,
            timestamp=datetime.utcnow(),
            provider_id=self.provider_id
        )
        self.session.add(log_entry)
        self.session.commit()

        # Return result
        return QuestionResult(
            id=question_id,  # Keep original type (int or str)
            status=final_status,
            data=response_data
        )
