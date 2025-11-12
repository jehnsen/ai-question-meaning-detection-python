"""
GraphRAG Service for Natural Language Vendor Risk Analysis
Combines graph traversal with LLM for conversational risk assessment
"""
from typing import List, Dict, Any, Optional
from openai import OpenAI
import json
from .vendor_graph import VendorGraphService
from .neo4j_service import Neo4jGraphService, is_neo4j_available

class GraphRAGService:
    """
    GraphRAG = Graph Traversal + Retrieval-Augmented Generation

    Allows users to ask natural language questions about vendor risks
    and get AI-generated insights based on the vendor graph.
    """

    def __init__(self):
        self.openai_client = OpenAI()

        # Use Neo4j if available, otherwise MySQL
        if is_neo4j_available():
            self.graph_service = Neo4jGraphService()
        else:
            self.graph_service = VendorGraphService()

    def answer_question(
        self,
        question: str,
        vendor_id: Optional[str] = None,
        max_depth: int = 10
    ) -> Dict[str, Any]:
        """
        Answer natural language questions about vendor risks using GraphRAG.

        Examples:
        - "What happens if our Australian supplier fails?"
        - "Which vendors are most critical to our supply chain?"
        - "Show me all unverified 3rd-party vendors"
        - "What's the risk of doing business with vendors in China?"

        Args:
            question: Natural language question
            vendor_id: Optional vendor ID to scope the question
            max_depth: Maximum graph depth to search

        Returns:
            {
                "question": str,
                "answer": str,
                "sources": List[dict],
                "graph_data": dict
            }
        """

        # Step 1: Use LLM to understand the question and extract parameters
        query_params = self._understand_question(question, vendor_id)

        # Step 2: Execute graph traversal based on understood parameters
        graph_results = self._execute_graph_query(query_params, max_depth)

        # Step 3: Use LLM to generate natural language answer
        answer = self._generate_answer(question, graph_results)

        return {
            "question": question,
            "answer": answer,
            "sources": graph_results.get("paths", []),
            "graph_data": graph_results,
            "understood_params": query_params
        }

    def _understand_question(
        self,
        question: str,
        vendor_id: Optional[str]
    ) -> Dict[str, Any]:
        """
        Use LLM to understand user's natural language question
        and extract graph query parameters.
        """

        system_prompt = """You are a vendor risk management AI assistant.
Your job is to understand user questions about vendor relationships and supply chains,
then extract structured parameters for graph database queries.

Extract the following from the user's question:
- vendor_id: Specific vendor mentioned (or null)
- search_type: "supply_chain" | "nth_party" | "risk_hotspots" | "vendor_search"
- min_depth: Minimum relationship depth (default: 1)
- max_depth: Maximum relationship depth (default: 10)
- filters: Any filters like country, industry, verified status, relationship type
- intent: What the user wants to know

Return ONLY valid JSON, no explanation."""

        user_prompt = f"""Question: {question}

Context vendor_id (if provided): {vendor_id or "Not specified"}

Extract query parameters as JSON."""

        response = self.openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.1,
            response_format={"type": "json_object"}
        )

        params = json.loads(response.choices[0].message.content)
        return params

    def _execute_graph_query(
        self,
        params: Dict[str, Any],
        max_depth: int
    ) -> Dict[str, Any]:
        """
        Execute graph traversal based on understood parameters.
        """

        search_type = params.get("search_type", "supply_chain")
        vendor_id = params.get("vendor_id")

        if search_type == "supply_chain" and vendor_id:
            # Find supply chain paths
            from app.schemas import GraphSearchInput
            search_input = GraphSearchInput(
                source_vendor_id=vendor_id,
                min_depth=params.get("min_depth", 1),
                max_depth=params.get("max_depth", max_depth),
                relationship_types=params.get("filters", {}).get("relationship_types"),
                min_strength=params.get("filters", {}).get("min_strength", 0.0)
            )

            paths = self.graph_service.find_paths(
                source_vendor_id=search_input.source_vendor_id,
                min_depth=search_input.min_depth,
                max_depth=search_input.max_depth,
                relationship_types=search_input.relationship_types,
                min_strength=search_input.min_strength
            )

            return {
                "search_type": "supply_chain",
                "paths_found": len(paths),
                "paths": [p.dict() for p in paths]
            }

        # Add other search types as needed
        return {"paths": [], "paths_found": 0}

    def _generate_answer(
        self,
        question: str,
        graph_results: Dict[str, Any]
    ) -> str:
        """
        Use LLM to generate natural language answer based on graph results.
        """

        system_prompt = """You are a vendor risk management expert.
Given graph database results about vendor relationships, provide clear,
actionable insights in natural language.

Focus on:
- Risk levels and their business impact
- Critical dependencies and bottlenecks
- Recommended actions
- Compliance considerations

Be concise but thorough. Use business language, not technical jargon."""

        # Prepare graph context
        paths_summary = []
        for path in graph_results.get("paths", [])[:10]:  # Limit context size
            paths_summary.append({
                "target": path.get("target_vendor_id"),
                "depth": path.get("path_length"),
                "risk_score": path.get("risk_score"),
                "strength": path.get("total_strength")
            })

        user_prompt = f"""Question: {question}

Graph Analysis Results:
- Total paths found: {graph_results.get('paths_found', 0)}
- Sample paths: {json.dumps(paths_summary, indent=2)}

Provide a natural language answer with:
1. Direct answer to the question
2. Key risks identified
3. Recommended actions
4. Risk prioritization"""

        response = self.openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.3
        )

        return response.choices[0].message.content

    def explain_path(self, path_data: Dict[str, Any]) -> str:
        """
        Generate natural language explanation of a single supply chain path.
        """

        prompt = f"""Explain this supply chain path in simple business terms:

Source: {path_data['source_vendor_id']}
Target: {path_data['target_vendor_id']}
Depth: {path_data['path_length']} degrees
Risk Score: {path_data['risk_score']:.2f}
Path: {json.dumps(path_data['path'], indent=2)}

Provide:
1. What this path represents in business terms
2. Why the risk score is at this level
3. What could go wrong
4. Recommended mitigation"""

        response = self.openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )

        return response.choices[0].message.content
