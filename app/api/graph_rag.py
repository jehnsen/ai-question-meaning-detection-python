"""
GraphRAG API endpoints for natural language vendor risk analysis.
Combines graph traversal with LLM for conversational risk assessment.
"""
from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from app.services.graph_rag_service import GraphRAGService

router = APIRouter(prefix="/graph-rag", tags=["graph-rag"])


# ==================== Request/Response Models ====================

class AskQuestionInput(BaseModel):
    """Input for natural language vendor risk questions."""
    question: str = Field(
        ...,
        description="Natural language question about vendor risks",
        min_length=5,
        examples=[
            "What happens if our Australian supplier fails?",
            "Show me all high-risk 3rd-party vendors",
            "Which vendors in China are critical to manufacturing?",
            "What's our exposure to unverified suppliers?"
        ]
    )
    vendor_id: Optional[str] = Field(
        default=None,
        description="Optional vendor ID to scope the question"
    )
    max_depth: int = Field(
        default=10,
        ge=1,
        le=15,
        description="Maximum graph depth to search (1-15)"
    )


class AskQuestionOutput(BaseModel):
    """Output from GraphRAG question answering."""
    question: str
    answer: str
    sources_count: int
    graph_data_summary: dict
    understood_params: dict


class ExplainPathInput(BaseModel):
    """Input for explaining a specific supply chain path."""
    source_vendor_id: str
    target_vendor_id: str
    path_data: dict = Field(
        ...,
        description="Path data from /risk/supply-chain-analysis response"
    )


class ExplainPathOutput(BaseModel):
    """Natural language explanation of a supply chain path."""
    source_vendor_id: str
    target_vendor_id: str
    explanation: str
    risk_level: str
    recommendations: list[str]


# ==================== Endpoints ====================

@router.post("/ask", response_model=AskQuestionOutput)
async def ask_vendor_question(input_data: AskQuestionInput):
    """
    Ask natural language questions about vendor risks using GraphRAG.

    This endpoint combines graph database queries with AI to provide
    natural language insights about your vendor supply chain.

    ## Examples:

    ### Supply Chain Risk
    ```json
    {
      "question": "What happens if our Australian supplier fails?",
      "vendor_id": "TECH-001",
      "max_depth": 10
    }
    ```

    ### Compliance
    ```json
    {
      "question": "Show me all unverified 3rd-party vendors"
    }
    ```

    ### Geopolitical Risk
    ```json
    {
      "question": "What's our risk exposure to vendors in China?",
      "max_depth": 7
    }
    ```

    ### Strategic Analysis
    ```json
    {
      "question": "Which vendors are single points of failure?",
      "vendor_id": "CLIENT-001"
    }
    ```

    ## Response:
    Returns AI-generated insights with:
    - Natural language answer
    - Risk assessment
    - Recommended actions
    - Source data references
    """
    try:
        rag_service = GraphRAGService()

        result = rag_service.answer_question(
            question=input_data.question,
            vendor_id=input_data.vendor_id,
            max_depth=input_data.max_depth
        )

        return AskQuestionOutput(
            question=result["question"],
            answer=result["answer"],
            sources_count=len(result.get("sources", [])),
            graph_data_summary={
                "paths_found": result["graph_data"].get("paths_found", 0),
                "search_type": result["graph_data"].get("search_type", "unknown")
            },
            understood_params=result["understood_params"]
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"GraphRAG analysis failed: {str(e)}"
        )


@router.post("/explain-path", response_model=ExplainPathOutput)
async def explain_supply_chain_path(input_data: ExplainPathInput):
    """
    Get natural language explanation of a specific supply chain path.

    Use this to explain paths returned from `/risk/supply-chain-analysis`.

    ## Example:

    First, get paths from supply chain analysis:
    ```bash
    POST /risk/supply-chain-analysis
    {
      "source_vendor_id": "TECH-001",
      "min_depth": 3,
      "max_depth": 5
    }
    ```

    Then, explain a specific path:
    ```json
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

    ## Response:
    Returns business-friendly explanation including:
    - What the path represents
    - Why the risk score is at this level
    - Potential failure scenarios
    - Recommended mitigation strategies
    """
    try:
        rag_service = GraphRAGService()

        explanation = rag_service.explain_path(input_data.path_data)

        # Determine risk level from score
        risk_score = input_data.path_data.get("risk_score", 0)
        if risk_score < 0.3:
            risk_level = "LOW"
        elif risk_score < 0.6:
            risk_level = "MEDIUM"
        elif risk_score < 0.8:
            risk_level = "HIGH"
        else:
            risk_level = "CRITICAL"

        # Extract recommendations (simple parse)
        recommendations = []
        if "Recommended" in explanation or "recommendation" in explanation.lower():
            # Try to extract bullet points or numbered items
            for line in explanation.split("\n"):
                line = line.strip()
                if line.startswith(("-", "*", "•")) or (len(line) > 0 and line[0].isdigit() and line[1] == "."):
                    recommendations.append(line.lstrip("-*•0123456789. "))

        return ExplainPathOutput(
            source_vendor_id=input_data.source_vendor_id,
            target_vendor_id=input_data.target_vendor_id,
            explanation=explanation,
            risk_level=risk_level,
            recommendations=recommendations if recommendations else ["Review vendor relationship", "Consider alternative suppliers"]
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Path explanation failed: {str(e)}"
        )


@router.get("/examples")
async def get_example_questions():
    """
    Get example questions you can ask the GraphRAG system.

    Returns categorized examples for different use cases.
    """
    return {
        "supply_chain_risk": [
            "What happens if our Australian supplier fails?",
            "Which vendors are single points of failure?",
            "Show me the complete supply chain for TECH-001",
            "What's the risk if manufacturing stops in China?"
        ],
        "compliance": [
            "Show me all unverified 3rd-party vendors",
            "List vendors that need compliance review",
            "Which 4th-party vendors haven't been verified?",
            "What suppliers are missing verification?"
        ],
        "geopolitical_risk": [
            "What's our risk exposure to vendors in China?",
            "Show me all Russian suppliers in the supply chain",
            "Which vendors operate in high-risk countries?",
            "What's our dependency on Asian manufacturing?"
        ],
        "strategic_analysis": [
            "Which vendors are most critical to operations?",
            "Show me vendors with the highest risk scores",
            "What are the top 5 supply chain vulnerabilities?",
            "Which relationships should we prioritize for backup planning?"
        ],
        "operational": [
            "How many vendors are in our supply chain?",
            "What's the average risk score for 3rd-party vendors?",
            "Show me the deepest supply chain paths",
            "Which industries are we most dependent on?"
        ]
    }


@router.get("/health")
async def health_check():
    """Check if GraphRAG service is operational."""
    try:
        rag_service = GraphRAGService()

        # Simple test - can we instantiate?
        test_result = {
            "status": "healthy",
            "graph_backend": "neo4j" if hasattr(rag_service.graph_service, 'driver') else "mysql",
            "llm_available": hasattr(rag_service, 'openai_client')
        }

        return test_result

    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"GraphRAG service unhealthy: {str(e)}"
        )
