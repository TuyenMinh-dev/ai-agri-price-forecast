import './ImpactFactors.css'

export default function ImpactFactors({ factors }) {
  return (
    <section className="if">
      <h2>Các yếu tố ảnh hưởng</h2>
      <p className="if-note"></p>
      <table className="if-table">
        <thead>
          <tr><th>Yếu tố</th><th>Tỷ trọng</th><th>Xu hướng</th></tr>
        </thead>
        <tbody>
          {factors.map(f => (
            <tr key={f.id}>
              <td>{f.name}</td>
              <td>
                <div className="if-weight">
                  <div className="if-bar"><div style={{ width: `${f.pct}%` }} /></div>
                  <span className="mono">{f.pct}%</span>
                </div>
              </td>
              <td className={`if-dir ${f.dir === 'up' ? 'up' : 'down'}`}>{f.dir === 'up' ? '▲ Tăng' : '▼ Giảm'}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  )
}
