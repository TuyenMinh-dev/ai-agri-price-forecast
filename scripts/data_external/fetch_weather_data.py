"""
Lay du lieu thoi tiet hang ngay cho vung Dong bang song Cuu Long (dai dien
boi toa do Can Tho) tu NASA POWER API, nap vao bang weather_data.

Nguon: NASA POWER (https://power.larc.nasa.gov) - API mo, tra ve du lieu
dang JSON theo ngay, khong can dang ky/API key.

Luu y: NASA POWER co do tre xu ly khoang vai ngay - vai ngay gan nhat co
the chua co du lieu, se tu dong bu sau khi chay lai script nhung lan tiep
theo (giong cach lam voi scripts/crawler, co the gop vao chay dinh ky).
"""

import sys
from datetime import date, datetime
from pathlib import Path

import requests

BASE_DIR = Path(__file__).resolve().parents[2]
sys.path.append(str(BASE_DIR / "backend"))

from app.db.session import SessionLocal
from app.models.tables import WeatherData

REGION = "Dong bang song Cuu Long"
# Toa do dai dien: Can Tho - trung tam vung DBSCL
LATITUDE = 10.0452
LONGITUDE = 105.7469

START_DATE = date(2026, 9, 1)  # chinh lai neu muon lay tu moc khac

API_URL = "https://power.larc.nasa.gov/api/temporal/daily/point"
PARAMETERS = "T2M,PRECTOTCORR"  # nhiet do trung binh (C), luong mua (mm/ngay)


def fetch_weather(start: date, end: date) -> dict:
    """Goi NASA POWER API, tra ve du lieu tho dang JSON."""
    params = {
        "parameters": PARAMETERS,
        "community": "AG",
        "longitude": LONGITUDE,
        "latitude": LATITUDE,
        "start": start.strftime("%Y%m%d"),
        "end": end.strftime("%Y%m%d"),
        "format": "JSON",
    }
    resp = requests.get(API_URL, params=params, timeout=30)
    resp.raise_for_status()
    return resp.json()


def parse_weather(raw: dict) -> list[dict]:
    """Chuyen JSON tra ve thanh list cac dict {weather_date, temperature_avg, rainfall_mm}."""
    params = raw["properties"]["parameter"]
    temps = params.get("T2M", {})
    rains = params.get("PRECTOTCORR", {})

    results = []
    for date_str in temps:
        temp = temps.get(date_str)
        rain = rains.get(date_str)

        # NASA POWER dung gia tri -999 de danh dau "chua co du lieu"
        if temp is None or temp == -999 or rain is None or rain == -999:
            continue

        weather_date = datetime.strptime(date_str, "%Y%m%d").date()
        results.append(
            {
                "weather_date": weather_date,
                "temperature_avg": round(float(temp), 2),
                "rainfall_mm": round(float(rain), 2),
            }
        )
    return results


def save_weather(session, rows: list[dict]) -> int:
    """Luu vao bang weather_data - cap nhat neu da co (region, weather_date), insert neu chua."""
    saved = 0
    for row in rows:
        existing = (
            session.query(WeatherData)
            .filter_by(region=REGION, weather_date=row["weather_date"])
            .first()
        )
        if existing:
            existing.temperature_avg = row["temperature_avg"]
            existing.rainfall_mm = row["rainfall_mm"]
        else:
            session.add(
                WeatherData(
                    region=REGION,
                    weather_date=row["weather_date"],
                    temperature_avg=row["temperature_avg"],
                    rainfall_mm=row["rainfall_mm"],
                )
            )
        saved += 1
    return saved


def main():
    end = date.today()
    print(f"Dang lay du lieu thoi tiet vung {REGION} tu {START_DATE} den {end}...")

    raw = fetch_weather(START_DATE, end)
    rows = parse_weather(raw)

    if not rows:
        print("Khong lay duoc du lieu nao - kiem tra lai ket noi mang hoac tham so goi API.")
        return

    print(f"Lay duoc {len(rows)} ngay co du lieu (vai ngay gan nhat co the con thieu do NASA POWER tre xu ly).")

    session = SessionLocal()
    try:
        saved = save_weather(session, rows)
        session.commit()
        print(f"Hoan tat. Da luu/cap nhat {saved} dong vao bang weather_data.")
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


if __name__ == "__main__":
    main()