import { useEffect, useState } from "react";
import logoUrl from "@assets/logo.png";
import MontoDisplay from "../components/MontoDisplay.jsx";
import Toast from "../components/Toast.jsx";
import NuevoMovimiento from "./NuevoMovimiento.jsx";
import { CURSO_CODIGO_PUBLICO, CURSO_DEMO_ID } from "../constants.js";
import { fetchAlumnos, fetchEstadoPublico, fetchMovimientos, getErrorMessage } from "../services/api.js";

export default function Dashboard() {
  const [estado, setEstado] = useState(null);
  const [movimientos, setMovimientos] = useState([]);
  const [totalAlumnos, setTotalAlumnos] = useState(0);
  const [modal, setModal] = useState(false);
  const [toast, setToast] = useState({ visible: false, mensaje: "", tipo: "error" });

  async function cargar() {
    try {
      const [pub, lista, alumnos] = await Promise.all([
        fetchEstadoPublico(CURSO_CODIGO_PUBLICO),
        fetchMovimientos(CURSO_DEMO_ID, 1),
        fetchAlumnos(CURSO_DEMO_ID),
      ]);
      setEstado(pub);
      setMovimientos(Array.isArray(lista) ? lista : []);
      setTotalAlumnos(Array.isArray(alumnos) ? alumnos.length : 0);
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
    <div className="min-h-screen pb-24">
      <header className="border-b border-primary/15 bg-surface shadow-sm">
        <div className="mx-auto flex max-w-5xl flex-wrap items-center gap-4 px-4 py-4">
          <img src={logoUrl} alt="CajaAlDía" className="h-12 w-auto" />
          <div>
            <h1 className="text-2xl font-bold text-primary">CajaAlDía</h1>
            <p className="text-sm text-muted">La plata del curso, siempre a la vista.</p>
            <p className="mt-1 font-semibold text-ink">{estado?.curso?.nombre ?? "…"}</p>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-5xl space-y-6 px-4 py-6">
        <div className="grid gap-4 md:grid-cols-3">
          <section className="md:col-span-3 lg:col-span-1 lg:row-span-2">
            <div className="rounded-2xl border-2 border-primary bg-surface p-6 shadow-md">
              <h2 className="font-semibold text-muted">Saldo disponible</h2>
              <div className="mt-4 text-4xl font-bold text-primary">
                <MontoDisplay monto={estado?.saldo ?? 0} tipo="neutro" className="!text-current" />
              </div>
            </div>
          </section>

          <section>
            <div className="rounded-2xl border border-success/30 bg-green-50 p-5 shadow">
              <h2 className="text-sm font-semibold text-muted">Total ingresos</h2>
              <div className="mt-2 text-2xl font-bold">
                <MontoDisplay monto={estado?.total_ingresos ?? 0} tipo="neutro" className="!text-success" />
              </div>
            </div>
          </section>

          <section>
            <div className="rounded-2xl border border-danger/30 bg-red-50 p-5 shadow">
              <h2 className="text-sm font-semibold text-muted">Total egresos</h2>
              <div className="mt-2 text-2xl font-bold">
                <MontoDisplay monto={estado?.total_egresos ?? 0} tipo="neutro" className="!text-danger" />
              </div>
            </div>
          </section>
        </div>

        <section className="overflow-hidden rounded-2xl border border-muted/20 bg-surface p-6 shadow-sm">
          <h2 className="mb-4 font-semibold text-primary">Resumen rápido</h2>
          <div className="grid gap-4 md:grid-cols-3">
            <div className="rounded-xl border border-primary/20 bg-primary/5 p-4">
              <div className="text-sm text-muted">Total alumnos activos</div>
              <div className="mt-2 text-3xl font-bold text-primary">{totalAlumnos}</div>
            </div>
          </div>
        </section>

        <div>
          <button
            type="button"
            onClick={() => setModal(true)}
            className="w-full rounded-xl bg-primary px-6 py-4 text-center text-lg font-medium text-white shadow-lg hover:bg-primary/90 md:w-auto"
          >
            + Nuevo movimiento
          </button>
        </div>

        <section className="overflow-hidden rounded-2xl border border-muted/20 bg-surface shadow-sm">
          <h2 className="border-b border-muted/15 bg-bg px-4 py-3 font-semibold text-primary">
            Últimos movimientos
          </h2>
          <div className="overflow-x-auto">
            <table className="w-full min-w-[640px] text-left text-sm">
              <thead className="bg-bg text-muted">
                <tr>
                  <th className="px-4 py-2 font-semibold">Fecha</th>
                  <th className="px-4 py-2 font-semibold">Tipo</th>
                  <th className="px-4 py-2 font-semibold">Descripción</th>
                  <th className="px-4 py-2 font-semibold">Monto</th>
                  <th className="px-4 py-2 font-semibold">Folio</th>
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
                      <td className="px-4 py-2 whitespace-nowrap">{m.fecha}</td>
                      <td className="px-4 py-2">
                        <span
                          className={`inline-flex rounded-full px-2 py-0.5 text-xs font-semibold ${
                            m.tipo === "ingreso"
                              ? "bg-green-100 text-success"
                              : "bg-red-100 text-danger"
                          }`}
                        >
                          {m.tipo === "ingreso" ? "Ingreso" : "Egreso"}
                        </span>
                      </td>
                      <td className="px-4 py-2">{m.descripcion}</td>
                      <td className="px-4 py-2">
                        <MontoDisplay monto={m.monto} tipo={m.tipo} />
                      </td>
                      <td className="px-4 py-2 font-mono text-xs">{m.folio}</td>
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
