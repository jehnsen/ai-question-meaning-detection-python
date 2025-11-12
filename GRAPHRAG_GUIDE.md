# GraphRAG - Natural Language Vendor Risk Analysis

## What is GraphRAG?

**GraphRAG** = **Graph Traversal** + **Retrieval-Augmented Generation (RAG)**

It combines your Neo4j vendor graph with OpenAI's LLM to answer natural language questions about vendor risks.

---

## 🚀 Quick Start

### 1. Start the Server

```bash
cd d:\xampp\apache\bin\python\question-linking
uvicorn main:app --reload
```

### 2. Ask Your First Question

**Using Postman/cURL**:
```bash
POST http://localhost:8000/graph-rag/ask
Content-Type: application/json

{
  "question": "What happens if our Australian supplier fails?",
  "vendor_id": "TECH-001",
  "max_depth": 10
}
```

**Response**:
```json
{
  "question": "What happens if our Australian supplier fails?",
  "answer": "If Raw Materials Inc (RAWMATERIAL-005) in Australia fails, you would face a CRITICAL supply chain disruption affecting:\n\n1. Component production via COMPONENT-004 (Taiwan)\n2. Packaging materials via PACKAGING-006 (Vietnam)\n\nThis is a single point of failure with HIGH RISK (avg risk score: 0.89).\n\nRECOMMENDED ACTIONS:\n- Identify backup Australian suppliers immediately\n- Diversify raw material sourcing to 2+ countries\n- Increase inventory buffer by 30 days\n- Add this to quarterly risk review\n\nCOMPLIANCE NOTE: Document this 4th-party risk for SOC 2 audit.",
  "sources_count": 2,
  "graph_data_summary": {
    "paths_found": 2,
    "search_type": "supply_chain"
  },
  "understood_params": {
    "vendor_id": "TECH-001",
    "search_type": "supply_chain",
    "filters": {
      "country": "Australia"
    }
  }
}
```

---

## 📚 API Endpoints

### 1. `/graph-rag/ask` - Ask Questions

Ask natural language questions about vendor risks.

**Request**:
```json
{
  "question": "string",
  "vendor_id": "string" (optional),
  "max_depth": 10
}
```

**Examples**:

#### Supply Chain Risk
```json
{
  "question": "What happens if our Australian supplier fails?",
  "vendor_id": "TECH-001"
}
```

#### Compliance
```json
{
  "question": "Show me all unverified 3rd-party vendors"
}
```

#### Geopolitical Risk
```json
{
  "question": "What's our risk exposure to vendors in China?",
  "max_depth": 7
}
```

#### Strategic Analysis
```json
{
  "question": "Which vendors are single points of failure?",
  "vendor_id": "CLIENT-001"
}
```

---

### 2. `/graph-rag/explain-path` - Explain Supply Chain Path

Get business-friendly explanation of a specific vendor relationship path.

**Workflow**:

**Step 1**: Get paths from standard API
```bash
POST /risk/supply-chain-analysis
{
  "source_vendor_id": "TECH-001",
  "min_depth": 3,
  "max_depth": 5
}
```

**Step 2**: Explain a specific path
```bash
POST /graph-rag/explain-path
{
  "source_vendor_id": "TECH-001",
  "target_vendor_id": "RAWMATERIAL-005",
  "path_data": {
    "path": [...],
    "relationships": [...],
    "total_strength": 0.494,
    "path_length": 3,
    "risk_score": 0.506
  }
}
```

**Response**:
```json
{
  "source_vendor_id": "TECH-001",
  "target_vendor_id": "RAWMATERIAL-005",
  "explanation": "This supply chain path represents a 3-degree dependency...",
  "risk_level": "MEDIUM",
  "recommendations": [
    "Identify backup suppliers in Australia",
    "Increase inventory buffer to 45 days",
    "Add quarterly vendor health checks"
  ]
}
```

---

