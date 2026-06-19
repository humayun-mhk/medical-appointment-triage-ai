from fastapi import Request
from sqlalchemy.orm import Session

from app.models import SecurityAuditLog
from app.security.pii_masking import mask_pii_payload


def get_client_ip(request: Request | None) -> str | None:
    if request is None:
        return None
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else None


def log_security_event(
    db: Session,
    *,
    action: str,
    resource_type: str,
    request: Request | None = None,
    user_id: int | None = None,
    resource_id: int | str | None = None,
    metadata: dict | None = None,
) -> SecurityAuditLog:
    log = SecurityAuditLog(
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=str(resource_id) if resource_id is not None else None,
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("user-agent")[:255] if request and request.headers.get("user-agent") else None,
        log_metadata=mask_pii_payload(metadata or {}),
    )
    db.add(log)
    db.flush()
    return log
