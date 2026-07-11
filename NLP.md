# JourneyIQ NLP Sentiment Intelligence

This document details the Natural Language Processing (NLP) sentiment analyzer, keyword extraction, and summarization pipeline integrated into JourneyIQ v1.1.

---

## 1. Sentiment Classification

The sentiment intelligence service analyzes text reviews to classify polarities:
- **Positive Sentiment (😊):** Triggered by highly supportive adjectives (e.g. *love, perfect, awesome*).
- **Neutral Sentiment (😐):** Calculated when matching counts are equal or fall within baseline scores.
- **Negative Sentiment (😞):** Triggered by critical verbs and expressions (e.g. *broken, slow, terrible*).

### HuggingFace Transformers Configuration
If the `transformers` library is installed and compatible weights are downloaded, the system automatically instantiates a pipeline utilizing the **DistilBERT** architecture:
- Model: `distilbert-base-uncased-finetuned-sst-2-english`
- Output: Standard sentiment classification with confidence score.

### Lexicon Rule-Based Fallback
If the transformer pipeline is unavailable (e.g. offline deploy or memory constraint), the analyzer falls back to a lexicon-based word density pattern matching positive and negative word occurrences to calculate normalized scores.

---

## 2. Keyword & Summary Extraction

1.  **Stopwords Filtering:** Common English function words (e.g. *the, that, this*) are dynamically stripped.
2.  **Frequency Counts:** Top keywords are extracted using Python's `collections.Counter` to identify trending talking points.
3.  **NLP Summarizer:** Compiles metrics to write an natural language paragraph output shown on the owner dashboard.