### 3. `/graph-rag/examples` - Get Example Questions

Returns categorized example questions.

```bash
GET /graph-rag/examples
```

**Response**:
```json
{
  "supply_chain_risk": [
    "What happens if our Australian supplier fails?",
    "Which vendors are single points of failure?",
    ...
  ],
  "compliance": [...],
  "geopolitical_risk": [...],
  "strategic_analysis": [...],
  "operational": [...]
}
```

---

### 4. `/graph-rag/health` - Health Check

Check if GraphRAG service is operational.

```bash
GET /graph-rag/health
```

**Response**:
```json
{
  "status": "healthy",
  "graph_backend": "neo4j",
  "llm_available": true
}
```

---

## 🎯 Use Cases

### Use Case 1: Executive Briefing

**Question**: "What are our top 3 vendor risks?"

**GraphRAG automatically**:
1. Searches the vendor graph
2. Ranks vendors by risk score
3. Generates executive summary with recommendations

**Traditional API would require**:
- Multiple API calls
- Manual data processing
- Risk interpretation by analyst

---

### Use Case 2: Compliance Audit

**Question**: "Show me all unverified 3rd-party vendors for SOC 2 audit"

**GraphRAG automatically**:
1. Understands "3rd-party" = depth 3
2. Filters by `verified: false`
3. Generates compliance report

---

### Use Case 3: Incident Response

**Question**: "A vendor in China was breached. What's our exposure?"

**GraphRAG automatically**:
1. Identifies Chinese vendors
2. Traces all dependent paths
3. Calculates impact and recommends actions

---

## 📊 GraphRAG vs Traditional API

| Feature | Traditional API | GraphRAG |
|---------|----------------|----------|
| **Input** | JSON parameters | Natural language |
| **Query** | Manual endpoint selection | AI understands intent |
| **Output** | Raw data (JSON) | Business insights |
| **User** | Technical (developers) | Non-technical (executives) |
| **Speed** | Fast (50-500ms) | Slower (2-5 seconds) |
| **Cost** | Low (DB only) | Higher (LLM API calls) |

**Recommendation**: Use both! GraphRAG for ad-hoc analysis, traditional API for dashboards.

---

## 🔧 How It Works

### Architecture:

```
User Question
    ↓
1. LLM Query Understanding
   - Extract vendor_id, depth, filters
   - Understand intent
    ↓
2. Graph Traversal
   - Neo4j Cypher query OR
   - MySQL BFS algorithm
    ↓
3. LLM Answer Generation
   - Analyze graph results
   - Generate insights
   - Recommend actions
    ↓
Natural Language Response
```

### Example Flow:

**Input**: "What happens if our Australian supplier fails?"

**Step 1 - Understanding**:
```json
{
  "vendor_id": "TECH-001",
  "search_type": "supply_chain",
  "filters": {
    "country": "Australia"
  },
  "intent": "impact_analysis"
}
```

**Step 2 - Graph Query**:
```cypher
MATCH path = (source:Vendor {vendor_id: 'TECH-001'})-[:DEPENDS_ON*1..10]->(target:Vendor)
WHERE target.country = 'Australia'
RETURN path, target
```

**Step 3 - LLM Analysis**:
```
Input: 2 paths found to RAWMATERIAL-005
Output: "CRITICAL supply chain disruption affecting:
         1. Component production
         2. Packaging materials

         RECOMMENDED ACTIONS:..."
```

---

## 💰 Cost Considerations

### API Call Costs:

| Endpoint | LLM Calls | Approx Cost |
|----------|-----------|-------------|
| `/ask` | 2 calls | $0.002-0.01 |
| `/explain-path` | 1 call | $0.001-0.005 |

**GPT-4o Mini** (default):
- Query understanding: ~500 tokens ($0.001)
- Answer generation: ~1500 tokens ($0.001)

**Total per question**: ~$0.002

**For 1000 questions/month**: ~$2

---

## 🎓 Best Practices

