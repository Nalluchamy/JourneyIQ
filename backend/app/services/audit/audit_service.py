from typing import Any
import structlog
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.audit_log import AuditLog

logger = structlog.get_logger()


async def log_audit_event(
    db: AsyncSession,
    event_type: str,
    user_id: int | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
    details: dict[str, Any] | None = None,
) -> None:
    """Inserts a security audit log record asynchronously into the database."""
    try:
        audit = AuditLog(
            user_id=user_id,
            event_type=event_type,
            ip_address=ip_address,
            user_agent=user_agent,
            details=details
        )
        db.add(audit)
        await db.commit()
    except Exception as e:
        logger.error(
            "Failed to write security audit log entry",
            event_type=event_type,
            user_id=user_id,
            error=str(e)
        )
