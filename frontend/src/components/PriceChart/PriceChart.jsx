import { useEffect, useRef, useState } from 'react'
import Delta from '../Delta/Delta'
import { changeBetween } from '../../utils/market'
import { formatNumber, showDate } from '../../utils/format'
import './PriceChart.css'

const H = 280, L = 26, R = 78, T = 24, B = 30

// points: [{ date: 'YYYY-MM-DD', min, max, avg }] theo thứ tự cũ → mới
// Đường nối các điểm = giá trung bình ngày. Đoạn tăng so với ngày trước màu xanh, đoạn giảm màu đỏ.
export default function PriceChart({ points, unit }) {
  const wrapRef = useRef(null)
  const [W, setW] = useState(720)
  const [hover, setHover] = useState(null)

  // Vẽ theo bề rộng thật của khung chứa để chữ không bị co giãn
  useEffect(() => {
    const ro = new ResizeObserver(([entry]) => setW(Math.max(360, Math.round(entry.contentRect.width))))
    ro.observe(wrapRef.current)
    return () => ro.disconnect()
  }, [])

  const n = points.length
  let min = Math.min(...points.map(p => p.min)), max = Math.max(...points.map(p => p.max))
  if (min === max) { const pad = Math.max(max * 0.02, 1); min -= pad; max += pad }

  // Trục giá với các mốc "đẹp"
  const raw = (max - min) / 4, mag = 10 ** Math.floor(Math.log10(raw))
  const step = [1, 2, 2.5, 5, 10].map(m => m * mag).find(s => s >= raw)
  const y0 = Math.floor(min / step) * step, y1 = Math.ceil(max / step) * step
  const ticks = []
  for (let v = y0; v <= y1 + 1e-6; v += step) ticks.push(v)

  const plotRight = W - R
  const x = i => L + (n === 1 ? (plotRight - L) / 2 : (i * (plotRight - L)) / (n - 1))
  const y = v => T + (1 - (v - y0) / (y1 - y0)) * (H - T - B)
  const clampY = v => Math.min(H - B, Math.max(T, y(v)))

  const changes = points.map((p, i) => (i === 0 ? null : changeBetween(points[i - 1].avg, p.avg)))
  const dirAt = i => changes[i]?.dir ?? changes[1]?.dir ?? 'flat'

  // Nhãn trục ngày thưa dần khi có nhiều ngày; luôn có nhãn ở ngày cuối
  const maxLabels = Math.max(2, Math.floor((plotRight - L) / 64))
  const every = Math.ceil(n / maxLabels)
  const showLabel = i => (n - 1 - i) % every === 0

  const onMove = e => {
    const rect = e.currentTarget.ownerSVGElement.getBoundingClientRect()
    const ratio = (e.clientX - rect.left - L) / (plotRight - L)
    setHover(n === 1 ? 0 : Math.min(n - 1, Math.max(0, Math.round(ratio * (n - 1)))))
  }

  const p = hover === null ? null : points[hover]
  const last = n - 1
  const lastDir = dirAt(last)

  return (
    <div className="pch">
      <div className="pch-wrap" ref={wrapRef}>
        <svg width={W} height={H} role="img" aria-label={`Biểu đồ giá trung bình theo ngày, từ ${showDate(points[0].date)} đến ${showDate(points[last].date)}`}>
          <text className="pch-txt" x={L} y={11}>{unit}</text>
          {ticks.map(v => (
            <g key={v}>
              <line className="pch-grid" x1={L} x2={plotRight} y1={y(v)} y2={y(v)} />
              <text className="pch-txt" x={plotRight + 10} y={y(v) + 4}>{formatNumber(v)}</text>
            </g>
          ))}
          {points.map((pt, i) => showLabel(i) && (
            <text key={pt.date} className="pch-txt" x={x(i)} y={H - 10} textAnchor="middle">{showDate(pt.date).slice(0, 5)}</text>
          ))}

          {p && <line className="pch-cross" x1={x(hover)} x2={x(hover)} y1={T} y2={H - B} />}
          {p && (
            <g className="pch-range">
              <rect x={x(hover) - 3} y={clampY(p.max)} width="6" height={Math.max(2, clampY(p.min) - clampY(p.max))} rx="1" />
              <line x1={x(hover) - 7} x2={x(hover) + 7} y1={clampY(p.max)} y2={clampY(p.max)} />
              <line x1={x(hover) - 7} x2={x(hover) + 7} y1={clampY(p.min)} y2={clampY(p.min)} />
            </g>
          )}

          {/* Đường giá: từng đoạn tô màu theo tăng / giảm so với ngày trước */}
          {points.slice(1).map((pt, k) => (
            <line key={pt.date} className={`pch-seg ${dirAt(k + 1)}`} x1={x(k)} y1={y(points[k].avg)} x2={x(k + 1)} y2={y(pt.avg)} />
          ))}
          {points.map((pt, i) => (n <= 40 || i === hover) && (
            <circle key={pt.date} className={`pch-pt ${dirAt(i)}`} cx={x(i)} cy={y(pt.avg)} r={i === hover ? 5 : 3} />
          ))}

          {/* Thẻ giá cuối */}
          <line className={`pch-last ${lastDir}`} x1={x(last)} x2={plotRight} y1={y(points[last].avg)} y2={y(points[last].avg)} />
          <g className={`pch-tag ${lastDir}`}>
            <rect x={plotRight + 2} y={y(points[last].avg) - 10} width={R - 6} height="20" rx="2" />
            <text x={plotRight + 2 + (R - 6) / 2} y={y(points[last].avg) + 4} textAnchor="middle">{formatNumber(points[last].avg)}</text>
          </g>

          <rect x="0" y={T} width={plotRight} height={H - T - B} fill="transparent" onMouseMove={onMove} onMouseLeave={() => setHover(null)} />
        </svg>

        {p && (
          <div className="pch-tip tnum" style={{ left: x(hover), top: y(p.avg), transform: `translate(${x(hover) > plotRight * 0.6 ? 'calc(-100% - 14px)' : '14px'}, ${y(p.avg) > H / 2 ? 'calc(-100% - 8px)' : '8px'})` }}>
            <b>{showDate(p.date)}</b>
            <div>Giá thấp nhất: <b>{formatNumber(p.min)} {unit}</b></div>
            <div>Giá cao nhất: <b>{formatNumber(p.max)} {unit}</b></div>
            <div>Giá trung bình: <b>{formatNumber(p.avg)} {unit}</b></div>
            <div className="pch-tip-delta">So với ngày trước: <Delta change={changes[hover]} /></div>
          </div>
        )}
      </div>

      <div className="pch-foot">
        <div className="pch-legend">
          <span><i className="sw up" />Giá tăng so với ngày trước</span>
          <span><i className="sw down" />Giá giảm</span>
          <span><i className="sw flat" />Không đổi</span>
        </div>
        <p className="pch-note">Giá hiển thị trên biểu đồ là giá trung bình của ngày.</p>
      </div>
    </div>
  )
}