### 1. Be Specific

❌ Bad: "Show me vendors"
✅ Good: "Show me all unverified 3rd-party vendors in China"

### 2. Provide Context

❌ Bad: "What's the risk?"
✅ Good: "What's the risk if our Australian supplier fails?"

### 3. Scope with vendor_id

```json
{
  "question": "What are my supply chain risks?",
  "vendor_id": "CLIENT-001"  // Scopes to this vendor
}
```

### 4. Adjust Depth

- **Quick analysis**: `max_depth: 3-5`
- **Compliance**: `max_depth: 7`
- **Strategic planning**: `max_depth: 10-15`

---

## 🚀 Getting Started

### 1. Load Sample Data

```bash
# Load sample vendors into Neo4j
python load_sample_vendors_neo4j.py sample_vendor_data.json
```

### 2. Start Server

```bash
uvicorn main:app --reload
```

### 3. Test GraphRAG

**Open**: http://localhost:8000/docs

**Navigate to**: `/graph-rag` section

**Try**:
```json
POST /graph-rag/ask
{
  "question": "What happens if RAWMATERIAL-005 fails?",
  "vendor_id": "TECH-001",
  "max_depth": 10
}
```

---

## 📖 More Examples

### Example 1: Bottleneck Detection
```json
{
  "question": "Which vendors appear in multiple supply chain paths?",
  "vendor_id": "TECH-001"
}
```

### Example 2: Geographic Risk
```json
{
  "question": "List all vendors in high-risk countries",
  "max_depth": 7
}
```

### Example 3: Relationship Verification
```json
{
  "question": "How many unverified relationships do we have?",
  "vendor_id": "CLIENT-001"
}
```

### Example 4: Industry Concentration
```json
{
  "question": "What's our dependency on the Manufacturing industry?",
  "max_depth": 10
}
```

---

## ✅ Summary

**GraphRAG enables**:
- ✅ Natural language vendor risk analysis
- ✅ AI-powered insights and recommendations
- ✅ Business-friendly explanations
- ✅ Automatic compliance reporting
- ✅ Executive-ready summaries

**Perfect for**:
- Executive briefings
- Compliance audits
- Incident response
- Strategic planning
- Training and onboarding

**Complements**:
- Traditional graph API (for dashboards)
- Neo4j direct queries (for developers)
- Risk management workflows (for analysts)

---

**Start asking questions about your vendor risks in plain English!** 🎯

1. **Direct Answer:**\n   If TechCorp Solutions' third-party supplier fails, there appears to be no immediate direct impact on the current vendor network, as no paths or dependencies were identified in the graph database results.\n\n2. **Key Risks Identified:**\n   Although no direct paths were found, the absence of data does not necessarily imply the absence of risk. Key risks could include potential hidden dependencies not captured in the current dataset, or indirect impacts such as reputational damage or financial implications if TechCorp Solutions is unable to fulfill its obligations due to this supplier's failure.\n\n3. **Recommended Actions:**\n   - **Conduct a Comprehensive Review:** Perform a thorough audit of TechCorp Solutions' vendor relationships and supply chain to identify any undocumented dependencies or indirect impacts.\n   - **Enhance Monitoring:** Implement enhanced monitoring and reporting mechanisms to quickly identify and respond to any emerging risks related to supplier performance.\n   - **Develop Contingency Plans:** Establish contingency plans, including alternative suppliers or backup strategies, to mitigate potential disruptions.\n   - **Engage in Regular Communication:** Maintain open lines of communication with TechCorp Solutions to ensure any changes in their supplier status are promptly reported and addressed.\n\n4. **Risk Prioritization:**\n   Given the lack of direct paths, the immediate risk level is low. However, the potential for hidden dependencies or indirect impacts necessitates a moderate level of prioritization. Focus should be on proactive measures to uncover and mitigate any unforeseen risks, thereby ensuring business continuity and compliance with regulatory requirements.