"""
AI-powered vendor matching service using embeddings.
"""
from typing import List, Optional, Tuple
from sqlmodel import Session, select
from app.models import Vendor
from app.schemas import VendorMatch, VendorOutput
from .embedding import get_embedding, cosine_similarity


class VendorMatcherService:
    """
    Service for AI-powered vendor matching using semantic embeddings.
    """

    def __init__(self, session: Session):
        """
        Initialize vendor matcher service.

        Args:
            session: Database session
        """
        self.session = session

    async def match_vendors(
        self,
        query: str,
        industry: Optional[str] = None,
        country: Optional[str] = None,
        top_k: int = 10
    ) -> List[VendorMatch]:
        """
        Find vendors matching the query using AI semantic search.

        Args:
            query: Search query or vendor description
            industry: Optional industry filter
            country: Optional country filter
            top_k: Number of top matches to return

        Returns:
            List of vendor matches sorted by similarity
        """
        # Generate embedding for query
        query_embedding = await get_embedding(query)

        # Build base query
        vendors_query = select(Vendor).where(Vendor.embedding.isnot(None))

        # Apply filters
        if industry:
            vendors_query = vendors_query.where(Vendor.industry == industry)
        if country:
            vendors_query = vendors_query.where(Vendor.country == country)

        vendors = self.session.exec(vendors_query).all()

        if not vendors:
            return []

        # Calculate similarities
        matches: List[Tuple[Vendor, float]] = []
        for vendor in vendors:
            if vendor.embedding:
                similarity = cosine_similarity(query_embedding, vendor.embedding)
                matches.append((vendor, similarity))

        # Sort by similarity (highest first)
        matches.sort(key=lambda x: x[1], reverse=True)

        # Return top K matches
        results = []
        for rank, (vendor, similarity) in enumerate(matches[:top_k], 1):
            results.append(VendorMatch(
                vendor=VendorOutput(
                    id=vendor.id,
                    vendor_id=vendor.vendor_id,
                    vendor_name=vendor.vendor_name,
                    description=vendor.description,
                    industry=vendor.industry,
                    country=vendor.country
                ),
                similarity_score=similarity,
                rank=rank
            ))

        return results

    async def find_similar_vendors(
        self,
        vendor_id: str,
        top_k: int = 10,
        exclude_self: bool = True
    ) -> List[VendorMatch]:
        """
        Find vendors similar to a given vendor.

        Args:
            vendor_id: Reference vendor ID
            top_k: Number of similar vendors to return
            exclude_self: Whether to exclude the reference vendor from results

        Returns:
            List of similar vendors sorted by similarity
        """
        # Get reference vendor
        ref_vendor = self.session.exec(
            select(Vendor).where(Vendor.vendor_id == vendor_id)
        ).first()

        if not ref_vendor or not ref_vendor.embedding:
            return []

        # Get all other vendors with embeddings
        vendors_query = select(Vendor).where(Vendor.embedding.isnot(None))

        if exclude_self:
            vendors_query = vendors_query.where(Vendor.vendor_id != vendor_id)

        vendors = self.session.exec(vendors_query).all()

        if not vendors:
            return []

        # Calculate similarities
        matches: List[Tuple[Vendor, float]] = []
        for vendor in vendors:
            if vendor.embedding:
                similarity = cosine_similarity(ref_vendor.embedding, vendor.embedding)
                matches.append((vendor, similarity))

        # Sort by similarity (highest first)
        matches.sort(key=lambda x: x[1], reverse=True)

        # Return top K matches
        results = []
        for rank, (vendor, similarity) in enumerate(matches[:top_k], 1):
            results.append(VendorMatch(
                vendor=VendorOutput(
                    id=vendor.id,
                    vendor_id=vendor.vendor_id,
                    vendor_name=vendor.vendor_name,
                    description=vendor.description,
                    industry=vendor.industry,
                    country=vendor.country
                ),
                similarity_score=similarity,
                rank=rank
            ))

        return results
