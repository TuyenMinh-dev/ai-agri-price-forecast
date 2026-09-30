"""
API endpoints liên quan đến giá nông sản.
"""

from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.app.db.session import get_db
from backend.app.models.tables import MarketPrice, Product
from backend.app.schemas.price import LatestPriceOut, PriceHistoryOut

router = APIRouter(prefix="/api/prices", tags=["prices"])


@router.get("/latest", response_model=list[LatestPriceOut])
def get_latest_prices(db: Session = Depends(get_db)):
    """
    Lấy giá MỚI NHẤT của từng mặt hàng nông sản.

    Trả về 1 danh sách, mỗi phần tử là mặt hàng kèm giá mới nhất của nó.
    """
    # Subquery: tìm ngày giá mới nhất của mỗi product
    latest_date_subq = (
        select(
            MarketPrice.product_id,
            func.max(MarketPrice.price_date).label("max_date"),
        )
        .group_by(MarketPrice.product_id)
        .subquery()
    )

    # Query chính: join market_prices với subquery + products
    stmt = (
        select(
            Product.id.label("product_id"),
            Product.crop_type,
            Product.category,
            Product.unit,
            MarketPrice.price_date,
            MarketPrice.price_min,
            MarketPrice.price_max,
            MarketPrice.source,
        )
        .join(latest_date_subq, latest_date_subq.c.product_id == Product.id)
        .join(
            MarketPrice,
            (MarketPrice.product_id == latest_date_subq.c.product_id)
            & (MarketPrice.price_date == latest_date_subq.c.max_date),
        )
        .order_by(Product.id)
    )

    rows = db.execute(stmt).all()
    return rows


@router.get("/history", response_model=list[PriceHistoryOut])
def get_price_history(
    product_id: Optional[int] = Query(None, description="Lọc theo ID sản phẩm"),
    crop_type: Optional[str] = Query(None, description="Lọc theo loại: rice/pepper/coffee"),
    start_date: Optional[date] = Query(None, description="Từ ngày (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="Đến ngày (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
):
    """
    Lấy lịch sử giá, có thể lọc theo sản phẩm / loại / khoảng ngày.

    Kết quả được nhóm theo từng sản phẩm, mỗi sản phẩm có 1 list history.
    """
    # Query: lấy tất cả bản ghi giá khớp điều kiện
    stmt = (
        select(
            Product.id.label("product_id"),
            Product.crop_type,
            Product.category,
            Product.unit,
            MarketPrice.price_date,
            MarketPrice.price_min,
            MarketPrice.price_max,
            MarketPrice.source,
        )
        .join(MarketPrice, MarketPrice.product_id == Product.id)
        .order_by(Product.id, MarketPrice.price_date.desc())
    )

    # Áp dụng filter nếu có
    if product_id is not None:
        stmt = stmt.where(Product.id == product_id)
    if crop_type is not None:
        stmt = stmt.where(Product.crop_type == crop_type)
    if start_date is not None:
        stmt = stmt.where(MarketPrice.price_date >= start_date)
    if end_date is not None:
        stmt = stmt.where(MarketPrice.price_date <= end_date)

    rows = db.execute(stmt).all()

    # Nhóm kết quả theo product_id
    grouped: dict[int, dict] = {}
    for row in rows:
        pid = row.product_id
        if pid not in grouped:
            grouped[pid] = {
                "product_id": pid,
                "crop_type": row.crop_type,
                "category": row.category,
                "unit": row.unit,
                "history": [],
            }
        grouped[pid]["history"].append(
            {
                "price_date": row.price_date,
                "price_min": row.price_min,
                "price_max": row.price_max,
                "source": row.source,
            }
        )

    return list(grouped.values())