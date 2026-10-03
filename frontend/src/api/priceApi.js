import * as mock from '../data/mockData'

const BASE_URL = import.meta.env?.VITE_API_URL ?? 'http://127.0.0.1:8000'
const MODEL = 'Random Forest' // mô hình dùng cho thẻ giá và biểu đồ (đổi tại đây nếu muốn)
const HISTORY_POINTS = 7
const FORECAST_POINTS = 3
const RECENT_DAYS = 30

// Dashboard hiển thị mọi sản phẩm thuộc các nhóm này (tiêu 'pepper' bị bỏ qua)
const CROPS = { rice: 'Lúa gạo', coffee: 'Cà phê' }

async function request(path, params = {}) {
  const query = new URLSearchParams(params).toString()
  const res = await fetch(`${BASE_URL}${path}${query ? `?${query}` : ''}`)
  if (!res.ok) throw new Error(`Lỗi ${res.status} khi gọi ${path}`)
  return res.json()
}

const mid = row => (Number(row.price_min) + Number(row.price_max)) / 2 // giá = trung bình min/max
const showDate = iso => iso.split('-').reverse().join('/')              // 2026-09-29 → 29/09/2026
const lastDate = rows => rows.map(r => r.price_date).sort().at(-1)

// Chỉ lấy lịch sử RECENT_DAYS ngày gần nhất (tính từ ngày có giá mới nhất)
function startDate(latest) {
  const d = new Date(lastDate(latest))
  d.setUTCDate(d.getUTCDate() - RECENT_DAYS)
  return d.toISOString().slice(0, 10)
}

export async function getDashboardData() {
  const latest = await request('/api/prices/latest')
  if (!latest.length) return { products: [] }

  const [history, forecasts] = await Promise.all([
    request('/api/prices/history', { crop_type: 'rice', start_date: startDate(latest) }),
    request('/api/forecasts', { crop_type: 'rice' }),
  ])

  const products = []
  const charts = {}
  const comparison = []
  const modelNames = new Set()

  for (const item of latest.filter(p => p.crop_type === 'rice')) {
    const id = `p${item.product_id}`
    const label = `${CROPS[item.crop_type]} · ${item.category}`

    // lịch sử: API trả mới → cũ, biểu đồ cần cũ → mới
    const rows = history.find(h => h.product_id === item.product_id)?.history ?? []
    const past = rows.length ? rows.slice(0, HISTORY_POINTS).reverse() : [item]

    // dự báo theo từng mô hình, sắp xếp theo ngày tăng dần
    const byModel = {}
    forecasts
      .filter(f => f.product_id === item.product_id)
      .sort((a, b) => a.forecast_date.localeCompare(b.forecast_date))
      .forEach(f => {
        (byModel[f.model_name] ??= []).push(f)
        modelNames.add(f.model_name)
      })

    // chỉ coi là "dự báo" những ngày sau ngày có giá cuối cùng
    const futureOf = list => list.filter(f => f.forecast_date > item.price_date).slice(0, FORECAST_POINTS)
    const pick = list => futureOf(list).at(-1) ?? list.at(-1)

    const modelRows = byModel[MODEL] ?? Object.values(byModel)[0] ?? []
    const future = futureOf(modelRows)
    const target = pick(modelRows)
    const current = mid(item)
    const predicted = target ? Number(target.predicted_price) : null

    let note = null
    if (!modelRows.length) note = 'Backend chưa trả dự báo cho sản phẩm này (kiểm tra /api/forecasts).'
    else if (!future.length) note = `Các dự báo hiện có đều không sau ngày giá mới nhất (${showDate(item.price_date)}) nên không vẽ đường dự báo.`

    products.push({
      id,
      group: item.crop_type,
      name: label,
      short: item.category,
      current,
      predicted,
      predictedDate: target ? showDate(target.forecast_date).slice(0, 5) : null,
      change: predicted == null ? null : ((predicted - current) / current) * 100,
      confidence: null, // backend chưa có độ tin cậy
      modelName: target?.model_name ?? null,
    })

    charts[id] = {
      dates: [...past.map(r => showDate(r.price_date)), ...future.map(f => showDate(f.forecast_date))],
      past: past.map(mid),
      pred: future.map(f => Number(f.predicted_price)),
      note,
    }

    comparison.push({
      name: label,
      current,
      trend: predicted == null ? null : predicted >= current ? 'up' : 'down',
      models: Object.fromEntries(Object.entries(byModel).map(([m, list]) => [m, Number(pick(list).predicted_price)])),
    })
  }

  return {
    lastUpdated: showDate(lastDate(latest)),
    products,
    charts,
    comparison,
    models: [...modelNames].sort(),
  }
}

export async function getPriceList() {
  const latest = await request('/api/prices/latest')
  if (!latest.length) return { groups: [], typesByGroup: {}, rows: [] }

  const history = (await request('/api/prices/history', { start_date: startDate(latest) })).filter(h => CROPS[h.crop_type])

  const rows = history
    .flatMap(h => h.history.map(r => ({ group: h.crop_type, type: h.category, date: r.price_date, min: Number(r.price_min), max: Number(r.price_max) })))
    .sort((a, b) => b.date.localeCompare(a.date))
    .map(r => ({ ...r, date: showDate(r.date) }))

  const typesByGroup = {}
  for (const h of history) {
    const list = (typesByGroup[h.crop_type] ??= [])
    if (!list.includes(h.category)) list.push(h.category)
  }

  return { groups: mock.groups.filter(g => typesByGroup[g.id]), typesByGroup, rows }
}
