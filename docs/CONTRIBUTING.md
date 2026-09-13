# Quy tắc làm việc nhóm

## Nhánh (Branch)
- `main` — code ổn định, luôn chạy được, chỉ merge qua Pull Request.
- `develop` — nhánh tích hợp, các feature merge vào đây trước khi lên `main`.
- `feature/<ten-module>` — mỗi người làm trên nhánh riêng, ví dụ:
  - `feature/crawler`
  - `feature/ml-models`
  - `feature/backend-api`
  - `feature/frontend-ui`

## Quy ước commit
Dùng dạng: `<loại>: <mô tả ngắn>`
- `feat:` thêm chức năng mới
- `fix:` sửa lỗi
- `docs:` cập nhật tài liệu
- `refactor:` sửa code không đổi hành vi
- `data:` cập nhật/thêm dữ liệu

Ví dụ: `feat: thêm API lấy giá theo vùng`

## Pull Request
- Đặt tên PR rõ ràng, mô tả ngắn gọn đã làm gì.
- Ít nhất 1 thành viên khác review trước khi merge vào `develop`.
- Không merge thẳng vào `main` — chỉ merge `develop` → `main` khi đã test ổn.

## Quản lý task
- Dùng GitHub Issues hoặc GitHub Projects (Kanban board): To do / In progress / Done.
- Mỗi issue gắn nhãn theo module: `crawler`, `ml`, `backend`, `frontend`, `docs`.

## Dữ liệu
- Không commit dữ liệu thô lớn hoặc model đã train vào git (đã có trong
  `.gitignore`) — nếu cần chia sẻ, dùng Google Drive/Releases và ghi link vào
  `docs/DATA_SOURCES.md`.
