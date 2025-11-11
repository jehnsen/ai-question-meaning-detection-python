"""
Sync vendor data from MySQL to Neo4j.

This script migrates all vendors and relationships from MySQL to Neo4j
for high-performance graph operations.
"""
import sys
from sqlmodel import Session, select
from app.models import Vendor, VendorRelationship
from app.services.database import engine
from app.services.neo4j_service import init_neo4j, Neo4jGraphService, is_neo4j_available


def sync_all_to_neo4j():
    """
    Sync all vendors and relationships from MySQL to Neo4j.
    """
    print("=" * 60)
    print("NEO4J SYNC SCRIPT")
    print("=" * 60)
    print()

    # Initialize Neo4j
    try:
        init_neo4j()
    except ImportError:
        print("❌ Error: neo4j package not installed")
        print("   Install with: pip install neo4j")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error connecting to Neo4j: {e}")
        print()
        print("Make sure Neo4j is running:")
        print("  docker-compose -f docker-compose.neo4j.yml up -d")
        sys.exit(1)

    if not is_neo4j_available():
        print("❌ Neo4j is not available")
        sys.exit(1)

    print("✅ Connected to Neo4j")
    print()

    # Initialize Neo4j service
    neo4j_service = Neo4jGraphService()

    # Create indexes
    print("[1/4] Creating Neo4j indexes...")
    try:
        neo4j_service.create_indexes()
        print("      ✅ Indexes created")
    except Exception as e:
        print(f"      ⚠️  Index creation failed: {e}")
    print()

    # Sync vendors
    print("[2/4] Syncing vendors from MySQL to Neo4j...")
    with Session(engine) as session:
        vendors = session.exec(select(Vendor)).all()

        if not vendors:
            print("      ⚠️  No vendors found in MySQL")
        else:
            synced_count = 0
            for vendor in vendors:
                try:
                    neo4j_service.sync_vendor({
                        "vendor_id": vendor.vendor_id,
                        "vendor_name": vendor.vendor_name,
                        "industry": vendor.industry,
                        "country": vendor.country
                    })
                    synced_count += 1
                except Exception as e:
                    print(f"      ❌ Failed to sync {vendor.vendor_id}: {e}")

            print(f"      ✅ Synced {synced_count}/{len(vendors)} vendors")
    print()

    # Sync relationships
    print("[3/4] Syncing relationships from MySQL to Neo4j...")
    with Session(engine) as session:
        relationships = session.exec(select(VendorRelationship)).all()

        if not relationships:
            print("      ⚠️  No relationships found in MySQL")
        else:
            synced_count = 0
            for rel in relationships:
                try:
                    neo4j_service.sync_relationship({
                        "source_vendor_id": rel.source_vendor_id,
                        "target_vendor_id": rel.target_vendor_id,
                        "relationship_type": rel.relationship_type,
                        "strength": rel.strength,
                        "description": rel.description,
                        "verified": rel.verified
                    })
                    synced_count += 1
                except Exception as e:
                    print(f"      ❌ Failed to sync relationship: {e}")

            print(f"      ✅ Synced {synced_count}/{len(relationships)} relationships")
    print()

    # Verify sync
    print("[4/4] Verifying Neo4j data...")
    try:
        with Session(engine) as session:
            vendor = session.exec(select(Vendor)).first()
            if vendor:
                stats = neo4j_service.get_vendor_stats(vendor.vendor_id)
                print(f"      ✅ Sample vendor {vendor.vendor_id} has {stats.get('total_connections', 0)} connections")
    except Exception as e:
        print(f"      ⚠️  Verification failed: {e}")
    print()

    print("=" * 60)
    print("SYNC COMPLETE! 🎉")
    print("=" * 60)
    print()
    print("Next steps:")
    print("  1. Access Neo4j Browser: http://localhost:7474")
    print("     Username: neo4j")
    print("     Password: test_password_123")
    print()
    print("  2. Restart your API server to use Neo4j:")
    print("     python main.py")
    print()
    print("  3. Test graph search:")
    print("     The API will automatically use Neo4j for graph operations")
    print()


if __name__ == "__main__":
    try:
        sync_all_to_neo4j()
    except KeyboardInterrupt:
        print("\n\n❌ Sync cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
