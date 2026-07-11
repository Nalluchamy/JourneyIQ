import random
from typing import Any

class LayoutGeneratorService:
    """Suggests alternative storefront UI layout configurations and design tokens for A/B testing."""

    def generate_layout(self, segment: str | None = None) -> dict[str, Any]:
        """
        Suggests layout styles (colors, cards, alignment) customized to segments or seasonal filters.
        """
        # Determine theme tokens dynamically based on segment
        seg_lower = (segment or "").lower()
        
        if "vip" in seg_lower:
            # Premium luxury gold theme
            hero_style = "split-screen"
            primary_color = "#d97706"  # Amber/Gold
            accent_color = "#1e293b"   # Slate
            button_style = "rounded-none border-2 border-amber-600"
            card_style = "luxury-minimalist"
            tagline = "Exclusive VIP Collections Curated For You"
        elif "at-risk" in seg_lower or "slipping" in seg_lower:
            # Urgent high conversion theme
            hero_style = "banner-full"
            primary_color = "#6366f1"  # Indigo
            accent_color = "#06b6d4"   # Cyan
            button_style = "rounded-full shadow-lg hover:shadow-indigo-500/30"
            card_style = "highlight-borders"
            tagline = "Welcome Back! Special Savings Inside"
        else:
            # Standard slate minimal layout
            hero_style = random.choice(["center", "split-screen", "banner-full"])
            primary_color = random.choice(["#4f46e5", "#0ea5e9", "#10b981"])
            accent_color = "#0f172a"
            button_style = random.choice(["rounded-xl", "rounded-md", "rounded-full"])
            card_style = "glassmorphic"
            tagline = "Optimize your shopping journey with real-time AI recommendations"

        return {
            "hero_layout": hero_style,
            "primary_color": primary_color,
            "accent_color": accent_color,
            "button_border": button_style,
            "product_card_style": card_style,
            "hero_title": tagline,
            "custom_tokens": {
                "font_family": "Outfit, sans-serif",
                "padding_class": "py-12 px-6",
                "glass_opacity": "bg-white/5 backdrop-blur-md"
            }
        }

layout_generator = LayoutGeneratorService()
