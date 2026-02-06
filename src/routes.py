"""
Rutas de la API
"""

from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc

from .db import get_db
from .models import User, SupportTicket, Message
from .models import SupportTicketResponse, UserResponse, TicketStats, MessageAnalytics

router = APIRouter()


# =============================================================================
# TICKETS
# =============================================================================

@router.get("/tickets", response_model=List[SupportTicketResponse])
async def list_tickets(
    status: Optional[str] = None,
    issue_type: Optional[str] = None,
    limit: int = Query(50, le=100),
    db: Session = Depends(get_db),
):
    """Listar tickets de soporte"""
    query = db.query(SupportTicket)

    if status:
        query = query.filter(SupportTicket.status == status)
    if issue_type:
        query = query.filter(SupportTicket.issue_type == issue_type)

    tickets = query.order_by(desc(SupportTicket.created_at)).limit(limit).all()
    return tickets


@router.get("/tickets/{ticket_id}", response_model=SupportTicketResponse)
async def get_ticket(ticket_id: str, db: Session = Depends(get_db)):
    """Obtener ticket por ID"""
    ticket = db.query(SupportTicket).filter(SupportTicket.ticket_id == ticket_id).first()

    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket no encontrado")

    return ticket


@router.get("/tickets/stats/summary", response_model=TicketStats)
async def get_ticket_stats(db: Session = Depends(get_db)):
    """Obtener estadísticas de tickets"""
    total = db.query(SupportTicket).count()
    open_count = db.query(SupportTicket).filter(SupportTicket.status == "open").count()
    in_progress = db.query(SupportTicket).filter(SupportTicket.status == "in_progress").count()
    resolved = db.query(SupportTicket).filter(SupportTicket.status.in_(["resolved", "closed"])).count()

    # Calcular tiempo promedio de resolución
    resolved_tickets = db.query(SupportTicket).filter(SupportTicket.resolved_at.isnot(None)).all()

    avg_hours = 0.0
    if resolved_tickets:
        total_hours = 0
        for ticket in resolved_tickets:
            diff = (ticket.resolved_at - ticket.created_at).total_seconds() / 3600
            total_hours += diff
        avg_hours = total_hours / len(resolved_tickets)

    return TicketStats(
        total_tickets=total,
        open_tickets=open_count,
        in_progress_tickets=in_progress,
        resolved_tickets=resolved,
        avg_resolution_time_hours=round(avg_hours, 2),
    )


# =============================================================================
# USUARIOS Y ANALYTICS
# =============================================================================

@router.get("/users", response_model=List[UserResponse])
async def list_users(limit: int = Query(50, le=100), db: Session = Depends(get_db)):
    """Listar usuarios"""
    users = db.query(User).order_by(desc(User.created_at)).limit(limit).all()
    return users


@router.get("/analytics/messages", response_model=MessageAnalytics)
async def get_message_analytics(
    days: int = Query(7, ge=1, le=30),
    db: Session = Depends(get_db)
):
    """Obtener analytics de mensajes"""
    since = datetime.utcnow() - timedelta(days=days)

    total = db.query(Message).filter(Message.created_at >= since).count()
    inbound = db.query(Message).filter(
        Message.created_at >= since,
        Message.direction == "inbound"
    ).count()
    outbound = db.query(Message).filter(
        Message.created_at >= since,
        Message.direction == "outbound"
    ).count()

    return MessageAnalytics(
        period_days=days,
        total_messages=total,
        inbound_messages=inbound,
        outbound_messages=outbound,
    )
