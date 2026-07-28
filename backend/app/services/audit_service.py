from sqlalchemy.orm import Session

from app.models.audit import AuditLog


def log_action(
    db: Session,
    action: str,
    user_id: int | None = None,
    resource_type: str | None = None,
    resource_id: int | None = None,
    ip_address: str | None = None,
    details: dict | None = None,
) -> None:
    db.add(AuditLog(
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        ip_address=ip_address,
        details=details or {},
    ))
