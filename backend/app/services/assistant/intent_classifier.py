import re

class IntentClassifier:
    """Classifies user queries into specific functional assistant intents."""

    def __init__(self) -> None:
        # Regex mappings for specific intent detection
        self.patterns = {
            "project_info": [
                r"\b(what is|about|tell me about|explain|describe)\b.*\b(journeyiq|journey iq|this app|this platform|this project|this website|this site|this store)\b",
                r"\b(journeyiq|journey iq)\b.*\b(what|about|is|mean|does)\b",
                r"\b(who built|who made|who created|who developed|tech stack|technology|architecture|features|how does it work|how it works)\b",
                r"\b(what can you do|your capabilities|your features|help me understand)\b",
                r"\b(deep learning|machine learning|neural|ncf|recommendation engine|recommendation system|collaborative filtering)\b",
                r"\b(how does|what does)\b.*\b(recommendation|ai|chatbot|assistant|nlp)\b",
                r"\b(agentic|agent loop|dashboard|analytics|sentiment)\b.*\b(what|how|explain|about)\b",
                r"\b(ml|dl|ai|nlp)\b.*\b(work|how|what|explain|about|in|project|used|use)\b",
                r"\b(how|what)\b.*\b(ml|dl|ai|nlp)\b",
                r"\b(pytorch|torch|vader|textblob|scikit|sklearn|numpy|pandas)\b",
                r"\b(model|training|inference|prediction|embedding|epoch|neural network)\b.*\b(how|what|explain|work|about)\b",
                r"\b(how|what)\b.*\b(model|training|inference|prediction)\b.*\b(work|used|about)\b",
                r"\b(data science|data flow|pipeline|workflow)\b",
            ],
            "greeting": [
                r"^(hi|hello|hey|good morning|good evening|good afternoon|howdy|sup|yo|hola)[\s!?.]*$",
                r"\b(continue shopping|keep browsing|browse more|shop more)\b",
            ],
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
                r"\b(trending|popular|best sellers|hot selling|most popular|best rated|top rated|highest rated|high rated)\b",
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
