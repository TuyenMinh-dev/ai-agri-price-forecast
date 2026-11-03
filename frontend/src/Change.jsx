// Hiển thị mức thay đổi giá: mũi tên + số + %, màu theo chiều giá.
// Tăng = xanh (▲), giảm = đỏ (▼), không đổi = xám (–). Không bao giờ chỉ dựa vào màu.
const nf = new Intl.NumberFormat("vi-VN");
const pf = new Intl.NumberFormat("vi-VN", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
const ARROW = { up: "▲", down: "▼", flat: "–" };
const WORD = { up: "tăng", down: "giảm", flat: "không đổi" };

export default function Change({ delta, base, pctOnly = false }) {
  const dir = delta > 0 ? "up" : delta < 0 ? "down" : "flat";
  const sign = delta > 0 ? "+" : delta < 0 ? "−" : "";
  const pct = base ? (Math.abs(delta) / base) * 100 : 0;
  return (
    <span className={`chg ${dir}`} title={WORD[dir]}>
      <span className="arrow" aria-hidden="true">{ARROW[dir]}</span>
      {!pctOnly && <span>{sign + nf.format(Math.abs(Math.round(delta)))}</span>}
      <span>{pctOnly ? `${sign}${pf.format(pct)}%` : `(${sign}${pf.format(pct)}%)`}</span>
    </span>
  );
}
