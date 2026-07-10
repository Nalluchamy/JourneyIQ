import datetime

from sqlalchemy import DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, declared_attr, mapped_column


class Base(DeclarativeBase):
    """Base declarative class for all SQLAlchemy database models."""

    # Automatically generate __tablename__ based on class name in lowercase
    @declared_attr.directive
    def __tablename__(cls) -> str:
        return cls.__name__.lower()


class BaseModel(Base):
    """Reusable base model containing auto-incrementing ID and auto timestamps."""

    __abstract__ = True

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class SoftDeleteMixin:
    """Mixin to add soft deletion fields to models."""

    is_deleted: Mapped[bool] = mapped_column(default=False, server_default="false")
    deleted_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
