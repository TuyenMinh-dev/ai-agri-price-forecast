// Logo AGRISIGHT: bông lúa (thân + các cặp hạt chếch lên) trong ô vuông xanh.
// Các nét chếch lên cũng đọc được như mũi tên giá đi lên.
const EAR = ['M16 27V5.5', 'M16 23L10.8 17.8', 'M16 23L21.2 17.8', 'M16 17.5L10.8 12.3', 'M16 17.5L21.2 12.3', 'M16 12L10.8 6.8', 'M16 12L21.2 6.8']

export function LogoMark({ size = 32 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 32 32" aria-hidden="true">
      <rect width="32" height="32" rx="5" className="lg-tile" />
      <g className="lg-ear">{EAR.map(d => <path key={d} d={d} />)}</g>
    </svg>
  )
}

// Biểu tượng tab trình duyệt (màu cố định, không phụ thuộc theme)
export const FAVICON_HREF = `data:image/svg+xml,${encodeURIComponent(
  `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32"><rect width="32" height="32" rx="5" fill="#1E5A3A"/><g fill="none" stroke="#fff" stroke-width="2.6" stroke-linecap="round">${EAR.map(d => `<path d="${d}"/>`).join('')}</g></svg>`
)}`

export default function Logo() {
  return (
    <div className="lg">
      <LogoMark size={32} />
      <div>
        <div className="lg-name"><span>AGRI</span>SIGHT</div>
        <div className="lg-sub">Commodity Intelligence</div>
      </div>
    </div>
  )
}
