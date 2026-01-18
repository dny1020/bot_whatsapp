"""
API Routes
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from .database import get_db
from .models import User, Order, Product, Message
from ..utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()


# Pydantic models
class OrderResponse(BaseModel):
    order_id: str
    status: str
    total: float
    created_at: datetime
    delivery_address: Optional[str]
    
    class Config:
        from_attributes = True


class UserResponse(BaseModel):
    id: int
    phone: str
    name: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


class ProductResponse(BaseModel):
    product_id: str
    name: str
    description: Optional[str]
    price: float
    category: str
    available: bool
    
    class Config:
        from_attributes = True


class OrderStats(BaseModel):
    total_orders: int
    pending_orders: int
    confirmed_orders: int
    delivered_orders: int
    total_revenue: float


# Orders endpoints
@router.get("/orders", response_model=List[OrderResponse])
async def list_orders(
    status: Optional[str] = None,
    limit: int = Query(50, le=100),
    db: Session = Depends(get_db)
):
    """List orders with optional status filter"""
    query = db.query(Order)
    
    if status:
        query = query.filter(Order.status == status)
    
    orders = query.order_by(desc(Order.created_at)).limit(limit).all()
    return orders


@router.get("/orders/{order_id}", response_model=OrderResponse)
async def get_order(order_id: str, db: Session = Depends(get_db)):
    """Get specific order by ID"""
    order = db.query(Order).filter(Order.order_id == order_id).first()
    
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    return order


@router.patch("/orders/{order_id}/status")
async def update_order_status(
    order_id: str,
    status: str,
    db: Session = Depends(get_db)
):
    """Update order status"""
    valid_statuses = ["pending", "confirmed", "preparing", "delivering", "delivered", "cancelled"]
    
    if status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {valid_statuses}")
    
    order = db.query(Order).filter(Order.order_id == order_id).first()
    
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    order.status = status
    
    if status == "delivered":
        order.delivered_at = datetime.utcnow()
    
    db.commit()
    db.refresh(order)
    
    logger.info("order_status_updated", order_id=order_id, new_status=status)
    
    return {"order_id": order_id, "status": status, "updated_at": datetime.utcnow()}


@router.get("/orders/stats/summary", response_model=OrderStats)
async def get_order_stats(db: Session = Depends(get_db)):
    """Get order statistics"""
    total_orders = db.query(Order).count()
    pending_orders = db.query(Order).filter(Order.status == "pending").count()
    confirmed_orders = db.query(Order).filter(Order.status.in_(["confirmed", "preparing", "delivering"])).count()
    delivered_orders = db.query(Order).filter(Order.status == "delivered").count()
    
    total_revenue = db.query(Order).filter(Order.status == "delivered").with_entities(
        db.func.sum(Order.total)
    ).scalar() or 0.0
    
    return OrderStats(
        total_orders=total_orders,
        pending_orders=pending_orders,
        confirmed_orders=confirmed_orders,
        delivered_orders=delivered_orders,
        total_revenue=total_revenue
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


@router.get("/users/{phone}/orders", response_model=List[OrderResponse])
async def get_user_orders(phone: str, db: Session = Depends(get_db)):
    """Get orders for specific user"""
    user = db.query(User).filter(User.phone == phone).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    orders = db.query(Order).filter(Order.user_id == user.id).order_by(desc(Order.created_at)).all()
    return orders


# Products endpoints
@router.get("/products", response_model=List[ProductResponse])
async def list_products(
    category: Optional[str] = None,
    available: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    """List products/menu items"""
    query = db.query(Product)
    
    if category:
        query = query.filter(Product.category == category)
    
    if available is not None:
        query = query.filter(Product.available == available)
    
    products = query.all()
    return products


@router.patch("/products/{product_id}/availability")
async def update_product_availability(
    product_id: str,
    available: bool,
    db: Session = Depends(get_db)
):
    """Update product availability"""
    product = db.query(Product).filter(Product.product_id == product_id).first()
    
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    product.available = available
    db.commit()
    db.refresh(product)
    
    logger.info("product_availability_updated", product_id=product_id, available=available)
    
    return {"product_id": product_id, "available": available}


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
