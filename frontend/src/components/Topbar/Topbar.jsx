import './Topbar.css'

export default function Topbar({ theme, onToggleTheme }) {
  const pick = value => { if (value !== theme) onToggleTheme() }
  return (
    <header className="tb">
      <div className="tb-title">Agricultural Commodity Intelligence</div>
      <div className="tb-right">
        <div className="tb-theme" role="group" aria-label="Giao diện">
          <button className={theme === 'light' ? 'on' : ''} aria-pressed={theme === 'light'} onClick={() => pick('light')}>Sáng</button>
          <button className={theme === 'dark' ? 'on' : ''} aria-pressed={theme === 'dark'} onClick={() => pick('dark')}>Tối</button>
        </div>
        <div className="tb-avatar" title="Người dùng">T</div>
      </div>
    </header>
  )
}
