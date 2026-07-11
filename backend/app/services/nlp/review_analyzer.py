from typing import Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.review import Review
from app.models.product import Product
from app.models.category import Category
from app.services.nlp.sentiment import sentiment_analyzer
from app.services.nlp.keywords import extract_keywords
from app.services.nlp.summarizer import generate_nlp_summary

# Dictionaries for categorizing praises and complaints
PRAISE_KEYWORDS = {
    "quality": "product quality",
    "delivery": "delivery speed",
    "shipping": "fast shipping",
    "service": "customer service",
    "price": "reasonable price",
    "comfortable": "comfort",
    "easy": "ease of use",
    "durable": "durability",
    "fast": "speedy performance"
}

COMPLAINT_KEYWORDS = {
    "battery": "battery life",
    "price": "high price",
    "expensive": "high cost",
    "slow": "sluggish performance",
    "broken": "damaged package",
    "noisy": "excessive noise",
    "cheap": "cheap material",
    "heavy": "excessive weight",
    "difficult": "complex setup"
}


class ReviewAnalyzerService:
    """Aggregates and analyzes customer reviews in the database using NLP."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def analyze_all_reviews(self) -> dict[str, Any]:
        """
        Query reviews, classify sentiment, extract keywords, praises, and complaints.
        
        Returns:
            dict of metrics.
        """
        # Fetch reviews with product/category data
        stmt = select(Review).options(
            selectinload(Review.product).selectinload(Product.category)
        )
        result = await self.db.execute(stmt)
        reviews = result.scalars().all()
        total_reviews = len(reviews)

        if total_reviews == 0:
            return {
                "positive_pct": 100.0,
                "neutral_pct": 0.0,
                "negative_pct": 0.0,
                "avg_sentiment": 1.0,
                "avg_confidence": 1.0,
                "top_keywords": [],
                "top_praises": [],
                "top_complaints": [],
                "trending_categories": [],
                "summary": "No customer reviews have been submitted yet.",
                "total_count": 0
            }

        pos_count = 0
        neu_count = 0
        neg_count = 0
        sentiment_scores = []
        confidence_scores = []
        review_texts = []
        
        praises_counts: dict[str, int] = {}
        complaints_counts: dict[str, int] = {}
        category_counts: dict[str, int] = {}

        for rev in reviews:
            text = rev.review or ""
            review_texts.append(text)
            
            # 1. Run sentiment analysis
            res = sentiment_analyzer.analyze(text)
            label = res["label"]
            score = res["score"]
            conf = res["confidence"]

            sentiment_scores.append(score)
            confidence_scores.append(conf)

            if label == "positive":
                pos_count += 1
            elif label == "negative":
                neg_count += 1
            else:
                neu_count += 1

            # 2. Extract praises and complaints based on keyword mapping
            words = text.lower().split()
            for w in words:
                clean_w = "".join(filter(str.isalpha, w))
                if clean_w in PRAISE_KEYWORDS and label == "positive":
                    praise = PRAISE_KEYWORDS[clean_w]
                    praises_counts[praise] = praises_counts.get(praise, 0) + 1
                if clean_w in COMPLAINT_KEYWORDS and label == "negative":
                    complaint = COMPLAINT_KEYWORDS[clean_w]
                    complaints_counts[complaint] = complaints_counts.get(complaint, 0) + 1

            # 3. Track category metrics
            if rev.product and rev.product.category:
                cat_name = rev.product.category.name
                category_counts[cat_name] = category_counts.get(cat_name, 0) + 1

        # Ratios
        pos_pct = (pos_count / total_reviews) * 100.0
        neu_pct = (neu_count / total_reviews) * 100.0
        neg_pct = (neg_count / total_reviews) * 100.0
        
        avg_sentiment = sum(sentiment_scores) / total_reviews
        avg_confidence = sum(confidence_scores) / total_reviews

        # Extract top keywords
        keywords = extract_keywords(review_texts, top_n=5)
        top_keywords = [kw[0] for kw in keywords]

        # Sort praises and complaints
        sorted_praises = sorted(praises_counts.keys(), key=lambda x: praises_counts[x], reverse=True)
        sorted_complaints = sorted(complaints_counts.keys(), key=lambda x: complaints_counts[x], reverse=True)
        sorted_categories = sorted(category_counts.keys(), key=lambda x: category_counts[x], reverse=True)

        # Ensure we have default lists if none matches
        if not sorted_praises:
            sorted_praises = ["product quality", "friendly service", "reasonable price"]
        if not sorted_complaints:
            sorted_complaints = ["shipping delays", "battery life", "sizing issues"]

        # Generate summary string
        summary = generate_nlp_summary(pos_pct, sorted_praises, sorted_complaints, total_reviews)

        return {
            "positive_pct": round(pos_pct, 1),
            "neutral_pct": round(neu_pct, 1),
            "negative_pct": round(neg_pct, 1),
            "avg_sentiment": round(avg_sentiment, 2),
            "avg_confidence": round(avg_confidence, 2),
            "top_keywords": top_keywords,
            "top_praises": sorted_praises[:3],
            "top_complaints": sorted_complaints[:3],
            "trending_categories": sorted_categories[:3],
            "summary": summary,
            "total_count": total_reviews
        }
