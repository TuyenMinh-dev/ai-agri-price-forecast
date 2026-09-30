"""
API endpoints liên quan đến giá nông sản.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.app.db.session import get_db
from backend.app.models.tables import MarketPrice, Product
from backend.app.schemas.price import LatestPriceOut

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