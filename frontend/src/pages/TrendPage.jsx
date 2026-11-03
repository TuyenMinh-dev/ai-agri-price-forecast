import PageState from '../components/PageState/PageState'
import PriceTrend from '../components/PriceChart/PriceTrend'
import useApi from '../utils/useApi'
import { loadPrices } from '../api/priceApi'
import { showDate } from '../utils/format'

export default function TrendPage() {
  const { status, data, error } = useApi(loadPrices)
  const empty = status === 'ready' && data.latest.length === 0 && 'Backend chưa có dữ liệu giá.'
  if (status !== 'ready' || empty) return <PageState status={status} error={error} empty={empty} />

  return (
    <div className="page">
      <div className="page-head">
        <div>
          <h1>Biểu đồ biến động giá</h1>
          <p>Phân tích lịch sử giá thực tế của từng sản phẩm</p>
        </div>
        <span className="page-meta">Cập nhật: {showDate(data.lastDate)}</span>
      </div>
      <PriceTrend title="Lịch sử giá" latest={data.latest} history={data.history} showStats />
    </div>
  )
}
