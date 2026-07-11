import re
from typing import Any


def sanitize_input(value: Any) -> Any:
    """Strips HTML script tags and raw HTML markup from input string values."""
    if not isinstance(value, str):
        return value

    # Remove script block sections
    clean = re.sub(r"<script.*?>.*?</script>", "", value, flags=re.IGNORECASE | re.DOTALL)
    # Remove any other HTML tag elements
    clean = re.sub(r"<[^>]*>", "", clean)

    return clean.strip()
