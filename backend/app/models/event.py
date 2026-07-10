import datetime
import uuid
from typing import TYPE_CHECKING, Any

from sqlalchemy import JSON, DateTime, ForeignKey, Index, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import BaseModel

if TYPE_CHECKING:
    from app.models.product import Product
    from app.models.user import User


class Event(BaseModel):
    """Event Tracker DB Model."""

    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("user.id", ondelete="SET NULL"), nullable=True, index=True
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), nullable=False, index=True
    )
    event_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    page: Mapped[str | None] = mapped_column(String(255), nullable=True)
    product_id: Mapped[int | None] = mapped_column(
        ForeignKey("product.id", ondelete="SET NULL"), nullable=True, index=True
    )
    metadata_: Mapped[dict[str, Any] | None] = mapped_column(
        "metadata", JSON, nullable=True
    )
    timestamp: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    user: Mapped["User | None"] = relationship(back_populates="events")
    product: Mapped["Product | None"] = relationship()


# Composite index on (user_id, timestamp) for rapid cohort chronological analysis
Index("idx_event_user_timestamp", Event.user_id, Event.timestamp)
