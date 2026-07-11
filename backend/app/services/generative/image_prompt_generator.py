from typing import Any

class ImagePromptGeneratorService:
    """Generates descriptions and textual prompts for design systems and image generation models."""

    def generate_prompt(
        self,
        style: str,          # "minimalist" | "vibrant" | "classic" | "cyberpunk"
        product_context: str,  # e.g. "Nike Running Shoes"
        colors: list[str]     # e.g. ["purple", "cyan"]
    ) -> dict[str, Any]:
        """
        Generate detailed image generation prompts.
        """
        colors_str = " and ".join(colors) if colors else "vibrant gradient colors"
        
        if style == "cyberpunk":
            prompt = (
                f"Futuristic neon display of {product_context}, floating in a dark cyberpunk street. "
                f"Surrounded by glowing hologram elements and neon signs casting deep {colors_str} light. "
                f"Ultra-detailed 3D render, octane render style, premium product shot, 8k resolution."
            )
        elif style == "minimalist":
            prompt = (
                f"Clean minimalist studio shot of {product_context} centered on a smooth concrete pedestal. "
                f"Monochromatic backdrop with soft accent lighting in {colors_str}. "
                f"Elegant shadows, sleek product placement, soft focus, high-end commercial aesthetic."
            )
        elif style == "vibrant":
            prompt = (
                f"Dynamic, high-energy advertising shot of {product_context} splashing through liquid paint. "
                f"Vibrant swirls of {colors_str} exploding around the item. "
                f"High-speed action photograph, studio strobe lighting, extreme detail, sharp focus."
            )
        else:
            prompt = (
                f"Premium studio commercial photograph of {product_context} with an elegant studio layout. "
                f"Professional lighting highlighting product details, with subtle background gradients in {colors_str}. "
                f"8k resolution, photorealistic, commercial advertising quality."
            )

        return {
            "style": style,
            "product_context": product_context,
            "colors": colors,
            "generated_prompt": prompt
        }

image_prompt_generator = ImagePromptGeneratorService()
