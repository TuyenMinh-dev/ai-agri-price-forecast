import { addDays } from '../utils/format'

// Toàn bộ lời gọi backend nằm ở file này.
const BASE_URL = import.meta.env?.VITE_API_URL ?? 'http://127.0.0.1:8000'

// Mô hình dùng cho con số "giá dự báo" ở Tổng quan và trang Dự báo (phải khớp model_name của backend)
export const MAIN_MODEL = 'Random Forest'

// "Ngày hiện tại" để tính ngày dự báo (= ngày hiện tại + 1):
//   'latest' → ngày cập nhật giá cuối cùng của backend
//   'today'  → ngày trên đồng hồ máy tính
const FORECAST_BASE = 'latest'

// Số ngày lịch sử tải về (lớn nhất trong các lựa chọn khoảng thời gian)
export const HISTORY_DAYS = 90

export const CROP_LABELS = { rice: 'Gạo', coffee: 'Cà phê', pepper: 'Hồ tiêu' }
const CROP_ORDER = Object.keys(CROP_LABELS)
export const cropLabel = crop => CROP_LABELS[crop] ?? crop
export const sortCrops = crops => [...crops].sort((a, b) => CROP_ORDER.indexOf(a) - CROP_ORDER.indexOf(b))

// ---------- gọi API ----------

const CACHE_MS = 10_000 // gộp các request trùng nhau (React StrictMode gọi effect 2 lần khi dev)
const cache = new Map()

async function fetchJson(url, path) {
  let res
  try {
    res = await fetch(url)
  } catch {
    throw new Error(`Không kết nối được backend (${BASE_URL})`)
  }
  if (!res.ok) throw new Error(`Backend trả lỗi ${res.status} tại ${path}`)
  return res.json()
}

function request(path, params = {}) {
  const query = new URLSearchParams(params).toString()
  const url = `${BASE_URL}${path}${query ? `?${query}` : ''}`
  const hit = cache.get(url)
  if (hit && Date.now() - hit.at < CACHE_MS) return hit.promise
  const promise = fetchJson(url, path).catch(err => {
    cache.delete(url)
    throw err
  })
  cache.set(url, { at: Date.now(), promise })
  return promise
}

// Giá trả về dạng chuỗi ("8700.00") → số; giá trung bình ngày = (thấp nhất + cao nhất) / 2
function toPriceRow(r) {
  const min = Number(r.price_min)
  const max = Number(r.price_max)
  return { date: r.price_date, min, max, avg: (min + max) / 2 }
}

// GET /api/prices/latest → giá mới nhất của từng sản phẩm
export async function getLatestPrices() {
  const raw = await request('/api/prices/latest')
  return raw
    .map(p => ({ productId: p.product_id, crop: p.crop_type, name: p.category, unit: p.unit, source: p.source, ...toPriceRow(p) }))
    .sort((a, b) => a.productId - b.productId)
}

// GET /api/prices/history → lịch sử giá (mỗi sản phẩm một danh sách, cũ → mới)
export async function getPriceHistory(startDate) {
  const raw = await request('/api/prices/history', startDate ? { start_date: startDate } : {})
  return raw.map(h => ({
    productId: h.product_id,
    crop: h.crop_type,
    name: h.category,
    rows: h.history.map(toPriceRow).sort((a, b) => a.date.localeCompare(b.date)),
  }))
}

// GET /api/forecasts → dự báo của các mô hình
export async function getForecasts() {
  const raw = await request('/api/forecasts')
  return raw.map(f => ({
    productId: f.product_id,
    crop: f.crop_type,
    name: f.category,
    date: f.forecast_date,
    price: Number(f.predicted_price),
    model: f.model_name,
  }))
}

// ---------- gộp dữ liệu cho từng trang ----------

const newestDate = rows => rows.map(r => r.date).sort().at(-1) ?? null

export function forecastDateFor(lastDate) {
  const base = FORECAST_BASE === 'today' ? new Date().toLocaleDateString('en-CA') : lastDate
  return addDays(base, 1)
}

async function load({ history = false, forecasts = false }) {
  const latest = await getLatestPrices()
  const lastDate = newestDate(latest)
  const [historyData, forecastData] = await Promise.all([
    history && lastDate ? getPriceHistory(addDays(lastDate, -(HISTORY_DAYS - 1))) : [],
    forecasts ? getForecasts() : [],
  ])
  return {
    latest,
    lastDate,
    history: historyData,
    forecasts: forecastData,
    targetDate: lastDate ? forecastDateFor(lastDate) : null,
  }
}

export const loadOverview = () => load({ history: true, forecasts: true })
export const loadPrices = () => load({ history: true })
export const loadForecast = () => load({ forecasts: true })

// Dự báo của một sản phẩm trong ngày `date`, ưu tiên mô hình chính
export function forecastsOf(forecasts, productId, date) {
  return forecasts.filter(f => f.productId === productId && f.date === date)
}
export function mainForecast(rows) {
  return rows.find(f => f.model === MAIN_MODEL) ?? rows[0] ?? null
}
