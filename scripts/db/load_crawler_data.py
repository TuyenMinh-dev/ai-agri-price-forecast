
from pathlib import Path
import sys

import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[2]
sys.path.append(str(BASE_DIR / "backend"))

from app.db.session import SessionLocal
from app.models.tables import MarketPrice, Product

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
    """Tim product da co (theo crop_type + category), neu chua co thi tao moi."""
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
        print(f"  Bo qua - khong tim thay file: {path}")
        return 0, 0

    df = pd.read_csv(path)
    new_count = 0
    skip_count = 0

    # Cache cac product da co trong DB theo category de tranh query lien tuc
    existing_products = {
        p.category: p
        for p in session.query(Product)
        .filter_by(crop_type=file_info["crop_type"])
        .all()
    }

    # Cache tat ca (product_id, price_date, source) da co vao memory set
    existing_records = set(
        (mp.product_id, str(mp.price_date), str(mp.source))
        for mp in session.query(
            MarketPrice.product_id, MarketPrice.price_date, MarketPrice.source
        ).all()
    )

    new_prices = []
    for _, row in df.iterrows():
        category = str(row["category"]).strip()
        if category in existing_products:
            product = existing_products[category]
        else:
            product = get_or_create_product(
                session, file_info["crop_type"], category, file_info["unit"]
            )
            existing_products[category] = product

        key = (product.id, str(row["price_date"]), str(row["source"]))
        if key in existing_records:
            skip_count += 1
            continue

        existing_records.add(key)
        price = MarketPrice(
            product_id=product.id,
            price_date=row["price_date"],
            price_min=row["price_min"] if pd.notna(row["price_min"]) else None,
            price_max=row["price_max"] if pd.notna(row["price_max"]) else None,
            source=row["source"],
        )
        new_prices.append(price)
        new_count += 1

    if new_prices:
        session.add_all(new_prices)
        session.flush()

    return new_count, skip_count


def main():
    session = SessionLocal()
    try:
        total_new = 0
        total_skip = 0
        for file_info in CRAWLER_FILES:
            print(f"Dang nap: {file_info['path'].name}")
            new_count, skip_count = load_file(session, file_info)
            print(f"  -> {new_count} dong moi, {skip_count} dong da co (bo qua)")
            total_new += new_count
            total_skip += skip_count

        session.commit()
        print(f"\nHoan tat. Tong: {total_new} dong moi, {total_skip} dong da ton tai.")
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


if __name__ == "__main__":
    main()
