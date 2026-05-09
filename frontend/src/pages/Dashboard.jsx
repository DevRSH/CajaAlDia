import { useEffect, useState } from "react";
import logoUrl from "@assets/logo.png";
import MontoDisplay from "../components/MontoDisplay.jsx";
import Toast from "../components/Toast.jsx";
import NuevoMovimiento from "./NuevoMovimiento.jsx";
import { fetchAlumnos, fetchEstadoPublico, fetchMovimientos, getConfiguracion, getErrorMessage } from "../services/api.js";

export default function Dashboard() {
  const [curso, setCurso] = useState(null);
  const [estado, setEstado] = useState(null);
  const [movimientos, setMovimientos] = useState([]);
  const [totalAlumnos, setTotalAlumnos] = useState(0);
  const [alumnosAlDia, setAlumnosAlDia] = useState(0);
  const [alumnosConDeuda, setAlumnosConDeuda] = useState(0);
  const [modal, setModal] = useState(false);
  const [toast, setToast] = useState({ visible: false, mensaje: "", tipo: "error" });

  async function cargar() {
    try {
      const config = await getConfiguracion();
      if (!config.configurada || !config.curso) {
        return;
      }
      setCurso(config.curso);

      const [pub, lista, alumnos] = await Promise.all([
        fetchEstadoPublico(config.curso.codigo),
        fetchMovimientos(config.curso.id, 1),
        fetchAlumnos(config.curso.id),
      ]);
      setEstado(pub);
      setMovimientos(Array.isArray(lista) ? lista : []);
      setTotalAlumnos(Array.isArray(alumnos) ? alumnos.length : 0);
      setAlumnosAlDia(pub?.resumen_cuotas?.al_dia ?? 0);
      setAlumnosConDeuda(pub?.resumen_cuotas?.con_deuda ?? 0);
    } catch (err) {
      try {
        setToast({ visible: true, tipo: "error", mensaje: getErrorMessage(err) });
      } catch {
        setToast({ visible: true, tipo: "error", mensaje: "Error al cargar datos." });
      }
    }
  }

  useEffect(() => {
    cargar();
  }, []);

  function mostrarToast(okMsg, errMsg) {
    if (errMsg) setToast({ visible: true, tipo: "error", mensaje: errMsg });
    else if (okMsg) setToast({ visible: true, tipo: "success", mensaje: okMsg });
  }

  function cerrarModal() {
    setModal(false);
    cargar();
  }

  return (
    <div className="min-h-screen w-full max-w-full overflow-x-hidden pb-24">
      {/* Header mobile-first: altura mínima 64px, padding consistente */}
      <header className="min-h-[64px] border-b border-primary/15 bg-surface shadow-sm">
        <div className="mx-auto flex max-w-5xl flex-col items-start gap-2 px-4 py-4 sm:flex-row sm:items-center sm:gap-4">
          <img src={logoUrl} alt="CajaAlDía" className="h-12 w-auto" />
          <div className="min-w-0 flex-1">
            <h1 className="text-xl font-bold text-primary sm:text-2xl">CajaAlDía</h1>
            <p className="text-sm text-muted">La plata del curso, siempre a la vista.</p>
            <p className="mt-1 truncate font-semibold text-ink">{curso?.nombre ?? "…"}</p>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-5xl space-y-6 px-4 py-6">
        {/* Grid responsive: 1 columna en mobile, 3 en sm+ */}
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {/* Tarjeta de saldo: full width en mobile */}
          <section className="col-span-1 sm:col-span-2 lg:col-span-1 lg:row-span-2">
            <div className="rounded-2xl border-2 border-primary bg-surface p-5 shadow-md sm:p-6">
              <h2 className="font-semibold text-muted">Saldo disponible</h2>
              <div className="mt-4 text-3xl font-bold text-primary sm:text-4xl">
                <MontoDisplay monto={estado?.saldo ?? 0} tipo="neutro" className="!text-current" />
              </div>
            </div>
          </section>

          <section>
            <div className="rounded-2xl border border-success/30 bg-green-50 p-4 shadow sm:p-5">
              <h2 className="text-sm font-semibold text-muted">Total ingresos</h2>
              <div className="mt-2 text-xl font-bold sm:text-2xl">
                <MontoDisplay monto={estado?.total_ingresos ?? 0} tipo="neutro" className="!text-success" />
              </div>
            </div>
          </section>

          <section>
            <div className="rounded-2xl border border-danger/30 bg-red-50 p-4 shadow sm:p-5">
              <h2 className="text-sm font-semibold text-muted">Total egresos</h2>
              <div className="mt-2 text-xl font-bold sm:text-2xl">
                <MontoDisplay monto={estado?.total_egresos ?? 0} tipo="neutro" className="!text-danger" />
              </div>
            </div>
          </section>
        </div>

        <section className="overflow-hidden rounded-2xl border border-muted/20 bg-surface p-4 shadow-sm sm:p-6">
          <h2 className="mb-4 font-semibold text-primary">Resumen rápido</h2>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
            <div className="rounded-xl border border-primary/20 bg-primary/5 p-4">
              <div className="text-sm text-muted">Total alumnos activos</div>
              <div className="mt-2 text-2xl font-bold text-primary sm:text-3xl">{totalAlumnos}</div>
            </div>
            <div className="rounded-xl border border-success/30 bg-green-50 p-4">
              <div className="text-sm text-muted">Alumnos al día</div>
              <div className="mt-2 text-2xl font-bold text-success sm:text-3xl">{alumnosAlDia}</div>
            </div>
            <div className="rounded-xl border border-danger/30 bg-red-50 p-4">
              <div className="text-sm text-muted">Alumnos con deuda</div>
              <div className="mt-2 text-2xl font-bold text-danger sm:text-3xl">{alumnosConDeuda}</div>
            </div>
          </div>
        </section>

        {/* Botón full-width en mobile, auto en desktop */}
        <div className="px-0 sm:px-0">
          <button
            type="button"
            onClick={() => setModal(true)}
            className="h-14 w-full rounded-xl bg-primary px-6 py-3 text-center text-lg font-medium text-white shadow-lg hover:bg-primary/90 active:bg-primary/80 sm:w-auto sm:px-8"
          >
            + Nuevo movimiento
          </button>
        </div>

        {/* Tabla con scroll horizontal en mobile */}
        <section className="overflow-hidden rounded-2xl border border-muted/20 bg-surface shadow-sm">
          <h2 className="border-b border-muted/15 bg-bg px-4 py-3 font-semibold text-primary">
            Últimos movimientos
          </h2>
          <div className="overflow-x-auto">
            <table className="w-full min-w-[640px] text-left text-sm">
              <thead className="bg-bg text-muted">
                <tr>
                  <th className="px-4 py-3 font-semibold">Fecha</th>
                  <th className="px-4 py-3 font-semibold">Tipo</th>
                  <th className="px-4 py-3 font-semibold">Descripción</th>
                  <th className="px-4 py-3 font-semibold">Monto</th>
                  <th className="px-4 py-3 font-semibold">Folio</th>
                </tr>
              </thead>
              <tbody>
                {movimientos.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="px-4 py-8 text-center text-muted">
                      No hay movimientos registrados.
                    </td>
                  </tr>
                ) : (
                  movimientos.map((m) => (
                    <tr key={m.id} className="border-t border-muted/10 hover:bg-bg/80">
                      <td className="px-4 py-3 whitespace-nowrap">{m.fecha}</td>
                      <td className="px-4 py-3">
                        <span
                          className={`inline-flex rounded-full px-2 py-1 text-xs font-semibold ${
                            m.tipo === "ingreso"
                              ? "bg-green-100 text-success"
                              : "bg-red-100 text-danger"
                          }`}
                        >
                          {m.tipo === "ingreso" ? "Ingreso" : "Egreso"}
                        </span>
                      </td>
                      <td className="px-4 py-3">{m.descripcion}</td>
                      <td className="px-4 py-3">
                        <MontoDisplay monto={m.monto} tipo={m.tipo} />
                      </td>
                      <td className="px-4 py-3 font-mono text-xs">{m.folio}</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </section>
      </main>

      <NuevoMovimiento
        abierto={modal}
        onCerrar={cerrarModal}
        onExitoGlobal={(ok, err) => mostrarToast(ok, err)}
      />

      <Toast
        visible={toast.visible}
        tipo={toast.tipo}
        mensaje={toast.mensaje}
        onClose={() => setToast((t) => ({ ...t, visible: false }))}
      />
    </div>
  );
}
