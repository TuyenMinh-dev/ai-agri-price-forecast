"""
Lấy dữ liệu giá từ CSDL (bảng market_prices), tạo các feature phục vụ train
model: giá ngày hôm trước (lag), trung bình trượt, thứ trong tuần...
"""

import sys
from pathlib import Path

import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[2]
sys.path.append(str(BASE_DIR / "backend"))

from app.db.session import SessionLocal
from app.models.tables import Product, MarketPrice


def load_price_data(crop_type: str) -> pd.DataFrame:
    session = SessionLocal()
    try:
        rows = (
            session.query(
                MarketPrice.product_id,
                Product.category,
                MarketPrice.price_date,
                MarketPrice.price_min,
                MarketPrice.price_max,
            )
            .join(Product, Product.id == MarketPrice.product_id)
            .filter(Product.crop_type == crop_type)
            .order_by(Product.category, MarketPrice.price_date)
            .all()
        )
    finally:
        session.close()

    df = pd.DataFrame(
        rows,
        columns=["product_id", "category", "price_date", "price_min", "price_max"],
    )
    if df.empty:
        return df

    df["price_avg"] = df[["price_min", "price_max"]].mean(axis=1)
    df["price_date"] = pd.to_datetime(df["price_date"])

    df = (
        df.groupby(["product_id", "category", "price_date"], as_index=False)
        .agg(price_avg=("price_avg", "mean"))
    )

    return df.sort_values(["category", "price_date"]).reset_index(drop=True)


def build_features(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df

    result_frames = []
    for category, group in df.groupby("category"):
        group = group.sort_values("price_date").reset_index(drop=True)

        group["lag_1"] = group["price_avg"].shift(1)
        group["rolling_mean_3"] = (
            group["price_avg"].shift(1).rolling(window=3, min_periods=1).mean()
        )
        group["day_of_week"] = group["price_date"].dt.dayofweek
        group["target"] = group["price_avg"]

        result_frames.append(group)

    result = pd.concat(result_frames, ignore_index=True)
    result = result.dropna(subset=["lag_1"]).reset_index(drop=True)

    return result


if __name__ == "__main__":
    df = load_price_data(crop_type="rice")
    print(f"Số dòng dữ liệu giá gốc: {len(df)}")
    print(df.head(10))

    features = build_features(df)
    print(f"\nSố dòng sau khi tạo feature (có thể dự đoán được): {len(features)}")
    print(features.head(10))