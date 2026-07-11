import re

class IntentClassifier:
    """Classifies user queries into specific functional assistant intents."""

    def __init__(self) -> None:
        # Regex mappings for specific intent detection
        self.patterns = {
            "order_status": [
                r"\border\b.*\b(track|status|where|history)\b",
                r"\btrack\b.*\border\b",
                r"\bwhere is my\b"
            ],
            "price_filter": [
                r"\b(under|below|less than|cheap|cheapest|budget)\b.*\b(rs|₹|\$)?\d+",
                r"\b(rs|₹|\$)?\d+.*\b(under|below|less than|budget)\b"
            ],
            "compare_products": [
                r"\b(compare|versus|vs|difference between|better|comparison)\b",
                r"\b(which is better|better choice)\b"
            ],
            "trending_products": [
                r"\b(trending|popular|best sellers|hot selling|most popular)\b",
                r"\btrending\b"
            ],
            "wishlist_based": [
                r"\b(wishlist|my items|favorite|favorites|saved)\b"
            ],
            "recommend_for_me": [
                r"\b(for me|personalized|personalize|my taste|tailor)\b"
            ],
            "similar_products": [
                r"\b(similar to|like this|alternatives to|alternative to)\b"
            ],
            "review_summary": [
                r"\b(reviews of|rating of|what do people say|what do customers like)\b"
            ],
            "recommend_product": [
                r"\b(recommend|show|find|search|suggest|buy|looking for)\b"
            ]
        }

    def classify(self, message: str) -> str:
        """
        Classifies a user message and returns one of the supported intent names.
        Defaults to 'general_qna'.
        """
        cleaned = message.lower().strip()
        
        for intent, regex_list in self.patterns.items():
            for pattern in regex_list:
                if re.search(pattern, cleaned):
                    return intent
                    
        return "general_qna"
