"""
API endpoints liên quan đến dự báo giá nông sản.
"""

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.tables import Forecast, Product
from app.schemas.price import ForecastOut

router = APIRouter(prefix="/api/forecasts", tags=["forecasts"])


@router.get("", response_model=list[ForecastOut])
def get_forecasts(
    product_id: Optional[int] = Query(None, description="Lọc theo ID sản phẩm"),
    crop_type: Optional[str] = Query(None, description="Lọc theo loại: rice/pepper/coffee"),
    model_name: Optional[str] = Query(None, description="Lọc theo tên model AI"),
    db: Session = Depends(get_db),
):
    """
    Lấy danh sách dự báo giá đã được model AI sinh ra.

    Có thể lọc theo product_id / crop_type / model_name.
    Nếu bảng forecasts rỗng → trả về mảng rỗng [].
    """
    stmt = (
        select(
            Forecast.id,
            Forecast.product_id,
            Product.crop_type,
            Product.category,
            Product.unit,
            Forecast.forecast_date,
            Forecast.predicted_price,
            Forecast.model_name,
        )
        .join(Product, Product.id == Forecast.product_id)
    )

    if product_id is not None:
        stmt = stmt.where(Forecast.product_id == product_id)
    if crop_type is not None:
        stmt = stmt.where(Product.crop_type == crop_type)
    if model_name is not None:
        stmt = stmt.where(Forecast.model_name == model_name)

    stmt = stmt.order_by(Product.id, Forecast.forecast_date)

    rows = db.execute(stmt).all()
    return rows