from typing import Annotated, Any
from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.response import APIResponse
from app.services.generative.marketing_generator import marketing_generator
from app.services.generative.layout_generator import layout_generator
from app.services.generative.customer_journey_simulator import journey_simulator
from app.services.generative.image_prompt_generator import image_prompt_generator

router = APIRouter()

class MarketingRequest(BaseModel):
    segment: str = Field(..., description="Target user segment")
    campaign_type: str = Field("email", description="email | sms | push | coupon | social")
    product_context: str | None = Field(None, description="Featured items description")

class LayoutRequest(BaseModel):
    segment: str | None = Field(None, description="Target segment")

class JourneyRequest(BaseModel):
    segment: str = Field(..., description="Target segment for checkout simulation")

class ImagePromptRequest(BaseModel):
    style: str = Field(..., description="minimalist | vibrant | classic | cyberpunk")
    product_context: str = Field(..., description="Product description")
    colors: list[str] = Field(default_factory=list, description="Theme colors list")


@router.post("/marketing", response_model=APIResponse[dict[str, Any]])
async def generate_marketing_campaign(body: MarketingRequest) -> Any:
    """Generate segment-optimized email/SMS promotion copies."""
    res = await marketing_generator.generate_campaign(
        segment=body.segment,
        campaign_type=body.campaign_type,
        product_context=body.product_context
    )
    return APIResponse(success=True, message="Marketing campaign generated.", data=res)


@router.post("/layout", response_model=APIResponse[dict[str, Any]])
async def generate_storefront_layout(body: LayoutRequest) -> Any:
    """Recommend styling custom properties for A/B tests."""
    res = layout_generator.generate_layout(segment=body.segment)
    return APIResponse(success=True, message="Layout recommendation generated.", data=res)


@router.post("/journey", response_model=APIResponse[dict[str, Any]])
async def generate_journey_simulation(body: JourneyRequest) -> Any:
    """Simulate customer checkout paths and conversion lifts."""
    res = journey_simulator.simulate_journey(segment=body.segment)
    return APIResponse(success=True, message="Journey simulation completed.", data=res)


@router.post("/image-prompt", response_model=APIResponse[dict[str, Any]])
async def generate_image_prompt(body: ImagePromptRequest) -> Any:
    """Generate image prompt text configs for design assets."""
    res = image_prompt_generator.generate_prompt(
        style=body.style,
        product_context=body.product_context,
        colors=body.colors
    )
    return APIResponse(success=True, message="Image prompt generated.", data=res)
