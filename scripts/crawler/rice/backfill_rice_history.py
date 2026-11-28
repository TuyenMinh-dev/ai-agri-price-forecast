"""
Script crawl nguoc (Backfill) du lieu gia lua gao 6 thang qua (tu thang 5/2026 den nay).
Quet qua cac trang chuyen muc Gao cua vietnambiz.vn, boc tach bang gia cua tung bai bao
va ghi bo sung vao file data/raw/rice_price_vietnambiz.csv (tu dong loc trung lap).
"""

from concurrent.futures import ThreadPoolExecutor, as_completed
import datetime
from pathlib import Path
import re
import sys
from bs4 import BeautifulSoup
import requests

# Tro toi thu muc storage/ nam cung cap de import duoc storage.py
sys.path.append(str(Path(__file__).resolve().parent.parent / "storage"))
from storage import append_new_rows

BASE_URL = "https://vietnambiz.vn"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    )
}

BASE_DIR = Path(__file__).resolve().parents[3]
OUTPUT_FILE = BASE_DIR / "data" / "raw" / "rice_price_vietnambiz.csv"

CATEGORY_MAP = {
    "Nguyên liệu IR 504": "NL IR 504",
    "Nguyên liệu OM 5451": "NL OM 5451",
    "Tấm thơm": "Tấm thơm",
    "Cám": "Cám",
    "Nguyên liệu CL 555": "NL CL 555",
    "Tấm 3,4": "Tấm 3,4",
    "IR 504": "NL IR 504",
    "OM 5451": "NL OM 5451",
    "CL 555": "NL CL 555",
    "Lúa tươi IR 50404": "Lúa tươi IR 504",
    "Lúa tươi IR 504": "Lúa tươi IR 504",
    "Lúa tươi Đài Thơm 8": "Lúa tươi Đài Thơm 8",
    "Lúa tươi OM 18": "Lúa tươi OM 18",
    "Lúa tươi OM 5451": "Lúa tươi OM 5451",
    "Lúa tươi OM 34": "Lúa tươi OM 34",
    "DS1": "DS1",
}


def parse_day_month_from_url(href: str):
    m = re.search(r"gia-lua-gao-hom-nay-(\d+)-", href, re.IGNORECASE)
    if not m:
        return None, None
    digits = m.group(1)
    if len(digits) == 4:
        return int(digits[:2]), int(digits[2:])
    elif len(digits) == 3:
        if digits[1:] in ["10", "11", "12"]:
            return int(digits[0]), int(digits[1:])
        else:
            return int(digits[:2]), int(digits[2])
    elif len(digits) == 2:
        return int(digits[0]), int(digits[1])
    return None, None


def find_all_articles(max_pages: int = 11) -> list[dict]:
    articles = []
    seen_dates = set()

    for p in range(1, max_pages + 1):
        url = f"{BASE_URL}/chu-de/gao-41/trang-{p}.htm"
        try:
            resp = requests.get(url, headers=HEADERS, timeout=12)
            resp.raise_for_status()
            resp.encoding = "utf-8"
            soup = BeautifulSoup(resp.text, "lxml")

            for a in soup.find_all("a", href=True):
                href = a["href"]
                if "gia-lua-gao-hom-nay" in href:
                    day, month = parse_day_month_from_url(href)
                    if day and month and 1 <= day <= 31 and 1 <= month <= 12:
                        d_str = f"2026-{month:02d}-{day:02d}"
                        if d_str not in seen_dates:
                            seen_dates.add(d_str)
                            full_url = href if href.startswith("http") else f"{BASE_URL}{href}"
                            articles.append({
                                "date_str": d_str,
                                "day": day,
                                "month": month,
                                "url": full_url,
                                "title": a.get_text(strip=True),
                            })
        except Exception as e:
            print(f"  [Canh bao] Loi khi quet trang {p}: {e}")

    # Sap xep theo thoi gian tang dan
    articles.sort(key=lambda x: x["date_str"])
    return articles


