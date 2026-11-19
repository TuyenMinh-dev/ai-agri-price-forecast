import './Select.css'

// options: [{ value, label }]
export default function Select({ label, value, onChange, options }) {
  return (
    <label className="sel">
      <span>{label}</span>
      <select value={value} onChange={e => onChange(e.target.value)}>
        {options.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
      </select>
    </label>
  )
}
