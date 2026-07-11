def get_fallback_reply(message: str) -> str:
    """Return a polite fallback reply when services are temporarily unavailable."""
    return (
        "I'm currently having trouble connecting to my AI processor. "
        "However, I can still help you find items! You can browse our full product catalog "
        "by clicking on the **'Products'** navigation tab above or typing other keywords like 'laptop' or 'headphones'."
    )
