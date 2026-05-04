/**
 * Barra de notificación fija.
 */
export default function Toast({ mensaje, tipo = "error", visible, onClose }) {
  if (!visible || !mensaje) return null;
  const bg = tipo === "success" ? "bg-success" : "bg-danger";
  return (
    <div
      role="alert"
      className={`fixed bottom-6 left-1/2 z-50 -translate-x-1/2 rounded-lg px-4 py-3 text-white shadow-lg ${bg}`}
    >
      <div className="flex items-center gap-3">
        <span className="text-sm font-medium">{mensaje}</span>
        <button
          type="button"
          className="text-white/90 hover:text-white"
          onClick={onClose}
          aria-label="Cerrar"
        >
          ×
        </button>
      </div>
    </div>
  );
}
