from typing import Any

class LocalAIProvider:
    """Offline template-based generator to handle chat responses when Gemini or OpenAI is unavailable."""

    def generate_response(
        self,
        message: str,
        intent: str,
        products: list[dict[str, Any]],
        context: dict[str, Any]
    ) -> str:
        """
        Generate natural language replies based on query intent and retrieved items.
        """
        if not products:
            return "I searched our store database but couldn't find any products that match your exact query. Try searching for other item categories like Laptops, Headphones, or Water Bottles!"

        prod_names = [p["name"] for p in products]
        
        if intent == "price_filter":
            return f"I found some great options fitting your budget criteria: {', '.join(prod_names[:3])}. These are priced under your threshold and are fully in stock!"
            
        elif intent == "compare_products":
            if len(products) >= 2:
                p1, p2 = products[0], products[1]
                return (
                    f"Let's compare **{p1['name']}** and **{p2['name']}**:\n\n"
                    f"- **Price**: {p1['brand']} costs ${p1['price']:.2f} while {p2['brand']} costs ${p2['price']:.2f}.\n"
                    f"- **Rating**: {p1['name']} is rated {p1['rating']}⭐ and {p2['name']} is rated {p2['rating']}⭐.\n\n"
                    f"If you want the best value, go for {p1['name'] if p1['price'] < p2['price'] else p2['name']}!"
                )
            return f"To compare items, please specify at least two matching products. Here is the closest match I found: {products[0]['name']}."
            
        elif intent == "trending_products":
            return f"Here are the top trending and highest-rated items popular with store shoppers right now: {', '.join(prod_names[:3])}."
            
        elif intent == "recommend_for_me":
            return f"Based on your profile browsing habits and past interest history, our Hybrid Recommender recommends checking out: {', '.join(prod_names[:3])}."
            
        elif intent == "order_status":
            return "To look up your order delivery status, please click the **'Track My Order'** button or navigate to the 'My Orders' section in your account profile dropdown!"

        # Default general recommend or general QnA
        return f"Here are some options I selected for you: {', '.join(prod_names[:3])}. Let me know if you would like me to compare them or filter by price!"
