"""
Pydantic schemas cho các API liên quan đến giá nông sản.

Mỗi class định nghĩa hình dạng JSON mà API sẽ trả về.
FastAPI dùng các class này để:
- Validate dữ liệu
- Tự sinh tài liệu Swagger UI ở /docs
"""

from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class ProductOut(BaseModel):
    """Thông tin cơ bản của 1 mặt hàng nông sản."""
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())

    id: int
    crop_type: str
    category: str
    unit: str


class LatestPriceOut(BaseModel):
    """Giá mới nhất của 1 mặt hàng."""
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())

    product_id: int
    crop_type: str
    category: str
    unit: str
    price_date: date
    price_min: Decimal
    price_max: Decimal
    source: str | None = None


class PriceHistoryItem(BaseModel):
    """1 bản ghi giá trong lịch sử."""
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())

    price_date: date
    price_min: Decimal
    price_max: Decimal
    source: str | None = None


class PriceHistoryOut(BaseModel):
    """Lịch sử giá của 1 mặt hàng."""
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())

    product_id: int
    crop_type: str
    category: str
    unit: str
    history: list[PriceHistoryItem]


class ForecastOut(BaseModel):
    """1 bản ghi dự báo giá do model AI sinh ra."""
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())

    id: int
    product_id: int
    crop_type: str
    category: str
    unit: str
    forecast_date: date
    predicted_price: Decimal
    model_name: str