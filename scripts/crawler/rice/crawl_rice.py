"""
Crawler gia lua gao thong minh 2 tang tu vietnambiz.vn.
- Tang 1 (Uu tien): Quet bai bao ban tin thi truong hang ngay (gia-lua-gao-hom-nay-DDMM-...)
  duoc xuat ban moi trua de lay du lieu chuan thoi gian thuc tung ngay va day du chung loai.
- Tang 2 (Du phong): Fallback sang bang widget tong quan tai vietnambiz.vn/gia-gao.html.
"""

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
WIDGET_URL = "https://vietnambiz.vn/gia-gao.html"
TOPIC_URL = "https://vietnambiz.vn/chu-de/gao-41.htm"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    )
}

# parents[3]: rice/crawl_rice.py -> rice -> crawler -> scripts -> goc project
BASE_DIR = Path(__file__).resolve().parents[3]
OUTPUT_FILE = BASE_DIR / "data" / "raw" / "rice_price_vietnambiz.csv"

# Bang anh xa ten chung loai trong bai bao ve chuan danh muc he thong
CATEGORY_MAP = {
    "Nguyên liệu IR 504": "NL IR 504",
    "Nguyên liệu OM 5451": "NL OM 5451",
    "Tấm thơm": "Tấm thơm",
    "Cám": "Cám",
    "Nguyên liệu CL 555": "NL CL 555",
    "Tấm 3,4": "Tấm 3,4",
    "IR 504": "NL IR 504",
    "OM 5451": "NL OM 5451",
}


def get_recent_daily_articles(limit: int = 3) -> list[dict]:
    """Quet tim cac bai bao gia lua gao hang ngay moi nhat tu chuyen muc Gao."""
    urls_to_check = [TOPIC_URL, WIDGET_URL]
    articles = []
    seen_urls = set()
    pattern = re.compile(r"gia-lua-gao-hom-nay-(\d{1,2})(\d{2})", re.IGNORECASE)

    for page_url in urls_to_check:
        try:
            resp = requests.get(page_url, headers=HEADERS, timeout=15)
            resp.raise_for_status()
            resp.encoding = "utf-8"
            soup = BeautifulSoup(resp.text, "lxml")

            for a in soup.find_all("a", href=True):
                href = a["href"]
                m = pattern.search(href)
                if m and href not in seen_urls:
                    seen_urls.add(href)
                    day = int(m.group(1))
                    month = int(m.group(2))
                    full_url = href if href.startswith("http") else f"{BASE_URL}{href}"
                    articles.append({
                        "day": day,
                        "month": month,
                        "url": full_url,
                        "title": a.get_text(strip=True),
                    })
                    if len(articles) >= limit:
                        return articles
        except Exception as e:
            print(f"  [Canh bao] Loi khi quet {page_url}: {e}")

    return articles


def parse_article_price_table(article_url: str, day: int, month: int, year: int = None) -> list[dict]:
    """Boc tach bang gia lua gao chi tiet tu mot bai bao hang ngay."""
    if year is None:
        year = datetime.date.today().year

    price_date = f"{year}-{month:02d}-{day:02d}"
    crawled_at = datetime.datetime.now().isoformat(timespec="seconds")

    try:
        resp = requests.get(article_url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        resp.encoding = "utf-8"
        soup = BeautifulSoup(resp.text, "lxml")
    except Exception as e:
        print(f"  [Loi] Khong the tai bai bao {article_url}: {e}")
        return []

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
        category = CATEGORY_MAP.get(raw_cat, raw_cat)

        price_str = cells[2]
        clean_p = price_str.replace(".", "").replace(" ", "").replace("–", "-")
        match = re.match(r"(\d+)-(\d+)", clean_p)
        if match:
            p_min, p_max = match.group(1), match.group(2)
        else:
            digits = re.sub(r"[^\d]", "", clean_p)
            p_min = p_max = digits or None

        results.append({
            "price_date": price_date,
            "category": category,
            "price_min": p_min,
            "price_max": p_max,
            "source": "vietnambiz.vn (goc: luagaoviet.com)",
            "crawled_at": crawled_at,
        })

    return results


def parse_widget_price_table(html: str) -> list[dict]:
    """Fallback: Boc tach bang widget tong quan tai vietnambiz.vn/gia-gao.html."""
    soup = BeautifulSoup(html, "lxml")
    tables = soup.find_all("table")
    price_table = None
    for t in tables:
        if "Chủng loại" in t.get_text(" ", strip=True):
            price_table = t
            break

    if price_table is None:
        return []

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

            results.append({
                "price_date": price_date,
                "category": category,
                "price_min": price_min,
                "price_max": price_max,
                "source": "vietnambiz.vn (goc: luagaoviet.com)",
                "crawled_at": crawled_at,
            })

    return results


def crawl_all_rice_data(recent_articles_limit: int = 3) -> list[dict]:
    """Thuc hien crawl thong minh: Quet cac bai bao hang ngay gan nhat truoc, fallback widget sau."""
    print("  [Tang 1] Dang quet bai bao gia lua gao hang ngay moi nhat...")
    articles = get_recent_daily_articles(limit=recent_articles_limit)

    all_rows = []
    if articles:
        for art in articles:
            print(f"    -> Boc tach bai ngay {art['day']:02d}/{art['month']:02d}: {art['url']}")
            rows = parse_article_price_table(art["url"], art["day"], art["month"])
            all_rows.extend(rows)

    if not all_rows:
        print("  [Tang 2] Khong tim thay bai bao moi. Chuyen sang fallback bang widget...")
        try:
            resp = requests.get(WIDGET_URL, headers=HEADERS, timeout=15)
            resp.raise_for_status()
            resp.encoding = "utf-8"
            all_rows = parse_widget_price_table(resp.text)
        except Exception as e:
            print(f"  [Loi] Khong the tai trang widget: {e}")

    return all_rows


def main():
    print(f"[{datetime.datetime.now()}] Bat dau chay Smart Rice Crawler...")
    rows = crawl_all_rice_data(recent_articles_limit=3)
    print(f"Tong cong trich xuat duoc: {len(rows)} ban ghi.")

    new_count = append_new_rows(OUTPUT_FILE, rows)
    print(f"Da ghi them {new_count} dong du lieu moi vao {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
