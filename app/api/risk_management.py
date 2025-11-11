"""
Vendor Risk Management API routes.

Specialized endpoints for supply chain risk assessment and third-party risk management.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from app.models import Vendor
from app.schemas import GraphSearchInput, GraphSearchOutput
from app.services import get_session
from app.services.vendor_graph import VendorGraphService

router = APIRouter(prefix="/risk", tags=["risk-management"])


@router.post("/supply-chain-analysis", response_model=GraphSearchOutput)
async def analyze_supply_chain_risk(
    search_input: GraphSearchInput,
    session: Session = Depends(get_session)
):
    """
    **SUPPLY CHAIN RISK ANALYSIS**

    Analyze risk propagation through vendor supply chains.

    **Use Cases:**
    - Identify indirect vendor exposures (3rd, 4th, 5th party vendors)
    - Map risk propagation pathways
    - Assess supply chain vulnerabilities
    - Third-party risk management (TPRM)
    - Fourth-party risk management (FPRM)

    **Recommended Settings for Risk Management:**
    - `min_depth`: 3 (third-party vendors)
    - `max_depth`: 10 (up to 10th-party vendors)
    - `min_strength`: 0.0 (include all risk paths)
    - `limit`: 500 (comprehensive analysis)

    **Risk Scoring:**
    - `risk_score`: 1.0 = Maximum risk (weak connection)
    - `risk_score`: 0.0 = Minimum risk (strong connection)
    - `total_strength`: Cumulative relationship confidence

    Args:
        search_input: Graph search parameters with risk analysis settings
        session: Database session

    Returns:
        Comprehensive supply chain risk analysis with risk scores

    Example:
        ```json
        {
          "source_vendor_id": "PRIMARY-VENDOR-001",
          "min_depth": 3,
          "max_depth": 10,
          "relationship_types": ["supplier", "subcontractor"],
          "min_strength": 0.0,
          "limit": 500
        }
        ```

    Response includes:
        - All paths from 3 to 10 degrees deep
        - Risk score for each path
        - Vendor nodes at each level
        - Relationship metadata
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

    # Find all risk paths
    paths = graph_service.find_paths(
        source_vendor_id=search_input.source_vendor_id,
        min_depth=search_input.min_depth,
        max_depth=search_input.max_depth,
        relationship_types=search_input.relationship_types,
        min_strength=search_input.min_strength,
        limit=search_input.limit
    )

    # Sort by risk score (highest risk first)
    paths_sorted = sorted(paths, key=lambda p: p.risk_score if p.risk_score else 0, reverse=True)

    return GraphSearchOutput(
        source_vendor_id=search_input.source_vendor_id,
        source_vendor_name=source_vendor.vendor_name,
        paths_found=len(paths_sorted),
        paths=paths_sorted
    )


@router.get("/deep-search/{vendor_id}")
async def deep_vendor_search(
    vendor_id: str,
    max_depth: int = 10,
    session: Session = Depends(get_session)
):
    """
    **DEEP VENDOR NETWORK SEARCH (Up to 15 degrees)**

    Comprehensive search of all vendor connections up to specified depth.

    **Risk Management Depths:**
    - **3-5 degrees**: Direct supply chain (TPRM)
    - **6-10 degrees**: Extended supply chain (FPRM)
    - **11-15 degrees**: Complete network analysis

    Args:
        vendor_id: Starting vendor for analysis
        max_depth: Maximum search depth (1-15, default: 10)
        session: Database session

    Returns:
        All vendor connections organized by depth level

    Raises:
        HTTPException: If vendor not found or invalid depth
    """
    if max_depth < 1 or max_depth > 15:
        raise HTTPException(
            status_code=400,
            detail="max_depth must be between 1 and 15"
        )

    # Verify vendor exists
    vendor = session.exec(
        select(Vendor).where(Vendor.vendor_id == vendor_id)
    ).first()

    if not vendor:
        raise HTTPException(status_code=404, detail=f"Vendor {vendor_id} not found")

    graph_service = VendorGraphService(session)

    # Search from depth 1 to max_depth
    all_paths = graph_service.find_paths(
        source_vendor_id=vendor_id,
        min_depth=1,
        max_depth=max_depth,
        limit=1000  # Higher limit for deep searches
    )

    # Organize by depth level
    paths_by_depth = {}
    for path in all_paths:
        depth = path.path_length
        if depth not in paths_by_depth:
            paths_by_depth[depth] = []
        paths_by_depth[depth].append({
            "target_vendor_id": path.target_vendor_id,
            "path_length": path.path_length,
            "total_strength": path.total_strength,
            "risk_score": path.risk_score,
            "path": [{"vendor_id": n.vendor_id, "vendor_name": n.vendor_name} for n in path.path]
        })

    # Calculate statistics per level
    depth_statistics = {}
    for depth, paths_list in paths_by_depth.items():
        depth_statistics[f"level_{depth}"] = {
            "degree": depth,
            "vendors_found": len(paths_list),
            "avg_risk_score": sum(p["risk_score"] for p in paths_list if p["risk_score"]) / len(paths_list) if paths_list else 0,
            "max_risk_score": max((p["risk_score"] for p in paths_list if p["risk_score"]), default=0),
            "paths": paths_list
        }

    return {
        "source_vendor_id": vendor_id,
        "source_vendor_name": vendor.vendor_name,
        "max_depth_searched": max_depth,
        "total_paths_found": len(all_paths),
        "depth_statistics": depth_statistics,
        "risk_summary": {
            "highest_risk_paths": sorted(
                all_paths,
                key=lambda p: p.risk_score if p.risk_score else 0,
                reverse=True
            )[:10]
        }
    }


