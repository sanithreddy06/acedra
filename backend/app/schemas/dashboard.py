from typing import Any, Dict, List

from pydantic import BaseModel


class RoleDashboardResponse(BaseModel):
    role: str
    summary_cards: List[Dict[str, Any]]
    quick_stats: Dict[str, Any]
    recent_activity: List[Dict[str, Any]]
    details: Dict[str, Any]
