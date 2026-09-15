
import sys
from pathlib import Path

import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[2]
sys.path.append(str(BASE_DIR / "backend"))

from app.db.session import SessionLocal
from app.models.tables import Product, MarketPrice

CRAWLER_FILES = [
    {
        "path": BASE_DIR / "data" / "raw" / "rice_price_vietnambiz.csv",
        "crop_type": "rice",
        "unit": "VND/kg",
    },
    {
        "path": BASE_DIR / "data" / "raw" / "pepper_price_vietnambiz.csv",
        "crop_type": "pepper",
        "unit": "VND/kg",
    },
    {
        "path": BASE_DIR / "data" / "raw" / "coffee_price_vietnambiz.csv",
        "crop_type": "coffee",
        "unit": "VND/kg",
    },
]


def get_or_create_product(session, crop_type: str, category: str, unit: str) -> Product:
    """Tìm product đã có (theo crop_type + category), nếu chưa có thì tạo mới."""
    product = (
        session.query(Product)
        .filter_by(crop_type=crop_type, category=category)
        .first()
    )
    if product is None:
        product = Product(crop_type=crop_type, category=category, unit=unit)
        session.add(product)
        session.flush()
    return product


def load_file(session, file_info: dict):
    path = file_info["path"]
    if not path.exists():
        print(f"  Bỏ qua - không tìm thấy file: {path}")
        return 0, 0

    df = pd.read_csv(path)
    new_count = 0
    skip_count = 0

    for _, row in df.iterrows():
        category = str(row["category"]).strip()
        product = get_or_create_product(
            session, file_info["crop_type"], category, file_info["unit"]
        )

        existing = (
            session.query(MarketPrice)
            .filter_by(
                product_id=product.id,
                price_date=row["price_date"],
                source=row["source"],
            )
            .first()
        )
        if existing:
            skip_count += 1
            continue

        price = MarketPrice(
            product_id=product.id,
            price_date=row["price_date"],
            price_min=row["price_min"] if pd.notna(row["price_min"]) else None,
            price_max=row["price_max"] if pd.notna(row["price_max"]) else None,
            source=row["source"],
        )
        session.add(price)
        new_count += 1

    return new_count, skip_count


def main():
    session = SessionLocal()
    try:
        total_new = 0
        total_skip = 0
        for file_info in CRAWLER_FILES:
            print(f"Đang nạp: {file_info['path'].name}")
            new_count, skip_count = load_file(session, file_info)
            print(f"  -> {new_count} dòng mới, {skip_count} dòng đã có (bỏ qua)")
            total_new += new_count
            total_skip += skip_count

        session.commit()
        print(f"\nHoàn tất. Tổng: {total_new} dòng mới, {total_skip} dòng đã tồn tại.")
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


if __name__ == "__main__":
    main()