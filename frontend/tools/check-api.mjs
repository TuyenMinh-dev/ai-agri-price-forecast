// Kiểm tra dữ liệu backend: node tools/check-api.mjs   (đặt API_URL nếu backend không ở cổng 8000)
const BASE = process.env.API_URL ?? 'http://127.0.0.1:8000'
const get = async path => {
  const res = await fetch(BASE + path)
  if (!res.ok) throw new Error(`${path} → HTTP ${res.status}`)
  return res.json()
}

const latest = await get('/api/prices/latest')
const forecasts = await get('/api/forecasts')
const history = await get('/api/prices/history')

const nextDay = iso => { const d = new Date(`${iso}T00:00:00Z`); d.setUTCDate(d.getUTCDate() + 1); return d.toISOString().slice(0, 10) }
const lastDate = latest.map(p => p.price_date).sort().at(-1)
const target = nextDay(lastDate)

console.log(`Backend: ${BASE}`)
console.log(`Ngày cập nhật giá cuối cùng: ${lastDate}  →  ngày dự báo (cuối + 1): ${target}`)
console.log(`Số sản phẩm trong /api/prices/latest: ${latest.length}`)
console.log(`Số dòng trong /api/forecasts: ${forecasts.length}\n`)

for (const crop of ['rice', 'coffee', 'pepper']) {
  const items = latest.filter(p => p.crop_type === crop)
  console.log(`== ${crop}: ${items.length} sản phẩm ==`)
  for (const p of items) {
    const f = forecasts.filter(x => x.product_id === p.product_id)
    const dates = [...new Set(f.map(x => x.forecast_date))].sort()
    const models = [...new Set(f.filter(x => x.forecast_date === target).map(x => x.model_name))]
    const h = history.find(x => x.product_id === p.product_id)?.history.length ?? 0
    const status = f.length === 0 ? 'KHÔNG CÓ dự báo' : models.length ? `dự báo ${target}: ${models.length} mô hình` : `THIẾU dự báo ${target}`
    console.log(`  product_id ${String(p.product_id).padStart(2)} | ${p.category.padEnd(22)} | giá ${p.price_date} ${p.price_min}–${p.price_max} | lịch sử ${h} ngày | ${status}${dates.length ? ` (các ngày có: ${dates.join(', ')})` : ''}`)
  }
}

// product_id có dự báo nhưng không có trong bảng giá
const known = new Set(latest.map(p => p.product_id))
const orphan = [...new Set(forecasts.map(f => f.product_id))].filter(id => !known.has(id))
console.log(orphan.length ? `\nCẢNH BÁO: dự báo có product_id không có trong bảng giá: ${orphan.join(', ')}` : '\nproduct_id của dự báo đều khớp với bảng giá.')
