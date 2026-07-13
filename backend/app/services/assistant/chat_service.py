import re
from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.assistant.intent_classifier import IntentClassifier
from app.services.assistant.retriever import ProductRetriever
from app.services.assistant.prompt_builder import PromptBuilder
from app.services.assistant.memory import assistant_memory
from app.services.assistant.fallback import get_fallback_reply
from app.services.assistant.providers.gemini import GeminiAIProvider
from app.services.assistant.providers.openai import OpenAIProvider
from app.services.assistant.providers.nvidia import NvidiaAIProvider
from app.services.assistant.providers.local import LocalAIProvider


class ChatAssistantService:
    """Coordinates conversational AI assistant workflows, memory, retrieval, and provider selection."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.classifier = IntentClassifier()
        self.retriever = ProductRetriever(db)
        self.prompt_builder = PromptBuilder()
        
        # Instantiate providers
        self.gemini_provider = GeminiAIProvider()
        self.openai_provider = OpenAIProvider()
        self.nvidia_provider = NvidiaAIProvider()
        self.local_provider = LocalAIProvider()

    async def process_message(
        self,
        message: str,
        session_id: str,
        user_id: int | None = None
    ) -> dict[str, Any]:
        """
        Handle conversational user messages.
        
        Steps:
        1. Classify prompt intent.
        2. Detect preferences to save to session memory.
        3. Retrieve real products from database.
        4. Route to AI provider based on configuration.
        5. Return formatted JSON response.
        """
        if not message or not message.strip():
            return {
                "reply": "Please say something! I am here to help you shop.",
                "products": [],
                "source": "local",
                "recommendation_engine": "None",
                "confidence": 1.0
            }

        # 1. Classify Intent
        intent = self.classifier.classify(message)

        # 2. Get and update session memory context
        context = assistant_memory.get_context(session_id)
        
        # Simple extraction of budget limits
        budget_match = re.search(r'\b(under|below|less than|budget)\b.*\b(rs|₹|\$)?(\d+[\d,]*)', message.lower())
        if budget_match:
            try:
                val = float(budget_match.group(3).replace(',', ''))
                context["budget"] = val
            except ValueError:
                pass

        # Update questions history
        assistant_memory.update_context(session_id, {"previous_questions": message})

        # 3. Retrieve matching items
        products = await self.retriever.retrieve_products(
            intent=intent,
            query=message,
            user_id=user_id,
            context=context
        )

        # Determine the primary recommendation engine label returned
        rec_label = "Database Query Search"
        if products:
            rec_label = products[0].get("recommendation_engine", "Database Query Search")

        # 4. Route generation to appropriate provider (Gemini -> OpenAI -> Local Fallback)
        reply = ""
        source = "local"
        confidence = 0.85

        prompt = self.prompt_builder.build_prompt(
            message=message,
            intent=intent,
            products=products,
            context=context
        )

        # Try Gemini
        if self.gemini_provider.is_configured():
            try:
                reply = await self.gemini_provider.generate_response(prompt)
                source = "gemini"
                confidence = 0.95
            except Exception:
                pass

        # Try OpenAI if Gemini failed or is unconfigured
        if not reply and self.openai_provider.is_configured():
            try:
                reply = await self.openai_provider.generate_response(prompt)
                source = "openai"
                confidence = 0.92
            except Exception:
                pass

        # Try NVIDIA if both Gemini and OpenAI failed or are unconfigured
        if not reply and self.nvidia_provider.is_configured():
            try:
                reply = await self.nvidia_provider.generate_response(prompt)
                source = "nvidia"
                confidence = 0.90
            except Exception:
                pass

        # Fallback to local template generator
        if not reply:
            try:
                reply = self.local_provider.generate_response(
                    message=message,
                    intent=intent,
                    products=products,
                    context=context
                )
                source = "local"
                confidence = 0.80
            except Exception:
                reply = get_fallback_reply(message)
                source = "local"
                confidence = 0.50

        return {
            "reply": reply,
            "products": products,
            "source": source,
            "recommendation_engine": rec_label,
            "confidence": confidence
        }
