import { useEffect, useState } from 'react'
import Sidebar from './components/Sidebar/Sidebar'
import Topbar from './components/Topbar/Topbar'
import Dashboard from './pages/Dashboard'
import PricePage from './pages/PricePage'
import './App.css'

function readTheme() {
  try {
    return localStorage.getItem('theme') === 'dark' ? 'dark' : 'light'
  } catch {
    return 'light'
  }
}

function App() {
  const [theme, setTheme] = useState(readTheme)
  const [page, setPage] = useState('overview')
  const [query, setQuery] = useState('')

  useEffect(() => {
    document.documentElement.dataset.theme = theme
    try { localStorage.setItem('theme', theme) } catch { /* bỏ qua */ }
  }, [theme])

  return (
    <>
      <Sidebar page={page} onNavigate={setPage} />
      <div className="app-main">
        <Topbar theme={theme} onToggleTheme={() => setTheme(t => (t === 'dark' ? 'light' : 'dark'))} query={query} onQuery={setQuery} />
        <main className="app-content">
          {page === 'overview' && <Dashboard query={query} />}
          {page === 'prices' && <PricePage query={query} />}
          {(page === 'forecast' || page === 'history') && <p className="app-empty">Chức năng này đang được phát triển.</p>}
        </main>
      </div>
    </>
  )
}

export default App
