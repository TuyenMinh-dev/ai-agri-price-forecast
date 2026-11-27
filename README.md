# AgriSight — Agricultural Price Monitoring & Forecasting

Hệ thống thu thập dữ liệu giá nông sản thực tế theo ngày và dự báo giá ngắn hạn (trọng tâm lúa gạo khu vực Đồng bằng Sông Cửu Long, mở rộng hồ tiêu và cà phê) bằng các mô hình hồi quy, học máy và mạng nơ-ron hồi quy sâu **LSTM**.

---

## 1. Kiến trúc hệ thống

```text
[Smart Crawler 2 tầng + NASA POWER API]
                  │
                  ▼
      [Neon Cloud PostgreSQL]
      (products, market_prices, weather_data, forecasts)
                  │
        ┌─────────┴─────────┐
        ▼                   ▼
[ML / LSTM Pipeline]   [FastAPI REST API]
(train, walk-forward,       │
 generate_forecast)         ▼
                    [ReactJS Web App]
```

* **Data Pipeline (`scripts/`):** Tự động thu thập giá nông sản hằng ngày từ `vietnambiz.vn` (gốc `luagaoviet.com`, `giacaphe.com`) và dữ liệu thời tiết từ NASA POWER API, nạp theo lô vào PostgreSQL trên Neon Cloud.
* **ML & Deep Learning (`ml/`):** Tiền xử lý chuỗi thời gian chống rò rỉ dữ liệu (*No Data Leakage*), huấn luyện và đối sánh 5 mô hình (`Naive`, `Linear Regression`, `Random Forest`, `XGBoost`, `LSTM PyTorch`).
* **Web Application (`backend/`, `frontend/`):** FastAPI cung cấp REST API kết nối với giao diện ReactJS (Vite) hiển thị bảng giá, biểu đồ lịch sử, so sánh dự báo đa mô hình và tự động lọc sản phẩm ngừng niêm yết.

---

## 2. Điểm nổi bật về kỹ thuật & khoa học dữ liệu

* **Smart Crawler 2 tầng & Backfill lịch sử 7 tháng:** Ưu tiên bóc tách bản tin thị trường hằng ngày (đủ cả gạo nguyên liệu và lúa tươi tại ruộng), tự động fallback sang bảng tổng quan khi ngày nghỉ; tích lũy liên tục từ `21/04/2026` đến nay (`>1.260` bản ghi lúa gạo).
* **Kiểm toán nguồn dữ liệu (`docs/DATA_SOURCES.md`):** `100%` bản ghi giá có trường `source` truy xuất nguồn gốc, tự động nhận diện ngày nghỉ giao dịch (Chủ nhật) và cơ chế xoay vòng mặt hàng theo mùa vụ.
* **Chống rò rỉ dữ liệu (No Data Leakage):** Toàn bộ quá trình chia Train/Test (`80/20`), trượt cửa sổ đặc trưng, chuẩn hóa `MinMaxScaler` (của LSTM) và thẩm định đều thực hiện độc lập trên dữ liệu quá khứ.
* **Thẩm định chuỗi thời gian chặt chẽ:**
  * **Walk-Forward Validation (`ml/experiments/evaluate_walk_forward.py`):** Đánh giá Expanding Window 6 folds trên 12 chủng loại lúa gạo (`docs/walk_forward_results.csv`).
  * **Feature Engineering (`ml/experiments/enhanced_features.py`):** Đối chứng bộ đặc trưng ngắn hạn với đặc trưng mở rộng và phân tích Gini Feature Importance (`docs/feature_comparison_results.csv`).

---

## 3. Kết quả thực nghiệm tóm tắt (Lúa gạo — 1.249 mẫu hợp lệ, Test 20% cuối)

| Mô hình | MAE (VND/kg) | RMSE (VND/kg) | MAPE (%) | Ghi chú |
| :--- | :---: | :---: | :---: | :--- |
| **Naive** *(Baseline)* | 41.75 | 101.10 | 0.54% | Đường chuẩn cơ sở |
| **Linear Regression** | **45.30** | **98.32** | **0.58%** | **Mô hình ML tốt nhất (RMSE thấp nhất)** |
| **Random Forest** | 104.90 | 196.65 | 1.25% | — |
| **LSTM** *(PyTorch, W=5)* | 138.26 | 190.53 | 1.74% | Giảm ~60% sai số khi mở rộng từ 50 ngày lên 7 tháng |
| **XGBoost** | 166.49 | 373.48 | 1.82% | — |

---

## 4. Cấu trúc thư mục chính

```text
├── backend/       # FastAPI REST API & SQLAlchemy models (Neon PostgreSQL)
├── frontend/      # ReactJS (Vite) — Dashboard, Bảng giá, Biểu đồ, Dự báo
├── ml/
│   ├── features/  # Tải dữ liệu từ DB & tạo đặc trưng chuỗi thời gian
│   ├── models/    # train_baseline.py (5 mô hình) & generate_forecast.py
│   └── experiments/ # Walk-Forward Validation, Enhanced Features, Weather Ablation
├── scripts/
│   ├── crawler/   # Smart Rice/Pepper/Coffee crawlers, backfill & run_all_crawlers.bat
│   ├── db/        # Nạp dữ liệu CSV lên PostgreSQL theo lô (batch cache)
│   └── data_external/ # Thu thập dữ liệu thời tiết NASA POWER API
└── docs/          # Tài liệu kiểm toán (DATA_SOURCES.md), CSV kết quả & biểu đồ (figures/)
```

---

## 5. Hướng dẫn cài đặt & khởi chạy

### Yêu cầu môi trường
* Python `3.10+` (khuyến nghị `3.11–3.14`), Node.js `18+`, PostgreSQL (Neon Cloud).

### Bước 1: Cài đặt thư viện & cấu hình `.env`
```bash
git clone https://github.com/TuyenMinh-dev/ai-agri-price-forecast.git
cd ai-agri-price-forecast

pip install -r requirements.txt
pip install torch
```
Tạo file `.env` ở thư mục gốc (tham khảo `.env.example`) và khai báo chuỗi kết nối CSDL:
```env
DATABASE_URL=postgresql://<user>:<password>@<host>/<db>?sslmode=require
```

### Bước 2: Chạy Pipeline dữ liệu & Mô hình AI
```bash
# Chạy toàn bộ pipeline hằng ngày (crawl giá, nạp DB, lấy thời tiết, sinh dự báo 4 mô hình)
cd scripts/crawler && run_all_crawlers.bat

# Huấn luyện & đối sánh 5 mô hình (bao gồm LSTM)
python ml/models/train_baseline.py

# Chạy thẩm định Walk-Forward Validation (6 folds)
python ml/experiments/evaluate_walk_forward.py
```

### Bước 3: Khởi chạy Web Application
```bash
# Terminal 1 — Backend (http://127.0.0.1:8000)
cd backend
python -m uvicorn app.main:app --reload

# Terminal 2 — Frontend (http://localhost:5173)
cd frontend
npm install
npm run dev
```
