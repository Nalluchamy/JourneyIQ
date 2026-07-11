import pytest
from app.services.nlp.sentiment import sentiment_analyzer
from app.services.nlp.keywords import extract_keywords
from app.services.nlp.summarizer import generate_nlp_summary


def test_sentiment_classification() -> None:
    """Verify correct sentiment tags and scores for standard reviews."""
    pos_res = sentiment_analyzer.analyze("This product is amazing and works perfectly! Highly recommend.")
    assert pos_res["label"] == "positive"
    assert pos_res["score"] > 0.0

    neg_res = sentiment_analyzer.analyze("Terrible product, it is broken and completely useless.")
    assert neg_res["label"] == "negative"
    assert neg_res["score"] < 0.0

    neu_res = sentiment_analyzer.analyze("It is an ordinary items. Standard functions, nothing special.")
    assert neu_res["label"] == "neutral"


def test_keyword_extraction() -> None:
    """Verify common stopwords are filtered out of extracted keywords."""
    texts = [
        "The battery life is really bad and slow.",
        "I love the battery, but the charger is slow. The charger works well."
    ]
    keywords = extract_keywords(texts, top_n=3)
    keywords_list = [kw[0] for kw in keywords]
    
    assert "battery" in keywords_list
    assert "charger" in keywords_list
    assert "the" not in keywords_list
    assert "but" not in keywords_list


def test_nlp_summary_generation() -> None:
    """Verify natural-language summaries construct correctly."""
    summary = generate_nlp_summary(
        positive_pct=85.0,
        praises=["delivery speed", "durability"],
        complaints=["high price"],
        total_reviews=10
    )
    
    assert "85% of customers" in summary
    assert "delivery speed" in summary
    assert "High price" in summary
