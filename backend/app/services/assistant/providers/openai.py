import os
from typing import Any

# Try importing openai package
try:
    import openai
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False


class OpenAIProvider:
    """Connects to OpenAI's API for prompt instruction execution."""

    def __init__(self) -> None:
        self.api_key = os.getenv("OPENAI_API_KEY")
        if HAS_OPENAI and self.api_key:
            self.client = openai.OpenAI(api_key=self.api_key)
        else:
            self.client = None

    def is_configured(self) -> bool:
        """Returns True if the SDK is installed and the API key is supplied."""
        return HAS_OPENAI and self.client is not None

    async def generate_response(self, prompt: str) -> str:
        """
        Generate conversational responses. Raises Exception if execution fails or unconfigured.
        """
        if not self.is_configured() or not self.client:
            raise ValueError("OpenAI API is not configured or openai package is uninstalled.")

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=0.7
            )
            return response.choices[0].message.content or ""
        except Exception as e:
            raise RuntimeError(f"OpenAI API invocation failed: {e}")
