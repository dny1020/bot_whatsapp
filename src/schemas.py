"""
Pydantic Schemas for API Request/Response
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class SupportTicketResponse(BaseModel):
    """Support ticket response schema"""

    ticket_id: str
    issue_type: str
    status: str
    priority: str
    subject: Optional[str]
    created_at: datetime
    resolved_at: Optional[datetime]

    class Config:
        from_attributes = True


class UserResponse(BaseModel):
    """User response schema"""

    id: int
    phone: str
    name: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class TicketStats(BaseModel):
    """Ticket statistics schema"""

    total_tickets: int
    open_tickets: int
    in_progress_tickets: int
    resolved_tickets: int
    avg_resolution_time_hours: float


class MessageAnalytics(BaseModel):
    """Message analytics response schema"""

    period_days: int
    total_messages: int
    inbound_messages: int
    outbound_messages: int
