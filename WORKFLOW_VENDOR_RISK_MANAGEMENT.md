# Vendor Risk Management - Step-by-Step Workflow Guide

## Table of Contents
1. [Quick Start](#quick-start)
2. [Setup & Installation](#setup--installation)
3. [Loading Your Vendor Data](#loading-your-vendor-data)
4. [Basic Risk Analysis Workflows](#basic-risk-analysis-workflows)
5. [Advanced Risk Management](#advanced-risk-management)
6. [Interpreting Results](#interpreting-results)
7. [Real-World Use Cases](#real-world-use-cases)
8. [Troubleshooting](#troubleshooting)

---

## Quick Start

### What This Feature Does
The Vendor Risk Management system helps you:
- **Map your supply chain** from direct vendors (1st party) to deep supply chain (15th party)
- **Assess risks** automatically using AI-powered relationship analysis
- **Identify vulnerabilities** like single points of failure and bottlenecks
- **Meet compliance requirements** for SOC 2, ISO 27001, GDPR, NIST 800-53

### 5-Minute Quick Start

```bash
# 1. Start the server
cd d:\xampp\apache\bin\python\question-linking
.\venv\Scripts\python -m uvicorn main:app --reload

# 2. Load sample data (optional)
.\venv\Scripts\python load_sample_vendors.py

# 3. Open API docs
# Visit: http://localhost:8000/docs

# 4. Run your first risk analysis
curl -X POST "http://localhost:8000/risk/supply-chain-analysis" \
  -H "Content-Type: application/json" \
  -d '{"source_vendor_id": "TECH-001", "min_depth": 3, "max_depth": 7}'
```

---

## Setup & Installation

### Option 1: Basic Setup (MySQL Only)

**Best for**: Testing, small vendor databases (<10,000 vendors)

```bash
# 1. Ensure MySQL is running (XAMPP)
# Start Apache & MySQL from XAMPP Control Panel

# 2. Activate virtual environment
cd d:\xampp\apache\bin\python\question-linking
.\venv\Scripts\activate

# 3. Install dependencies (if not already done)
pip install -r requirements.txt

# 4. Verify .env configuration
# Check that DATABASE_URL is set correctly:
# DATABASE_URL=mysql+pymysql://root:password123@localhost:3306/sbb_db

# 5. Start the API server
uvicorn main:app --reload

# 6. Verify it's running
# Open: http://localhost:8000/docs
# You should see "MySQL for vendor relationships" in logs
```

### Option 2: Neo4j Setup (Recommended for Production)

**Best for**: Large vendor databases (>10,000 vendors), deep searches (10+ degrees)

```bash
# 1. Install Docker Desktop
# Download from: https://www.docker.com/products/docker-desktop

# 2. Run automated Neo4j setup
cd d:\xampp\apache\bin\python\question-linking
setup_neo4j.bat

# This script will:
# - Start Neo4j container
# - Wait for Neo4j to be ready
# - Sync all MySQL data to Neo4j
# - Verify the connection

# 3. Start your API server
uvicorn main:app --reload

# You should see: "✅ Neo4j connected - Using graph database"
```

**Verify Neo4j Installation**:
```bash
# Open Neo4j Browser: http://localhost:7474
# Login: neo4j / password123
# Run test query: MATCH (v:Vendor) RETURN count(v)
```

---

## Loading Your Vendor Data

### Method 1: Load Sample Test Data (Recommended for First-Time Users)

```bash
# Load 10 sample vendors with relationships
.\venv\Scripts\python load_sample_vendors.py
```

**Sample data includes**:
- 10 vendors (TECH-001 through LOGISTICS-010)
- 12 relationships forming a connected graph
- Industries: Technology, Manufacturing, Logistics, Finance
- Multiple relationship types: supplier, partner, subcontractor

### Method 2: Bulk Load Your Own Vendors

**Create a JSON file** (e.g., `my_vendors.json`):

```json
{
  "vendors": [
    {
      "vendor_id": "ACME-001",
      "vendor_name": "Acme Corporation",
      "description": "Global technology provider",
      "industry": "Technology",
      "country": "USA"
    },
    {
      "vendor_id": "SUPPLIER-001",
      "vendor_name": "Supplier Inc",
      "description": "Hardware supplier",
      "industry": "Manufacturing",
      "country": "China"
    }
  ],
  "relationships": [
    {
      "source_vendor_id": "ACME-001",
      "target_vendor_id": "SUPPLIER-001",
      "relationship_type": "supplier",
      "strength": 0.9,
      "description": "Primary hardware supplier",
      "verified": true
    }
  ]
}
```

**Load via API**:

```bash
# Bulk create vendors
curl -X POST "http://localhost:8000/api/vendors/bulk" \
  -H "Content-Type: application/json" \
  -d @my_vendors.json

# Bulk create relationships
curl -X POST "http://localhost:8000/api/vendors/relationships/bulk" \
  -H "Content-Type: application/json" \
  -d @my_relationships.json
```

### Method 3: Load Vendors One-by-One via API

```bash
# Create a single vendor
curl -X POST "http://localhost:8000/api/vendors" \
  -H "Content-Type: application/json" \
  -d '{
    "vendor_id": "VENDOR-001",
    "vendor_name": "Example Vendor",
    "description": "This is a test vendor",
    "industry": "Technology",
    "country": "USA"
  }'

# Create a relationship
curl -X POST "http://localhost:8000/api/vendors/relationships" \
  -H "Content-Type: application/json" \
  -d '{
    "source_vendor_id": "VENDOR-001",
    "target_vendor_id": "VENDOR-002",
    "relationship_type": "supplier",
    "strength": 0.8,
    "verified": true
  }'
```

---

## Basic Risk Analysis Workflows

### Workflow 1: First-Party Vendor Review (Direct Vendors)

**When to use**: Review your direct vendor relationships

```bash
# Get all direct vendors (1 degree away)
curl -X POST "http://localhost:8000/risk/supply-chain-analysis" \
  -H "Content-Type: application/json" \
  -d '{
    "source_vendor_id": "YOUR-COMPANY",
    "min_depth": 1,
    "max_depth": 1,
    "limit": 100
  }'
```

**Response Example**:
```json
{
  "source_vendor_id": "YOUR-COMPANY",
  "source_vendor_name": "Your Company Inc",
  "paths_found": 15,
  "paths": [
    {
      "target_vendor_id": "VENDOR-A",
      "path_length": 1,
      "total_strength": 0.95,
      "risk_score": 0.05,  // LOW RISK
      "path": [
        {"vendor_id": "VENDOR-A", "vendor_name": "Vendor A Corp"}
      ]
    }
  ]
}
```

### Workflow 2: Third-Party Risk Management (TPRM)

**When to use**: Standard third-party vendor assessment (regulatory requirement)

```bash
# Assess 3rd-party vendors (3 degrees away)
curl -X POST "http://localhost:8000/risk/nth-party-assessment" \
  -H "Content-Type: application/json" \
  -d '{
    "vendor_id": "YOUR-COMPANY",
    "party_level": 3
  }'
```

**Response Example**:
```json
{
  "source_vendor_id": "YOUR-COMPANY",
  "party_level": 3,
  "party_classification": "3rd-party vendors",
  "vendors_found": 12,
  "vendors": [
    {
      "vendor_id": "THIRD-PARTY-001",
      "vendor_name": "Third Party Vendor",
      "industry": "Manufacturing",
      "paths_to_vendor": 2,
      "avg_risk_score": 0.35,  // MEDIUM RISK
      "strongest_path_strength": 0.65
    }
  ]
}
```

**What to do next**:
- **Risk Score 0.0-0.3** (Low): Standard monitoring
- **Risk Score 0.3-0.6** (Medium): Enhanced due diligence required
- **Risk Score 0.6-0.8** (High): Detailed risk assessment needed
- **Risk Score 0.8-1.0** (Critical): Immediate action required

### Workflow 3: Supply Chain Bottleneck Detection

**When to use**: Identify single points of failure in your supply chain

```bash
# Find vendors with 5+ connections (potential bottlenecks)
curl -X GET "http://localhost:8000/risk/risk-hotspots?min_connections=5"
```

**Response Example**:
```json
{
  "hotspots_found": 3,
  "criteria": "Vendors with 5+ connections",
  "hotspots": [
    {
      "vendor_id": "HUB-VENDOR-001",
      "vendor_name": "Critical Hub Vendor",
      "total_connections": 12,
      "outgoing_connections": 7,
      "incoming_connections": 5,
      "risk_classification": "CRITICAL"  // ⚠️ HIGH PRIORITY
    }
  ],
  "risk_summary": {
    "critical_hotspots": [...],  // 10+ connections
    "high_risk_hotspots": [...],  // 7-9 connections
    "medium_risk_hotspots": [...]  // 5-6 connections
  }
}
```

**Action Items**:
1. **Critical Hotspots**: Create contingency plans, identify backup vendors
2. **High Risk Hotspots**: Monitor closely, diversify dependencies
3. **Medium Risk Hotspots**: Track in quarterly reviews

---

## Advanced Risk Management

### Workflow 4: Fourth-Party Risk Management (FPRM)

**When to use**: Deep supply chain analysis for strategic planning

```bash
# Analyze 4th to 7th party vendors
curl -X POST "http://localhost:8000/risk/supply-chain-analysis" \
  -H "Content-Type: application/json" \
  -d '{
    "source_vendor_id": "YOUR-COMPANY",
    "min_depth": 4,
    "max_depth": 7,
    "relationship_types": ["supplier", "subcontractor"],
    "min_strength": 0.3,
    "limit": 500
  }'
```

**Response Interpretation**:
- **min_depth: 4** = Start at 4th-party vendors (vendors of your vendors' vendors)
- **max_depth: 7** = Go up to 7th-party vendors
- **min_strength: 0.3** = Only include relationships with 30%+ confidence
- **limit: 500** = Return up to 500 risk paths

### Workflow 5: Complete Supply Chain Mapping

**When to use**: Quarterly risk assessments, compliance audits

```bash
# Map entire supply chain (1 to 15 degrees)
curl -X GET "http://localhost:8000/risk/deep-search/YOUR-COMPANY?max_depth=15"
```

**Response Example**:
```json
{
  "source_vendor_id": "YOUR-COMPANY",
  "max_depth_searched": 15,
  "total_paths_found": 487,
  "depth_statistics": {
    "level_3": {
      "degree": 3,
      "vendors_found": 25,
      "avg_risk_score": 0.28,
      "max_risk_score": 0.65
    },
    "level_7": {
      "degree": 7,
      "vendors_found": 89,
      "avg_risk_score": 0.52,
      "max_risk_score": 0.88
    },
    "level_15": {
      "degree": 15,
      "vendors_found": 142,
      "avg_risk_score": 0.79,  // ⚠️ HIGH RISK AT DEEP LEVELS
      "max_risk_score": 0.96
    }
  },
  "risk_summary": {
    "highest_risk_paths": [...]  // Top 10 highest risk paths
  }
}
```

### Workflow 6: Filtered Risk Analysis (Specific Relationship Types)

**When to use**: Focus on specific supply chain segments

```bash
# Analyze only "supplier" relationships
curl -X POST "http://localhost:8000/risk/supply-chain-analysis" \
  -H "Content-Type: application/json" \
  -d '{
    "source_vendor_id": "YOUR-COMPANY",
    "min_depth": 3,
    "max_depth": 10,
    "relationship_types": ["supplier"],  // Only suppliers
    "min_strength": 0.5,  // High-confidence only
    "limit": 200
  }'
```

**Available Relationship Types**:
- `supplier` - Goods/services providers
- `partner` - Business partners
- `subcontractor` - Subcontracted services
- `distributor` - Distribution channels
- `reseller` - Resale relationships
- `service_provider` - Service providers

---

## Interpreting Results

### Understanding Risk Scores

**Risk Score Formula**:
```
risk_score = 1.0 - total_strength
```

**Where**:
```
total_strength = relationship₁.strength × relationship₂.strength × ... × relationshipₙ.strength
```

**Example Calculation**:
```
Path: YOUR-COMPANY → VENDOR-A → VENDOR-B → VENDOR-C
Strengths: 0.9 × 0.8 × 0.7 = 0.504

Risk Score = 1.0 - 0.504 = 0.496 (MEDIUM RISK)
```

### Risk Classification Guide

| Risk Score | Classification | Action Required | Frequency |
|------------|---------------|-----------------|-----------|
| 0.0 - 0.3 | ✅ LOW | Standard monitoring | Quarterly |
| 0.3 - 0.6 | ⚠️ MEDIUM | Enhanced due diligence | Monthly |
| 0.6 - 0.8 | 🔴 HIGH | Detailed assessment | Weekly |
| 0.8 - 1.0 | 🚨 CRITICAL | Immediate action | Daily |

### Path Strength Interpretation

| Total Strength | Meaning | Confidence Level |
|----------------|---------|-----------------|
| 0.8 - 1.0 | Very strong verified relationship | ✅ High confidence |
| 0.6 - 0.8 | Strong relationship | ✅ Good confidence |
| 0.4 - 0.6 | Moderate relationship | ⚠️ Medium confidence |
| 0.2 - 0.4 | Weak relationship | 🔴 Low confidence |
| 0.0 - 0.2 | Very weak/unverified | 🚨 Very low confidence |

---

## Real-World Use Cases

### Use Case 1: Compliance Audit (SOC 2 / ISO 27001)

**Scenario**: Your auditor needs documentation of all third-party service providers.

**Workflow**:
```bash
# Step 1: Get all 3rd-party vendors
curl -X POST "http://localhost:8000/risk/nth-party-assessment" \
  -d '{"vendor_id": "YOUR-COMPANY", "party_level": 3}' \
  > third_party_vendors.json

# Step 2: Get detailed paths for each vendor
curl -X POST "http://localhost:8000/risk/supply-chain-analysis" \
  -d '{"source_vendor_id": "YOUR-COMPANY", "min_depth": 1, "max_depth": 3}' \
  > compliance_report.json

# Step 3: Export to CSV for auditor
# Use the Python integration example below
```

**Python Integration**:
```python
import requests
import pandas as pd

# Fetch data
response = requests.post('http://localhost:8000/risk/supply-chain-analysis', json={
    "source_vendor_id": "YOUR-COMPANY",
    "min_depth": 1,
    "max_depth": 3
})

data = response.json()

# Convert to DataFrame
paths = []
for path in data['paths']:
    paths.append({
        'Vendor ID': path['target_vendor_id'],
        'Degree': path['path_length'],
        'Risk Score': path['risk_score'],
        'Classification': 'LOW' if path['risk_score'] < 0.3 else 'MEDIUM' if path['risk_score'] < 0.6 else 'HIGH'
    })

df = pd.DataFrame(paths)
df.to_csv('compliance_audit_report.csv', index=False)
print(f"✅ Exported {len(df)} vendors for audit")
```

### Use Case 2: Strategic Risk Assessment (M&A Due Diligence)

**Scenario**: Evaluating acquisition target's supply chain risks.

**Workflow**:
```bash
# Step 1: Map complete supply chain
curl -X GET "http://localhost:8000/risk/deep-search/TARGET-COMPANY?max_depth=10" \
  > target_supply_chain.json

# Step 2: Identify risk hotspots
curl -X GET "http://localhost:8000/risk/risk-hotspots?min_connections=5" \
  > supply_chain_bottlenecks.json

# Step 3: Assess deep supply chain risks (4th-10th party)
curl -X POST "http://localhost:8000/risk/supply-chain-analysis" \
  -d '{
    "source_vendor_id": "TARGET-COMPANY",
    "min_depth": 4,
    "max_depth": 10,
    "limit": 1000
  }' > deep_supply_chain_risks.json
```

**Analysis Checklist**:
- [ ] Are there any CRITICAL risk hotspots? (10+ connections)
- [ ] What is the average risk score at 5+ degrees?
- [ ] Are there geopolitical concentration risks? (single country dependencies)
- [ ] How many unverified relationships exist?

### Use Case 3: Quarterly Risk Monitoring

**Scenario**: Regular risk monitoring for board reporting.

**Automated Workflow**:
```bash
# Create a monitoring script (quarterly_risk_report.sh)
#!/bin/bash

echo "🔍 Quarterly Vendor Risk Assessment - $(date)"

# 1. Third-party risk summary
echo "\n📊 Third-Party Vendors (TPRM)"
curl -s -X POST "http://localhost:8000/risk/nth-party-assessment" \
  -H "Content-Type: application/json" \
  -d '{"vendor_id": "YOUR-COMPANY", "party_level": 3}' \
  | jq '.vendors_found, .vendors[] | select(.avg_risk_score > 0.6)'

# 2. Risk hotspots
echo "\n⚠️  Supply Chain Hotspots"
curl -s -X GET "http://localhost:8000/risk/risk-hotspots?min_connections=5" \
  | jq '.hotspots_found, .risk_summary.critical_hotspots[]'

# 3. Deep supply chain risks
echo "\n🔎 Fourth-Party Risks (FPRM)"
curl -s -X POST "http://localhost:8000/risk/supply-chain-analysis" \
  -H "Content-Type: application/json" \
  -d '{
    "source_vendor_id": "YOUR-COMPANY",
    "min_depth": 4,
    "max_depth": 7,
    "limit": 100
  }' | jq '.paths_found'

echo "\n✅ Quarterly risk assessment complete"
```

### Use Case 4: Incident Response (Vendor Breach)

**Scenario**: A vendor was breached. Identify all downstream impacts.

**Immediate Response Workflow**:
```bash
# Step 1: Find all vendors connected to breached vendor
curl -X GET "http://localhost:8000/risk/deep-search/BREACHED-VENDOR?max_depth=5"

# Step 2: Identify your exposure to this vendor
curl -X POST "http://localhost:8000/risk/supply-chain-analysis" \
  -d '{
    "source_vendor_id": "YOUR-COMPANY",
    "min_depth": 1,
    "max_depth": 10,
    "limit": 1000
  }' | jq '.paths[] | select(.path[].vendor_id == "BREACHED-VENDOR")'

# Step 3: Find alternate suppliers
curl -X POST "http://localhost:8000/api/vendors/match" \
  -d '{
    "query": "Similar vendors to BREACHED-VENDOR",
    "limit": 10
  }'
```

---

## Troubleshooting

### Issue 1: "Vendor not found" Error

**Error**:
```json
{
  "detail": "Source vendor YOUR-COMPANY not found"
}
```

**Solution**:
```bash
# 1. Check if vendor exists
curl -X GET "http://localhost:8000/api/vendors/YOUR-COMPANY"

# 2. If not found, create it
curl -X POST "http://localhost:8000/api/vendors" \
  -d '{
    "vendor_id": "YOUR-COMPANY",
    "vendor_name": "Your Company Inc",
    "industry": "Technology"
  }'
```

### Issue 2: No Paths Found

**Error**:
```json
{
  "paths_found": 0,
  "paths": []
}
```

**Possible Causes**:
1. **No relationships exist** - Create relationships first
2. **Depth too high** - Try min_depth=1, max_depth=3 first
3. **min_strength too high** - Try min_strength=0.0

**Solution**:
```bash
# Check existing relationships
curl -X GET "http://localhost:8000/api/vendors/YOUR-COMPANY/relationships"

# Create a test relationship
curl -X POST "http://localhost:8000/api/vendors/relationships" \
  -d '{
    "source_vendor_id": "YOUR-COMPANY",
    "target_vendor_id": "VENDOR-001",
    "relationship_type": "supplier",
    "strength": 0.9
  }'
```

### Issue 3: Slow Performance (>5 seconds)

**Symptoms**: Searches taking 5-30 seconds

**Solutions**:

**Option A: Reduce search scope**
```bash
# Instead of max_depth=15, use max_depth=7
curl -X POST "http://localhost:8000/risk/supply-chain-analysis" \
  -d '{"source_vendor_id": "YOUR-COMPANY", "min_depth": 3, "max_depth": 7}'
```

**Option B: Set up Neo4j (5-50× faster)**
```bash
# Run automated Neo4j setup
setup_neo4j.bat

# Performance improvement:
# MySQL: 5-30 seconds for depth 10+
# Neo4j: 500ms-2s for depth 10+
```

### Issue 4: Neo4j Connection Failed

**Error**:
```
⚠️  Neo4j initialization failed: Could not connect to bolt://localhost:7687
```

**Solution**:
```bash
# 1. Check if Neo4j container is running
docker ps | findstr neo4j

# If not running, start it:
docker-compose -f docker-compose.neo4j.yml up -d

# 2. Wait 30 seconds for Neo4j to start

# 3. Test connection
curl http://localhost:7474

# 4. Restart your API server
uvicorn main:app --reload
```

### Issue 5: Invalid Depth Parameters

**Error**:
```json
{
  "detail": "max_depth must be between 1 and 15"
}
```

**Solution**:
```bash
# Ensure: 1 <= min_depth <= max_depth <= 15
curl -X POST "http://localhost:8000/risk/supply-chain-analysis" \
  -d '{
    "source_vendor_id": "YOUR-COMPANY",
    "min_depth": 3,
    "max_depth": 10
  }'
```

---

## API Quick Reference

### Endpoints Summary

| Endpoint | Method | Purpose | Depth Range |
|----------|--------|---------|-------------|
| `/risk/supply-chain-analysis` | POST | Deep supply chain risk analysis | 1-15 |
| `/risk/nth-party-assessment` | POST | Specific party level assessment | 1-15 |
| `/risk/risk-hotspots` | GET | Identify vendor bottlenecks | N/A |
| `/risk/deep-search/{vendor_id}` | GET | Complete network mapping | 1-15 |

### Common Parameters

```json
{
  "source_vendor_id": "YOUR-COMPANY",    // Starting vendor
  "min_depth": 3,                         // Start at 3rd-party vendors
  "max_depth": 10,                        // End at 10th-party vendors
  "relationship_types": ["supplier"],     // Optional filter
  "min_strength": 0.0,                    // 0.0 = include all
  "limit": 500                            // Max results
}
```

---

## Next Steps

### Week 1: Setup & Testing
- [ ] Run basic setup (MySQL)
- [ ] Load sample vendor data
- [ ] Test first-party vendor review
- [ ] Verify API responses

### Week 2: Data Migration
- [ ] Export your vendor data to JSON
- [ ] Bulk load vendors via API
- [ ] Create vendor relationships
- [ ] Validate data integrity

### Week 3: Risk Analysis
- [ ] Run TPRM assessment (3rd-party)
- [ ] Identify risk hotspots
- [ ] Document high-risk vendors
- [ ] Create action plans

### Week 4: Production Readiness
- [ ] Set up Neo4j (if >1000 vendors)
- [ ] Sync data to Neo4j
- [ ] Performance testing
- [ ] Schedule quarterly assessments

---

## Additional Resources

- **Technical Documentation**: [VENDOR_RISK_MANAGEMENT.md](VENDOR_RISK_MANAGEMENT.md)
- **Neo4j Setup Guide**: [NEO4J_SETUP.md](NEO4J_SETUP.md)
- **Quick Start**: [QUICK_START_NEO4J.md](QUICK_START_NEO4J.md)
- **API Documentation**: http://localhost:8000/docs
- **Neo4j Browser**: http://localhost:7474 (after Neo4j setup)

---

## Support

**Common Questions**:

**Q: How deep should I search?**
- **Daily operations**: 1-3 degrees
- **TPRM compliance**: 3-5 degrees
- **FPRM strategic**: 6-10 degrees
- **Complete mapping**: 10-15 degrees

**Q: When should I use Neo4j?**
- **<1,000 vendors**: MySQL is fine
- **1,000-10,000 vendors**: Neo4j recommended for 7+ degree searches
- **>10,000 vendors**: Neo4j required

**Q: How often should I run risk assessments?**
- **Critical vendors**: Weekly
- **High-risk vendors**: Monthly
- **All vendors**: Quarterly
- **Complete audit**: Annually

**Q: What's a good risk score threshold?**
- **0.6+**: Requires immediate attention
- **0.3-0.6**: Enhanced monitoring
- **<0.3**: Standard oversight

---

**You're now ready to use the Vendor Risk Management system!** 🎉

Start with the [Quick Start](#quick-start) section above and gradually explore more advanced features as your needs grow.
