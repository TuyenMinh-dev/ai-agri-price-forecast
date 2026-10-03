import { useEffect, useState } from 'react'
import PriceCard from '../components/PriceCard/PriceCard'
import PriceChart from '../components/PriceChart/PriceChart'
import ComparisonTable from '../components/ComparisonTable/ComparisonTable'
import { getDashboardData } from '../api/priceApi'
import { matchesQuery } from '../utils/format'
import './Dashboard.css'

export default function Dashboard({ query }) {
  const [productId, setProductId] = useState(null)
  const [state, setState] = useState({ status: 'loading', data: null })

  useEffect(() => {
    getDashboardData()
      .then(data => setState({ status: data?.products?.length ? 'ready' : 'empty', data }))
      .catch(() => setState({ status: 'error', data: null }))
  }, [])

  const { status, data } = state
  if (status === 'loading') return <p className="dash-status">Đang tải dữ liệu...</p>
  if (status === 'error') return <p className="dash-status down">Không tải được dữ liệu từ backend. Hãy kiểm tra backend đã chạy chưa rồi tải lại trang.</p>
  if (status === 'empty') return <p className="dash-status">Chưa có dữ liệu giá lúa gạo để hiển thị.</p>

  const visible = data.products.filter(p => matchesQuery(p.name, query))
  const selected = visible.find(p => p.id === productId) ?? visible[0]

  return (
    <div className="dash">
      <div className="dash-head">
        <div>
          <h1>Dự đoán giá lúa gạo</h1>
          <p>Theo dõi giá thị trường và dự báo xu hướng bằng dữ liệu</p>
        </div>
        <span className="dash-updated">Cập nhật lần cuối: {data.lastUpdated}</span>
      </div>

      {visible.length === 0 ? (
        <p className="dash-status">Không tìm thấy sản phẩm nào khớp với "{query.trim()}".</p>
      ) : (
        <>
          <div className="dash-cards">
            {visible.map(p => <PriceCard key={p.id} {...p} />)}
          </div>

          {visible.length > 1 && (
            <div className="dash-select">
              <span>Xem biểu đồ:</span>
              <div className="dash-tabs">
                {visible.map(p => (
                  <button key={p.id} className={selected.id === p.id ? 'on' : ''} onClick={() => setProductId(p.id)}>{p.short}</button>
                ))}
              </div>
            </div>
          )}

          <PriceChart name={selected.name} confidence={selected.confidence} modelName={selected.modelName} {...data.charts[selected.id]} />

          <ComparisonTable rows={data.comparison.filter(r => matchesQuery(r.name, query))} models={data.models} />
        </>
      )}
    </div>
  )
}
