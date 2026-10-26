from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Order
from app.timefmt import format_dt

router = APIRouter()


@router.get("/orders")
def list_orders(
    status: str | None = None,
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    query = db.query(Order).order_by(Order.created_at.desc()).offset(offset).limit(limit)
    if status:
        query = query.filter(Order.status == status)
    orders = query.all()
    return [
        {
            "id": order.id,
            "customer": order.customer_name,
            "status": order.status,
            "item_count": len(order.items),
            "created_at": format_dt(order.created_at),
        }
        for order in orders
    ]
