from typing import Any

class PromptBuilder:
    """Builds highly focused, context-aware prompts for Gemini/OpenAI models."""

    def build_prompt(
        self,
        message: str,
        intent: str,
        products: list[dict[str, Any]],
        context: dict[str, Any]
    ) -> str:
        """
        Construct the final system instructions prompt.
        """
        # Format the database products list
        products_str = ""
        for i, p in enumerate(products):
            products_str += f"{i+1}. {p['name']} (Brand: {p['brand']}, Price: ${p['price']:.2f}, Rating: {p['rating']}⭐, ID: {p['id']})\n"

        # Format session memory history
        history_str = ""
        if context.get("previous_questions"):
            history_str = "Previous conversation questions:\n" + "\n".join(
                [f"- {q}" for q in context["previous_questions"][-3:]]
            )

        prompt = f"""
You are the JourneyIQ AI Shopping Assistant, a helpful and polite conversational retail agent.
Your primary objective is to assist customers with product recommendations, comparisons, and general storefront questions.

CONSTRAINTS:
1. ONLY recommend products from the database list supplied below.
2. NEVER make up, invent, or hallucinate products or brands. If no items match, politely advise the user.
3. Be concise and friendly. Format your answer nicely in Markdown.

DATABASE PRODUCTS MATCHED FOR USER QUERY:
{products_str if products_str else "No matching products found in the database."}

SESSION CONTEXT:
{history_str}
Current Budget Constraint: {context.get('budget') or 'None'}
Preferred Product Categories: {', '.join(context.get('preferred_categories', [])) or 'None'}

USER QUERY:
"{message}"

Write your helpful, markdown-formatted response:
"""
        return prompt.strip()
