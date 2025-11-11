# -*- coding: utf-8 -*-
"""
Load Sample Vendor Data into Neo4j Graph Database
For Vendor Risk Management System with Deep Node Searching (10-15 degrees)
"""
import json
import sys
import io
from pathlib import Path
from neo4j import GraphDatabase
import os
from dotenv import load_dotenv

# Fix Windows console encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Load environment variables
load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password123")


class Neo4jLoader:
    """Load sample vendor data directly into Neo4j graph database."""

    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def clear_database(self):
        """Clear all existing vendor data (for testing)."""
        with self.driver.session() as session:
            print("\n🗑️  Clearing existing vendor data...")
            result = session.run("MATCH (n:Vendor) DETACH DELETE n")
            print("   ✅ Database cleared")

    def create_indexes(self):
        """Create indexes for better performance."""
        with self.driver.session() as session:
            print("\n📊 Creating indexes...")

            # Index on vendor_id for fast lookups
            session.run("CREATE INDEX vendor_id_index IF NOT EXISTS FOR (v:Vendor) ON (v.vendor_id)")
            print("   ✅ Created index on vendor_id")

            # Index on vendor_name for search
            session.run("CREATE INDEX vendor_name_index IF NOT EXISTS FOR (v:Vendor) ON (v.vendor_name)")
            print("   ✅ Created index on vendor_name")

            # Index on industry for filtering
            session.run("CREATE INDEX vendor_industry_index IF NOT EXISTS FOR (v:Vendor) ON (v.industry)")
            print("   ✅ Created index on industry")

    def create_vendor(self, vendor_data):
        """Create a vendor node in Neo4j."""
        with self.driver.session() as session:
            query = """
            MERGE (v:Vendor {vendor_id: $vendor_id})
            SET v.vendor_name = $vendor_name,
                v.description = $description,
                v.industry = $industry,
                v.country = $country
            RETURN v.vendor_id as vendor_id, v.vendor_name as vendor_name
            """
            result = session.run(
                query,
                vendor_id=vendor_data['vendor_id'],
                vendor_name=vendor_data['vendor_name'],
                description=vendor_data.get('description', ''),
                industry=vendor_data.get('industry', ''),
                country=vendor_data.get('country', '')
            )
            return result.single()

    def create_relationship(self, rel_data):
        """Create a relationship between two vendors."""
        with self.driver.session() as session:
            query = """
            MATCH (source:Vendor {vendor_id: $source_vendor_id})
            MATCH (target:Vendor {vendor_id: $target_vendor_id})
            MERGE (source)-[r:SUPPLIES {
                relationship_type: $relationship_type,
                strength: $strength,
                description: $description,
                verified: $verified
            }]->(target)
            RETURN source.vendor_id as source, target.vendor_id as target, r.relationship_type as type
            """
            result = session.run(
                query,
                source_vendor_id=rel_data['source_vendor_id'],
                target_vendor_id=rel_data['target_vendor_id'],
                relationship_type=rel_data['relationship_type'],
                strength=rel_data.get('strength', 1.0),
                description=rel_data.get('description', ''),
                verified=rel_data.get('verified', False)
            )
            return result.single()

    def test_deep_search(self, vendor_id, max_depth=10):
        """Test deep graph search (10-15 degrees)."""
        with self.driver.session() as session:
            query = f"""
            MATCH path = (source:Vendor {{vendor_id: $vendor_id}})-[r:SUPPLIES*1..{max_depth}]->(target:Vendor)
            WITH path,
                 length(path) as depth,
                 reduce(s = 1.0, rel in relationships(path) | s * rel.strength) as total_strength,
                 [node in nodes(path) | node.vendor_name] as vendor_names
            RETURN depth,
                   count(*) as paths_at_depth,
                   avg(total_strength) as avg_strength,
                   max(total_strength) as max_strength,
                   min(total_strength) as min_strength
            ORDER BY depth
            """
            results = session.run(query, vendor_id=vendor_id)
            return list(results)

    def get_statistics(self):
        """Get database statistics."""
        with self.driver.session() as session:
            # Count vendors
            vendor_count = session.run("MATCH (v:Vendor) RETURN count(v) as count").single()['count']

            # Count relationships
            rel_count = session.run("MATCH ()-[r:SUPPLIES]->() RETURN count(r) as count").single()['count']

            # Get max depth
            max_depth_result = session.run("""
                MATCH path = (source:Vendor)-[r:SUPPLIES*]->(target:Vendor)
                RETURN max(length(path)) as max_depth
            """).single()
            max_depth = max_depth_result['max_depth'] if max_depth_result else 0

            return {
                'vendors': vendor_count,
                'relationships': rel_count,
                'max_depth': max_depth
            }


