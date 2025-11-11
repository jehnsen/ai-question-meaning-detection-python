"""
Hybrid graph service that uses Neo4j when available, falls back to MySQL.

This provides future-proof architecture with graceful degradation.
"""
from typing import List, Optional, Dict, Any
from sqlmodel import Session
from app.services.vendor_graph import VendorGraphService
from app.services.neo4j_service import Neo4jGraphService, is_neo4j_available


class HybridGraphService:
    """
    Intelligent graph service that automatically chooses the best backend.

    - Prefers Neo4j for performance and advanced features
    - Falls back to MySQL if Neo4j unavailable
    - Transparent to API consumers
    """

    def __init__(self, session: Session):
        """
        Initialize hybrid graph service.

        Args:
            session: MySQL database session (always needed for fallback)
        """
        self.session = session
        self.mysql_service = VendorGraphService(session)
        self.neo4j_service = None

        # Try to initialize Neo4j
        if is_neo4j_available():
            try:
                self.neo4j_service = Neo4jGraphService()
                self.backend = "neo4j"
            except Exception as e:
                print(f"Neo4j initialization failed, using MySQL: {e}")
                self.backend = "mysql"
        else:
            self.backend = "mysql"

    def get_backend(self) -> str:
        """
        Get current graph backend being used.

        Returns:
            "neo4j" or "mysql"
        """
        return self.backend

    def find_paths(
        self,
        source_vendor_id: str,
        min_depth: int = 3,
        max_depth: int = 7,
        relationship_types: Optional[List[str]] = None,
        min_strength: float = 0.0,
        limit: int = 100
    ) -> Dict[str, Any]:
        """
        Find paths using best available backend.

        Args:
            source_vendor_id: Starting vendor
            min_depth: Minimum path length
            max_depth: Maximum path length
            relationship_types: Filter by types
            min_strength: Minimum strength
            limit: Maximum results

        Returns:
            Dictionary with paths and metadata
        """
        if self.neo4j_service:
            # Use Neo4j for superior performance
            try:
                paths = self.neo4j_service.find_paths(
                    source_vendor_id,
                    min_depth,
                    max_depth,
                    relationship_types,
                    min_strength,
                    limit
                )
                return {
                    "backend": "neo4j",
                    "paths": paths,
                    "performance_note": "Using Neo4j for optimal graph performance"
                }
            except Exception as e:
                print(f"Neo4j query failed, falling back to MySQL: {e}")
                # Fall through to MySQL

        # Use MySQL fallback
        paths = self.mysql_service.find_paths(
            source_vendor_id,
            min_depth,
            max_depth,
            relationship_types,
            min_strength,
            limit
        )
        return {
            "backend": "mysql",
            "paths": [self._convert_mysql_path_to_dict(p) for p in paths],
            "performance_note": "Using MySQL (consider Neo4j for better performance)"
        }

    def find_shortest_path(
        self,
        source_vendor_id: str,
        target_vendor_id: str,
        max_depth: int = 7
    ) -> Optional[Dict[str, Any]]:
        """
        Find shortest path using best available backend.

        Args:
            source_vendor_id: Start vendor
            target_vendor_id: End vendor
            max_depth: Maximum depth

        Returns:
            Shortest path or None
        """
        if self.neo4j_service:
            try:
                return self.neo4j_service.find_shortest_path(
                    source_vendor_id,
                    target_vendor_id,
                    max_depth
                )
            except Exception as e:
                print(f"Neo4j shortest path failed, falling back to MySQL: {e}")

        # MySQL fallback
        path = self.mysql_service.find_shortest_path(
            source_vendor_id,
            target_vendor_id,
            max_depth
        )
        return self._convert_mysql_path_to_dict(path) if path else None

    def get_vendor_stats(self, vendor_id: str) -> Dict[str, Any]:
        """
        Get vendor network statistics.

        Args:
            vendor_id: Vendor to analyze

        Returns:
            Network statistics
        """
        if self.neo4j_service:
            try:
                stats = self.neo4j_service.get_vendor_stats(vendor_id)
                stats["backend"] = "neo4j"
                return stats
            except Exception as e:
                print(f"Neo4j stats failed, falling back to MySQL: {e}")

        # MySQL fallback
        stats = self.mysql_service.get_vendor_network_stats(vendor_id)
        stats["backend"] = "mysql"
        return stats

    def _convert_mysql_path_to_dict(self, path) -> Dict[str, Any]:
        """
        Convert MySQL path object to dictionary format.

        Args:
            path: RelationshipPath object from MySQL service

        Returns:
            Dictionary representation
        """
        if not path:
            return None

        return {
            "source_vendor_id": path.source_vendor_id,
            "target_vendor_id": path.target_vendor_id,
            "path_length": path.path_length,
            "total_strength": path.total_strength,
            "nodes": [
                {
                    "vendor_id": node.vendor_id,
                    "vendor_name": node.vendor_name,
                    "industry": node.industry,
                    "depth": node.depth
                }
                for node in path.path
            ],
            "relationships": [
                {
                    "source": rel.source_vendor_id,
                    "target": rel.target_vendor_id,
                    "type": rel.relationship_type,
                    "strength": rel.strength,
                    "description": rel.description,
                    "verified": rel.verified
                }
                for rel in path.relationships
            ]
        }
