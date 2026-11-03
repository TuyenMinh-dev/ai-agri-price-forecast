import Delta from '../Delta/Delta'
import { changeBetween } from '../../utils/market'
import { formatNumber, formatUnit } from '../../utils/format'

// rows: [{ model, price }]; currentAvg: giá trung bình hiện tại để so sánh
export default function ComparisonTable({ rows, currentAvg, unit }) {
  return (
    <section className="panel">
      <header className="panel-head"><h2>So sánh mô hình</h2></header>
      <div className="tbl-wrap">
        <table className="tbl">
          <thead>
            <tr>
              <th>Mô hình</th>
              <th className="num">Giá dự báo ({formatUnit(unit)})</th>
              <th className="num">So với giá trung bình hiện tại</th>
            </tr>
          </thead>
          <tbody>
            {rows.map(r => (
              <tr key={r.model}>
                <td>{r.model}</td>
                <td className="num">{formatNumber(r.price)}</td>
                <td className="num"><Delta change={changeBetween(currentAvg, r.price)} variant="pct" /></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  )
}
