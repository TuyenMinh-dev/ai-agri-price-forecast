// Logo AGRISIGHT cho sidebar (nền tối). File SVG nằm ở src/assets/.
import logoOnDark from "../assets/agrisight-logo-on-dark.svg";

export default function Logo() {
  return (
    <div className="brand">
      <img src={logoOnDark} alt="AGRISIGHT" height="32" style={{ display: "block" }} />
    </div>
  );
}
