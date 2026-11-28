import { useState } from 'react'
import Delta from '../Delta/Delta'
import PriceChart from './PriceChart'
import Select from '../Select/Select'
import { cropLabel, sortCrops } from '../../api/priceApi'
import { changeBetween } from '../../utils/market'
import { addDays, formatNumber, formatUnit, showDate } from '../../utils/format'
import './PriceTrend.css'

const RANGES = [7, 14, 30, 90].map(d => ({ value: String(d), label: `${d} ngày` }))

// showStats: true → dải thống kê kỳ (trang Biểu đồ biến động giá); false → giá hiện tại + thay đổi (Tổng quan)
export default function PriceTrend({ title, latest, history, showStats }) {
  const crops = sortCrops(new Set(latest.map(p => p.crop)))
  const [crop, setCrop] = useState(crops[0])
  const [productId, setProductId] = useState(null)
  const [days, setDays] = useState('7')

  const products = latest.filter(p => p.crop === crop)
  const product = products.find(p => String(p.productId) === productId) ?? products[0]

  // Lịch sử của sản phẩm, cắt theo khoảng thời gian tính từ ngày có giá cuối cùng của sản phẩm đó
  const allRows = history.find(h => h.productId === product.productId)?.rows ?? []
  const lastDate = allRows.at(-1)?.date
  const rows = lastDate ? allRows.filter(r => r.date >= addDays(lastDate, -(Number(days) - 1))) : []
  const unit = formatUnit(product.unit)
  const period = rows.length > 1 ? changeBetween(rows[0].avg, rows.at(-1).avg) : null

  const stats = rows.length > 0 && [
    ['Giá trung bình kỳ', `${formatNumber(rows.reduce((s, r) => s + r.avg, 0) / rows.length)} ${unit}`],
    ['Thấp nhất kỳ', `${formatNumber(Math.min(...rows.map(r => r.min)))} ${unit}`],
    ['Cao nhất kỳ', `${formatNumber(Math.max(...rows.map(r => r.max)))} ${unit}`],
  ]

  return (
    <section className="panel pt">
      <header className="panel-head pt-head">
        <h2>{title}</h2>
        <div className="toolbar">
          <Select label="Loại nông sản" value={crop} onChange={c => { setCrop(c); setProductId(null) }} options={crops.map(c => ({ value: c, label: cropLabel(c) }))} />
          <Select label="Sản phẩm" value={String(product.productId)} onChange={setProductId} options={products.map(p => ({ value: String(p.productId), label: p.name }))} />
          <Select label="Khoảng thời gian" value={days} onChange={setDays} options={RANGES} />
        </div>
      </header>

      {rows.length === 0 ? (
        <p className="pt-empty">Chưa có dữ liệu lịch sử giá của sản phẩm này.</p>
      ) : (
        <>
          {showStats ? (
            <dl className="pt-stats">
              {stats.map(([label, value]) => (
                <div key={label}><dt>{label}</dt><dd className="tnum">{value}</dd></div>
              ))}
              <div><dt>Thay đổi so với đầu kỳ</dt><dd className="tnum"><Delta change={period} variant="pct" /></dd></div>
            </dl>
          ) : (
            <div className="pt-headline">
              <span className="pt-price tnum">{formatNumber(rows.at(-1).avg)} <small>{unit}</small></span>
              <span className="pt-asof">Giá trung bình ngày {showDate(rows.at(-1).date)}</span>
              {period && <span className="pt-delta tnum"><Delta change={period} variant="pct" /> <small>trong {days} ngày qua</small></span>}
            </div>
          )}
          <div className="pt-body"><PriceChart points={rows} unit={unit} /></div>
        </>
      )}
    </section>
  )
}
