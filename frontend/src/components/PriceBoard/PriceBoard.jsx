import Delta from '../Delta/Delta'
import Sparkline from './Sparkline'
import { changeBetween, directionOf } from '../../utils/market'
import { formatNumber, formatUnit, showDate } from '../../utils/format'
import './PriceBoard.css'

// rows: [{ product, series, change, forecast }]
export default function PriceBoard({ title, rows, targetDate }) {
  const count = { up: 0, down: 0, flat: 0 }
  rows.forEach(r => { if (r.change) count[r.change.dir] += 1 })
  const model = rows.find(r => r.forecast)?.forecast.model
  const missing = rows.filter(r => !r.forecast).length
  const sources = [...new Set(rows.map(r => r.product.source).filter(Boolean))]

  return (
    <section className="panel pb">
      <header className="panel-head">
        <h2>{title}</h2>
        <div className="pb-count">
          <span className="up">▲ {count.up} tăng</span>
          <span className="down">▼ {count.down} giảm</span>
          <span className="flat">– {count.flat} không đổi</span>
        </div>
      </header>

      <div className="tbl-wrap">
        <table className="tbl pb-table">
          <thead>
            <tr>
              <th>Sản phẩm</th>
              <th className="num">Khoảng giá hiện tại</th>
              <th className="num">So với ngày trước</th>
              <th>Xu hướng</th>
              <th className="num pb-fc">
                Dự báo ngày mai
                <span className="sub">{showDate(targetDate)}{model && <> · {model}</>}</span>
              </th>
            </tr>
          </thead>
          <tbody>
            {rows.map(({ product: p, series, change, forecast }) => {
              const recent = series.slice(-7).map(r => r.avg)
              const trend = recent.length > 1 ? directionOf(recent.at(-1) - recent[0]) : 'flat'
              const unit = formatUnit(p.unit)
              return (
                <tr key={p.productId}>
                  <td className="pb-name">{p.name}</td>
                  <td className="num">
                    <b>{formatNumber(p.min)} – {formatNumber(p.max)}</b> <span className="pb-unit">{unit}</span>
                    <span className="sub">Cập nhật: {showDate(p.date)}</span>
                  </td>
                  <td className="num"><Delta change={change} /></td>
                  <td><Sparkline values={recent} dir={trend} width={84} /></td>
                  <td className="num pb-fc">
                    {forecast ? (
                      <>
                        <b>{formatNumber(forecast.price)}</b> <span className="pb-unit">{unit}</span>
                        <span className="sub"><Delta change={changeBetween(p.avg, forecast.price)} variant="pct" /> so với hiện tại</span>
                      </>
                    ) : '—'}
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>

      <footer className="panel-foot">
        {missing > 0 && <p className="note">{missing} sản phẩm chưa có dự báo cho ngày {showDate(targetDate)} trong dữ liệu backend.</p>}
        <p>
          Thay đổi so sánh giá trung bình của ngày với ngày có giá liền trước; dự báo so với giá trung bình hiện tại.
          {sources.length > 0 && <> Nguồn dữ liệu: {sources.join('; ')}.</>}
        </p>
      </footer>
    </section>
  )
}
