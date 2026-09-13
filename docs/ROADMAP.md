# Lộ trình thực hiện (8 tuần)

> Nguyên tắc: crawl dữ liệu giá phải chạy **liên tục ngay từ tuần 1** vì đây
> là tài nguyên tích lũy theo thời gian thực, không thể dồn về sau.

## Tuần 1 — Khởi tạo & phân tích yêu cầu
- [ ] Chốt phạm vi: loại nông sản (lúa/hồ tiêu), vùng trồng theo dõi.
- [ ] Phân tích yêu cầu chức năng (use case, ai dùng, dùng để làm gì).
- [ ] Thiết kế sơ bộ CSDL (bảng: giá, vùng, nguồn tin, dự báo, người dùng...).
- [ ] Setup repo, phân quyền, tạo board quản lý task (GitHub Projects/Issues).
- [ ] **Bắt đầu chạy crawler thu thập giá theo ngày** (chạy nền, không chờ).

## Tuần 2 — Thu thập & khảo sát dữ liệu
- [ ] Hoàn thiện crawler (giá theo ngày, nhiều nguồn, retry/logging).
- [ ] Tải dữ liệu năm: sản lượng/diện tích (GSO, FAOSTAT).
- [ ] Tải dữ liệu thời tiết theo vùng (NASA POWER API).
- [ ] Tìm và đánh giá dataset lịch sử giá quốc tế (nối dài chuỗi thời gian).
- [ ] Thiết kế API contract (endpoint nào, trả về dữ liệu gì) để backend/
      frontend làm song song.

## Tuần 3-4 — Xử lý dữ liệu & xây dựng backend nền tảng
- [ ] Làm sạch, ghép dữ liệu (giá + thời tiết + sản lượng theo mốc thời gian).
- [ ] Xử lý missing value, chuẩn hoá định dạng giữa các nguồn.
- [ ] Feature engineering ban đầu (trung bình trượt, độ trễ giá, mùa vụ...).
- [ ] Backend: dựng khung API (CRUD dữ liệu giá, kết nối DB).
- [ ] Frontend: dựng khung giao diện (layout, trang chủ, trang biểu đồ).

## Tuần 5 — Xây dựng & huấn luyện mô hình
- [ ] Xây baseline (Linear Regression) — chạy được end-to-end trước.
- [ ] Xây mô hình phi tuyến (Random Forest/XGBoost).
- [ ] Xây mô hình chuỗi thời gian (ARIMA hoặc LSTM) nếu đủ dữ liệu.
- [ ] Đánh giá bằng RMSE/MAE, log lại kết quả để so sánh.

## Tuần 6 — Tích hợp mô hình vào hệ thống
- [ ] Export mô hình đã train (pickle/ONNX/saved model).
- [ ] Backend: API phục vụ dự đoán, đọc dữ liệu thị trường mới nhất.
- [ ] Frontend: trang hiển thị biểu đồ giá + kết quả dự báo, cảnh báo biến động.
- [ ] Test tích hợp toàn hệ thống (crawler → DB → model → API → web).

## Tuần 7 — Hoàn thiện, kiểm thử, tinh chỉnh
- [ ] Kiểm thử chức năng (test case cho từng module).
- [ ] Tinh chỉnh UI/UX, xử lý lỗi, responsive.
- [ ] So sánh lại 3 mô hình bằng bộ dữ liệu mới nhất (bao gồm dữ liệu tự crawl
      làm tập kiểm chứng thực tế).
- [ ] Viết tài liệu kỹ thuật, chuẩn bị số liệu cho báo cáo.

## Tuần 8 — Báo cáo & bảo vệ
- [ ] Hoàn thiện báo cáo (Word/slide).
- [ ] Chuẩn bị demo trực tiếp trên website.
- [ ] Rà soát lại toàn bộ repo (README, code sạch, comment cần thiết).
- [ ] Tập dượt bảo vệ, phân công ai trình bày phần nào.

## Rủi ro cần theo dõi
- Crawl không đủ dữ liệu lịch sử theo ngày → cần nguồn dữ liệu quốc tế bù đắp
  (xem `docs/DATA_SOURCES.md`).
- Phân công công việc chồng chéo giữa backend/frontend/ML → dùng GitHub
  Issues + branch riêng theo module để tránh conflict.
