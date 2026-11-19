import { useEffect, useState } from 'react'
import Sidebar from './components/Sidebar/Sidebar'
import { FAVICON_HREF } from './components/Sidebar/Logo'
import Topbar from './components/Topbar/Topbar'
import Dashboard from './pages/Dashboard'
import PricePage from './pages/PricePage'
import TrendPage from './pages/TrendPage'
import ForecastPage from './pages/ForecastPage'
import './App.css'

const PAGES = { overview: Dashboard, prices: PricePage, trend: TrendPage, forecast: ForecastPage }

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

  useEffect(() => {
    document.documentElement.dataset.theme = theme
    try { localStorage.setItem('theme', theme) } catch { /* bỏ qua */ }
  }, [theme])

  // Tên tab và biểu tượng tab của AGRISIGHT
  useEffect(() => {
    document.title = 'AGRISIGHT'
    let link = document.querySelector("link[rel~='icon']")
    if (!link) {
      link = document.createElement('link')
      link.rel = 'icon'
      document.head.appendChild(link)
    }
    link.type = 'image/svg+xml'
    link.href = FAVICON_HREF
  }, [])

  const Page = PAGES[page]

  return (
    <>
      <Sidebar page={page} onNavigate={setPage} />
      <div className="app-main">
        <Topbar theme={theme} onToggleTheme={() => setTheme(t => (t === 'dark' ? 'light' : 'dark'))} />
        <main className="app-content"><Page /></main>
      </div>
    </>
  )
}

export default App
