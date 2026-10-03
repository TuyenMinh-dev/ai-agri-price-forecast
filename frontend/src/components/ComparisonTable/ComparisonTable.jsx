import { formatNumber } from '../../utils/format'
import './ComparisonTable.css'

export default function ComparisonTable({ rows, models }) {
  const columns = models.length ? models : ['Dự báo']
  return (
    <section className="ct">
      <div className="ct-head">
        <h2>So sánh giá dự báo theo mô hình</h2>
        <span>Đơn vị: đ/kg</span>
      </div>
      <table className="ct-table">
        <thead>
          <tr>
            <th>Sản phẩm</th>
            <th className="num">Giá hiện tại</th>
            {columns.map(m => <th key={m} className="num">{m}</th>)}
            <th>Xu hướng</th>
          </tr>
        </thead>
        <tbody>
          {rows.map(r => (
            <tr key={r.name}>
              <td>{r.name}</td>
              <td className="num mono">{formatNumber(r.current)}</td>
              {Object.keys(r.models).length === 0 ? (
                <td className="ct-none" colSpan={columns.length}>Backend chưa có dự báo cho sản phẩm này</td>
              ) : (
                columns.map(m => (
                  <td key={m} className="num mono">{r.models[m] != null ? formatNumber(r.models[m]) : '—'}</td>
                ))
              )}
              <td className={`ct-trend ${r.trend === 'up' ? 'up' : r.trend === 'down' ? 'down' : ''}`}>
                {r.trend === 'up' ? '▲ Tăng' : r.trend === 'down' ? '▼ Giảm' : '—'}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  )
}
