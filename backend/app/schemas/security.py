from datetime import datetime
from typing import Any

from pydantic import BaseModel


class SecurityAuditLogResponse(BaseModel):
    id: int
    user_id: int | None = None
    user_name: str | None = None
    action: str
    resource_type: str
    resource_id: str | None = None
    ip_address: str | None = None
    user_agent: str | None = None
    metadata: dict[str, Any]
    suspicious: bool = False
    created_at: datetime | None = None
