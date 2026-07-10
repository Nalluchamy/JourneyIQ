import datetime
import uuid
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class EventRead(BaseModel):
    """Event response schema."""

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: int
    user_id: int | None = None
    session_id: uuid.UUID
    event_type: str
    page: str | None = None
    product_id: int | None = None
    metadata: dict[str, Any] | None = Field(
        None, validation_alias="metadata_", serialization_alias="metadata"
    )
    timestamp: datetime.datetime
