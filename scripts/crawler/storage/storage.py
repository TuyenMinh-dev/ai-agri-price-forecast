"""Lưu dữ liệu giá đã crawl vào CSV, tự lọc trùng theo (price_date, category)."""

import csv
from pathlib import Path

CSV_COLUMNS = ["price_date", "category", "price_min", "price_max", "source", "crawled_at"]


def load_existing_keys(path: Path) -> set:
    keys = set()
    if not path.exists():
        return keys
    with open(path, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            keys.add((row["price_date"], row["category"]))
    return keys


def append_new_rows(path: Path, new_rows: list[dict]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    existing_keys = load_existing_keys(path)

    rows_to_write = [
        r for r in new_rows if (r["price_date"], r["category"]) not in existing_keys
    ]

    file_exists = path.exists()
    with open(path, "a", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        if not file_exists:
            writer.writeheader()
        for row in rows_to_write:
            writer.writerow(row)

    return len(rows_to_write)