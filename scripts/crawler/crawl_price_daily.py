"""
Script crawl giá nông sản theo ngày.
Chạy định kỳ (cron job) để tích luỹ dữ liệu lịch sử theo thời gian.

TODO:
- Đọc danh sách nguồn từ sources_config.yaml
- Parse HTML lấy giá theo vùng
- Lưu vào data/raw/ dạng CSV theo ngày (vd: prices_2026-09-13.csv)
- Ghi log lỗi nếu nguồn nào không truy cập được
"""

import datetime


def main():
    today = datetime.date.today().isoformat()
    print(f"[TODO] Crawl giá ngày {today} — chưa triển khai")


if __name__ == "__main__":
    main()
