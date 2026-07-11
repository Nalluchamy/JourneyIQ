import os
from typing import Any

# Try importing google-generativeai package
try:
    import google.generativeai as genai
    HAS_GEMINI = True
except ImportError:
    HAS_GEMINI = False


class GeminiAIProvider:
    """Connects to Google's Gemini API for prompt instruction execution."""

    def __init__(self) -> None:
        self.api_key = os.getenv("GEMINI_API_KEY")
        if HAS_GEMINI and self.api_key:
            genai.configure(api_key=self.api_key)

    def is_configured(self) -> bool:
        """Returns True if the SDK is installed and the API key is supplied."""
        return HAS_GEMINI and bool(self.api_key)

    async def generate_response(self, prompt: str) -> str:
        """
        Generate conversational responses. Raises Exception if execution fails or unconfigured.
        """
        if not self.is_configured():
            raise ValueError("Gemini API is not configured or google-generativeai is uninstalled.")

        try:
            model = genai.GenerativeModel("gemini-1.5-flash")
            # Run in executor or call block
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            raise RuntimeError(f"Gemini API invocation failed: {e}")
