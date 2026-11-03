// Tính tăng/giảm từ dữ liệu giá thật. Giá của một ngày = trung bình (thấp nhất, cao nhất).

const EPS = 0.5 // chênh lệch dưới 0,5 đ coi là không đổi

export const directionOf = delta => (delta > EPS ? 'up' : delta < -EPS ? 'down' : 'flat')

// Thay đổi từ giá `from` sang giá `to`
export function changeBetween(from, to) {
  const abs = to - from
  return { abs, pct: from ? (abs / from) * 100 : 0, dir: directionOf(abs) }
}

// Chuỗi giá (cũ → mới) của một sản phẩm, kết thúc đúng ở ngày có giá mới nhất
export function seriesFor(history, product) {
  const rows = history.find(h => h.productId === product.productId)?.rows ?? []
  const upToLatest = rows.filter(r => r.date <= product.date)
  return upToLatest.at(-1)?.date === product.date ? upToLatest : [...upToLatest, product]
}

// Thay đổi của ngày cuối so với ngày liền trước
export function lastChange(series) {
  return series.length < 2 ? null : changeBetween(series.at(-2).avg, series.at(-1).avg)
}

// Map ngày → thay đổi so với dòng liền trước (rows đã sắp cũ → mới)
export function changesByDate(rows) {
  const map = new Map()
  rows.forEach((r, i) => {
    if (i > 0) map.set(r.date, changeBetween(rows[i - 1].avg, r.avg))
  })
  return map
}
