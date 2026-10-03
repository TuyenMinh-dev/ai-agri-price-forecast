import './Sidebar.css'

const MENU = [
  ['overview', 'Tổng quan'],
  ['prices', 'Giá nông sản'],
  ['forecast', 'Dự báo'],
  ['history', 'Lịch sử giá'],
]

export default function Sidebar({ page, onNavigate }) {
  return (
    <aside className="sb">
      <div className="sb-brand">
        <span className="sb-logo">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M11 20A7 7 0 0 1 9.8 6.1C15.5 5 17 4.5 19 2c1 2 2 4.5 2 8 0 5.5-4.78 10-10 10Z" />
            <path d="M2 21c0-3 1.85-5.36 5.08-6C9.5 14.52 12 13 13 12" />
          </svg>
        </span>
        <div>
          <div className="sb-name">AgriPredict AI</div>
          <div className="sb-sub">Phân tích giá nông sản</div>
        </div>
      </div>
      <nav className="sb-menu">
        {MENU.map(([id, label]) => (
          <button key={id} className={`sb-item ${page === id ? 'active' : ''}`} onClick={() => onNavigate(id)}>{label}</button>
        ))}
      </nav>
    </aside>
  )
}
