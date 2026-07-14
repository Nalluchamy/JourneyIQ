import datetime
from sqlalchemy import String, Text, DateTime, Float, Integer
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func
from app.db.base_class import BaseModel


class AgentAction(BaseModel):
    """AgentAction DB Model.
    Stores proposed, pending, and executed agent actions.
    """
    __tablename__ = "agentaction"

    action_type: Mapped[str] = mapped_column(String(50), nullable=False)  # e.g., RESTOCK, COUPON, NOTIFICATION, AD_CAMPAIGN, RETRAIN_MODEL
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    priority: Mapped[str] = mapped_column(String(20), default="LOW", nullable=False)  # LOW, MEDIUM, HIGH, CRITICAL
    status: Mapped[str] = mapped_column(String(20), default="PENDING", nullable=False)  # PENDING, APPROVED, REJECTED, COMPLETED, FAILED
    source_issue: Mapped[str] = mapped_column(String(255), nullable=False)  # e.g., "LOW_STOCK", "REVENUE_DROP"
    confidence: Mapped[float] = mapped_column(Float, default=0.90, nullable=False)
    reasoning: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Timing
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    approved_at: Mapped[datetime.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    executed_at: Mapped[datetime.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    start_time: Mapped[datetime.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    end_time: Mapped[datetime.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Execution stats
    execution_time_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    execution_result: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_by: Mapped[str] = mapped_column(String(100), default="Agent", server_default="Agent", nullable=False)
