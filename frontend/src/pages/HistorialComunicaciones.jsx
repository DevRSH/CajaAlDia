import { useEffect, useState } from "react";
import { RefreshCw } from "lucide-react";
import Toast from "../components/Toast.jsx";
import {
  fetchHistorialNotificaciones,
  getConfiguracion,
  getErrorMessage,
  notificarPagoCuota,
} from "../services/api.js";

const FILTROS = [
  { label: "Todos", valor: null },
  { label: "Comprobantes", valor: "pago" },
  { label: "Deudas", valor: "deuda" },
];

function BadgeEstado({ estado }) {
  const estilos = {
    enviado: "bg-green-100 text-green-700",
    fallido: "bg-red-100 text-red-700",
    simulado: "bg-gray-100 text-gray-600",
  };
  const labels = {
    enviado: "Enviado",
    fallido: "Fallido",
    simulado: "Simulado",
  };
  const clase = estilos[estado] ?? "bg-gray-100 text-gray-600";
  return (
    <span className={`inline-flex items-center rounded-full px-2 py-1 text-xs font-semibold ${clase}`}>
      {labels[estado] ?? estado}
    </span>
  );
}

function formatFecha(isoStr) {
  if (!isoStr) return "—";
  try {
    return new Date(isoStr).toLocaleString("es-CL", {
      day: "2-digit",
      month: "2-digit",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return isoStr;
  }
}

export default function HistorialComunicaciones() {
  const [cursoId, setCursoId] = useState(null);
  const [items, setItems] = useState([]);
  const [page, setPage] = useState(1);
  const [filtroTipo, setFiltroTipo] = useState(null);
  const [cargando, setCargando] = useState(true);
  const [reintentando, setReintentando] = useState(null);
  const [toast, setToast] = useState({ visible: false, mensaje: "", tipo: "success" });
  const SIZE = 20;

  async function cargarCurso() {
    try {
      const config = await getConfiguracion();
      if (config.configurada && config.curso) {
        setCursoId(config.curso.id);
      }
    } catch (err) {
      console.error("Error al cargar curso:", err);
    }
  }

  async function cargarHistorial(id, p, tipo) {
    if (!id) return;
    setCargando(true);
    try {
      const data = await fetchHistorialNotificaciones(id, p, SIZE, tipo);
      setItems(data.items ?? []);
    } catch (err) {
      setToast({ visible: true, tipo: "error", mensaje: getErrorMessage(err) });
    } finally {
      setCargando(false);
    }
  }

  useEffect(() => {
    cargarCurso();
  }, []);

  useEffect(() => {
    if (cursoId) cargarHistorial(cursoId, page, filtroTipo);
  }, [cursoId, page, filtroTipo]);

  function cambiarFiltro(valor) {
    setFiltroTipo(valor);
    setPage(1);
  }

  async function reintentar(item) {
    if (!item.pago_cuota_id) {
      setToast({ visible: true, tipo: "error", mensaje: "Solo se pueden reintentar comprobantes de pago desde aquí." });
      return;
    }
    setReintentando(item.id);
    try {
      await notificarPagoCuota(item.pago_cuota_id);
      setToast({ visible: true, tipo: "success", mensaje: "Email reenviado correctamente." });
      cargarHistorial(cursoId, page, filtroTipo);
    } catch (err) {
      setToast({ visible: true, tipo: "error", mensaje: getErrorMessage(err) });
    } finally {
      setReintentando(null);
    }
  }

  return (
    <div className="min-h-screen w-full max-w-full overflow-x-hidden pb-24">
      <header className="min-h-[64px] border-b border-primary/15 bg-surface shadow-sm">
        <div className="mx-auto max-w-5xl px-4 py-4">
          <h1 className="text-xl font-bold text-primary sm:text-2xl">Historial de Comunicaciones</h1>
          <p className="text-sm text-muted">Registro de emails enviados a apoderados</p>
        </div>
      </header>

      <main className="mx-auto max-w-5xl space-y-4 px-4 py-6">
        {/* Filtros */}
        <div className="flex flex-wrap gap-2">
          {FILTROS.map((f) => (
            <button
              key={String(f.valor)}
              type="button"
              onClick={() => cambiarFiltro(f.valor)}
              className={`rounded-full px-4 py-1.5 text-sm font-medium transition-colors ${
                filtroTipo === f.valor
                  ? "bg-primary text-white"
                  : "border border-muted/30 text-muted hover:border-primary hover:text-primary"
              }`}
            >
              {f.label}
            </button>
          ))}
        </div>

        {/* Tabla */}
        <div className="overflow-hidden rounded-2xl border border-muted/20 bg-surface shadow-sm">
          <div className="overflow-x-auto">
            <table className="w-full min-w-[700px] text-left text-sm">
              <thead className="bg-bg text-muted">
                <tr>
                  <th className="px-4 py-3 font-semibold">Fecha</th>
                  <th className="px-4 py-3 font-semibold">Alumno</th>
                  <th className="px-4 py-3 font-semibold">Email</th>
                  <th className="px-4 py-3 font-semibold">Tipo</th>
                  <th className="px-4 py-3 font-semibold">Estado</th>
                  <th className="px-4 py-3 font-semibold">Acción</th>
                </tr>
              </thead>
              <tbody>
                {cargando ? (
                  <tr>
                    <td colSpan={6} className="px-4 py-10 text-center text-muted">
                      Cargando...
                    </td>
                  </tr>
                ) : items.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="px-4 py-10 text-center text-muted">
                      No hay registros de emails.
                    </td>
                  </tr>
                ) : (
                  items.map((item) => (
                    <tr key={item.id} className="border-t border-muted/10 hover:bg-bg/80">
                      <td className="px-4 py-3 whitespace-nowrap text-xs">
                        {formatFecha(item.enviado_en)}
                      </td>
                      <td className="px-4 py-3 font-medium">
                        {item.alumno_nombre ?? "—"}
                      </td>
                      <td className="px-4 py-3 text-xs text-muted">
                        {item.email_destinatario}
                      </td>
                      <td className="px-4 py-3">
                        <span className="text-xs capitalize text-ink">
                          {item.tipo === "pago" ? "Comprobante" : "Deuda"}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        <BadgeEstado estado={item.estado} />
                        {item.estado === "fallido" && item.error_detalle && (
                          <p className="mt-1 text-xs text-danger">{item.error_detalle}</p>
                        )}
                      </td>
                      <td className="px-4 py-3">
                        {item.estado === "fallido" && item.pago_cuota_id && (
                          <button
                            type="button"
                            disabled={reintentando === item.id}
                            onClick={() => reintentar(item)}
                            className="flex items-center gap-1 rounded-lg border border-primary/30 px-3 py-1.5 text-xs font-medium text-primary hover:bg-primary/5 disabled:opacity-50"
                          >
                            <RefreshCw size={12} className={reintentando === item.id ? "animate-spin" : ""} />
                            Reintentar
                          </button>
                        )}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Paginación */}
        <div className="flex items-center justify-between">
          <button
            type="button"
            disabled={page <= 1 || cargando}
            onClick={() => setPage((p) => p - 1)}
            className="rounded-lg border border-muted/30 px-4 py-2 text-sm font-medium text-muted hover:border-primary hover:text-primary disabled:opacity-40"
          >
            ← Anterior
          </button>
          <span className="text-sm text-muted">Página {page}</span>
          <button
            type="button"
            disabled={items.length < SIZE || cargando}
            onClick={() => setPage((p) => p + 1)}
            className="rounded-lg border border-muted/30 px-4 py-2 text-sm font-medium text-muted hover:border-primary hover:text-primary disabled:opacity-40"
          >
            Siguiente →
          </button>
        </div>
      </main>

      <Toast
        visible={toast.visible}
        tipo={toast.tipo}
        mensaje={toast.mensaje}
        onClose={() => setToast((t) => ({ ...t, visible: false }))}
      />
    </div>
  );
}
