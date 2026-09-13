"""Crawler giá lúa gạo từ vietnambiz.vn/gia-gao.html"""

import datetime
import re
import sys
from pathlib import Path

import requests
from bs4 import BeautifulSoup

# Trỏ tới thư mục storage/ nằm cùng cấp để import được storage.py
sys.path.append(str(Path(__file__).resolve().parent.parent / "storage"))
from storage import append_new_rows

URL = "https://vietnambiz.vn/gia-gao.html"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    )
}
# parents[3]: rice/crawl_rice.py -> rice -> crawler -> scripts -> gốc project
BASE_DIR = Path(__file__).resolve().parents[3]
OUTPUT_FILE = BASE_DIR / "data" / "raw" / "rice_price_vietnambiz.csv"


def fetch_html() -> str:
    resp = requests.get(URL, headers=HEADERS, timeout=15)
    resp.raise_for_status()
    resp.encoding = "utf-8"
    return resp.text


def parse_price_table(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "lxml")

    tables = soup.find_all("table")
    price_table = None
    for t in tables:
        if "Chủng loại" in t.get_text(" ", strip=True):
            price_table = t
            break

    if price_table is None:
        raise ValueError("Không tìm thấy bảng giá — trang có thể đã đổi cấu trúc.")

    rows = price_table.find_all("tr")
    if not rows:
        return []

    header_cells = [c.get_text(strip=True) for c in rows[0].find_all(["th", "td"])]
    date_columns = header_cells[1:]

    current_year = datetime.date.today().year
    crawled_at = datetime.datetime.now().isoformat(timespec="seconds")
    results = []

    for row in rows[1:]:
        cells = [c.get_text(strip=True) for c in row.find_all(["th", "td"])]
        if len(cells) < 2:
            continue
        category = cells[0]
        prices = cells[1:]

        for date_str, price_str in zip(date_columns, prices):
            if not price_str:
                continue
            match = re.match(r"(\d+)\s*-\s*(\d+)", price_str.replace(".", ""))
            if match:
                price_min, price_max = match.group(1), match.group(2)
            else:
                digits = re.sub(r"[^\d]", "", price_str)
                price_min = price_max = digits or None

            try:
                day, month = date_str.split("/")
                price_date = f"{current_year}-{int(month):02d}-{int(day):02d}"
            except ValueError:
                price_date = date_str

            results.append(
                {
                    "price_date": price_date,
                    "category": category,
                    "price_min": price_min,
                    "price_max": price_max,
                    "source": "vietnambiz.vn (gốc: luagaoviet.com)",
                    "crawled_at": crawled_at,
                }
            )

    return results


def main():
    print(f"[{datetime.datetime.now()}] Đang crawl giá lúa gạo ...")
    html = fetch_html()
    rows = parse_price_table(html)
    print(f"Tìm thấy {len(rows)} dòng dữ liệu.")

    new_count = append_new_rows(OUTPUT_FILE, rows)
    print(f"Đã ghi thêm {new_count} dòng dữ liệu mới vào {OUTPUT_FILE}")


if __name__ == "__main__":
    main()