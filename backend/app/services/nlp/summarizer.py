def generate_nlp_summary(
    positive_pct: float,
    praises: list[str],
    complaints: list[str],
    total_reviews: int
) -> str:
    """
    Generate a human-readable text summary of customer reviews and satisfaction.
    
    Example output:
        "84% of customers are satisfied. Most customers praise delivery speed and product quality.
         Battery life is the most common complaint."
    """
    if total_reviews == 0:
        return "No reviews have been posted for this period yet."

    summary = f"{round(positive_pct)}% of customers are satisfied based on recent storefront reviews. "

    if praises:
        summary += f"Most customers praise {', '.join(praises[:2])}. "
    else:
        summary += "Customers highlight overall standard performance. "

    if complaints:
        summary += f"{complaints[0].capitalize()} is the most common complaint mentioned in critical feedback."
    else:
        summary += "There are no significant complaints reported in recent feedback."

    return summary
