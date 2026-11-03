import './PageState.css'

// Hiển thị trạng thái loading / lỗi / rỗng. Trả về null khi dữ liệu đã sẵn sàng.
export default function PageState({ status, error, empty }) {
  if (status === 'loading') return <p className="ps">Đang tải dữ liệu...</p>
  if (status === 'error') {
    return (
      <div className="ps ps-error">
        <p>Không tải được dữ liệu từ backend. Hãy kiểm tra backend đã chạy chưa rồi tải lại trang.</p>
        {error?.message && <small>{error.message}</small>}
      </div>
    )
  }
  if (empty) return <p className="ps">{empty}</p>
  return null
}
