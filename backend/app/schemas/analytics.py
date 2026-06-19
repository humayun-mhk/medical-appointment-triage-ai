from typing import Any

from pydantic import BaseModel


class AnalyticsResponse(BaseModel):
    data: dict[str, Any] | list[dict[str, Any]]
