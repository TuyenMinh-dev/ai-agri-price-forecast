"""
Entry point cho backend API.
TODO: khởi tạo FastAPI app, include router từ app/api/
"""

from fastapi import FastAPI

app = FastAPI(title="Agri Price Forecast API")


@app.get("/health")
def health_check():
    return {"status": "ok"}
