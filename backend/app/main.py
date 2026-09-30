"""
Entry point cho backend API.
TODO: khởi tạo FastAPI app, include router từ app/api/
"""

from fastapi import FastAPI
from backend.app.api import forecasts, prices
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Agri Price Forecast API")


# CORS: cho phép Frontend (chạy port khác) gọi API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],      # Dev: cho phép mọi origin. Production: nên giới hạn cụ thể.
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



# Đăng ký các router
app.include_router(prices.router)
app.include_router(forecasts.router)



@app.get("/health")
def health_check():
    return {"status": "ok"}
