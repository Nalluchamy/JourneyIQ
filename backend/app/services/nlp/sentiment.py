import re
from typing import Any

# Simple sentiment lexicon for fallback word-matching
POSITIVE_WORDS = {
    "love", "great", "excellent", "awesome", "perfect", "good", "nice", "fantastic",
    "amazing", "satisfied", "happy", "recommend", "best", "superb", "wonderful", "easy",
    "fast", "friendly", "helpful", "delighted", "smooth", "comfortable", "durable",
    "high-quality", "efficient", "recommend", "well", "pleased", "outstanding", "impressive"
}

NEGATIVE_WORDS = {
    "hate", "bad", "terrible", "worst", "poor", "awful", "horrible", "disappointed",
    "broken", "slow", "expensive", "useless", "cheap", "faulty", "defect", "fail",
    "flaw", "issue", "problem", "return", "refund", "waste", "annoyed", "difficult",
    "uncomfortable", "noisy", "dislike", "angry", "frustrated", "sad", "pain"
}

# Try loading HuggingFace transformers pipeline if available
try:
    from transformers import pipeline
    # Load pipeline lazily or check imports
    HAS_TRANSFORMERS = True
except ImportError:
    HAS_TRANSFORMERS = False


class SentimentAnalyzer:
    """Performs sentiment classification and score computation for review text."""

    def __init__(self) -> None:
        self.pipeline = None
        if HAS_TRANSFORMERS:
            try:
                # Use a small, lightweight DistilBERT sentiment model
                self.pipeline = pipeline(
                    "sentiment-analysis",
                    model="distilbert-base-uncased-finetuned-sst-2-english",
                    device=-1  # Force CPU
                )
            except Exception:
                self.pipeline = None

    def analyze(self, text: str) -> dict[str, Any]:
        """
        Analyze a text string and return sentiment metrics.
        
        Returns:
            dict: {
                "label": "positive" | "neutral" | "negative",
                "score": float (-1.0 to 1.0),
                "confidence": float (0.0 to 1.0)
            }
        """
        if not text or not text.strip():
            return {"label": "neutral", "score": 0.0, "confidence": 1.0}

        cleaned_text = text.lower().strip()

        # If transformer pipeline is available, use it
        if self.pipeline is not None:
            try:
                result = self.pipeline(cleaned_text[:512])[0]
                label = result["label"].lower() # e.g. "positive" or "negative"
                confidence = float(result["score"])
                
                # Normalize score to [-1.0, 1.0] range
                if label == "positive":
                    score = confidence
                elif label == "negative":
                    score = -confidence
                    label = "negative"
                else:
                    score = 0.0
                    label = "neutral"
                
                # If score is close to 0, call it neutral
                if abs(score) < 0.2:
                    label = "neutral"
                    
                return {
                    "label": label,
                    "score": round(score, 2),
                    "confidence": round(confidence, 2)
                }
            except Exception:
                pass  # Fall back to lexicon-based analyzer on failure

        # Lexicon/rule-based fallback analyzer
        # Tokenize by splitting non-word characters
        words = re.findall(r'\b\w+\b', cleaned_text)
        if not words:
            return {"label": "neutral", "score": 0.0, "confidence": 1.0}

        pos_count = sum(1 for w in words if w in POSITIVE_WORDS)
        neg_count = sum(1 for w in words if w in NEGATIVE_WORDS)
        total_tokens = len(words)

        # Calculate sentiment score (-1.0 to 1.0)
        net_score = pos_count - neg_count
        score = net_score / max(pos_count + neg_count, 1)

        # Map to label
        if score > 0.15:
            label = "positive"
        elif score < -0.15:
            label = "negative"
        else:
            label = "neutral"

        # Calculate a pseudo confidence score based on match density
        match_density = (pos_count + neg_count) / total_tokens
        confidence = 0.5 + (0.5 * abs(score)) * min(1.0, match_density * 2.0)
        confidence = min(0.99, max(0.5, confidence))

        return {
            "label": label,
            "score": round(score, 2),
            "confidence": round(confidence, 2)
        }


# Singleton instance
sentiment_analyzer = SentimentAnalyzer()
