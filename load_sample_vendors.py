# -*- coding: utf-8 -*-
"""
Load Sample Vendor Data for Testing Vendor Risk Management System

This script loads sample vendors and relationships into the database
to demonstrate the vendor risk management features.
"""
import requests
import json
import sys
import io
from pathlib import Path

# Fix Windows console encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# API base URL
BASE_URL = "http://localhost:8000"

def load_sample_data():
    """Load sample vendors and relationships from JSON file."""

    # Read sample data
    sample_file = Path(__file__).parent / "sample_vendor_data.json"

    if not sample_file.exists():
        print(f"❌ Error: {sample_file} not found")
        print("Creating sample data file...")
        create_sample_data_file()
        return

    with open(sample_file, 'r') as f:
        data = json.load(f)

    print("=" * 60)
    print("🔄 Loading Sample Vendor Risk Management Data")
    print("=" * 60)

    # Load vendors
    print(f"\n📦 Loading {len(data['vendors'])} vendors...")
    vendors_created = 0
    vendors_skipped = 0

    for vendor in data['vendors']:
        try:
            response = requests.post(
                f"{BASE_URL}/vendors/create",
                json=vendor,
                headers={"Content-Type": "application/json"}
            )

            if response.status_code == 200:
                print(f"  ✅ Created: {vendor['vendor_id']} - {vendor['vendor_name']}")
                vendors_created += 1
            elif response.status_code == 400 and "already exists" in response.text:
                print(f"  ⚠️  Skipped: {vendor['vendor_id']} (already exists)")
                vendors_skipped += 1
            else:
                print(f"  ❌ Failed: {vendor['vendor_id']} - {response.text}")
        except Exception as e:
            print(f"  ❌ Error creating {vendor['vendor_id']}: {e}")

    # Load relationships
    print(f"\n🔗 Loading {len(data['relationships'])} relationships...")
    relationships_created = 0
    relationships_skipped = 0

    for rel in data['relationships']:
        try:
            response = requests.post(
                f"{BASE_URL}/vendors/relationships/create",
                json=rel,
                headers={"Content-Type": "application/json"}
            )

            if response.status_code == 200:
                print(f"  ✅ Created: {rel['source_vendor_id']} → {rel['target_vendor_id']} ({rel['relationship_type']})")
                relationships_created += 1
            elif response.status_code == 400 and "already exists" in response.text:
                print(f"  ⚠️  Skipped: {rel['source_vendor_id']} → {rel['target_vendor_id']} (already exists)")
                relationships_skipped += 1
            else:
                print(f"  ❌ Failed: {rel['source_vendor_id']} → {rel['target_vendor_id']} - {response.text}")
        except Exception as e:
            print(f"  ❌ Error creating relationship: {e}")

    # Summary
    print("\n" + "=" * 60)
    print("📊 Summary")
    print("=" * 60)
    print(f"✅ Vendors created: {vendors_created}")
    print(f"⚠️  Vendors skipped: {vendors_skipped}")
    print(f"✅ Relationships created: {relationships_created}")
    print(f"⚠️  Relationships skipped: {relationships_skipped}")

    # Test queries
    print("\n" + "=" * 60)
    print("🧪 Testing Risk Management Queries")
    print("=" * 60)

    # Test 1: Find 3rd party vendors
    print("\n1️⃣  Testing 3rd-party vendor assessment...")
    try:
        response = requests.post(
            f"{BASE_URL}/risk/nth-party-assessment",
            json={"vendor_id": "TECH-001", "party_level": 3}
        )
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ Found {result['vendors_found']} third-party vendors")
        else:
            print(f"   ❌ Failed: {response.text}")
    except Exception as e:
        print(f"   ❌ Error: {e}")

    # Test 2: Supply chain analysis
    print("\n2️⃣  Testing supply chain risk analysis...")
    try:
        response = requests.post(
            f"{BASE_URL}/risk/supply-chain-analysis",
            json={
                "source_vendor_id": "TECH-001",
                "min_depth": 3,
                "max_depth": 7,
                "limit": 50
            }
        )
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ Found {result['paths_found']} risk paths")
            if result['paths_found'] > 0:
                highest_risk = max(result['paths'], key=lambda p: p['risk_score'])
                print(f"   📊 Highest risk score: {highest_risk['risk_score']:.3f} (depth: {highest_risk['path_length']})")
        else:
            print(f"   ❌ Failed: {response.text}")
    except Exception as e:
        print(f"   ❌ Error: {e}")

    # Test 3: Risk hotspots
    print("\n3️⃣  Testing risk hotspot detection...")
    try:
        response = requests.get(f"{BASE_URL}/risk/risk-hotspots?min_connections=3")
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ Found {result['hotspots_found']} risk hotspots")
            if result['hotspots_found'] > 0:
                top_hotspot = result['hotspots'][0]
                print(f"   ⚠️  Top hotspot: {top_hotspot['vendor_name']} ({top_hotspot['total_connections']} connections)")
        else:
            print(f"   ❌ Failed: {response.text}")
    except Exception as e:
        print(f"   ❌ Error: {e}")

    print("\n" + "=" * 60)
    print("✅ Sample data loading complete!")
    print("=" * 60)
    print("\n📚 Next Steps:")
    print("   1. Open API docs: http://localhost:8000/docs")
    print("   2. Try the /risk endpoints in the 'risk-management' section")
    print("   3. See WORKFLOW_VENDOR_RISK_MANAGEMENT.md for usage examples")
    print()

