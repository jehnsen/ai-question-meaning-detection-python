"""
Vendor relationship graph service with BFS/DFS traversal algorithms.
"""
from typing import List, Dict, Set, Optional, Tuple
from collections import deque
from sqlmodel import Session, select
from app.models import Vendor, VendorRelationship
from app.schemas import RelationshipPath, VendorNode, RelationshipOutput


class VendorGraphService:
    """
    Service for traversing and searching vendor relationship graphs.

    Supports multi-level relationship discovery from 3rd to 7th degree connections.
    """

    def __init__(self, session: Session):
        """
        Initialize vendor graph service.

        Args:
            session: Database session
        """
        self.session = session

    def find_paths(
        self,
        source_vendor_id: str,
        min_depth: int = 3,
        max_depth: int = 7,
        relationship_types: Optional[List[str]] = None,
        min_strength: float = 0.0,
        limit: int = 100
    ) -> List[RelationshipPath]:
        """
        Find all paths from source vendor within specified depth range.

        Uses BFS (Breadth-First Search) to explore the graph level by level.

        Args:
            source_vendor_id: Starting vendor ID
            min_depth: Minimum path length (3-7)
            max_depth: Maximum path length (3-7)
            relationship_types: Filter by relationship types (optional)
            min_strength: Minimum relationship strength threshold
            limit: Maximum number of paths to return

        Returns:
            List of relationship paths within depth range
        """
        paths = []
        visited_paths: Set[str] = set()  # Track unique paths to avoid duplicates

        # BFS queue: (current_vendor_id, path_nodes, path_relationships, total_strength)
        queue = deque([(
            source_vendor_id,
            [],  # path nodes
            [],  # path relationships
            1.0  # cumulative strength
        )])

        # Get source vendor info
        source_vendor = self._get_vendor(source_vendor_id)
        if not source_vendor:
            return []

        while queue and len(paths) < limit:
            current_id, path_nodes, path_relationships, cumulative_strength = queue.popleft()
            current_depth = len(path_nodes)

            # If we've reached max depth, don't explore further
            if current_depth >= max_depth:
                continue

            # Get all outgoing relationships from current vendor
            relationships = self._get_outgoing_relationships(
                current_id,
                relationship_types,
                min_strength
            )

            for rel in relationships:
                target_id = rel.target_vendor_id

                # Avoid cycles: don't revisit vendors in current path
                if target_id in [n.vendor_id for n in path_nodes] or target_id == source_vendor_id:
                    continue

                # Get target vendor info
                target_vendor = self._get_vendor(target_id)
                if not target_vendor:
                    continue

                # Build new path
                new_nodes = path_nodes + [VendorNode(
                    vendor_id=target_vendor.vendor_id,
                    vendor_name=target_vendor.vendor_name,
                    industry=target_vendor.industry,
                    depth=current_depth + 1
                )]

                new_relationships = path_relationships + [RelationshipOutput(
                    id=rel.id,
                    source_vendor_id=rel.source_vendor_id,
                    target_vendor_id=rel.target_vendor_id,
                    relationship_type=rel.relationship_type,
                    strength=rel.strength,
                    description=rel.description,
                    created_at=rel.created_at,
                    verified=rel.verified
                )]

                new_strength = cumulative_strength * rel.strength
                new_depth = len(new_nodes)

                # Create path signature to avoid duplicates
                path_signature = f"{source_vendor_id}->" + "->".join([n.vendor_id for n in new_nodes])

                # If path is within desired depth range, add to results
                if min_depth <= new_depth <= max_depth:
                    if path_signature not in visited_paths:
                        visited_paths.add(path_signature)
                        # Calculate risk score: 1 - strength (lower strength = higher risk)
                        risk_score = 1.0 - new_strength
                        paths.append(RelationshipPath(
                            source_vendor_id=source_vendor_id,
                            target_vendor_id=target_id,
                            path=new_nodes,
                            relationships=new_relationships,
                            total_strength=new_strength,
                            path_length=new_depth,
                            risk_score=risk_score
                        ))

                # Continue exploring if not at max depth
                if new_depth < max_depth:
                    queue.append((target_id, new_nodes, new_relationships, new_strength))

        # Sort by path length (shorter first) then by strength (stronger first)
        paths.sort(key=lambda p: (p.path_length, -p.total_strength))

        return paths[:limit]

    def find_shortest_path(
        self,
        source_vendor_id: str,
        target_vendor_id: str,
        max_depth: int = 7
    ) -> Optional[RelationshipPath]:
        """
        Find the shortest path between two vendors using BFS.

        Args:
            source_vendor_id: Starting vendor
            target_vendor_id: Destination vendor
            max_depth: Maximum search depth

        Returns:
            Shortest path if found, None otherwise
        """
        if source_vendor_id == target_vendor_id:
            return None

        # BFS queue: (current_id, path_nodes, path_relationships, strength)
        queue = deque([(source_vendor_id, [], [], 1.0)])
        visited: Set[str] = {source_vendor_id}

        while queue:
            current_id, path_nodes, path_relationships, cumulative_strength = queue.popleft()

            # Stop if max depth reached
            if len(path_nodes) >= max_depth:
                continue

            # Get outgoing relationships
            relationships = self._get_outgoing_relationships(current_id)

            for rel in relationships:
                next_id = rel.target_vendor_id

                if next_id in visited:
                    continue

                visited.add(next_id)

                # Get vendor info
                vendor = self._get_vendor(next_id)
                if not vendor:
                    continue

                # Build new path
                new_nodes = path_nodes + [VendorNode(
                    vendor_id=vendor.vendor_id,
                    vendor_name=vendor.vendor_name,
                    industry=vendor.industry,
                    depth=len(path_nodes) + 1
                )]

                new_relationships = path_relationships + [RelationshipOutput(
                    id=rel.id,
                    source_vendor_id=rel.source_vendor_id,
                    target_vendor_id=rel.target_vendor_id,
                    relationship_type=rel.relationship_type,
                    strength=rel.strength,
                    description=rel.description,
                    created_at=rel.created_at,
                    verified=rel.verified
                )]

                new_strength = cumulative_strength * rel.strength

                # Found target!
                if next_id == target_vendor_id:
                    return RelationshipPath(
                        source_vendor_id=source_vendor_id,
                        target_vendor_id=target_vendor_id,
                        path=new_nodes,
                        relationships=new_relationships,
                        total_strength=new_strength,
                        path_length=len(new_nodes)
                    )

                # Continue exploring
                queue.append((next_id, new_nodes, new_relationships, new_strength))

        return None

    def get_vendor_network_stats(self, vendor_id: str) -> Dict:
        """
        Get statistics about a vendor's network.

        Args:
            vendor_id: Vendor to analyze

        Returns:
            Dictionary with network statistics
        """
        # Count outgoing relationships
        outgoing_query = select(VendorRelationship).where(
            VendorRelationship.source_vendor_id == vendor_id
        )
        outgoing = self.session.exec(outgoing_query).all()

        # Count incoming relationships
        incoming_query = select(VendorRelationship).where(
            VendorRelationship.target_vendor_id == vendor_id
        )
        incoming = self.session.exec(incoming_query).all()

        # Group by relationship type
        outgoing_by_type = {}
        for rel in outgoing:
            outgoing_by_type[rel.relationship_type] = outgoing_by_type.get(rel.relationship_type, 0) + 1

        incoming_by_type = {}
        for rel in incoming:
            incoming_by_type[rel.relationship_type] = incoming_by_type.get(rel.relationship_type, 0) + 1

        return {
            "vendor_id": vendor_id,
            "total_outgoing": len(outgoing),
            "total_incoming": len(incoming),
            "total_connections": len(outgoing) + len(incoming),
            "outgoing_by_type": outgoing_by_type,
            "incoming_by_type": incoming_by_type,
            "average_outgoing_strength": sum(r.strength for r in outgoing) / len(outgoing) if outgoing else 0.0,
            "average_incoming_strength": sum(r.strength for r in incoming) / len(incoming) if incoming else 0.0,
        }

    def _get_vendor(self, vendor_id: str) -> Optional[Vendor]:
        """
        Get vendor by ID.

        Args:
            vendor_id: Vendor identifier

        Returns:
            Vendor object or None
        """
        query = select(Vendor).where(Vendor.vendor_id == vendor_id)
        return self.session.exec(query).first()

    def _get_outgoing_relationships(
        self,
        vendor_id: str,
        relationship_types: Optional[List[str]] = None,
        min_strength: float = 0.0
    ) -> List[VendorRelationship]:
        """
        Get all outgoing relationships for a vendor.

        Args:
            vendor_id: Source vendor ID
            relationship_types: Filter by types (optional)
            min_strength: Minimum strength threshold

        Returns:
            List of relationships
        """
        query = select(VendorRelationship).where(
            VendorRelationship.source_vendor_id == vendor_id,
            VendorRelationship.strength >= min_strength
        )

        if relationship_types:
            query = query.where(VendorRelationship.relationship_type.in_(relationship_types))

        return self.session.exec(query).all()
