// Đường xu hướng nhỏ; màu theo hướng đi của cả đoạn (tăng / giảm / đi ngang)
export default function Sparkline({ values, dir, width = 92, height = 28 }) {
  if (values.length < 2) return <span className="flat">—</span>
  const pad = 3
  const min = Math.min(...values), max = Math.max(...values)
  const x = i => pad + (i * (width - 2 * pad)) / (values.length - 1)
  const y = v => (max === min ? height / 2 : pad + (1 - (v - min) / (max - min)) * (height - 2 * pad))
  const points = values.map((v, i) => `${x(i)},${y(v)}`).join(' ')
  const last = values.length - 1
  return (
    <svg className={`spark ${dir}`} width={width} height={height} aria-hidden="true">
      <polyline points={points} fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinejoin="round" strokeLinecap="round" />
      <circle cx={x(last)} cy={y(values[last])} r="2.4" fill="currentColor" />
    </svg>
  )
}
