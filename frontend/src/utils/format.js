// 8200 → "8.200"
export const formatNumber = n => String(Math.round(n)).replace(/\B(?=(\d{3})+(?!\d))/g, '.')

// 3.6 → "+3,6%", -2.8 → "-2,8%"
export const formatPercent = n => `${n > 0 ? '+' : n < 0 ? '-' : ''}${Math.abs(n).toFixed(1).replace('.', ',')}%`

// Tìm theo tên, không phân biệt hoa thường
export const matchesQuery = (text, query) => text.toLowerCase().includes(query.trim().toLowerCase())
