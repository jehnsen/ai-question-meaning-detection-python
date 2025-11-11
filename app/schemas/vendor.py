"""
Pydantic schemas for vendor and relationship management.
"""
from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import datetime


# ==================== Vendor Schemas ====================

class VendorInput(BaseModel):
    """
    Input for creating/updating a vendor.

    Attributes:
        vendor_id: Unique vendor identifier
        vendor_name: Name of the vendor
        description: Business description for AI embedding
        industry: Industry classification
        country: Country/region
    """
    vendor_id: str
    vendor_name: str
    description: Optional[str] = None
    industry: Optional[str] = None
    country: Optional[str] = None


class VendorOutput(BaseModel):
    """
    Output for vendor information.
    """
    id: int
    vendor_id: str
    vendor_name: str
    description: Optional[str]
    industry: Optional[str]
    country: Optional[str]


class BatchVendorInput(BaseModel):
    """
    Batch input for creating multiple vendors.
    """
    vendors: List[VendorInput]


# ==================== Relationship Schemas ====================

class RelationshipInput(BaseModel):
    """
    Input for creating a vendor relationship.

    Attributes:
        source_vendor_id: Vendor initiating the relationship
        target_vendor_id: Vendor receiving the relationship
        relationship_type: Type (partner, supplier, client, subsidiary, etc.)
        strength: Relationship strength (0.0-1.0)
        description: Optional description
        verified: Whether manually verified
    """
    source_vendor_id: str
    target_vendor_id: str
    relationship_type: str = Field(..., examples=["partner", "supplier", "client", "subsidiary"])
    strength: float = Field(default=1.0, ge=0.0, le=1.0)
    description: Optional[str] = None
    verified: bool = Field(default=False)


class RelationshipOutput(BaseModel):
    """
    Output for relationship information.
    """
    id: int
    source_vendor_id: str
    target_vendor_id: str
    relationship_type: str
    strength: float
    description: Optional[str]
    created_at: datetime
    verified: bool


class BatchRelationshipInput(BaseModel):
    """
    Batch input for creating multiple relationships.
    """
    relationships: List[RelationshipInput]


# ==================== Graph Search Schemas ====================

class VendorNode(BaseModel):
    """
    Represents a vendor node in the relationship graph.
    """
    vendor_id: str
    vendor_name: str
    industry: Optional[str]
    depth: int  # Distance from source (0 = source, 1 = direct connection, etc.)


class RelationshipPath(BaseModel):
    """
    Represents a path of relationships between vendors.

    For Risk Management:
    - path_length indicates degrees of separation (risk distance)
    - total_strength shows cumulative risk exposure
    - Lower strength = Higher risk propagation potential
    """
    source_vendor_id: str
    target_vendor_id: str
    path: List[VendorNode]  # All nodes in the path
    relationships: List[RelationshipOutput]  # All edges in the path
    total_strength: float  # Combined relationship strength (risk multiplier)
    path_length: int  # Number of hops (degrees of separation)
    risk_score: Optional[float] = None  # Calculated risk score (1 - total_strength)


class GraphSearchInput(BaseModel):
    """
    Input for searching vendor relationship graph.

    **VENDOR RISK MANAGEMENT USE CASE:**
    - Deep searches (up to 15 degrees) to identify supply chain risks
    - Risk propagation analysis through vendor networks
    - Compliance checking across indirect vendor relationships
    - Third-party risk assessment (Nth-party vendors)

    Attributes:
        source_vendor_id: Starting vendor
        min_depth: Minimum relationship depth (1-15, default: 3)
        max_depth: Maximum relationship depth (1-15, default: 10 for risk analysis)
        relationship_types: Filter by relationship types (optional)
        min_strength: Minimum relationship strength threshold (for risk cutoff)
        limit: Maximum number of results
    """
    source_vendor_id: str
    min_depth: int = Field(default=3, ge=1, le=15, description="Minimum depth for risk analysis")
    max_depth: int = Field(default=10, ge=1, le=15, description="Maximum depth (10 recommended for risk management)")
    relationship_types: Optional[List[str]] = None
    min_strength: float = Field(default=0.0, ge=0.0, le=1.0, description="Risk threshold (0=all risks, 0.8=high-confidence only)")
    limit: int = Field(default=100, ge=1, le=1000)


class GraphSearchOutput(BaseModel):
    """
    Output for graph search results.
    """
    source_vendor_id: str
    source_vendor_name: str
    paths_found: int
    paths: List[RelationshipPath]


# ==================== Vendor Matching Schemas ====================

class VendorMatchInput(BaseModel):
    """
    Input for AI-powered vendor matching.

    Attributes:
        query: Search query or vendor description
        industry: Optional industry filter
        country: Optional country filter
        top_k: Number of top matches to return
    """
    query: str
    industry: Optional[str] = None
    country: Optional[str] = None
    top_k: int = Field(default=10, ge=1, le=100)


class VendorMatch(BaseModel):
    """
    A single vendor match result.
    """
    vendor: VendorOutput
    similarity_score: float
    rank: int


class VendorMatchOutput(BaseModel):
    """
    Output for vendor matching results.
    """
    query: str
    matches_found: int
    matches: List[VendorMatch]
