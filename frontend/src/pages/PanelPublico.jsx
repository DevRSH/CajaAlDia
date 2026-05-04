import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import logoUrl from "@assets/logo.png";
import MontoDisplay from "../components/MontoDisplay.jsx";
import { fetchEstadoPublico, getErrorMessage } from "../services/api.js";

export default function PanelPublico() {
  const { codigo_curso } = useParams();
  const navigate = useNavigate();
  const [datos, setDatos] = useState(null);
  const [error, setError] = useState("");
  const [busqueda, setBusqueda] = useState("");
  const [notFound, setNotFound] = useState(false);

  useEffect(() => {
    let cancel = false;
    async function cargar() {
      try {
        const d = await fetchEstadoPublico(codigo_curso ?? "");
        if (!cancel) {
          setDatos(d);
          setError("");
          setNotFound(false);
        }
      } catch (err) {
        if (!cancel) {
          if (err?.response?.status === 404) {
            setNotFound(true);
            setError("");
          } else {
            setError(getErrorMessage(err));
            setNotFound(false);
          }
        }
      }
    }
    cargar();
    return () => {
      cancel = true;
    };
  }, [codigo_curso]);

  const movimientosFiltrados = datos?.ultimos_movimientos?.filter((m) =>
    m.descripcion.toLowerCase().includes(busqueda.toLowerCase())
  ) || [];

  function DonutChart({ alDia, conDeuda, porcentaje }) {
    const total = alDia + conDeuda;
    if (total === 0) return null;

    const radio = 40;
    const circunferencia = 2 * Math.PI * radio;
    const alDiaOffset = circunferencia - (alDia / total) * circunferencia;

    return (
      <div className="relative flex items-center justify-center">
        <svg width="120" height="120" viewBox="0 0 120 120">
          <circle
            cx="60"
            cy="60"
            r={radio}
            fill="none"
            stroke="#DC2626"
            strokeWidth="12"
          />
          <circle
            cx="60"
            cy="60"
            r={radio}
            fill="none"
            stroke="#16A34A"
            strokeWidth="12"
            strokeDasharray={circunferencia}
            strokeDashoffset={alDiaOffset}
            transform="rotate(-90 60 60)"
          />
        </svg>
        <div className="absolute flex flex-col items-center">
          <span className="text-2xl font-bold text-primary">{porcentaje}%</span>
          <span className="text-xs text-muted">al día</span>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen pb-16">
      <header className="border-b border-primary/15 bg-surface">
        <div className="mx-auto flex max-w-3xl items-center gap-4 px-4 py-6">
          <img src={logoUrl} alt="CajaAlDía" className="h-12 w-auto" />
          <div>
            <h1 className="text-xl font-bold text-primary">{datos?.curso?.nombre ?? "Consulta pública"}</h1>
            {datos?.curso ? (
              <p className="text-sm text-muted">
                {datos.curso.colegio} · {datos.curso.año}
              </p>
            ) : (
              !error && <p className="text-sm text-muted">Cargando…</p>
            )}
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-3xl space-y-6 px-4 py-8">
        {notFound ? (
          <div className="rounded-lg bg-red-50 p-8 text-center">
            <p className="text-lg font-semibold text-danger">Código de curso no encontrado</p>
            <button
              onClick={() => navigate("/public")}
              className="mt-4 rounded-lg bg-primary px-6 py-2 font-semibold text-white transition-colors hover:bg-primary/90"
            >
              Intentar de nuevo
            </button>
          </div>
        ) : error ? (
          <p className="rounded-lg bg-red-50 p-4 text-danger">{error}</p>
        ) : (
          datos && (
            <>
              <section className="rounded-2xl border-2 border-primary bg-surface p-6 shadow">
                <h2 className="font-semibold text-muted">Saldo disponible</h2>
                <div className="mt-3 text-4xl font-bold text-primary">
                  <MontoDisplay monto={datos.saldo} tipo="neutro" className="!text-current" />
                </div>
              </section>

              {datos.resumen_cuotas && datos.resumen_cuotas.total_alumnos > 0 && (
                <section className="rounded-2xl border border-muted/25 bg-surface p-6 shadow-sm">
                  <h2 className="mb-4 font-semibold text-primary">Estado de cuotas</h2>
                  <div className="flex flex-wrap items-center justify-around gap-6">
                    <DonutChart
                      alDia={datos.resumen_cuotas.al_dia}
                      conDeuda={datos.resumen_cuotas.con_deuda}
                      porcentaje={datos.resumen_cuotas.porcentaje_al_dia}
                    />
                    <div className="space-y-2 text-sm">
                      <div className="flex items-center gap-2">
                        <span className="h-3 w-3 rounded-full bg-success"></span>
                        <span className="text-muted">Al día: {datos.resumen_cuotas.al_dia}</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="h-3 w-3 rounded-full bg-danger"></span>
                        <span className="text-muted">Con deuda: {datos.resumen_cuotas.con_deuda}</span>
                      </div>
                      <p className="text-muted">
                        {datos.resumen_cuotas.al_dia} de {datos.resumen_cuotas.total_alumnos} alumnos al día
                      </p>
                    </div>
                  </div>
                </section>
              )}

              <section className="rounded-2xl border border-muted/25 bg-surface p-5 shadow-sm">
                <div className="mb-3 flex items-center justify-between">
                  <h2 className="font-semibold text-primary">Últimos movimientos</h2>
                  <input
                    type="text"
                    placeholder="Buscar..."
                    value={busqueda}
                    onChange={(e) => setBusqueda(e.target.value)}
                    className="rounded-lg border border-muted/40 px-3 py-1 text-sm outline-none ring-primary focus:ring-2"
                  />
                </div>
                <ul className="divide-y divide-muted/15">
                  {movimientosFiltrados.length === 0 ? (
                    <li className="py-6 text-center text-muted">
                      {busqueda ? "No se encontraron movimientos." : "Sin movimientos aún."}
                    </li>
                  ) : (
                    movimientosFiltrados.map((m, idx) => (
                      <li key={`${m.folio}-${idx}`} className="flex flex-wrap items-start justify-between gap-2 py-3">
                        <div>
                          <p className="text-sm text-muted">{m.fecha}</p>
                          <p className="font-medium">{m.descripcion}</p>
                          <p className="font-mono text-xs text-muted">{m.folio}</p>
                        </div>
                        <MontoDisplay monto={m.monto} tipo={m.tipo} />
                      </li>
                    ))
                  )}
                </ul>
              </section>
            </>
          )
        )}

        <p className="text-center text-sm text-muted">Información actualizada en tiempo real</p>
      </main>
    </div>
  );
}
