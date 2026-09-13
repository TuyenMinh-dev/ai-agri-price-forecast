# Nguồn dữ liệu

## 1. Giá thị trường theo ngày (dùng để crawl)
| Nguồn | Loại | Ghi chú |
|---|---|---|
| giacaphe.com | Hồ tiêu, cà phê | Cập nhật theo ngày |
| giahotieu.com | Hồ tiêu | Theo vùng trồng trọng điểm |
| banggianongsan.com | Nhiều loại nông sản | Có cả lúa, tiêu, ngô... |
| vietnambiz.vn/gia-gao.html | Lúa gạo | Cập nhật theo ngày |

> Lưu ý: các trang trên thường chỉ hiển thị giá **hiện tại**, không cho tải
> lịch sử hàng loạt — cần crawl định kỳ (cron job hàng ngày) để tự tích luỹ
> dữ liệu theo thời gian.

## 2. Dữ liệu năm/tháng (sản lượng, diện tích — feature phụ trợ)
| Nguồn | Nội dung |
|---|---|
| gso.gov.vn (Tổng cục Thống kê) | Diện tích, sản lượng, năng suất theo tỉnh/năm |
| fao.org (FAOSTAT) | Sản lượng, giá nông sản toàn cầu theo năm |
| worldbank.org (Commodity Markets) | Giá hàng hoá thế giới theo tháng |

## 3. Dữ liệu thời tiết theo ngày (feature phụ trợ)
| Nguồn | Nội dung |
|---|---|
| NASA POWER API | Lượng mưa, nhiệt độ theo toạ độ vùng trồng |
| OpenWeatherMap API | Tương tự, cần đăng ký API key |

## 4. Dữ liệu lịch sử quốc tế (để nối dài chuỗi thời gian nếu tự crawl chưa đủ)
- Investing.com, Trading Economics: giá hàng hoá nông sản lịch sử theo ngày/tháng.
- Kaggle: tìm kiếm theo từ khoá "rice price", "pepper price", "commodity price".

## Việc cần làm
- [ ] Xác nhận vùng trồng cụ thể để lấy đúng toạ độ cho API thời tiết.
- [ ] Kiểm tra điều khoản sử dụng (robots.txt) trước khi crawl từng trang.
- [ ] Ghi log rõ nguồn gốc từng dòng dữ liệu (cột `source`) để dễ truy vết lỗi.
