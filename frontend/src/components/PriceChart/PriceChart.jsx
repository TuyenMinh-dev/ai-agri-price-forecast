import { useState } from 'react'
import { formatNumber } from '../../utils/format'
import './PriceChart.css'

const W = 860, H = 340, L = 72, R = 24, T = 30, B = 40

export default function PriceChart({ name, confidence, modelName, dates, past, pred, note }) {
  const [hover, setHover] = useState(null)

  const n0 = past.length - 1 // chỉ số của ngày có giá cuối cùng
  const pts = [...past, ...pred]

  // Thang trục Y với các mốc "đẹp"
  const min = Math.min(...pts), max = Math.max(...pts)
  const raw = Math.max((max - min) / 4, 1), mag = 10 ** Math.floor(Math.log10(raw))
  const step = [1, 2, 2.5, 5, 10].map(m => m * mag).find(s => s >= raw)
  const y0 = Math.floor(min / step) * step, y1 = Math.ceil(max / step) * step || step
  const ticks = []
  for (let v = y0; v <= y1 + 1e-6; v += step) ticks.push(v)

  const x = i => L + (i * (W - L - R)) / (pts.length - 1 || 1)
  const y = v => T + (1 - (v - y0) / (y1 - y0)) * (H - T - B)

  const pastPath = 'M' + past.map((v, i) => `${x(i)},${y(v)}`).join('L')
  const predPath = 'M' + [past[n0], ...pred].map((v, i) => `${x(n0 + i)},${y(v)}`).join('L')
  const isPred = hover !== null && hover > n0

  return (
    <section className="ch">
      <div className="ch-head">
        <div>
          <h2>Diễn biến và dự báo giá</h2>
          <p>{name} · {past.length} ngày thực tế, {pred.length} ngày dự báo</p>
        </div>
        <div className="ch-legend">
          <span><i className="ch-key solid" />Giá thực tế</span>
          <span><i className="ch-key dashed" />Dự báo</span>
        </div>
      </div>

      {note && <p className="ch-note">{note}</p>}

      <div className="ch-wrap">
        <svg viewBox={`0 0 ${W} ${H}`}>
          <text className="ch-txt" x={L - 10} y={12} textAnchor="end">đ/kg</text>
          {ticks.map(v => (
            <g key={v}>
              <line className="ch-grid" x1={L} x2={W - R} y1={y(v)} y2={y(v)} />
              <text className="ch-txt" x={L - 10} y={y(v) + 4} textAnchor="end">{formatNumber(v)}</text>
            </g>
          ))}
          {dates.map((d, i) => (
            <text key={i} className="ch-txt" x={x(i)} y={H - 14} textAnchor="middle">{d.slice(0, 5)}</text>
          ))}

          {pred.length > 0 && <line className="ch-today" x1={x(n0)} x2={x(n0)} y1={T} y2={H - B} />}
          <path className="ch-line" d={pastPath} />
          {pred.length > 0 && <path className="ch-line ch-pred" d={predPath} />}

          {pts.map((v, i) => (
            <g key={i} onMouseEnter={() => setHover(i)} onMouseLeave={() => setHover(null)}>
              <circle cx={x(i)} cy={y(v)} r="14" fill="transparent" />
              <circle className={`ch-pt ${i > n0 ? 'pred' : ''}`} cx={x(i)} cy={y(v)} r={hover === i ? 5.5 : 4} />
            </g>
          ))}
        </svg>

        {hover !== null && (
          <div
            className="ch-tip mono"
            style={{
              left: `${(x(hover) / W) * 100}%`,
              top: `${(y(pts[hover]) / H) * 100}%`,
              transform: hover >= pts.length - 2 ? 'translate(-88%, -125%)' : 'translate(-50%, -125%)',
            }}
          >
            <b>{dates[hover]}</b>
            <div>{isPred ? 'Giá dự báo' : 'Giá'}: {formatNumber(pts[hover])} đ/kg</div>
            <div>
              {!isPred ? 'Loại: Giá thực tế' : confidence != null ? `Độ tin cậy: ${confidence}%` : `Mô hình: ${modelName ?? '—'}`}
            </div>
          </div>
        )}
      </div>
    </section>
  )
}
