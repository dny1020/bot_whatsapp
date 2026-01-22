"""
API Routes - ISP Support Chatbot
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from .database import get_db
from .models import User, SupportTicket, Message
from ..utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()


# Pydantic models
class SupportTicketResponse(BaseModel):
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
    id: int
    phone: str
    name: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


class TicketStats(BaseModel):
    total_tickets: int
    open_tickets: int
    in_progress_tickets: int
    resolved_tickets: int
    avg_resolution_time_hours: float


# Support Tickets endpoints
@router.get("/tickets", response_model=List[SupportTicketResponse])
async def list_tickets(
    status: Optional[str] = None,
    issue_type: Optional[str] = None,
    limit: int = Query(50, le=100),
    db: Session = Depends(get_db)
):
    """List support tickets with optional filters"""
    query = db.query(SupportTicket)
    
    if status:
        query = query.filter(SupportTicket.status == status)
    
    if issue_type:
        query = query.filter(SupportTicket.issue_type == issue_type)
    
    tickets = query.order_by(desc(SupportTicket.created_at)).limit(limit).all()
    return tickets


@router.get("/tickets/{ticket_id}", response_model=SupportTicketResponse)
async def get_ticket(ticket_id: str, db: Session = Depends(get_db)):
    """Get specific support ticket by ID"""
    ticket = db.query(SupportTicket).filter(SupportTicket.ticket_id == ticket_id).first()
    
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    return ticket


@router.patch("/tickets/{ticket_id}/status")
async def update_ticket_status(
    ticket_id: str,
    status: str,
    resolution: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Update support ticket status"""
    valid_statuses = ["open", "in_progress", "resolved", "closed"]
    
    if status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {valid_statuses}")
    
    ticket = db.query(SupportTicket).filter(SupportTicket.ticket_id == ticket_id).first()
    
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    ticket.status = status
    
    if status == "resolved" and resolution:
        ticket.resolution = resolution
        ticket.resolved_at = datetime.utcnow()
    
    db.commit()
    db.refresh(ticket)
    
    logger.info("ticket_status_updated", ticket_id=ticket_id, new_status=status)
    
    return {"ticket_id": ticket_id, "status": status, "updated_at": datetime.utcnow()}


@router.get("/tickets/stats/summary", response_model=TicketStats)
async def get_ticket_stats(db: Session = Depends(get_db)):
    """Get support ticket statistics"""
    from datetime import timedelta
    
    total_tickets = db.query(SupportTicket).count()
    open_tickets = db.query(SupportTicket).filter(SupportTicket.status == "open").count()
    in_progress_tickets = db.query(SupportTicket).filter(SupportTicket.status == "in_progress").count()
    resolved_tickets = db.query(SupportTicket).filter(SupportTicket.status.in_(["resolved", "closed"])).count()
    
    # Calculate average resolution time
    resolved_with_time = db.query(SupportTicket).filter(
        SupportTicket.resolved_at.isnot(None)
    ).all()
    
    avg_hours = 0.0
    if resolved_with_time:
        total_hours = sum([
            (ticket.resolved_at - ticket.created_at).total_seconds() / 3600
            for ticket in resolved_with_time
        ])
        avg_hours = total_hours / len(resolved_with_time)
    
    return TicketStats(
        total_tickets=total_tickets,
        open_tickets=open_tickets,
        in_progress_tickets=in_progress_tickets,
        resolved_tickets=resolved_tickets,
        avg_resolution_time_hours=round(avg_hours, 2)
    )


# Users endpoints
@router.get("/users", response_model=List[UserResponse])
async def list_users(
    limit: int = Query(50, le=100),
    db: Session = Depends(get_db)
):
    """List users"""
    users = db.query(User).order_by(desc(User.created_at)).limit(limit).all()
    return users


@router.get("/users/{phone}/tickets", response_model=List[SupportTicketResponse])
async def get_user_tickets(phone: str, db: Session = Depends(get_db)):
    """Get support tickets for specific user"""
    user = db.query(User).filter(User.phone == phone).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    tickets = db.query(SupportTicket).filter(SupportTicket.user_id == user.id).order_by(desc(SupportTicket.created_at)).all()
    return tickets


# Analytics endpoint
@router.get("/analytics/messages")
async def get_message_analytics(
    days: int = Query(7, ge=1, le=30),
    db: Session = Depends(get_db)
):
    """Get message analytics"""
    from datetime import timedelta
    
    since = datetime.utcnow() - timedelta(days=days)
    
    total_messages = db.query(Message).filter(Message.created_at >= since).count()
    inbound_messages = db.query(Message).filter(
        Message.created_at >= since,
        Message.direction == "inbound"
    ).count()
    outbound_messages = db.query(Message).filter(
        Message.created_at >= since,
        Message.direction == "outbound"
    ).count()
    
    return {
        "period_days": days,
        "total_messages": total_messages,
        "inbound_messages": inbound_messages,
        "outbound_messages": outbound_messages
    }
