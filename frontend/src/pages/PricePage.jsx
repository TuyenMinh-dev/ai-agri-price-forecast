import { useState } from 'react'
import Delta from '../components/Delta/Delta'
import PageState from '../components/PageState/PageState'
import Select from '../components/Select/Select'
import useApi from '../utils/useApi'
import { cropLabel, loadPrices, sortCrops } from '../api/priceApi'
import { changesByDate } from '../utils/market'
import { addDays, formatNumber, formatUnit, matchesQuery, showDate } from '../utils/format'
import './PricePage.css'

const RANGES = [
  { value: 'latest', label: 'Mới nhất' },
  ...[7, 30, 90].map(d => ({ value: String(d), label: `${d} ngày` })),
]

export default function PricePage() {
  const { status, data, error } = useApi(loadPrices)
  const [crop, setCrop] = useState('all')
  const [productId, setProductId] = useState('all')
  const [range, setRange] = useState('latest')
  const [query, setQuery] = useState('')

  const empty = status === 'ready' && data.latest.length === 0 && 'Backend chưa có dữ liệu giá.'
  if (status !== 'ready' || empty) return <PageState status={status} error={error} empty={empty} />

  const { latest, history, lastDate } = data
  const crops = sortCrops(new Set(latest.map(p => p.crop)))
  const products = latest.filter(p => crop === 'all' || p.crop === crop)

  // Thay đổi so với ngày liền trước, tính trên toàn bộ lịch sử của từng sản phẩm
  const changes = new Map(history.map(h => [h.productId, changesByDate(h.rows)]))
  const withChange = r => ({ ...r, change: changes.get(r.productId)?.get(r.date) ?? null })

  // "Mới nhất": mỗi sản phẩm một dòng; còn lại: lịch sử trong N ngày gần nhất
  const cutoff = range === 'latest' ? null : addDays(lastDate, -(Number(range) - 1))
  const source = range === 'latest'
    ? latest
    : history.flatMap(h => h.rows.filter(r => r.date >= cutoff).map(r => ({ ...r, productId: h.productId, crop: h.crop, name: h.name, unit: latest.find(p => p.productId === h.productId)?.unit })))

  const rows = source
    .filter(r => (crop === 'all' || r.crop === crop) && (productId === 'all' || String(r.productId) === productId))
    .filter(r => matchesQuery(`${cropLabel(r.crop)} ${r.name}`, query))
    .sort((a, b) => b.date.localeCompare(a.date) || a.productId - b.productId)
    .map(withChange)

  return (
    <div className="page">
      <div className="page-head">
        <div>
          <h1>Bảng giá</h1>
          <p>Giá thấp nhất và cao nhất theo từng sản phẩm</p>
        </div>
        <span className="page-meta">Cập nhật: {showDate(lastDate)}</span>
      </div>

      <section className="panel">
        <div className="panel-head pp-tools">
          <label className="pp-search">
            <span>Tìm kiếm</span>
            <div>
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" aria-hidden="true"><circle cx="11" cy="11" r="7" /><path d="M21 21l-4.3-4.3" /></svg>
              <input value={query} onChange={e => setQuery(e.target.value)} placeholder="Nhập tên nông sản hoặc sản phẩm..." />
            </div>
          </label>
          <Select label="Loại nông sản" value={crop} onChange={c => { setCrop(c); setProductId('all') }} options={[{ value: 'all', label: 'Tất cả' }, ...crops.map(c => ({ value: c, label: cropLabel(c) }))]} />
          <Select label="Sản phẩm" value={productId} onChange={setProductId} options={[{ value: 'all', label: 'Tất cả' }, ...products.map(p => ({ value: String(p.productId), label: p.name }))]} />
          <Select label="Thời gian" value={range} onChange={setRange} options={RANGES} />
        </div>

        <div className="tbl-wrap">
          <table className="tbl">
            <thead>
              <tr><th>Loại</th><th>Sản phẩm</th><th>Ngày</th><th className="num">Giá thấp nhất</th><th className="num">Giá cao nhất</th><th className="num">So với ngày trước</th></tr>
            </thead>
            <tbody>
              {rows.map(r => (
                <tr key={`${r.productId}-${r.date}`}>
                  <td>{cropLabel(r.crop)}</td>
                  <td>{r.name}</td>
                  <td>{showDate(r.date)}</td>
                  <td className="num">{formatNumber(r.min)} {formatUnit(r.unit)}</td>
                  <td className="num">{formatNumber(r.max)} {formatUnit(r.unit)}</td>
                  <td className="num"><Delta change={r.change} variant="pct" /></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {rows.length === 0 && <p className="pp-none">Không có kết quả phù hợp.</p>}
        {rows.length > 0 && <p className="panel-foot pp-count">{rows.length} dòng · thay đổi so sánh giá trung bình của ngày với ngày có giá liền trước</p>}
      </section>
    </div>
  )
}
