import json
from typing import Any


class CopilotBusinessContext:
    """Serializes live analytics data frames and telemetry details into LLM prompt context."""

    def build_llm_context(self, question: str, query_data: dict[str, Any], history: list[str]) -> str:
        """Assembles a detailed context description string grounding LLM inputs."""
        intent = query_data.get("intent", "GENERAL_ANALYTICS")
        sources = ", ".join(query_data.get("sources", ["Storefront Database"]))
        data = query_data.get("data", {})

        serialized_data = json.dumps(data, indent=2)
        history_str = "\n".join([f"- {h}" for h in history]) if history else "None"

        context_prompt = f"""[SYSTEM DATA GROUNDING CONTEXT]
The user is asking a retail business question about their store.
Your response MUST be based STRICTLY on the live database records provided below.
DO NOT invent or hallucinate any numbers. All statistics, counts, revenue values, and KPIs MUST come directly from this data.

User Question: "{question}"
Classified Business Intent: {intent}
Queried Data Sources: {sources}

Recent Conversation History:
{history_str}

Live Database Metrics JSON:
{serialized_data}

[INSTRUCTIONS]
1. Read the JSON telemetry data carefully.
2. Structure your business answer using the requested sections (Observation, Evidence, Explanation, Recommendation, Confidence).
3. Do not formulate suggestions unsupported by the metrics.
4. Keep explanations clear, actionable, and grounded in the data.
"""
        return context_prompt
