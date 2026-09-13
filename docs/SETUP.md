# Hướng dẫn cài đặt môi trường

## Yêu cầu chung
- Python 3.10+
- Node.js 18+
- PostgreSQL hoặc MySQL (tuỳ nhóm chọn)
- Git

## Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp ../.env.example ../.env    # điền thông tin DB, API key...
python -m app.main            # chạy server
```

## Frontend
```bash
cd frontend
npm install
npm run dev
```

## ML pipeline
```bash
cd ml
pip install -r requirements.txt
# Chạy notebook trong ml/notebooks để khám phá dữ liệu
# Chạy script train:
python models/train_linear.py
python models/train_tree_based.py
python models/evaluate.py
```

## Crawler
```bash
cd scripts/crawler
pip install -r requirements.txt   # nếu tách riêng requirements
python crawl_price_daily.py
```
Khuyến nghị: thiết lập cron job (Linux/Mac) hoặc Task Scheduler (Windows) để
chạy script này mỗi ngày tự động, tránh phải chạy tay.

## Biến môi trường (.env)
Xem file `.env.example` ở thư mục gốc — copy thành `.env` và điền giá trị
thật (không commit `.env` lên GitHub).
