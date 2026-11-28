import Logo from './Logo'
import './Sidebar.css'

const MENU = [
  ['overview', 'Tổng quan'],
  ['prices', 'Bảng giá'],
  ['trend', 'Biểu đồ biến động giá'],
  ['forecast', 'Dự báo'],
]

export default function Sidebar({ page, onNavigate }) {
  return (
    <aside className="sb">
      <div className="sb-brand"><Logo /></div>
      <nav className="sb-menu">
        {MENU.map(([id, label]) => (
          <button key={id} className={`sb-item ${page === id ? 'active' : ''}`} aria-current={page === id ? 'page' : undefined} onClick={() => onNavigate(id)}>{label}</button>
        ))}
      </nav>
      <div className="sb-foot">Phạm vi: gạo, cà phê, hồ tiêu</div>
    </aside>
  )
}
