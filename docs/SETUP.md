# Hướng dẫn cài đặt môi trường

## Yêu cầu chung
- Python 3.10+
- Node.js 18+
- Git
- Database — dự án dùng CSDL cloud (Neon) từ PostgreSQL
## Bước 1 — Clone repo và cài thư viện Python
```bash
git clone https://github.com/TuyenMinh-dev/ai-agri-price-forecast.git
cd ai-agri-price-forecast

python -m venv venv
venv\Scripts\activate      # Mac/Linux: source venv/bin/activate
pip install -r requirements.txt
```

## Bước 2 — Cấu hình biến môi trường
```bash
copy .env.example .env     # Mac/Linux: cp .env.example .env
```
Mở file `.env`, dán đúng `DATABASE_URL`  vào.

## Bước 3 — Kiểm tra kết nối CSDL
```bash
cd ml\models
python train_baseline.py
```

## Backend
```bash
cd backend
python -m app.main
```

## Frontend
```bash
cd frontend
npm install
npm run dev
```

## Train / so sánh model
```bash
cd ml\models
python train_baseline.py
```
