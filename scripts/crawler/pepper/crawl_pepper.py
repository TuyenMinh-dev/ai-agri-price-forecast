"""
Crawler giá hồ tiêu từ vietnambiz.vn/gia-tieu-hom-nay.html

Bảng giá dạng "chụp nhanh" theo vùng (không có cột theo ngày như bảng gạo):
    | Khu vực | Giá mua | Thay đổi |
Mỗi lần crawl chỉ lấy được giá NGÀY HÔM ĐÓ.
"""

import datetime
import sys
from pathlib import Path

import requests
from bs4 import BeautifulSoup

sys.path.append(str(Path(__file__).resolve().parent.parent / "storage"))
from storage import append_new_rows

URL = "https://vietnambiz.vn/gia-tieu-hom-nay.html"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    )
}
BASE_DIR = Path(__file__).resolve().parents[3]
OUTPUT_FILE = BASE_DIR / "data" / "raw" / "pepper_price_vietnambiz.csv"


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
        if "Khu vực" in t.get_text(" ", strip=True):
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
        region, price_str = cells[0], cells[1]
        price_digits = price_str.replace(",", "").replace(".", "")
        if not price_digits.isdigit():
            continue

        results.append(
            {
                "price_date": today,
                "category": region,
                "price_min": price_digits,
                "price_max": price_digits,
                "source": "vietnambiz.vn (gốc: giacaphe.com)",
                "crawled_at": crawled_at,
            }
        )

    return results


def main():
    print(f"[{datetime.datetime.now()}] Đang crawl giá hồ tiêu ...")
    html = fetch_html()
    rows = parse_price_table(html)
    print(f"Tìm thấy {len(rows)} dòng dữ liệu.")

    new_count = append_new_rows(OUTPUT_FILE, rows)
    print(f"Đã ghi thêm {new_count} dòng dữ liệu mới vào {OUTPUT_FILE}")


if __name__ == "__main__":
    main()