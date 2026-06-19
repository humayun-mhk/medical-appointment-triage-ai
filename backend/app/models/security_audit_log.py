from sqlalchemy import Column, DateTime, ForeignKey, Index, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.database import Base


class SecurityAuditLog(Base):
    __tablename__ = "security_audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    action = Column(String(120), nullable=False, index=True)
    resource_type = Column(String(120), nullable=False, index=True)
    resource_id = Column(String(120), nullable=True, index=True)
    ip_address = Column(String(80), nullable=True, index=True)
    user_agent = Column(String(255), nullable=True)
    log_metadata = Column("metadata", JSONB, nullable=False, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User")

    __table_args__ = (
        Index("ix_security_audit_logs_action_created", "action", "created_at"),
        Index("ix_security_audit_logs_resource", "resource_type", "resource_id"),
    )
