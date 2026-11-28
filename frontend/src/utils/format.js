// 18400 → "18.400"
export const formatNumber = n => String(Math.round(n)).replace(/\B(?=(\d{3})+(?!\d))/g, '.')

// 356 → "+356", -120 → "-120", 0 → "0"
export const formatSigned = n => `${n > 0 ? '+' : n < 0 ? '-' : ''}${formatNumber(Math.abs(n))}`

// 3.6 → "+3,6%", -2.8 → "-2,8%"
export const formatPercent = n => `${n > 0 ? '+' : n < 0 ? '-' : ''}${Math.abs(n).toFixed(1).replace('.', ',')}%`

// "VND/kg" → "đ/kg"
export const formatUnit = unit => (unit ?? 'VND/kg').replace('VND', 'đ')

// "2026-10-03" → "03/10/2026"
export const showDate = iso => iso.split('-').reverse().join('/')

// Cộng/trừ ngày trên chuỗi "YYYY-MM-DD"
export const addDays = (iso, n) => {
  const d = new Date(`${iso}T00:00:00Z`)
  d.setUTCDate(d.getUTCDate() + n)
  return d.toISOString().slice(0, 10)
}

// Tìm theo tên, không phân biệt hoa thường
export const matchesQuery = (text, query) => text.toLowerCase().includes(query.trim().toLowerCase())
