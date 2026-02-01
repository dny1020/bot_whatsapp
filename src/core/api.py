"""
API Routes
Consolidated from src/backend/routes.py
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from .database import get_db, User, SupportTicket, Message
from .config import get_logger

logger = get_logger(__name__)
router = APIRouter()

# ============================================================================
# SCHEMAS
# ============================================================================

class SupportTicketResponse(BaseModel):
    ticket_id: str
    issue_type: str
    status: str
    priority: str
    subject: Optional[str]
    created_at: datetime
    resolved_at: Optional[datetime]
    class Config: from_attributes = True

class UserResponse(BaseModel):
    id: int
    phone: str
    name: Optional[str]
    created_at: datetime
    class Config: from_attributes = True

class TicketStats(BaseModel):
    total_tickets: int
    open_tickets: int
    in_progress_tickets: int
    resolved_tickets: int
    avg_resolution_time_hours: float

# ============================================================================
# TICKETS
# ============================================================================

@router.get("/tickets", response_model=List[SupportTicketResponse])
async def list_tickets(status: str = None, issue_type: str = None, limit: int = Query(50, le=100), db: Session = Depends(get_db)):
    query = db.query(SupportTicket)
    if status: query = query.filter(SupportTicket.status == status)
    if issue_type: query = query.filter(SupportTicket.issue_type == issue_type)
    return query.order_by(desc(SupportTicket.created_at)).limit(limit).all()

@router.get("/tickets/{ticket_id}", response_model=SupportTicketResponse)
async def get_ticket(ticket_id: str, db: Session = Depends(get_db)):
    ticket = db.query(SupportTicket).filter(SupportTicket.ticket_id == ticket_id).first()
    if not ticket: raise HTTPException(status_code=404, detail="Ticket not found")
    return ticket

@router.get("/tickets/stats/summary", response_model=TicketStats)
async def get_ticket_stats(db: Session = Depends(get_db)):
    total = db.query(SupportTicket).count()
    open_t = db.query(SupportTicket).filter(SupportTicket.status == "open").count()
    prog = db.query(SupportTicket).filter(SupportTicket.status == "in_progress").count()
    res = db.query(SupportTicket).filter(SupportTicket.status.in_(["resolved", "closed"])).count()
    
    resolved = db.query(SupportTicket).filter(SupportTicket.resolved_at.isnot(None)).all()
    avg_hours = 0.0
    if resolved:
        avg_hours = sum([(t.resolved_at - t.created_at).total_seconds() / 3600 for t in resolved]) / len(resolved)
    
    return TicketStats(total_tickets=total, open_tickets=open_t, in_progress_tickets=prog, resolved_tickets=res, avg_resolution_time_hours=round(avg_hours, 2))

# ============================================================================
# USERS & ANALYTICS
# ============================================================================

@router.get("/users", response_model=List[UserResponse])
async def list_users(limit: int = Query(50, le=100), db: Session = Depends(get_db)):
    return db.query(User).order_by(desc(User.created_at)).limit(limit).all()

@router.get("/analytics/messages")
async def get_message_analytics(days: int = Query(7, ge=1, le=30), db: Session = Depends(get_db)):
    from datetime import timedelta
    since = datetime.utcnow() - timedelta(days=days)
    total = db.query(Message).filter(Message.created_at >= since).count()
    inbound = db.query(Message).filter(Message.created_at >= since, Message.direction == "inbound").count()
    outbound = db.query(Message).filter(Message.created_at >= since, Message.direction == "outbound").count()
    return {"period_days": days, "total_messages": total, "inbound_messages": inbound, "outbound_messages": outbound}
