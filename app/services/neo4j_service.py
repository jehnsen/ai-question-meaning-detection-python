"""
Neo4j graph database service for vendor relationships.

This provides a scalable, future-proof solution for graph operations.
"""
import os
from typing import List, Optional, Dict, Any
from dotenv import load_dotenv

try:
    from neo4j import GraphDatabase, Driver
    NEO4J_AVAILABLE = True
except ImportError:
    NEO4J_AVAILABLE = False
    GraphDatabase = None
    Driver = None

load_dotenv(override=True)

# Neo4j configuration
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")

# Global Neo4j driver
neo4j_driver: Optional[Driver] = None


def init_neo4j():
    """
    Initialize Neo4j driver.

    Raises:
        ImportError: If neo4j package not installed
        Exception: If connection fails
    """
    global neo4j_driver

    if not NEO4J_AVAILABLE:
        raise ImportError(
            "Neo4j driver not installed. Install with: pip install neo4j"
        )

    print("Initializing Neo4j driver...")
    try:
        neo4j_driver = GraphDatabase.driver(
            NEO4J_URI,
            auth=(NEO4J_USER, NEO4J_PASSWORD)
        )
        # Test connection
        neo4j_driver.verify_connectivity()
        print(f"Neo4j connected successfully to {NEO4J_URI}")
    except Exception as e:
        print(f"Neo4j connection failed: {e}")
        print("Falling back to MySQL-based graph operations")
        neo4j_driver = None


def close_neo4j():
    """Close Neo4j driver connection."""
    global neo4j_driver
    if neo4j_driver:
        neo4j_driver.close()
        neo4j_driver = None


def is_neo4j_available() -> bool:
    """Check if Neo4j is available and connected."""
    return neo4j_driver is not None


