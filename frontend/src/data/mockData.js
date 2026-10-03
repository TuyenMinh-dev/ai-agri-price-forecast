// Toàn bộ dữ liệu giả. Khi có backend, thay ở src/api/priceApi.js.

const base = new Date(2026, 8, 29)
const shiftDate = n => {
  const d = new Date(base)
  d.setDate(base.getDate() + n)
  return d.toLocaleDateString('en-GB') // dd/mm/yyyy
}

export const lastUpdated = shiftDate(0)

export const products = [
  { id: 'rice', name: 'Lúa gạo', short: 'Lúa gạo', current: 8200, predicted: 8500, change: 3.6, confidence: 87 },
  { id: 'robusta', name: 'Cà phê Robusta', short: 'Robusta', current: 42000, predicted: 40800, change: -2.8, confidence: 82 },
  { id: 'arabica', name: 'Cà phê Arabica', short: 'Arabica', current: 58000, predicted: 60000, change: 3.4, confidence: 79 },
]

export const groups = [
  { id: 'rice', label: 'Lúa gạo' },
  { id: 'coffee', label: 'Cà phê' },
]

// 7 ngày thực tế (23/09 → 29/09) + 3 ngày dự báo (30/09 → 02/10)
export const chartDates = Array.from({ length: 10 }, (_, i) => shiftDate(i - 6))

export const charts = {
  rice: { past: [7900, 7950, 8050, 8000, 8100, 8150, 8200], pred: [8320, 8410, 8500] },
  robusta: { past: [43500, 43200, 42900, 42600, 42300, 42100, 42000], pred: [41600, 41200, 40800] },
  arabica: { past: [55800, 56200, 56600, 57000, 57200, 57700, 58000], pred: [58700, 59400, 60000] },
}

export const comparison = [
  { name: 'Lúa gạo', today: 8200, week: 8500, month: 8700, trend: 'up' },
  { name: 'Robusta', today: 42000, week: 40800, month: 41500, trend: 'down' },
  { name: 'Arabica', today: 58000, week: 60000, month: 61000, trend: 'up' },
]

// Trang "Giá nông sản"
export const riceTypes = ['NL IR 504', 'NL CL 555', 'Tấm', 'Cám']
const priceBase = [[12000, 14000], [12500, 14500], [10000, 12000], [8000, 9500]]
export const priceRows = [0, -1, -2].flatMap(day =>
  riceTypes.map((type, i) => ({
    type,
    date: shiftDate(day),
    min: priceBase[i][0] + day * 100,
    max: priceBase[i][1] + day * 100,
  }))
)
