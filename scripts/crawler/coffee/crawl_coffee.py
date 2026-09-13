"""
Crawler giá cà phê từ vietnambiz.vn/gia-ca-phe.html

Bảng giá dạng "chụp nhanh" theo vùng, giống cấu trúc bảng hồ tiêu:
    | Thị trường | Trung bình | Thay đổi |
Lưu ý: bảng này có kèm 1 dòng "Hồ tiêu" ở cuối (giá tham chiếu) -> cần loại bỏ,
vì đây là crawler cho cà phê, không phải hồ tiêu.
"""

import datetime
import sys
from pathlib import Path

import requests
from bs4 import BeautifulSoup

sys.path.append(str(Path(__file__).resolve().parent.parent / "storage"))
from storage import append_new_rows

URL = "https://vietnambiz.vn/gia-ca-phe.html"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    )
}
BASE_DIR = Path(__file__).resolve().parents[3]
OUTPUT_FILE = BASE_DIR / "data" / "raw" / "coffee_price_vietnambiz.csv"

# Loại bỏ dòng không phải cà phê (trang gộp chung 1 dòng "Hồ tiêu" tham chiếu)
EXCLUDE_CATEGORIES = {"hồ tiêu", "ho tieu"}


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
        if "Thị trường" in t.get_text(" ", strip=True):
            price_table = t
            break

    if price_table is None:
        raise ValueError("Không tìm thấy bảng giá — trang có thể đã đổi cấu trúc.")

    rows = price_table.find_all("tr")
    if not rows:
        return []

    today = datetime.date.today().isoformat()
    crawled_at = datetime.datetime.now().isoformat(timespec="seconds")
    results = []

    for row in rows[1:]:
        cells = [c.get_text(strip=True) for c in row.find_all(["th", "td"])]
        if len(cells) < 2:
            continue
        market, price_str = cells[0], cells[1]

        if market.strip().lower() in EXCLUDE_CATEGORIES:
            continue

        price_digits = price_str.replace(",", "").replace(".", "")
        if not price_digits.isdigit():
            continue

        results.append(
            {
                "price_date": today,
                "category": market,
                "price_min": price_digits,
                "price_max": price_digits,
                "source": "vietnambiz.vn (gốc: giacaphe.com)",
                "crawled_at": crawled_at,
            }
        )

    return results


def main():
    print(f"[{datetime.datetime.now()}] Đang crawl giá cà phê ...")
    html = fetch_html()
    rows = parse_price_table(html)
    print(f"Tìm thấy {len(rows)} dòng dữ liệu.")

    new_count = append_new_rows(OUTPUT_FILE, rows)
    print(f"Đã ghi thêm {new_count} dòng dữ liệu mới vào {OUTPUT_FILE}")


if __name__ == "__main__":
    main()