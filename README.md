# Website hỗ trợ cập nhật thông tin thị trường và dự báo giá nông sản

## 1. Tổng quan dự án

Hệ thống web hỗ trợ nông dân và thương lái theo dõi thông tin thị trường và
dự báo giá nông sản (lúa hoặc hồ tiêu — xem `docs/SCOPE.md` để chốt phạm vi
cụ thể), gồm 3 phần chính:

- **Thu thập dữ liệu**: crawl giá thị trường theo ngày + dữ liệu sản lượng/thời
  tiết làm feature phụ trợ.
- **Mô hình học máy**: xây dựng và so sánh nhiều mô hình dự báo giá (baseline
  tuyến tính, mô hình cây/ensemble, mô hình chuỗi thời gian).
- **Website**: hiển thị thông tin thị trường cập nhật + kết quả dự báo cho
  người dùng cuối.

## 2. Kiến trúc hệ thống

```
[Crawler] --> [data/raw] --> [ETL/tiền xử lý] --> [data/processed]
                                                        |
                                                        v
                                                 [ml/ - train & so sánh mô hình]
                                                        |
                                                        v
                                            [backend API] <--> [frontend web]
```

- **Backend**: cung cấp API (giá lịch sử, kết quả dự báo, dữ liệu thị trường).
- **Frontend**: giao diện xem biểu đồ giá, thông tin thị trường, dự báo.
- **ML pipeline**: tách biệt khỏi backend — train offline, xuất model để
  backend load và phục vụ dự đoán (không train trực tiếp trong request).

## 3. Cấu trúc thư mục

Xem chi tiết trong `docs/PROJECT_STRUCTURE.md`.

## 4. Lộ trình thực hiện (2 tháng)

Xem chi tiết trong `docs/ROADMAP.md`.

## 5. Phân công & quy tắc làm việc nhóm

Xem `docs/CONTRIBUTING.md` — quy tắc nhánh (branch), quy ước commit, cách
review pull request.

## 6. Bắt đầu nhanh (Getting Started)

```bash
# Clone repo
git clone <repo-url>
cd agri-price-forecast

# Backend
cd backend
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Frontend
cd ../frontend
npm install
npm run dev
```

Chi tiết cấu hình môi trường xem `docs/SETUP.md`.
