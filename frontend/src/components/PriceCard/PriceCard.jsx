import { formatNumber, formatPercent } from '../../utils/format'
import './PriceCard.css'

export default function PriceCard({ name, current, predicted, predictedDate, change, confidence, modelName }) {
  const hasForecast = predicted != null
  const up = (change ?? 0) >= 0
  return (
    <div className="pc">
      <div className="pc-name">{name}</div>
      <div className="pc-label">Giá hiện tại</div>
      <div className="pc-price mono">{formatNumber(current)}<span> đ/kg</span></div>
      <dl className="pc-list">
        <div>
          <dt>Dự báo{predictedDate ? ` (${predictedDate})` : ''}</dt>
          <dd className="mono">{hasForecast ? `${formatNumber(predicted)} đ/kg` : 'Chưa có'}</dd>
        </div>
        {hasForecast && (
          <div><dt>Thay đổi</dt><dd className={`mono ${up ? 'up' : 'down'}`}>{up ? '▲' : '▼'} {formatPercent(change)}</dd></div>
        )}
        {modelName && <div><dt>Mô hình</dt><dd>{modelName}</dd></div>}
        {confidence != null && <div><dt>Độ tin cậy</dt><dd className="mono">{confidence}%</dd></div>}
      </dl>
      {confidence != null && <div className="pc-bar"><div style={{ width: `${confidence}%` }} /></div>}
    </div>
  )
}
