"""
API Routes
"""

from datetime import datetime, timedelta
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc

from .db import get_db
from .models import User, SupportTicket, Message
from .schemas import SupportTicketResponse, UserResponse, TicketStats, MessageAnalytics
from .settings import get_logger

logger = get_logger(__name__)
router = APIRouter()


# ============================================================================
# TICKETS
# ============================================================================


@router.get("/tickets", response_model=List[SupportTicketResponse])
async def list_tickets(
    status: str | None = None,
    issue_type: str | None = None,
    limit: int = Query(50, le=100),
    db: Session = Depends(get_db),
):
    """List support tickets with optional filters"""
    query = db.query(SupportTicket)

    if status:
        query = query.filter(SupportTicket.status == status)
    if issue_type:
        query = query.filter(SupportTicket.issue_type == issue_type)

    return query.order_by(desc(SupportTicket.created_at)).limit(limit).all()


@router.get("/tickets/{ticket_id}", response_model=SupportTicketResponse)
async def get_ticket(ticket_id: str, db: Session = Depends(get_db)):
    """Get a specific ticket by ID"""
    ticket = (
        db.query(SupportTicket).filter(SupportTicket.ticket_id == ticket_id).first()
    )

    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    return ticket


@router.get("/tickets/stats/summary", response_model=TicketStats)
async def get_ticket_stats(db: Session = Depends(get_db)):
    """Get ticket statistics summary"""
    total = db.query(SupportTicket).count()
    open_t = db.query(SupportTicket).filter(SupportTicket.status == "open").count()
    prog = db.query(SupportTicket).filter(SupportTicket.status == "in_progress").count()
    res = (
        db.query(SupportTicket)
        .filter(SupportTicket.status.in_(["resolved", "closed"]))
        .count()
    )

    # Calculate average resolution time
    resolved = (
        db.query(SupportTicket).filter(SupportTicket.resolved_at.isnot(None)).all()
    )

    avg_hours = 0.0
    if resolved:
        total_hours = sum(
            [(t.resolved_at - t.created_at).total_seconds() / 3600 for t in resolved]
        )
        avg_hours = total_hours / len(resolved)

    return TicketStats(
        total_tickets=total,
        open_tickets=open_t,
        in_progress_tickets=prog,
        resolved_tickets=res,
        avg_resolution_time_hours=round(avg_hours, 2),
    )


# ============================================================================
# USERS & ANALYTICS
# ============================================================================


@router.get("/users", response_model=List[UserResponse])
async def list_users(limit: int = Query(50, le=100), db: Session = Depends(get_db)):
    """List users"""
    return db.query(User).order_by(desc(User.created_at)).limit(limit).all()


@router.get("/analytics/messages", response_model=MessageAnalytics)
async def get_message_analytics(
    days: int = Query(7, ge=1, le=30), db: Session = Depends(get_db)
):
    """Get message analytics for specified period"""
    since = datetime.utcnow() - timedelta(days=days)

    total = db.query(Message).filter(Message.created_at >= since).count()
    inbound = (
        db.query(Message)
        .filter(Message.created_at >= since, Message.direction == "inbound")
        .count()
    )
    outbound = (
        db.query(Message)
        .filter(Message.created_at >= since, Message.direction == "outbound")
        .count()
    )

    return MessageAnalytics(
        period_days=days,
        total_messages=total,
        inbound_messages=inbound,
        outbound_messages=outbound,
    )