def load_sample_data(data_file="sample_vendor_data.json"):
    """Load sample vendor data into Neo4j."""

    # Read sample data
    sample_file = Path(__file__).parent / data_file

    if not sample_file.exists():
        print(f"❌ Error: {sample_file} not found")
        return

    with open(sample_file, 'r') as f:
        data = json.load(f)

    print("=" * 60)
    print("🚀 Neo4j Vendor Risk Management Data Loader")
    print("=" * 60)
    print(f"\n📍 Neo4j URI: {NEO4J_URI}")
    print(f"👤 User: {NEO4J_USER}")

    # Connect to Neo4j
    print("\n🔌 Connecting to Neo4j...")
    try:
        loader = Neo4jLoader(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)
        print("   ✅ Connected to Neo4j")
    except Exception as e:
        print(f"   ❌ Failed to connect: {e}")
        print("\n💡 Make sure Neo4j is running:")
        print("   docker-compose -f docker-compose.neo4j.yml up -d")
        return

    try:
        # Clear existing data
        loader.clear_database()

        # Create indexes
        loader.create_indexes()

        # Load vendors
        print(f"\n📦 Loading {len(data['vendors'])} vendors into Neo4j...")
        vendors_created = 0

        for vendor in data['vendors']:
            try:
                result = loader.create_vendor(vendor)
                if result:
                    print(f"   ✅ Created: {vendor['vendor_id']} - {vendor['vendor_name']}")
                    vendors_created += 1
            except Exception as e:
                print(f"   ❌ Failed: {vendor['vendor_id']} - {e}")

        # Load relationships
        print(f"\n🔗 Loading {len(data['relationships'])} relationships into Neo4j...")
        relationships_created = 0

        for rel in data['relationships']:
            try:
                result = loader.create_relationship(rel)
                if result:
                    print(f"   ✅ Created: {rel['source_vendor_id']} → {rel['target_vendor_id']} ({rel['relationship_type']})")
                    relationships_created += 1
            except Exception as e:
                print(f"   ❌ Failed: {rel['source_vendor_id']} → {rel['target_vendor_id']} - {e}")

        # Summary
        print("\n" + "=" * 60)
        print("📊 Summary")
        print("=" * 60)
        print(f"✅ Vendors created: {vendors_created}")
        print(f"✅ Relationships created: {relationships_created}")

        # Get statistics
        stats = loader.get_statistics()
        print(f"\n📈 Neo4j Database Statistics:")
        print(f"   • Total vendors: {stats['vendors']}")
        print(f"   • Total relationships: {stats['relationships']}")
        print(f"   • Maximum depth: {stats['max_depth']} degrees")

        # Test deep search
        print("\n" + "=" * 60)
        print("🧪 Testing Deep Graph Search (10 Degrees)")
        print("=" * 60)

        test_vendor = "TECH-001"
        print(f"\n🔍 Searching from: {test_vendor}")
        print(f"   Max depth: 10 degrees (10th-party vendors)")

        results = loader.test_deep_search(test_vendor, max_depth=10)

        if results:
            print("\n   📊 Results by depth:")
            print("   " + "-" * 56)
            print(f"   {'Depth':<8} {'Paths':<10} {'Avg Strength':<15} {'Risk Score':<12}")
            print("   " + "-" * 56)

            for row in results:
                depth = row['depth']
                paths = row['paths_at_depth']
                avg_strength = row['avg_strength']
                risk_score = 1.0 - avg_strength

                risk_level = "🟢 LOW" if risk_score < 0.3 else "🟡 MEDIUM" if risk_score < 0.6 else "🔴 HIGH"
                print(f"   {depth:<8} {paths:<10} {avg_strength:.3f}          {risk_score:.3f} {risk_level}")

            print("   " + "-" * 56)
            print(f"\n   ✅ Found vendor relationships up to {max(r['depth'] for r in results)} degrees deep!")
        else:
            print("   ⚠️  No paths found (graph might be too small)")

        # Test 15-degree search
        print("\n" + "=" * 60)
        print("🧪 Testing Ultra-Deep Search (15 Degrees)")
        print("=" * 60)

        print(f"\n🔍 Searching from: {test_vendor}")
        print(f"   Max depth: 15 degrees (15th-party vendors)")

        results_15 = loader.test_deep_search(test_vendor, max_depth=15)

        if results_15:
            max_depth_found = max(r['depth'] for r in results_15)
            total_paths = sum(r['paths_at_depth'] for r in results_15)
            print(f"\n   ✅ Maximum depth reached: {max_depth_found} degrees")
            print(f"   ✅ Total paths found: {total_paths}")
        else:
            print("   ℹ️  Graph depth is less than 15 degrees")

        print("\n" + "=" * 60)
        print("✅ Neo4j Data Loading Complete!")
        print("=" * 60)

        print("\n📚 Next Steps:")
        print("   1. Open Neo4j Browser: http://localhost:7474")
        print("   2. Login: neo4j / password123")
        print("   3. Run Cypher query:")
        print("      MATCH (v:Vendor)-[r:SUPPLIES*1..10]->(target)")
        print("      RETURN v, r, target LIMIT 100")
        print("\n   4. Start API server and test risk endpoints:")
        print("      python -m uvicorn main:app --reload")
        print()

    finally:
        loader.close()


if __name__ == "__main__":
    import sys
    data_file = sys.argv[1] if len(sys.argv) > 1 else "sample_vendor_data.json"
    load_sample_data(data_file)
