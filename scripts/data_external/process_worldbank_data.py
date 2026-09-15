"""
Xử lý file CMO-Historical-Data-Monthly.xlsx (World Bank) — lọc ra các cột
giá lúa gạo và cà phê, xuất ra CSV gọn để dùng làm dữ liệu lịch sử bổ trợ.

"""

from pathlib import Path

import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[2]  # scripts/data_external/ -> gốc project
INPUT_FILE = BASE_DIR / "data" / "external" / "CMO-Historical-Data-Monthly.xlsx"
OUTPUT_FILE = BASE_DIR / "data" / "external" / "worldbank_rice_coffee_monthly.csv"

SHEET_NAME = "Monthly Prices"
HEADER_ROW_INDEX = 4  # dòng chứa tên hàng hoá (dòng thứ 5 trong Excel, đếm từ 0)

# Các cột cần lấy — khớp với tên trong file gốc của World Bank
TARGET_COLUMNS = {
    "Coffee, Arabica": "coffee_arabica_usd_kg",
    "Coffee, Robusta": "coffee_robusta_usd_kg",
    "Rice, Thai 5%": "rice_thai_5_usd_ton",
    "Rice, Viet Namese 5%": "rice_vietnam_5_usd_ton",
}


def parse_wb_date(value: str):
    """Chuyển '1960M01' -> '1960-01' """
    value = str(value).strip()
    if "M" in value:
        year, month = value.split("M")
        return f"{year}-{int(month):02d}"
    return value


def main():
    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Không tìm thấy file {INPUT_FILE}. Hãy tải file 'Monthly Prices' từ "
            "worldbank.org/en/research/commodity-markets và đặt đúng vào "
            "data/external/CMO-Historical-Data-Monthly.xlsx trước khi chạy."
        )

    df = pd.read_excel(INPUT_FILE, sheet_name=SHEET_NAME, header=HEADER_ROW_INDEX)

    # File gốc của World Bank có một số tên cột bị dư khoảng trắng ở cuối
    # (vd "Rice, Thai 5% ") - cần strip() để khớp đúng với TARGET_COLUMNS
    df.columns = [str(c).strip() if isinstance(c, str) else c for c in df.columns]

    date_col = df.columns[0]
    df = df.rename(columns={date_col: "date"})

    # Dòng đầu tiên sau header là dòng đơn vị tính ("($/kg)"...) - bỏ đi
    df = df.iloc[1:].reset_index(drop=True)

    available = {k: v for k, v in TARGET_COLUMNS.items() if k in df.columns}
    missing = [k for k in TARGET_COLUMNS if k not in df.columns]
    if missing:
        print(f"Cảnh báo: không tìm thấy các cột sau trong file: {missing}")
    if not available:
        raise ValueError("Không tìm thấy cột nào trong TARGET_COLUMNS - kiểm tra lại tên cột.")

    result = df[["date"] + list(available.keys())].copy()
    result = result.rename(columns=available)
    result["date"] = result["date"].apply(parse_wb_date)

    price_cols = list(available.values())
    for c in price_cols:
        result[c] = pd.to_numeric(result[c], errors="coerce")
    result = result.dropna(subset=price_cols, how="all")

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(OUTPUT_FILE, index=False, encoding="utf-8")

    print(f"Đã lưu {len(result)} dòng dữ liệu vào {OUTPUT_FILE}")
    print(result.head())
    print(result.tail())


if __name__ == "__main__":
    main()