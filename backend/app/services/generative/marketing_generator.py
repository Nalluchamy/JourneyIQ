import os
from typing import Any
from app.services.assistant.providers.gemini import GeminiAIProvider
from app.services.assistant.providers.openai import OpenAIProvider

class MarketingGeneratorService:
    """Generates personalized, segment-aware marketing messages (Email, SMS, Push, Coupon)."""

    def __init__(self) -> None:
        self.gemini = GeminiAIProvider()
        self.openai = OpenAIProvider()

    async def generate_campaign(
        self,
        segment: str,
        campaign_type: str,  # "email" | "sms" | "push" | "coupon" | "social"
        product_context: str | None = None
    ) -> dict[str, Any]:
        """
        Generate marketing copies tailored to specific customer segments.
        """
        # Determine fallback local templates
        fallback_subject = f"Special Offer for our {segment} Shoppers!"
        fallback_body = ""
        
        seg_lower = segment.lower()
        if "vip" in seg_lower:
            fallback_subject = "★ JourneyIQ VIP: An Exclusive Invitation Awaits"
            fallback_body = "Hello valued shopper, as one of our most loyal VIP customers, we're thrilled to offer you an exclusive preview of our newest arrivals. Use coupon code **VIPPREMIER** for 15% off your next purchase!"
        elif "at-risk" in seg_lower or "slipping" in seg_lower:
            fallback_subject = "We Miss You! Here is 20% off your next order"
            fallback_body = "It's been a while since your last visit. We'd love to welcome you back with a special 20% coupon code: **WELCOMEBACK20** valid on all catalog products this week!"
        elif "new" in seg_lower:
            fallback_subject = "Welcome to JourneyIQ! Enjoy your first discount"
            fallback_body = "Thanks for registering an account! Use discount code **FIRSTORDER10** to get 10% off your checkout today."
        else:
            fallback_body = "Check out our latest trending products recommended just for you! Visit our online catalog to explore top deals."

        if campaign_type == "sms":
            fallback_body = f"{fallback_subject}: {fallback_body[:100]}..."
        elif campaign_type == "push":
            fallback_body = f"🔥 {fallback_subject} - Click to explore now!"

        prompt = f"""
You are an expert copywriter. Write a highly converting {campaign_type} campaign targeted to the "{segment}" customer segment.
Context or products to feature: {product_context or 'Latest store collections'}

CONSTRAINTS:
1. Subject line must be catchy.
2. Maintain a friendly and professional brand voice.
3. Keep it concise.

Format your response exactly as:
Subject: [Your Subject Line]
Body: [Your Campaign Body Copy]
"""
        
        reply = ""
        source = "local"
        
        # Try Gemini
        if self.gemini.is_configured():
            try:
                reply = await self.gemini.generate_response(prompt)
                source = "gemini"
            except Exception:
                pass
                
        # Try OpenAI
        if not reply and self.openai.is_configured():
            try:
                reply = await self.openai.generate_response(prompt)
                source = "openai"
            except Exception:
                pass

        # Parse reply
        subject = fallback_subject
        body = fallback_body
        
        if reply:
            try:
                if "subject:" in reply.lower() and "body:" in reply.lower():
                    parts = re.split(r'body:', reply, flags=re.IGNORECASE)
                    sub_part = parts[0]
                    body_part = parts[1]
                    
                    sub_match = re.search(r'subject:\s*(.*)', sub_part, re.IGNORECASE)
                    if sub_match:
                        subject = sub_match.group(1).strip()
                    body = body_part.strip()
                else:
                    body = reply.strip()
            except Exception:
                pass

        return {
            "subject": subject,
            "body": body,
            "segment": segment,
            "campaign_type": campaign_type,
            "source": source
        }

# Singleton instance
marketing_generator = MarketingGeneratorService()
import re
