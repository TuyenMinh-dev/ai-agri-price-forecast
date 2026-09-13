# Cấu trúc thư mục dự án

```
agri-price-forecast/
├── README.md                      # Tổng quan dự án
├── .gitignore
├── .env.example                   # Mẫu biến môi trường (copy thành .env)
├── docker-compose.yml             # (tuỳ chọn) chạy backend+db+frontend cùng lúc
│
├── docs/                          # Tài liệu dự án
│   ├── ROADMAP.md                 # Lộ trình 8 tuần
│   ├── PROJECT_STRUCTURE.md       # File này
│   ├── SCOPE.md                   # Phạm vi: loại nông sản, vùng, đối tượng dùng
│   ├── DATA_SOURCES.md            # Danh sách nguồn dữ liệu + cách lấy
│   ├── API_SPEC.md                # Đặc tả API (endpoint, request/response)
│   ├── SETUP.md                   # Hướng dẫn cài đặt môi trường chi tiết
│   └── CONTRIBUTING.md            # Quy tắc branch, commit, review PR
│
├── data/
│   ├── raw/                       # Dữ liệu thô crawl được (không sửa tay)
│   ├── processed/                 # Dữ liệu đã làm sạch, sẵn sàng train
│   └── external/                  # Dữ liệu tải từ GSO/FAOSTAT/thời tiết...
│
├── ml/                            # Toàn bộ phần học máy (tách biệt backend)
│   ├── notebooks/                 # Notebook khám phá dữ liệu, thử nghiệm
│   ├── features/                  # Script feature engineering
│   ├── models/                    # Code định nghĩa + train từng mô hình
│   │   ├── train_linear.py
│   │   ├── train_tree_based.py    # Random Forest / XGBoost
│   │   ├── train_timeseries.py    # ARIMA / LSTM
│   │   └── evaluate.py            # So sánh RMSE/MAE giữa các mô hình
│   ├── artifacts/                 # Model đã train (file .pkl/.onnx) — gitignore
│   └── requirements.txt
│
├── backend/                       # API phục vụ dữ liệu + kết quả dự báo
│   ├── app/
│   │   ├── api/                   # Định nghĩa route/endpoint
│   │   ├── models/                # Model DB (ORM), schema
│   │   ├── services/              # Business logic (gọi model ML, xử lý dữ liệu)
│   │   ├── utils/                 # Hàm tiện ích dùng chung
│   │   └── main.py                # Entry point (FastAPI/Flask app)
│   ├── tests/                     # Unit test backend
│   ├── requirements.txt
│   └── Dockerfile                 # (tuỳ chọn)
│
├── frontend/                      # Giao diện web
│   ├── src/
│   │   ├── components/            # Component tái sử dụng (biểu đồ, bảng giá...)
│   │   ├── pages/                 # Các trang (Trang chủ, Dự báo, Thị trường)
│   │   ├── services/              # Gọi API backend
│   │   └── assets/                # Hình ảnh, icon, style
│   ├── package.json
│   └── vite.config.js             # (nếu dùng React + Vite)
│
├── scripts/                        # Script tiện ích, chạy độc lập
│   ├── crawler/                    # Script crawl giá theo ngày
│   │   ├── crawl_price_daily.py
│   │   └── sources_config.yaml     # Danh sách URL nguồn crawl
│   └── run_pipeline.sh              # Chạy toàn bộ pipeline (crawl→process→train)
│
└── .github/
    └── workflows/                   # CI (tuỳ chọn): lint, test tự động khi push
```

## Ghi chú phân công theo thư mục (gợi ý)

| Thư mục | Vai trò phù hợp |
|---|---|
| `scripts/crawler/`, `data/` | Người phụ trách thu thập dữ liệu |
| `ml/` | Người phụ trách xây dựng & so sánh mô hình |
| `backend/` | Người phụ trách API/server |
| `frontend/` | Người phụ trách giao diện |
| `docs/` | Cả nhóm cùng cập nhật, 1 người tổng hợp |

Mỗi module có thể phát triển độc lập theo nhánh riêng (`feature/crawler`,
`feature/ml-models`, `feature/backend-api`, `feature/frontend-ui`) để tránh
xung đột code, sau đó merge vào `develop` rồi `main`.
