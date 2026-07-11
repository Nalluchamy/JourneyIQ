import re
from collections import Counter

# Common English stopwords to exclude
STOPWORDS = {
    "the", "a", "an", "and", "or", "but", "if", "because", "as", "what", "how", "why",
    "when", "where", "who", "whom", "this", "that", "these", "those", "i", "me", "my",
    "myself", "we", "our", "ours", "ourselves", "you", "your", "yours", "yourself",
    "yourselves", "he", "him", "his", "himself", "she", "her", "hers", "herself",
    "it", "its", "itself", "they", "them", "their", "theirs", "themselves", "is",
    "are", "was", "were", "be", "been", "being", "have", "has", "had", "having", "do",
    "does", "did", "doing", "to", "for", "with", "about", "against", "between",
    "into", "through", "during", "before", "after", "above", "below", "to", "from",
    "up", "down", "in", "out", "on", "off", "over", "under", "again", "further",
    "then", "once", "here", "there", "all", "any", "both", "each", "few", "more",
    "most", "other", "some", "such", "no", "nor", "not", "only", "own", "same", "so",
    "than", "too", "very", "s", "t", "can", "will", "just", "don", "should", "now",
    "product", "item", "buy", "bought", "get", "got", "really", "very", "great", "good"
}


def extract_keywords(texts: list[str], top_n: int = 10) -> list[tuple[str, int]]:
    """
    Extract the most frequent descriptive keywords from a list of strings, filtering stopwords.
    
    Args:
        texts: List of input strings.
        top_n: Number of top keywords to return.
        
    Returns:
        list of tuples: [(keyword, frequency), ...]
    """
    words = []
    for text in texts:
        if not text:
            continue
        # Clean text and split into words
        cleaned = text.lower().strip()
        tokens = re.findall(r'\b[a-z]{3,}\b', cleaned) # Minimum 3 letters
        filtered = [t for t in tokens if t not in STOPWORDS]
        words.extend(filtered)
        
    counter = Counter(words)
    return counter.most_common(top_n)