@router.get("/risk-hotspots")
async def identify_risk_hotspots(
    min_connections: int = 5,
    session: Session = Depends(get_session)
):
    """
    **IDENTIFY VENDOR RISK HOTSPOTS**

    Find vendors with many connections (potential single points of failure).

    High-connectivity vendors pose risks:
    - Supply chain bottlenecks
    - Cascading failure points
    - Systemic risk concentrations

    Args:
        min_connections: Minimum connections to qualify as hotspot (default: 5)
        session: Database session

    Returns:
        List of high-risk vendor hotspots with connection counts
    """
    graph_service = VendorGraphService(session)

    # Get all vendors
    all_vendors = session.exec(select(Vendor)).all()

    hotspots = []
    for vendor in all_vendors:
        stats = graph_service.get_vendor_network_stats(vendor.vendor_id)

        if stats["total_connections"] >= min_connections:
            hotspots.append({
                "vendor_id": vendor.vendor_id,
                "vendor_name": vendor.vendor_name,
                "industry": vendor.industry,
                "total_connections": stats["total_connections"],
                "outgoing_connections": stats["outgoing_count"],
                "incoming_connections": stats["incoming_count"],
                "risk_classification": (
                    "CRITICAL" if stats["total_connections"] >= 10 else
                    "HIGH" if stats["total_connections"] >= 7 else
                    "MEDIUM"
                )
            })

    # Sort by connection count (highest risk first)
    hotspots_sorted = sorted(hotspots, key=lambda x: x["total_connections"], reverse=True)

    return {
        "hotspots_found": len(hotspots_sorted),
        "criteria": f"Vendors with {min_connections}+ connections",
        "hotspots": hotspots_sorted,
        "risk_summary": {
            "critical_hotspots": [h for h in hotspots_sorted if h["risk_classification"] == "CRITICAL"],
            "high_risk_hotspots": [h for h in hotspots_sorted if h["risk_classification"] == "HIGH"],
            "medium_risk_hotspots": [h for h in hotspots_sorted if h["risk_classification"] == "MEDIUM"]
        }
    }


@router.post("/nth-party-assessment")
async def nth_party_vendor_assessment(
    vendor_id: str,
    party_level: int = 3,
    session: Session = Depends(get_session)
):
    """
    **NTH-PARTY VENDOR ASSESSMENT**

    Assess specific levels of vendor relationships:
    - 1st party: Direct vendors
    - 2nd party: Vendors' vendors
    - 3rd party: Third-party vendors (TPRM focus)
    - 4th+ party: Fourth-party and beyond (FPRM focus)

    Args:
        vendor_id: Starting vendor
        party_level: Which level to assess (1-15)
        session: Database session

    Returns:
        All vendors at the specified party level

    Example:
        `party_level=3` returns all third-party vendors
    """
    if party_level < 1 or party_level > 15:
        raise HTTPException(
            status_code=400,
            detail="party_level must be between 1 and 15"
        )

    vendor = session.exec(
        select(Vendor).where(Vendor.vendor_id == vendor_id)
    ).first()

    if not vendor:
        raise HTTPException(status_code=404, detail=f"Vendor {vendor_id} not found")

    graph_service = VendorGraphService(session)

    # Get paths exactly at this depth
    paths = graph_service.find_paths(
        source_vendor_id=vendor_id,
        min_depth=party_level,
        max_depth=party_level,
        limit=500
    )

    # Extract unique vendors at this level
    vendors_at_level = {}
    for path in paths:
        if path.path:
            target_node = path.path[-1]
            if target_node.vendor_id not in vendors_at_level:
                vendors_at_level[target_node.vendor_id] = {
                    "vendor_id": target_node.vendor_id,
                    "vendor_name": target_node.vendor_name,
                    "industry": target_node.industry,
                    "paths_to_vendor": 1,
                    "avg_risk_score": path.risk_score if path.risk_score else 0,
                    "strongest_path_strength": path.total_strength
                }
            else:
                vendors_at_level[target_node.vendor_id]["paths_to_vendor"] += 1
                # Update average risk
                current_risk = vendors_at_level[target_node.vendor_id]["avg_risk_score"]
                vendors_at_level[target_node.vendor_id]["avg_risk_score"] = (
                    (current_risk + (path.risk_score if path.risk_score else 0)) / 2
                )

    vendors_list = list(vendors_at_level.values())

    return {
        "source_vendor_id": vendor_id,
        "source_vendor_name": vendor.vendor_name,
        "party_level": party_level,
        "party_classification": (
            "First-party (Direct vendors)" if party_level == 1 else
            "Second-party (Vendors' vendors)" if party_level == 2 else
            f"{party_level}rd-party vendors" if party_level == 3 else
            f"{party_level}th-party vendors"
        ),
        "vendors_found": len(vendors_list),
        "vendors": sorted(vendors_list, key=lambda x: x["avg_risk_score"], reverse=True)
    }