def create_sample_data_file():
    """Create sample vendor data file if it doesn't exist."""
    sample_data = {
        "vendors": [
            {
                "vendor_id": "TECH-001",
                "vendor_name": "TechCorp Solutions",
                "description": "Enterprise technology solutions provider",
                "industry": "Technology",
                "country": "USA"
            },
            {
                "vendor_id": "MANUFACTURING-002",
                "vendor_name": "Global Manufacturing Co",
                "description": "Large-scale manufacturing operations",
                "industry": "Manufacturing",
                "country": "China"
            },
            {
                "vendor_id": "LOGISTICS-003",
                "vendor_name": "Worldwide Logistics",
                "description": "International shipping and logistics",
                "industry": "Logistics",
                "country": "Germany"
            },
            {
                "vendor_id": "COMPONENT-004",
                "vendor_name": "Component Suppliers Ltd",
                "description": "Electronic component supplier",
                "industry": "Manufacturing",
                "country": "Taiwan"
            },
            {
                "vendor_id": "RAWMATERIAL-005",
                "vendor_name": "Raw Materials Inc",
                "description": "Raw materials and commodities",
                "industry": "Mining",
                "country": "Australia"
            },
            {
                "vendor_id": "PACKAGING-006",
                "vendor_name": "Packaging Solutions",
                "description": "Custom packaging manufacturer",
                "industry": "Manufacturing",
                "country": "Vietnam"
            },
            {
                "vendor_id": "FREIGHT-007",
                "vendor_name": "Freight Express",
                "description": "Freight forwarding services",
                "industry": "Logistics",
                "country": "Singapore"
            },
            {
                "vendor_id": "WAREHOUSE-008",
                "vendor_name": "Storage & Warehouse Co",
                "description": "Warehousing and distribution",
                "industry": "Logistics",
                "country": "USA"
            },
            {
                "vendor_id": "CHEMICALS-009",
                "vendor_name": "Chemical Suppliers",
                "description": "Industrial chemical supplier",
                "industry": "Chemicals",
                "country": "India"
            },
            {
                "vendor_id": "FINANCE-010",
                "vendor_name": "Trade Finance Corp",
                "description": "Trade finance and insurance",
                "industry": "Finance",
                "country": "UK"
            }
        ],
        "relationships": [
            # 1st degree relationships (direct vendors)
            {
                "source_vendor_id": "TECH-001",
                "target_vendor_id": "MANUFACTURING-002",
                "relationship_type": "supplier",
                "strength": 0.95,
                "description": "Primary manufacturing partner",
                "verified": True
            },
            {
                "source_vendor_id": "TECH-001",
                "target_vendor_id": "LOGISTICS-003",
                "relationship_type": "supplier",
                "strength": 0.90,
                "description": "Main logistics provider",
                "verified": True
            },
            # 2nd degree relationships
            {
                "source_vendor_id": "MANUFACTURING-002",
                "target_vendor_id": "COMPONENT-004",
                "relationship_type": "supplier",
                "strength": 0.85,
                "description": "Component supplier",
                "verified": True
            },
            {
                "source_vendor_id": "MANUFACTURING-002",
                "target_vendor_id": "PACKAGING-006",
                "relationship_type": "subcontractor",
                "strength": 0.80,
                "description": "Packaging subcontractor",
                "verified": True
            },
            {
                "source_vendor_id": "LOGISTICS-003",
                "target_vendor_id": "FREIGHT-007",
                "relationship_type": "partner",
                "strength": 0.88,
                "description": "Freight partner",
                "verified": True
            },
            {
                "source_vendor_id": "LOGISTICS-003",
                "target_vendor_id": "WAREHOUSE-008",
                "relationship_type": "supplier",
                "strength": 0.92,
                "description": "Warehouse services",
                "verified": True
            },
            # 3rd degree relationships
            {
                "source_vendor_id": "COMPONENT-004",
                "target_vendor_id": "RAWMATERIAL-005",
                "relationship_type": "supplier",
                "strength": 0.75,
                "description": "Raw material supplier",
                "verified": True
            },
            {
                "source_vendor_id": "COMPONENT-004",
                "target_vendor_id": "CHEMICALS-009",
                "relationship_type": "supplier",
                "strength": 0.70,
                "description": "Chemical supplier",
                "verified": False
            },
            {
                "source_vendor_id": "PACKAGING-006",
                "target_vendor_id": "RAWMATERIAL-005",
                "relationship_type": "supplier",
                "strength": 0.65,
                "description": "Packaging materials",
                "verified": True
            },
            # 4th degree relationships
            {
                "source_vendor_id": "RAWMATERIAL-005",
                "target_vendor_id": "FINANCE-010",
                "relationship_type": "service_provider",
                "strength": 0.82,
                "description": "Trade finance",
                "verified": True
            },
            # Cross-links (creating network complexity)
            {
                "source_vendor_id": "FREIGHT-007",
                "target_vendor_id": "FINANCE-010",
                "relationship_type": "service_provider",
                "strength": 0.78,
                "description": "Shipping insurance",
                "verified": True
            },
            {
                "source_vendor_id": "WAREHOUSE-008",
                "target_vendor_id": "FREIGHT-007",
                "relationship_type": "partner",
                "strength": 0.85,
                "description": "Freight coordination",
                "verified": True
            }
        ]
    }

    sample_file = Path(__file__).parent / "sample_vendor_data.json"
    with open(sample_file, 'w') as f:
        json.dump(sample_data, f, indent=2)

    print(f"✅ Created {sample_file}")
    print("🔄 Loading data...")
    load_sample_data()

def check_server():
    """Check if API server is running."""
    try:
        response = requests.get(f"{BASE_URL}/docs")
        return response.status_code == 200
    except:
        return False

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("🚀 Sample Vendor Risk Management Data Loader")
    print("=" * 60)

    # Check if server is running
    print("\n🔍 Checking API server status...")
    if not check_server():
        print("❌ Error: API server is not running!")
        print("\n📝 Please start the server first:")
        print("   cd d:\\xampp\\apache\\bin\\python\\question-linking")
        print("   .\\venv\\Scripts\\python -m uvicorn main:app --reload")
        print("\n   Then run this script again.")
        sys.exit(1)

    print("✅ API server is running\n")

    # Load sample data
    load_sample_data()
