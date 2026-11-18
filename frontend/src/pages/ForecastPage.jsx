import { useState } from 'react'
import ComparisonTable from '../components/ComparisonTable/ComparisonTable'
import PageState from '../components/PageState/PageState'
import Select from '../components/Select/Select'
import useApi from '../utils/useApi'
import { cropLabel, forecastsOf, loadForecast, mainForecast, sortCrops } from '../api/priceApi'
import { formatNumber, formatUnit, showDate } from '../utils/format'
import './ForecastPage.css'

export default function ForecastPage() {
  const { status, data, error } = useApi(loadForecast)
  const [crop, setCrop] = useState(null)
  const [productId, setProductId] = useState(null)

  const empty = status === 'ready' && data.latest.length === 0 && 'Backend chưa có dữ liệu giá.'
  if (status !== 'ready' || empty) return <PageState status={status} error={error} empty={empty} />

  const { latest, forecasts, lastDate, targetDate } = data
  const crops = sortCrops(new Set(latest.map(p => p.crop)))
  const activeCrop = crop ?? crops[0]
  const products = latest.filter(p => p.crop === activeCrop)
  const product = products.find(p => String(p.productId) === productId) ?? products[0]

  // Dự báo của sản phẩm trong ngày dự báo; các ngày dự báo khác chỉ dùng để báo lỗi dữ liệu
  const rows = forecastsOf(forecasts, product.productId, targetDate).sort((a, b) => a.model.localeCompare(b.model))
  const otherDates = [...new Set(forecasts.filter(f => f.productId === product.productId).map(f => f.date))].sort()
  const main = mainForecast(rows)
  const unit = formatUnit(product.unit)

  return (
    <div className="page">
      <div className="page-head">
        <div>
          <h1>Dự báo</h1>
          <p>Dự báo giá cho ngày tiếp theo và so sánh các mô hình</p>
        </div>
        <span className="page-meta">Cập nhật: {showDate(lastDate)}</span>
      </div>

      <div className="toolbar">
        <Select label="Loại nông sản" value={activeCrop} onChange={c => { setCrop(c); setProductId(null) }} options={crops.map(c => ({ value: c, label: cropLabel(c) }))} />
        <Select label="Sản phẩm" value={String(product.productId)} onChange={setProductId} options={products.map(p => ({ value: String(p.productId), label: p.name }))} />
      </div>

      <dl className="panel fc-stats">
        <div><dt>Ngày dự báo</dt><dd className="tnum">{showDate(targetDate)}</dd></div>
        <div><dt>Giá hiện tại (cập nhật {showDate(product.date)})</dt><dd className="tnum">{formatNumber(product.min)} – {formatNumber(product.max)} {unit}</dd></div>
        <div className="fc-main"><dt>Giá dự báo{main ? ` (${main.model})` : ''}</dt><dd className="tnum">{main ? `${formatNumber(main.price)} ${unit}` : '—'}</dd></div>
      </dl>

      {rows.length > 0 ? (
        <ComparisonTable rows={rows} currentAvg={product.avg} unit={product.unit} />
      ) : (
        <section className="panel">
          <header className="panel-head"><h2>So sánh mô hình</h2></header>
          {product.date < lastDate ? (
            <div className="note fc-missing" style={{ lineHeight: '1.6', padding: '16px' }}>
              <span style={{ color: '#e5a50a', display: 'block', marginBottom: '8px', fontSize: '15px', fontWeight: 'bold' }}>
                ℹ️ Thông báo thị trường:
              </span>
              Mặt hàng <strong>{cropLabel(product.crop)} – {product.name}</strong> hiện đã tạm dừng niêm yết trên trang nguồn 
              (ngày ghi nhận giá cuối cùng là <strong>{showDate(product.date)}</strong>).
              <br />
              Để đảm bảo độ chính xác và tính khách quan khoa học, hệ thống <strong>chủ động không tạo dự báo</strong> đối với các chủng loại đã ngừng giao dịch thực tế.
            </div>
          ) : (
            <p className="note fc-missing">
              Chưa có dữ liệu dự báo cho ngày {showDate(targetDate)}.
            </p>
          )}
        </section>
      )}
    </div>
  )
}

