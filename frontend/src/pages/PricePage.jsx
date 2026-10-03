import { useEffect, useState } from 'react'
import { getPriceList } from '../api/priceApi'
import { formatNumber, matchesQuery } from '../utils/format'
import './PricePage.css'

export default function PricePage({ query }) {
  const [group, setGroup] = useState('all')
  const [type, setType] = useState('Tất cả')
  const [state, setState] = useState({ status: 'loading', data: null })

  useEffect(() => {
    getPriceList()
      .then(data => setState({ status: data?.rows?.length ? 'ready' : 'empty', data }))
      .catch(() => setState({ status: 'error', data: null }))
  }, [])

  const { status, data } = state
  if (status === 'loading') return <p className="pp-status">Đang tải dữ liệu...</p>
  if (status === 'error') return <p className="pp-status down">Không tải được dữ liệu từ backend. Hãy kiểm tra backend đã chạy chưa rồi tải lại trang.</p>
  if (status === 'empty') return <p className="pp-status">Chưa có dữ liệu giá để hiển thị.</p>

  const groupLabel = id => data.groups.find(g => g.id === id)?.label ?? id
  const types = group === 'all' ? [] : ['Tất cả', ...data.typesByGroup[group]]
  const rows = data.rows.filter(r => (group === 'all' || r.group === group) && (type === 'Tất cả' || r.type === type) && matchesQuery(`${groupLabel(r.group)} ${r.type}`, query))

  const chooseGroup = id => { setGroup(id); setType('Tất cả') }

  return (
    <div className="pp">
      <div>
        <h1>Giá nông sản</h1>
        <p>Giá thấp nhất và cao nhất theo loại lúa gạo, cà phê (30 ngày gần nhất)</p>
      </div>

      <div className="pp-filters">
        <div className="pp-tabs">
          {[{ id: 'all', label: 'Tất cả' }, ...data.groups].map(g => (
            <button key={g.id} className={g.id === group ? 'on' : ''} onClick={() => chooseGroup(g.id)}>{g.label}</button>
          ))}
        </div>
        {types.length > 0 && (
          <div className="pp-tabs">
            {types.map(t => (
              <button key={t} className={t === type ? 'on' : ''} onClick={() => setType(t)}>{t}</button>
            ))}
          </div>
        )}
      </div>

      <section className="pp-card">
        <table className="pp-table">
          <thead>
            <tr><th>Nhóm</th><th>Loại</th><th>Ngày</th><th className="num">Giá thấp nhất</th><th className="num">Giá cao nhất</th></tr>
          </thead>
          <tbody>
            {rows.map(r => (
              <tr key={r.group + r.type + r.date}>
                <td>{groupLabel(r.group)}</td>
                <td>{r.type}</td>
                <td>{r.date}</td>
                <td className="num mono">{formatNumber(r.min)} đ</td>
                <td className="num mono">{formatNumber(r.max)} đ</td>
              </tr>
            ))}
          </tbody>
        </table>
        {rows.length === 0 && <p className="pp-none">Không có kết quả phù hợp.</p>}
      </section>
    </div>
  )
}
