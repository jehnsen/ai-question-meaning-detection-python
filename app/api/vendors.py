"""
Vendor management and relationship search API routes.
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from app.models import Vendor, VendorRelationship
from app.schemas import (
    VendorInput, VendorOutput, BatchVendorInput,
    RelationshipInput, RelationshipOutput, BatchRelationshipInput,
    GraphSearchInput, GraphSearchOutput,
    VendorMatchInput, VendorMatchOutput
)
from app.services import get_session, get_embedding, get_batch_embeddings
from app.services.vendor_graph import VendorGraphService
from app.services.vendor_matcher import VendorMatcherService

router = APIRouter(prefix="/vendors", tags=["vendors"])


# ==================== Vendor Management ====================

@router.post("/create", response_model=VendorOutput)
async def create_vendor(
    vendor_input: VendorInput,
    session: Session = Depends(get_session)
):
    """
    Create a new vendor with AI embedding.

    Args:
        vendor_input: Vendor information
        session: Database session

    Returns:
        Created vendor

    Raises:
        HTTPException: If vendor_id already exists
    """
    # Check if vendor exists
    existing = session.exec(
        select(Vendor).where(Vendor.vendor_id == vendor_input.vendor_id)
    ).first()

    if existing:
        raise HTTPException(status_code=400, detail=f"Vendor {vendor_input.vendor_id} already exists")

    # Generate embedding from vendor description
    embedding = None
    if vendor_input.description:
        # Combine vendor info for better embedding
        embedding_text = f"{vendor_input.vendor_name}. {vendor_input.description}"
        if vendor_input.industry:
            embedding_text += f" Industry: {vendor_input.industry}"
        embedding = await get_embedding(embedding_text)

    # Create vendor
    vendor = Vendor(
        vendor_id=vendor_input.vendor_id,
        vendor_name=vendor_input.vendor_name,
        description=vendor_input.description,
        industry=vendor_input.industry,
        country=vendor_input.country,
        embedding=embedding
    )

    session.add(vendor)
    session.commit()
    session.refresh(vendor)

    return VendorOutput(
        id=vendor.id,
        vendor_id=vendor.vendor_id,
        vendor_name=vendor.vendor_name,
        description=vendor.description,
        industry=vendor.industry,
        country=vendor.country
    )


@router.post("/batch-create")
async def batch_create_vendors(
    input_data: BatchVendorInput,
    session: Session = Depends(get_session)
):
    """
    Batch create vendors with AI embeddings.

    Performance optimized: Single API call for all embeddings.

    Args:
        input_data: Batch vendor input
        session: Database session

    Returns:
        Count and list of created vendors

    Raises:
        HTTPException: If any vendor_id already exists
    """
    if not input_data.vendors:
        raise HTTPException(status_code=400, detail="No vendors provided")

    # Check for duplicates in batch
    vendor_ids = [v.vendor_id for v in input_data.vendors]
    if len(vendor_ids) != len(set(vendor_ids)):
        raise HTTPException(status_code=400, detail="Duplicate vendor_ids in batch")

    # Check for existing vendors
    existing_query = select(Vendor.vendor_id).where(Vendor.vendor_id.in_(vendor_ids))
    existing_ids = session.exec(existing_query).all()
    if existing_ids:
        raise HTTPException(
            status_code=400,
            detail=f"Vendors already exist: {', '.join(existing_ids)}"
        )

    # Prepare embedding texts
    texts_to_embed = []
    for vendor_input in input_data.vendors:
        if vendor_input.description:
            embedding_text = f"{vendor_input.vendor_name}. {vendor_input.description}"
            if vendor_input.industry:
                embedding_text += f" Industry: {vendor_input.industry}"
            texts_to_embed.append(embedding_text)
        else:
            texts_to_embed.append(None)

    # Batch generate embeddings
    embeddings_list = []
    non_none_texts = [t for t in texts_to_embed if t is not None]
    if non_none_texts:
        batch_embeddings = await get_batch_embeddings(non_none_texts)
        embedding_idx = 0
        for text in texts_to_embed:
            if text is None:
                embeddings_list.append(None)
            else:
                embeddings_list.append(batch_embeddings[embedding_idx])
                embedding_idx += 1
    else:
        embeddings_list = [None] * len(texts_to_embed)

    # Create all vendors
    created_vendors = []
    for idx, vendor_input in enumerate(input_data.vendors):
        vendor = Vendor(
            vendor_id=vendor_input.vendor_id,
            vendor_name=vendor_input.vendor_name,
            description=vendor_input.description,
            industry=vendor_input.industry,
            country=vendor_input.country,
            embedding=embeddings_list[idx]
        )
        session.add(vendor)
        created_vendors.append(vendor_input.vendor_id)

    session.commit()

    return {
        "message": f"Successfully created {len(created_vendors)} vendors",
        "count": len(created_vendors),
        "vendor_ids": created_vendors
    }


@router.get("/list", response_model=list[VendorOutput])
async def list_vendors(
    industry: Optional[str] = None,
    country: Optional[str] = None,
    limit: int = 100,
    session: Session = Depends(get_session)
):
    """
    List vendors with optional filters.

    Args:
        industry: Filter by industry
        country: Filter by country
        limit: Maximum number of results
        session: Database session

    Returns:
        List of vendors
    """
    query = select(Vendor)

    if industry:
        query = query.where(Vendor.industry == industry)
    if country:
        query = query.where(Vendor.country == country)

    query = query.limit(limit)
    vendors = session.exec(query).all()

    return [VendorOutput(
        id=v.id,
        vendor_id=v.vendor_id,
        vendor_name=v.vendor_name,
        description=v.description,
        industry=v.industry,
        country=v.country
    ) for v in vendors]


@router.get("/{vendor_id}", response_model=VendorOutput)
async def get_vendor(
    vendor_id: str,
    session: Session = Depends(get_session)
):
    """
    Get vendor by ID.

    Args:
        vendor_id: Vendor identifier
        session: Database session

    Returns:
        Vendor information

    Raises:
        HTTPException: If vendor not found
    """
    vendor = session.exec(
        select(Vendor).where(Vendor.vendor_id == vendor_id)
    ).first()

    if not vendor:
        raise HTTPException(status_code=404, detail=f"Vendor {vendor_id} not found")

    return VendorOutput(
        id=vendor.id,
        vendor_id=vendor.vendor_id,
        vendor_name=vendor.vendor_name,
        description=vendor.description,
        industry=vendor.industry,
        country=vendor.country
    )


# ==================== Relationship Management ====================

@router.post("/relationships/create", response_model=RelationshipOutput)
async def create_relationship(
    rel_input: RelationshipInput,
    session: Session = Depends(get_session)
):
    """
    Create a vendor relationship.

    Args:
        rel_input: Relationship information
        session: Database session

    Returns:
        Created relationship

    Raises:
        HTTPException: If vendors don't exist
    """
    # Verify both vendors exist
    source = session.exec(
        select(Vendor).where(Vendor.vendor_id == rel_input.source_vendor_id)
    ).first()
    target = session.exec(
        select(Vendor).where(Vendor.vendor_id == rel_input.target_vendor_id)
    ).first()

    if not source:
        raise HTTPException(status_code=404, detail=f"Source vendor {rel_input.source_vendor_id} not found")
    if not target:
        raise HTTPException(status_code=404, detail=f"Target vendor {rel_input.target_vendor_id} not found")

    # Create relationship
    relationship = VendorRelationship(
        source_vendor_id=rel_input.source_vendor_id,
        target_vendor_id=rel_input.target_vendor_id,
        relationship_type=rel_input.relationship_type,
        strength=rel_input.strength,
        description=rel_input.description,
        verified=rel_input.verified
    )

    session.add(relationship)
    session.commit()
    session.refresh(relationship)

    return RelationshipOutput(
        id=relationship.id,
        source_vendor_id=relationship.source_vendor_id,
        target_vendor_id=relationship.target_vendor_id,
        relationship_type=relationship.relationship_type,
        strength=relationship.strength,
        description=relationship.description,
        created_at=relationship.created_at,
        verified=relationship.verified
    )


@router.post("/relationships/batch-create")
async def batch_create_relationships(
    input_data: BatchRelationshipInput,
    session: Session = Depends(get_session)
):
    """
    Batch create vendor relationships.

    Args:
        input_data: Batch relationship input
        session: Database session

    Returns:
        Count of created relationships
    """
    if not input_data.relationships:
        raise HTTPException(status_code=400, detail="No relationships provided")

    # Get all unique vendor IDs
    vendor_ids = set()
    for rel in input_data.relationships:
        vendor_ids.add(rel.source_vendor_id)
        vendor_ids.add(rel.target_vendor_id)

    # Verify all vendors exist
    existing_vendors = session.exec(
        select(Vendor.vendor_id).where(Vendor.vendor_id.in_(list(vendor_ids)))
    ).all()
    existing_set = set(existing_vendors)

    missing = vendor_ids - existing_set
    if missing:
        raise HTTPException(
            status_code=404,
            detail=f"Vendors not found: {', '.join(missing)}"
        )

    # Create all relationships
    created_count = 0
    for rel_input in input_data.relationships:
        relationship = VendorRelationship(
            source_vendor_id=rel_input.source_vendor_id,
            target_vendor_id=rel_input.target_vendor_id,
            relationship_type=rel_input.relationship_type,
            strength=rel_input.strength,
            description=rel_input.description,
            verified=rel_input.verified
        )
        session.add(relationship)
        created_count += 1

    session.commit()

    return {
        "message": f"Successfully created {created_count} relationships",
        "count": created_count
    }


@router.get("/relationships/list")
async def list_relationships(
    vendor_id: Optional[str] = None,
    relationship_type: Optional[str] = None,
    limit: int = 100,
    session: Session = Depends(get_session)
):
    """
    List relationships with optional filters.

    Args:
        vendor_id: Filter by source or target vendor
        relationship_type: Filter by relationship type
        limit: Maximum number of results
        session: Database session

    Returns:
        List of relationships
    """
    query = select(VendorRelationship)

    if vendor_id:
        query = query.where(
            (VendorRelationship.source_vendor_id == vendor_id) |
            (VendorRelationship.target_vendor_id == vendor_id)
        )

    if relationship_type:
        query = query.where(VendorRelationship.relationship_type == relationship_type)

    query = query.limit(limit)
    relationships = session.exec(query).all()

    return [RelationshipOutput(
        id=r.id,
        source_vendor_id=r.source_vendor_id,
        target_vendor_id=r.target_vendor_id,
        relationship_type=r.relationship_type,
        strength=r.strength,
        description=r.description,
        created_at=r.created_at,
        verified=r.verified
    ) for r in relationships]


# ==================== Graph Search ====================

@router.post("/graph/search", response_model=GraphSearchOutput)
async def search_vendor_graph(
    search_input: GraphSearchInput,
    session: Session = Depends(get_session)
):
    """
    Search vendor relationship graph for connections.

    Finds all paths from source vendor within specified depth range (3-7 degrees).

    Uses BFS (Breadth-First Search) for efficient graph traversal.

    Args:
        search_input: Graph search parameters
        session: Database session

    Returns:
        All paths found within depth range

    Raises:
        HTTPException: If source vendor not found
    """
    # Verify source vendor exists
    source_vendor = session.exec(
        select(Vendor).where(Vendor.vendor_id == search_input.source_vendor_id)
    ).first()

    if not source_vendor:
        raise HTTPException(
            status_code=404,
            detail=f"Source vendor {search_input.source_vendor_id} not found"
        )

    # Initialize graph service
    graph_service = VendorGraphService(session)

    # Find paths
    paths = graph_service.find_paths(
        source_vendor_id=search_input.source_vendor_id,
        min_depth=search_input.min_depth,
        max_depth=search_input.max_depth,
        relationship_types=search_input.relationship_types,
        min_strength=search_input.min_strength,
        limit=search_input.limit
    )

    return GraphSearchOutput(
        source_vendor_id=search_input.source_vendor_id,
        source_vendor_name=source_vendor.vendor_name,
        paths_found=len(paths),
        paths=paths
    )


@router.get("/graph/stats/{vendor_id}")
async def get_vendor_network_stats(
    vendor_id: str,
    session: Session = Depends(get_session)
):
    """
    Get network statistics for a vendor.

    Args:
        vendor_id: Vendor to analyze
        session: Database session

    Returns:
        Network statistics

    Raises:
        HTTPException: If vendor not found
    """
    # Verify vendor exists
    vendor = session.exec(
        select(Vendor).where(Vendor.vendor_id == vendor_id)
    ).first()

    if not vendor:
        raise HTTPException(status_code=404, detail=f"Vendor {vendor_id} not found")

    graph_service = VendorGraphService(session)
    return graph_service.get_vendor_network_stats(vendor_id)


# ==================== AI Matching ====================

@router.post("/match", response_model=VendorMatchOutput)
async def match_vendors(
    match_input: VendorMatchInput,
    session: Session = Depends(get_session)
):
    """
    AI-powered vendor matching using semantic search.

    Finds vendors matching the query description using OpenAI embeddings.

    Args:
        match_input: Match search parameters
        session: Database session

    Returns:
        Top matching vendors sorted by similarity
    """
    matcher = VendorMatcherService(session)

    matches = await matcher.match_vendors(
        query=match_input.query,
        industry=match_input.industry,
        country=match_input.country,
        top_k=match_input.top_k
    )

    return VendorMatchOutput(
        query=match_input.query,
        matches_found=len(matches),
        matches=matches
    )


@router.get("/similar/{vendor_id}")
async def find_similar_vendors(
    vendor_id: str,
    top_k: int = 10,
    session: Session = Depends(get_session)
):
    """
    Find vendors similar to a given vendor using AI.

    Args:
        vendor_id: Reference vendor ID
        top_k: Number of similar vendors to return
        session: Database session

    Returns:
        Similar vendors sorted by similarity

    Raises:
        HTTPException: If vendor not found
    """
    # Verify vendor exists
    vendor = session.exec(
        select(Vendor).where(Vendor.vendor_id == vendor_id)
    ).first()

    if not vendor:
        raise HTTPException(status_code=404, detail=f"Vendor {vendor_id} not found")

    matcher = VendorMatcherService(session)
    matches = await matcher.find_similar_vendors(vendor_id, top_k)

    return {
        "reference_vendor_id": vendor_id,
        "reference_vendor_name": vendor.vendor_name,
        "matches_found": len(matches),
        "matches": matches
    }
