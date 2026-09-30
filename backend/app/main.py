"""
Entry point cho backend API.
TODO: khởi tạo FastAPI app, include router từ app/api/
"""

from fastapi import FastAPI
from backend.app.api import forecasts, prices

app = FastAPI(title="Agri Price Forecast API")

# Đăng ký các router
app.include_router(prices.router)


app.include_router(forecasts.router)



@app.get("/health")
def health_check():
    return {"status": "ok"}
