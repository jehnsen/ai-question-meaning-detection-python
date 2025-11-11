# Neo4j Setup Guide - Future-Proof Graph Database

This guide explains how to add Neo4j to your AI Integration Service for high-performance, scalable vendor relationship graph operations.

## Why Neo4j?

### Performance Comparison

| Operation | MySQL | Neo4j | Improvement |
|-----------|-------|-------|-------------|
| 3-degree search | 50-200ms | 10-50ms | **4x faster** |
| 7-degree search | 500ms-2s | 100-500ms | **5x faster** |
| Max vendors | ~50,000 | Millions | **Unlimited** |
| Deep traversal (10+) | Very slow | <1s | **100x faster** |

### CEO-Approved Features

✅ **Scalability**: Handles millions of vendors and relationships
✅ **Performance**: Sub-second queries even for 10+ degree searches
✅ **Advanced Analytics**: Community detection, PageRank, centrality
✅ **Future-Proof**: Industry standard for graph databases
✅ **Graceful Degradation**: Falls back to MySQL if Neo4j unavailable

## Installation Options

### Option 1: Docker (Recommended for Development)

```bash
# Run Neo4j in Docker
docker run \
    --name neo4j \
    -p 7474:7474 \
    -p 7687:7687 \
    -e NEO4J_AUTH=neo4j/your_password \
    -v neo4j_data:/data \
    neo4j:latest
```

Access Neo4j Browser at: http://localhost:7474

### Option 2: Neo4j Desktop (Easiest)

1. Download from: https://neo4j.com/download/
2. Install and create a new database
3. Set password
4. Start the database

### Option 3: Neo4j AuraDB (Cloud - Production)

1. Go to: https://neo4j.com/cloud/aura/
2. Create free account
3. Create database instance
4. Copy connection credentials

### Option 4: Manual Installation

**Windows**:
```bash
# Download from https://neo4j.com/download/
# Install and run as Windows service
```

**Linux**:
```bash
wget -O - https://debian.neo4j.com/neotechnology.gpg.key | sudo apt-key add -
echo 'deb https://debian.neo4j.com stable 5' | sudo tee /etc/apt/sources.list.d/neo4j.list
sudo apt-get update
sudo apt-get install neo4j
sudo systemctl start neo4j
```

## Python Dependencies

Install Neo4j Python driver:

```bash
cd d:\xampp\apache\bin\python\question-linking
./venv/Scripts/activate
pip install neo4j
```

## Configuration

### 1. Update .env file

Add Neo4j connection settings to your `.env` file:

```env
# Existing settings
DATABASE_URL=mysql+pymysql://root:@localhost:3306/sbb_db
OPENAI_API_KEY=your_openai_key_here

# Neo4j settings (add these)
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_neo4j_password
```

### 2. Initialize Neo4j in application

Update `main.py` to initialize Neo4j:

```python
from app.services.neo4j_service import init_neo4j, close_neo4j, is_neo4j_available

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup and shutdown events."""
    # Startup
    print("Starting application...")
    init_db()
    init_openai_client()

    # Try to initialize Neo4j (optional)
    try:
        init_neo4j()
        if is_neo4j_available():
            print("✅ Neo4j enabled - Using graph database for relationships")
        else:
            print("⚠️  Neo4j unavailable - Using MySQL for relationships")
    except Exception as e:
        print(f"⚠️  Neo4j initialization failed: {e}")
        print("   Continuing with MySQL fallback")

    print("Application ready!")
    yield

    # Shutdown
    print("Shutting down application...")
    close_neo4j()
```

## Data Migration to Neo4j

### Manual Sync Script

Create `sync_to_neo4j.py`:

```python
"""
Sync vendor data from MySQL to Neo4j.
"""
from sqlmodel import Session, select
from app.models import Vendor, VendorRelationship
from app.services.database import engine
from app.services.neo4j_service import init_neo4j, Neo4jGraphService

def sync_all_to_neo4j():
    """Sync all vendors and relationships to Neo4j."""
    init_neo4j()
    neo4j_service = Neo4jGraphService()

    # Create indexes
    print("Creating Neo4j indexes...")
    neo4j_service.create_indexes()

    with Session(engine) as session:
        # Sync vendors
        print("Syncing vendors...")
        vendors = session.exec(select(Vendor)).all()
        for vendor in vendors:
            neo4j_service.sync_vendor({
                "vendor_id": vendor.vendor_id,
                "vendor_name": vendor.vendor_name,
                "industry": vendor.industry,
                "country": vendor.country
            })
        print(f"Synced {len(vendors)} vendors")

        # Sync relationships
        print("Syncing relationships...")
        relationships = session.exec(select(VendorRelationship)).all()
        for rel in relationships:
            neo4j_service.sync_relationship({
                "source_vendor_id": rel.source_vendor_id,
                "target_vendor_id": rel.target_vendor_id,
                "relationship_type": rel.relationship_type,
                "strength": rel.strength,
                "description": rel.description,
                "verified": rel.verified
            })
        print(f"Synced {len(relationships)} relationships")

    print("✅ Migration complete!")

if __name__ == "__main__":
    sync_all_to_neo4j()
```

Run sync:
```bash
python sync_to_neo4j.py
```

### Automatic Sync (Production)

Update vendor creation endpoints to sync to both databases:

```python
from app.services.neo4j_service import is_neo4j_available, Neo4jGraphService

@router.post("/create", response_model=VendorOutput)
async def create_vendor(
    vendor_input: VendorInput,
    session: Session = Depends(get_session)
):
    # ... existing MySQL logic ...

    # Sync to Neo4j if available
    if is_neo4j_available():
        try:
            neo4j_service = Neo4jGraphService()
            neo4j_service.sync_vendor({
                "vendor_id": vendor.vendor_id,
                "vendor_name": vendor.vendor_name,
                "industry": vendor.industry,
                "country": vendor.country
            })
        except Exception as e:
            print(f"Neo4j sync failed (non-fatal): {e}")

    return VendorOutput(...)
```

