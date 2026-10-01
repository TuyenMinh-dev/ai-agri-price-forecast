# API Specification — Agri Price Forecast

Tài liệu mô tả các API mà Backend cung cấp cho Frontend.

- **Base URL (dev):** `http://127.0.0.1:8000`
- **Swagger UI:** `http://127.0.0.1:8000/docs` (test trực tiếp trên trình duyệt)
- **Ngày tháng:** Tất cả tham số ngày dùng format `YYYY-MM-DD` (ví dụ: `2026-09-29`)
- **Số tiền:** Trả về dạng string (`"8700.00"`) để bảo toàn độ chính xác
- **CORS:** Đã cấu hình cho phép mọi origin (dev). Frontend gọi trực tiếp không bị chặn.

---

## 1. Health Check

Kiểm tra server còn sống không.

- **Method:** `GET`
- **URL:** `/health`
- **Params:** Không

**Response mẫu:**
```json
{ "status": "ok" }
```



## 2. Lấy giá mới nhất của từng mặt hàng
- **Method:** `GET`

- **URL:**  `/api/prices/latest`

- **Params:** Không

**Response mẫu: Mảng các object, mỗi object = 1 sản phẩm + giá mới nhất của nó.**
```json
[
  {
    "product_id": 1,
    "crop_type": "rice",
    "category": "NL IR 504",
    "unit": "VND/kg",
    "price_date": "2026-09-29",
    "price_min": "8700.00",
    "price_max": "8800.00",
    "source": "vietnambiz.vn (gốc: luagaoviet.com)"
  }
]
```
**Ghi chú:**

- Trả về 13 phần tử (tương ứng 13 sản phẩm hiện có trong CSDL).
- price_date là ngày mới nhất của riêng sản phẩm đó — có thể khác nhau giữa các sản phẩm.


## 3. Lấy lịch sử giá (có filter)

- **Method:** `GET`
- **URL:** `/api/prices/history`

**Query parameters (tất cả optional):**

| Tên | Kiểu | Mô tả |
|-----|------|-------|
| `product_id` | int | Lọc theo ID sản phẩm (ví dụ: `1`) |
| `crop_type` | string | Lọc theo loại: `rice`, `pepper`, `coffee` |
| `start_date` | date `YYYY-MM-DD` | Lọc từ ngày |
| `end_date` | date `YYYY-MM-DD` | Lọc đến ngày |

**Ví dụ URL:** /api/prices/history?crop_type=coffee&start_date=2026-09-01&end_date=2026-09-30

**Response mẫu:** Mảng các object, mỗi object = 1 sản phẩm + list history của nó.

```json
[
  {
    "product_id": 1,
    "crop_type": "rice",
    "category": "NL IR 504",
    "unit": "VND/kg",
    "history": [
      {
        "price_date": "2026-09-29",
        "price_min": "8700.00",
        "price_max": "8800.00",
        "source": "vietnambiz.vn (gốc: luagaoviet.com)"
      }
    ]
  }
]
```
**Ghi chú:**

- Nếu không truyền filter nào → trả về tất cả lịch sử giá của mọi sản phẩm.
- Lịch sử được sắp xếp mới nhất trước (giảm dần theo price_date).
- Format ngày PHẢI là YYYY-MM-DD. Nếu sai → FastAPI trả lỗi 422 với thông báo rõ ràng.


## 4. Lấy dự báo giá

- **Method:** `GET`
- **URL:** `/api/forecasts`

**Query parameters (tất cả optional):**

| Tên | Kiểu | Mô tả |
|-----|------|-------|
| `product_id` | int | Lọc theo ID sản phẩm |
| `crop_type` | string | Lọc theo loại: `rice`, `pepper`, `coffee` |
| `model_name` | string | Lọc theo tên model AI (ví dụ: `Random Forest`) |

**Ví dụ URL:** /api/forecasts?crop_type=rice&model_name=Random%20Forest


**Response mẫu:**

```json
[
  {
    "id": 1,
    "product_id": 1,
    "crop_type": "rice",
    "category": "NL IR 504",
    "unit": "VND/kg",
    "forecast_date": "2026-09-19",
    "predicted_price": "8615.56",
    "model_name": "Linear Regression"
  }
]
``` 
**Ghi chú:**

- Mỗi sản phẩm hiện có 3 model dự báo: Linear Regression, Random Forest, XGBoost.
- Nếu bảng forecasts rỗng → trả về mảng rỗng [] (không phải lỗi).


## 5. Lỗi có thể gặp

| HTTP Code | Nguyên nhân | Cách xử lý |
|-----------|-------------|------------|
| `422 Unprocessable Entity` | Tham số sai format (ví dụ ngày dùng `_` thay vì `-`) | Kiểm tra lại format: ngày `YYYY-MM-DD`, số là số nguyên |
| `500 Internal Server Error` | CSDL cloud tạm mất kết nối | Thử lại sau vài giây. Backend đã bật `pool_pre_ping` để tự phục hồi. |



## 6. Ghi chú cho Frontend

- **CORS đã cấu hình** cho mọi origin (dev). Production sẽ giới hạn cụ thể.
- **Số tiền trả về dạng string** — nếu cần tính toán, dùng thư viện `decimal` (JS: `BigNumber`, Python: `decimal.Decimal`).
- **Mọi API đều là `GET`** — không có POST/PUT/DELETE trong giai đoạn hiện tại.
- **Swagger UI** ở `/docs` cho phép test trực tiếp — dùng để debug khi cần.

