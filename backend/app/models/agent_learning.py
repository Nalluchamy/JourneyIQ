import datetime
from sqlalchemy import ForeignKey, DateTime, Float, Integer, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.db.base_class import BaseModel


class AgentLearning(BaseModel):
    """AgentLearning DB Model.
    Stores dynamic business performance outcomes pre- and post-action execution.
    """
    __tablename__ = "agentlearning"

    action_id: Mapped[int] = mapped_column(ForeignKey("agentaction.id", ondelete="CASCADE"), nullable=False, index=True)
    revenue_before: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    revenue_after: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    conversion_before: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    conversion_after: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    roi: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    success: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    execution_time_ms: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationship
    action: Mapped["AgentAction"] = relationship()