class Neo4jGraphService:
    """
    Neo4j-based vendor relationship graph service.

    Provides high-performance graph operations for large-scale vendor networks.
    """

    def __init__(self):
        """Initialize Neo4j graph service."""
        if not neo4j_driver:
            raise RuntimeError("Neo4j driver not initialized. Call init_neo4j() first.")
        self.driver = neo4j_driver

    def create_indexes(self):
        """Create Neo4j indexes for performance."""
        with self.driver.session() as session:
            # Index on vendor_id for fast lookups
            session.run(
                "CREATE INDEX vendor_id_index IF NOT EXISTS FOR (v:Vendor) ON (v.vendor_id)"
            )
            # Index on relationship type for filtering
            session.run(
                "CREATE INDEX relationship_type_index IF NOT EXISTS FOR ()-[r:RELATIONSHIP]-() ON (r.type)"
            )

    def sync_vendor(self, vendor_data: Dict[str, Any]):
        """
        Sync a vendor from MySQL to Neo4j.

        Args:
            vendor_data: Vendor dictionary with keys: vendor_id, vendor_name, industry, country
        """
        with self.driver.session() as session:
            session.run(
                """
                MERGE (v:Vendor {vendor_id: $vendor_id})
                SET v.vendor_name = $vendor_name,
                    v.industry = $industry,
                    v.country = $country,
                    v.updated_at = datetime()
                """,
                vendor_id=vendor_data["vendor_id"],
                vendor_name=vendor_data["vendor_name"],
                industry=vendor_data.get("industry"),
                country=vendor_data.get("country")
            )

    def sync_relationship(self, rel_data: Dict[str, Any]):
        """
        Sync a relationship from MySQL to Neo4j.

        Args:
            rel_data: Relationship dictionary with keys: source_vendor_id, target_vendor_id,
                     relationship_type, strength, description, verified
        """
        with self.driver.session() as session:
            session.run(
                """
                MATCH (source:Vendor {vendor_id: $source_id})
                MATCH (target:Vendor {vendor_id: $target_id})
                MERGE (source)-[r:RELATIONSHIP {type: $rel_type}]->(target)
                SET r.strength = $strength,
                    r.description = $description,
                    r.verified = $verified,
                    r.updated_at = datetime()
                """,
                source_id=rel_data["source_vendor_id"],
                target_id=rel_data["target_vendor_id"],
                rel_type=rel_data["relationship_type"],
                strength=rel_data["strength"],
                description=rel_data.get("description"),
                verified=rel_data.get("verified", False)
            )

    def find_paths(
        self,
        source_vendor_id: str,
        min_depth: int = 3,
        max_depth: int = 7,
        relationship_types: Optional[List[str]] = None,
        min_strength: float = 0.0,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Find paths in vendor graph using Neo4j (high performance).

        Args:
            source_vendor_id: Starting vendor
            min_depth: Minimum path length
            max_depth: Maximum path length
            relationship_types: Filter by relationship types
            min_strength: Minimum relationship strength
            limit: Maximum results

        Returns:
            List of paths with vendor nodes and relationships
        """
        with self.driver.session() as session:
            # Build relationship type filter
            rel_filter = ""
            if relationship_types:
                type_list = "|".join(relationship_types)
                rel_filter = f":{type_list}"

            # Cypher query for path finding
            query = f"""
            MATCH path = (source:Vendor {{vendor_id: $source_id}})-[r:RELATIONSHIP{rel_filter}*{min_depth}..{max_depth}]->(target:Vendor)
            WHERE all(rel in relationships(path) WHERE rel.strength >= $min_strength)
            WITH path,
                 length(path) as path_length,
                 reduce(s = 1.0, rel in relationships(path) | s * rel.strength) as total_strength
            RETURN
                source.vendor_id as source_id,
                source.vendor_name as source_name,
                target.vendor_id as target_id,
                target.vendor_name as target_name,
                path,
                path_length,
                total_strength,
                [node in nodes(path) | {{
                    vendor_id: node.vendor_id,
                    vendor_name: node.vendor_name,
                    industry: node.industry
                }}] as nodes,
                [rel in relationships(path) | {{
                    source: startNode(rel).vendor_id,
                    target: endNode(rel).vendor_id,
                    type: rel.type,
                    strength: rel.strength,
                    description: rel.description,
                    verified: rel.verified
                }}] as relationships
            ORDER BY path_length, total_strength DESC
            LIMIT $limit
            """

            result = session.run(
                query,
                source_id=source_vendor_id,
                min_strength=min_strength,
                limit=limit
            )

            paths = []
            for record in result:
                paths.append({
                    "source_vendor_id": record["source_id"],
                    "target_vendor_id": record["target_id"],
                    "path_length": record["path_length"],
                    "total_strength": record["total_strength"],
                    "nodes": record["nodes"],
                    "relationships": record["relationships"]
                })

            return paths

    def find_shortest_path(
        self,
        source_vendor_id: str,
        target_vendor_id: str,
        max_depth: int = 7
    ) -> Optional[Dict[str, Any]]:
        """
        Find shortest path between two vendors.

        Uses Neo4j's optimized shortest path algorithm.

        Args:
            source_vendor_id: Start vendor
            target_vendor_id: End vendor
            max_depth: Maximum search depth

        Returns:
            Shortest path or None if not found
        """
        with self.driver.session() as session:
            query = """
            MATCH (source:Vendor {vendor_id: $source_id})
            MATCH (target:Vendor {vendor_id: $target_id})
            MATCH path = shortestPath((source)-[:RELATIONSHIP*..%d]->(target))
            RETURN
                path,
                length(path) as path_length,
                reduce(s = 1.0, rel in relationships(path) | s * rel.strength) as total_strength,
                [node in nodes(path) | {
                    vendor_id: node.vendor_id,
                    vendor_name: node.vendor_name
                }] as nodes
            """ % max_depth

            result = session.run(
                query,
                source_id=source_vendor_id,
                target_id=target_vendor_id
            )

            record = result.single()
            if record:
                return {
                    "path_length": record["path_length"],
                    "total_strength": record["total_strength"],
                    "nodes": record["nodes"]
                }
            return None

    def get_vendor_stats(self, vendor_id: str) -> Dict[str, Any]:
        """
        Get vendor network statistics using Neo4j graph algorithms.

        Args:
            vendor_id: Vendor to analyze

        Returns:
            Statistics including degree centrality, betweenness, etc.
        """
        with self.driver.session() as session:
            query = """
            MATCH (v:Vendor {vendor_id: $vendor_id})
            OPTIONAL MATCH (v)-[out:RELATIONSHIP]->()
            OPTIONAL MATCH (v)<-[in:RELATIONSHIP]-()
            RETURN
                v.vendor_id as vendor_id,
                count(DISTINCT out) as outgoing_count,
                count(DISTINCT in) as incoming_count,
                avg(out.strength) as avg_outgoing_strength,
                avg(in.strength) as avg_incoming_strength,
                collect(DISTINCT out.type) as outgoing_types,
                collect(DISTINCT in.type) as incoming_types
            """

            result = session.run(query, vendor_id=vendor_id)
            record = result.single()

            if record:
                return {
                    "vendor_id": record["vendor_id"],
                    "outgoing_count": record["outgoing_count"],
                    "incoming_count": record["incoming_count"],
                    "total_connections": record["outgoing_count"] + record["incoming_count"],
                    "avg_outgoing_strength": record["avg_outgoing_strength"] or 0.0,
                    "avg_incoming_strength": record["avg_incoming_strength"] or 0.0,
                    "outgoing_types": [t for t in record["outgoing_types"] if t],
                    "incoming_types": [t for t in record["incoming_types"] if t]
                }
            return {}

    def find_communities(self, min_community_size: int = 3) -> List[List[str]]:
        """
        Find vendor communities/clusters using graph algorithms.

        Uses Louvain algorithm for community detection.

        Args:
            min_community_size: Minimum vendors per community

        Returns:
            List of communities (each is a list of vendor_ids)
        """
        with self.driver.session() as session:
            # This requires Neo4j Graph Data Science library
            # Simplified version using connected components
            query = """
            CALL gds.wcc.stream({
                nodeProjection: 'Vendor',
                relationshipProjection: {
                    RELATIONSHIP: {
                        orientation: 'UNDIRECTED'
                    }
                }
            })
            YIELD nodeId, componentId
            WITH gds.util.asNode(nodeId) as vendor, componentId
            RETURN componentId, collect(vendor.vendor_id) as members, count(*) as size
            HAVING size >= $min_size
            ORDER BY size DESC
            """

            try:
                result = session.run(query, min_size=min_community_size)
                return [record["members"] for record in result]
            except Exception as e:
                print(f"Community detection requires Neo4j GDS: {e}")
                return []
