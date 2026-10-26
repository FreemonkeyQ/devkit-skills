from fastapi import FastAPI

from app import admin, orders

app = FastAPI(title="orders-api")
app.include_router(orders.router)
app.include_router(admin.router)
