from fastapi import APIRouter

from app.db import SessionLocal
from app.models import Order

router = APIRouter()


@router.get("/admin/stats")
def stats():
    db = SessionLocal()
    try:
        return {"orders": db.query(Order).count()}
    finally:
        db.close()
