import './Topbar.css'

export default function Topbar({ theme, onToggleTheme, query, onQuery }) {
  return (
    <header className="tb">
      <div className="tb-title">Hệ thống dự đoán giá nông sản</div>
      <label className="tb-search">
        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"><circle cx="11" cy="11" r="7" /><path d="M21 21l-4.3-4.3" /></svg>
        <input value={query} onChange={e => onQuery(e.target.value)} placeholder="Tìm kiếm nông sản..." />
      </label>
      <div className="tb-right">
        <button className="tb-theme" onClick={onToggleTheme}>{theme === 'dark' ? 'Chế độ sáng' : 'Chế độ tối'}</button>
        <div className="tb-avatar" title="Người dùng">T</div>
      </div>
    </header>
  )
}
