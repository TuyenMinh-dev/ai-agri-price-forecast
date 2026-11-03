import PageState from '../components/PageState/PageState'
import PriceBoard from '../components/PriceBoard/PriceBoard'
import PriceTrend from '../components/PriceChart/PriceTrend'
import useApi from '../utils/useApi'
import { forecastsOf, loadOverview, mainForecast } from '../api/priceApi'
import { lastChange, seriesFor } from '../utils/market'
import { showDate } from '../utils/format'
import './Dashboard.css'

export default function Dashboard() {
  const { status, data, error } = useApi(loadOverview)
  const empty = status === 'ready' && data.latest.length === 0 && 'Backend chưa có dữ liệu giá.'
  if (status !== 'ready' || empty) return <PageState status={status} error={error} empty={empty} />

  const { latest, history, forecasts, lastDate, targetDate } = data
  const rice = latest.filter(p => p.crop === 'rice')

  // Mỗi loại gạo: chuỗi giá, thay đổi so với ngày trước, dự báo của ngày hiện tại + 1
  const rows = rice.map(product => {
    const series = seriesFor(history, product)
    return {
      product,
      series,
      change: lastChange(series),
      forecast: mainForecast(forecastsOf(forecasts, product.productId, targetDate)),
    }
  })

  return (
    <div className="page">
      <div className="page-head">
        <div>
          <h1>Tổng quan thị trường gạo</h1>
          <p>Giá mới nhất, mức thay đổi và dự báo ngày mai của từng loại gạo</p>
        </div>
        <span className="page-meta">Cập nhật: {showDate(lastDate)}</span>
      </div>

      {rice.length === 0 ? (
        <p className="dash-empty">Backend chưa có dữ liệu giá gạo (crop_type = rice).</p>
      ) : (
        <PriceBoard title="Giá gạo mới nhất" rows={rows} targetDate={targetDate} />
      )}

      <PriceTrend title="Biểu đồ giá" latest={latest} history={history} />
    </div>
  )
}
