import { formatPercent, formatSigned } from '../../utils/format'
import './Delta.css'

// change: { abs, pct, dir } — variant "full": ▲ +356 (+1,9%) · "pct": ▲ +1,9%
export default function Delta({ change, variant = 'full' }) {
  if (!change) return <span className="flat">—</span>
  const arrow = { up: '▲', down: '▼', flat: '–' }[change.dir]
  return (
    <span className={`dl ${change.dir}`}>
      {arrow}{' '}
      {variant === 'pct' ? formatPercent(change.pct) : <>{formatSigned(change.abs)} <small>({formatPercent(change.pct)})</small></>}
    </span>
  )
}
