const fmt = new Intl.NumberFormat("es-CL", { style: "currency", currency: "CLP" });

/**
 * @param {{ monto: number, tipo?: 'ingreso'|'egreso'|'neutro', className?: string }} props
 */
export default function MontoDisplay({ monto, tipo = "neutro", className = "" }) {
  const texto = fmt.format(Math.abs(Number(monto)) || 0);
  let color = "";
  let prefijo = "";
  if (tipo === "ingreso") {
    color = "text-success";
    prefijo = "+";
  } else if (tipo === "egreso") {
    color = "text-danger";
    prefijo = "-";
  } else {
    color = "text-ink";
  }
  return (
    <span className={`tabular-nums font-medium ${color} ${className}`}>
      {prefijo}
      {texto}
    </span>
  );
}