## Testing Neo4j

### 1. Verify Connection

```bash
python -c "from app.services.neo4j_service import init_neo4j; init_neo4j()"
```

Expected output:
```
Initializing Neo4j driver...
Neo4j connected successfully to bolt://localhost:7687
```

### 2. Test Graph Query

In Neo4j Browser (http://localhost:7474):

```cypher
// Create test vendors
CREATE (v1:Vendor {vendor_id: 'TEST-001', vendor_name: 'Test Corp'})
CREATE (v2:Vendor {vendor_id: 'TEST-002', vendor_name: 'Test Inc'})
CREATE (v1)-[:RELATIONSHIP {type: 'partner', strength: 0.9}]->(v2)

// Query relationships
MATCH (v1)-[r]->(v2)
RETURN v1, r, v2
```

### 3. Test API with Neo4j

```bash
# Graph search will automatically use Neo4j
curl -X POST "http://localhost:8000/vendors/graph/search" \
  -H "Content-Type: application/json" \
  -d '{
    "source_vendor_id": "TECH-001",
    "min_depth": 3,
    "max_depth": 7
  }'
```

Response will include:
```json
{
  "backend": "neo4j",
  "performance_note": "Using Neo4j for optimal graph performance",
  ...
}
```

## Advanced Features with Neo4j

### 1. Community Detection

Find vendor clusters:

```cypher
// Install Graph Data Science library first
CALL gds.louvain.stream({
    nodeProjection: 'Vendor',
    relationshipProjection: 'RELATIONSHIP'
})
YIELD nodeId, communityId
RETURN gds.util.asNode(nodeId).vendor_name AS vendor, communityId
ORDER BY communityId
```

### 2. PageRank (Vendor Importance)

Find most influential vendors:

```cypher
CALL gds.pageRank.stream({
    nodeProjection: 'Vendor',
    relationshipProjection: 'RELATIONSHIP'
})
YIELD nodeId, score
RETURN gds.util.asNode(nodeId).vendor_name AS vendor, score
ORDER BY score DESC
LIMIT 10
```

### 3. Shortest Path

```cypher
MATCH (source:Vendor {vendor_id: 'TECH-001'})
MATCH (target:Vendor {vendor_id: 'FINTECH-001'})
MATCH path = shortestPath((source)-[:RELATIONSHIP*]-(target))
RETURN path, length(path) as degrees
```

## Deployment Architecture

### Development
```
MySQL (localhost) + Neo4j (Docker)
```

### Production
```
MySQL (RDS/Cloud SQL) + Neo4j AuraDB
```

### High Availability
```
MySQL Cluster + Neo4j Cluster (3+ nodes)
```

## Performance Tuning

### Neo4j Settings

In `neo4j.conf`:

```conf
# Increase memory for large graphs
dbms.memory.heap.initial_size=4G
dbms.memory.heap.max_size=8G
dbms.memory.pagecache.size=4G

# Parallel query execution
dbms.cypher.parallel_runtime_enabled=true

# Connection pool
dbms.connector.bolt.thread_pool_max_size=400
```

### Index Strategy

```cypher
// Create indexes for performance
CREATE INDEX vendor_id FOR (v:Vendor) ON (v.vendor_id);
CREATE INDEX vendor_industry FOR (v:Vendor) ON (v.industry);
CREATE INDEX rel_type FOR ()-[r:RELATIONSHIP]-() ON (r.type);
CREATE INDEX rel_strength FOR ()-[r:RELATIONSHIP]-() ON (r.strength);
```

## Cost Analysis

| Deployment | Cost/Month | Vendors Supported | Performance |
|------------|------------|-------------------|-------------|
| **Docker (Dev)** | $0 | ~100K | Fast |
| **Neo4j Aura Free** | $0 | ~10K | Fast |
| **Neo4j Aura Pro** | $65+ | Millions | Very Fast |
| **Self-Hosted** | $50-200 | Unlimited | Configurable |

## Monitoring

### Health Check

Add to your health endpoint:

```python
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "version": "5.0.0",
        "databases": {
            "mysql": "connected",
            "neo4j": "connected" if is_neo4j_available() else "unavailable"
        }
    }
```

### Query Performance

Log query times:

```python
import time

def find_paths(...):
    start_time = time.time()
    paths = neo4j_service.find_paths(...)
    duration = time.time() - start_time

    print(f"Neo4j query completed in {duration:.2f}s")
    return paths
```

## Troubleshooting

### Connection Failed

```
Error: Unable to connect to Neo4j at bolt://localhost:7687
```

**Solution**:
1. Check Neo4j is running: `docker ps` or `systemctl status neo4j`
2. Verify credentials in `.env`
3. Check firewall allows port 7687

### Import Error

```
ImportError: cannot import name 'neo4j'
```

**Solution**:
```bash
pip install neo4j
```

### Fallback to MySQL

```
⚠️ Neo4j unavailable - Using MySQL for relationships
```

**This is expected and safe!** The system works fine with MySQL. Neo4j is optional but recommended for scale.

## Summary

✅ **Immediate**: System works with MySQL (current)
✅ **Future-Proof**: Add Neo4j when ready (CEO approved)
✅ **Graceful**: Falls back to MySQL if Neo4j unavailable
✅ **Scalable**: Neo4j handles millions of vendors + deep searches
✅ **Advanced**: Community detection, PageRank, and more

**Recommendation**: Start with MySQL, add Neo4j when you reach 10,000+ vendors or need sub-100ms queries.
