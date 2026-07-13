import os
from typing import Any

try:
    import openai
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False


class NvidiaAIProvider:
    """Connects to NVIDIA API Catalog (NIMs) for conversational LLM execution."""

    def __init__(self) -> None:
        self.api_key = os.getenv("NVIDIA_API_KEY")
        if HAS_OPENAI and self.api_key:
            self.client = openai.OpenAI(
                base_url="https://integrate.api.nvidia.com/v1",
                api_key=self.api_key
            )
        else:
            self.client = None

    def is_configured(self) -> bool:
        """Returns True if the SDK is installed and the NVIDIA API key is supplied."""
        return HAS_OPENAI and self.client is not None

    async def generate_response(self, prompt: str) -> str:
        """
        Generate conversational responses using NVIDIA NIM models.
        """
        if not self.is_configured() or not self.client:
            raise ValueError("NVIDIA API is not configured or openai package is uninstalled.")

        try:
            # Using meta/llama-3.1-8b-instruct as the default high-performance chat model
            response = self.client.chat.completions.create(
                model="meta/llama-3.1-8b-instruct",
                messages=[
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=0.7
            )
            return response.choices[0].message.content or ""
        except Exception as e:
            raise RuntimeError(f"NVIDIA API Catalog invocation failed: {e}")