def parse_single_article(art: dict) -> list[dict]:
    url = art["url"]
    price_date = art["date_str"]
    crawled_at = datetime.datetime.now().isoformat(timespec="seconds")

    try:
        resp = requests.get(url, headers=HEADERS, timeout=12)
        resp.raise_for_status()
        resp.encoding = "utf-8"
        soup = BeautifulSoup(resp.text, "lxml")

        table = soup.find("table")
        if not table:
            return []

        rows = table.find_all("tr")
        if not rows:
            return []

        results = []
        for row in rows[1:]:
            cells = [c.get_text(strip=True) for c in row.find_all(["th", "td"])]
            if len(cells) < 3:
                continue

            raw_cat = cells[0].lstrip("- ").strip()
            # Chi lay cac chung loai hop le hoac map ve danh muc he thong
            category = CATEGORY_MAP.get(raw_cat, raw_cat)

            price_str = cells[2]
            clean_p = price_str.replace(".", "").replace(" ", "").replace("–", "-")
            match = re.match(r"(\d+)-(\d+)", clean_p)
            if match:
                p_min, p_max = match.group(1), match.group(2)
            else:
                digits = re.sub(r"[^\d]", "", clean_p)
                p_min = p_max = digits or None

            if p_min is not None:
                results.append({
                    "price_date": price_date,
                    "category": category,
                    "price_min": p_min,
                    "price_max": p_max,
                    "source": "vietnambiz.vn (goc: luagaoviet.com)",
                    "crawled_at": crawled_at,
                })
        return results
    except Exception:
        return []


def main():
    print("=" * 70)
    print("BAT DAU BACKFILL DU LIEU GIA LUA GAO 6 THANG (TU THANG 5/2026 DEN NAY)")
    print("=" * 70)

    print("\n[Buoc 1] Dang quet danh sach bai bao tu trang 1 den trang 11...")
    articles = find_all_articles(max_pages=11)
    print(f"Tim thay {len(articles)} bai bao tu ngay {articles[0]['date_str']} den {articles[-1]['date_str']}.")

    print("\n[Buoc 2] Dang boc tach du lieu tu cac bai bao (chay da luong)...")
    all_rows = []
    success_count = 0

    with ThreadPoolExecutor(max_workers=6) as executor:
        future_to_art = {executor.submit(parse_single_article, art): art for art in articles}
        for future in as_completed(future_to_art):
            art = future_to_art[future]
            try:
                rows = future.result()
                if rows:
                    all_rows.extend(rows)
                    success_count += 1
            except Exception as e:
                print(f"  Loi khi xu ly bai ngay {art['date_str']}: {e}")

    print(f"Boc tach thanh cong {success_count}/{len(articles)} bai bao.")
    print(f"Tong so ban ghi trich xuat duoc: {len(all_rows)}")

    # Ghi vao CSV (tu dong loc trung theo price_date, category)
    new_count = append_new_rows(OUTPUT_FILE, all_rows)
    print(f"\nDa ghi them {new_count} dong moi vao: {OUTPUT_FILE}")

    # Sap xep lai file CSV theo ngay va category cho dep mat
    import pandas as pd
    df = pd.read_csv(OUTPUT_FILE)
    df = df.sort_values(by=["price_date", "category"]).drop_duplicates(subset=["price_date", "category"])
    df.to_csv(OUTPUT_FILE, index=False, encoding="utf-8")
    print(f"Tong so dong du lieu hien tai trong CSV: {len(df)}")
    print(f"Khoang thoi gian: {df['price_date'].min()} den {df['price_date'].max()}")
    print("So luong chung loai:", len(df["category"].unique()))
    print("=" * 70)
    print("HOAN TAT BUOC 1: BACKFILL CSV THANH CONG!")
    print("=" * 70)


if __name__ == "__main__":
    main()
