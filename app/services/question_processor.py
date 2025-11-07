"""
Question processing service implementing 4-step matching logic.
"""
from sqlmodel import Session, select
from app.models import ResponseEntry, QuestionLink
from app.schemas import Question, QuestionResult, ResponseData
from .embedding import get_embedding, get_batch_embeddings, cosine_similarity


class QuestionProcessor:
    """
    Service for processing questions using 4-step logic:
    1. Check for saved link
    2. Check for exact ID match
    3. Run AI search using embeddings
    4. Apply 3-tier confidence logic
    """

    def __init__(self, session: Session, vendor_id: str):
        """
        Initialize question processor for a specific vendor.

        Args:
            session: Database session
            vendor_id: Vendor identifier for multi-tenant filtering
        """
        self.session = session
        self.vendor_id = vendor_id

    async def process_single_question(self, question: Question) -> QuestionResult:
        """
        Process a single question through 4-step logic.

        Args:
            question: Question to process

        Returns:
            QuestionResult with status and data
        """
        # Step 1: Check for saved link
        link_query = select(QuestionLink).where(
            QuestionLink.vendor_id == self.vendor_id,
            QuestionLink.new_question_id == question.id
        )
        existing_link = self.session.exec(link_query).first()

        if existing_link:
            response_entry = self.session.get(ResponseEntry, existing_link.linked_response_id)
            if response_entry:
                return QuestionResult(
                    id=question.id,
                    status="LINKED",
                    data=ResponseData(
                        answer_text=response_entry.answer_text,
                        evidence=response_entry.evidence,
                        canonical_question_text=response_entry.question_text,
                        similarity_score=1.0
                    )
                )

        # Step 2: Check for exact ID match
        exact_match_query = select(ResponseEntry).where(
            ResponseEntry.vendor_id == self.vendor_id,
            ResponseEntry.question_id == str(question.id)
        )
        exact_match = self.session.exec(exact_match_query).first()

        if exact_match:
            return QuestionResult(
                id=question.id,
                status="LINKED",
                data=ResponseData(
                    answer_text=exact_match.answer_text,
                    evidence=exact_match.evidence,
                    canonical_question_text=exact_match.question_text,
                    similarity_score=1.0
                )
            )

        # Step 3: Run AI search
        embedding = await get_embedding(question.text)
        all_responses = self.session.exec(
            select(ResponseEntry).where(ResponseEntry.vendor_id == self.vendor_id)
        ).all()

        if not all_responses:
            return QuestionResult(id=question.id, status="NO_MATCH")

        # Calculate similarities
        similarities = [
            (response, cosine_similarity(embedding, response.embedding))
            for response in all_responses
        ]
        similarities.sort(key=lambda x: x[1], reverse=True)
        top_match, similarity_score = similarities[0]

        # Step 4: Apply 3-tier logic
        return self._apply_confidence_logic(question.id, top_match, similarity_score)

    async def process_batch_questions(self, questions: list[Question]) -> list[QuestionResult]:
        """
        Process multiple questions with optimized batch embedding.

        Args:
            questions: List of questions to process

        Returns:
            List of QuestionResult objects
        """
        results = []
        questions_needing_ai_search = []

        # Phase 1: Process Steps 1 & 2
        for question in questions:
            # Step 1: Check for saved link
            link_query = select(QuestionLink).where(
                QuestionLink.vendor_id == self.vendor_id,
                QuestionLink.new_question_id == question.id
            )
            existing_link = self.session.exec(link_query).first()

            if existing_link:
                response_entry = self.session.get(ResponseEntry, existing_link.linked_response_id)
                if response_entry:
                    results.append(QuestionResult(
                        id=question.id,
                        status="LINKED",
                        data=ResponseData(
                            answer_text=response_entry.answer_text,
                            evidence=response_entry.evidence,
                            canonical_question_text=response_entry.question_text,
                            similarity_score=1.0
                        )
                    ))
                    continue

            # Step 2: Check for exact ID match
            exact_match_query = select(ResponseEntry).where(
                ResponseEntry.vendor_id == self.vendor_id,
                ResponseEntry.question_id == str(question.id)
            )
            exact_match = self.session.exec(exact_match_query).first()

            if exact_match:
                results.append(QuestionResult(
                    id=question.id,
                    status="LINKED",
                    data=ResponseData(
                        answer_text=exact_match.answer_text,
                        evidence=exact_match.evidence,
                        canonical_question_text=exact_match.question_text,
                        similarity_score=1.0
                    )
                ))
                continue

            questions_needing_ai_search.append(question)

        # Phase 2: Batch generate embeddings
        if questions_needing_ai_search:
            texts_to_embed = [q.text for q in questions_needing_ai_search]
            embeddings = await get_batch_embeddings(texts_to_embed)

            # Phase 3: Process AI search results
            for idx, question in enumerate(questions_needing_ai_search):
                embedding = embeddings[idx]

                all_responses = self.session.exec(
                    select(ResponseEntry).where(ResponseEntry.vendor_id == self.vendor_id)
                ).all()

                if not all_responses:
                    results.append(QuestionResult(id=question.id, status="NO_MATCH"))
                    continue

                similarities = [
                    (response, cosine_similarity(embedding, response.embedding))
                    for response in all_responses
                ]
                similarities.sort(key=lambda x: x[1], reverse=True)
                top_match, similarity_score = similarities[0]

                result = self._apply_confidence_logic(question.id, top_match, similarity_score)
                results.append(result)

        return results

    def _apply_confidence_logic(
        self,
        question_id: int,
        top_match: ResponseEntry,
        similarity_score: float
    ) -> QuestionResult:
        """
        Apply 3-tier confidence logic to determine result status.

        Args:
            question_id: ID of the question
            top_match: Best matching response entry
            similarity_score: Cosine similarity score

        Returns:
            QuestionResult with appropriate status
        """
        if similarity_score > 0.92:
            # HIGH CONFIDENCE: Auto-link
            auto_link = QuestionLink(
                vendor_id=self.vendor_id,
                new_question_id=question_id,
                linked_response_id=top_match.id
            )
            self.session.add(auto_link)
            self.session.commit()

            return QuestionResult(
                id=question_id,
                status="LINKED",
                data=ResponseData(
                    answer_text=top_match.answer_text,
                    evidence=top_match.evidence,
                    canonical_question_text=top_match.question_text,
                    similarity_score=similarity_score
                )
            )

        elif similarity_score >= 0.80:
            # MEDIUM CONFIDENCE: Confirmation required
            return QuestionResult(
                id=question_id,
                status="CONFIRMATION_REQUIRED",
                data=ResponseData(
                    answer_text=top_match.answer_text,
                    evidence=top_match.evidence,
                    canonical_question_text=top_match.question_text,
                    similarity_score=similarity_score
                )
            )

        else:
            # LOW CONFIDENCE: No match
            return QuestionResult(id=question_id, status="NO_MATCH")
