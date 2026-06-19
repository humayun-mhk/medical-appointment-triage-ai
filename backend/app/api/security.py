from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.core.dependencies import require_admin
from app.db.database import get_db
from app.models import SecurityAuditLog, User
from app.schemas import SecurityAuditLogResponse
from app.security.pii_masking import mask_pii_payload
from app.security.rate_limit import admin_rate_limit

router = APIRouter(prefix="/admin/security-audit-logs", tags=["Security Audit"], dependencies=[Depends(require_admin), Depends(admin_rate_limit)])

SUSPICIOUS_ACTIONS = {"login_failure", "unauthorized_access", "rate_limit_exceeded", "forbidden_role_access"}


def _log_response(log: SecurityAuditLog) -> dict:
    return {
        "id": log.id,
        "user_id": log.user_id,
        "user_name": log.user.full_name if log.user else None,
        "action": log.action,
        "resource_type": log.resource_type,
        "resource_id": log.resource_id,
        "ip_address": log.ip_address,
        "user_agent": log.user_agent,
        "metadata": mask_pii_payload(log.log_metadata or {}),
        "suspicious": log.action in SUSPICIOUS_ACTIONS,
        "created_at": log.created_at,
    }


@router.get("", response_model=list[SecurityAuditLogResponse])
def security_audit_logs(
    action: str | None = Query(default=None),
    user_id: int | None = Query(default=None),
    resource_type: str | None = Query(default=None),
    ip_address: str | None = Query(default=None),
    selected_date: date | None = Query(default=None, alias="date"),
    db: Session = Depends(get_db),
):
    query = db.query(SecurityAuditLog).options(joinedload(SecurityAuditLog.user)).order_by(SecurityAuditLog.created_at.desc())
    if action:
        query = query.filter(SecurityAuditLog.action == action)
    if user_id:
        query = query.filter(SecurityAuditLog.user_id == user_id)
    if resource_type:
        query = query.filter(SecurityAuditLog.resource_type == resource_type)
    if ip_address:
        query = query.filter(SecurityAuditLog.ip_address == ip_address)
    if selected_date:
        query = query.filter(func.date(SecurityAuditLog.created_at) == selected_date)
    return [_log_response(log) for log in query.limit(500).all()]
