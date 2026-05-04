import { useEffect, useState } from "react";
import { FileText, Calendar, Users, DollarSign } from "lucide-react";
import { getConfiguracion } from "../services/api.js";

export default function Reportes() {
  const [cursoId, setCursoId] = useState(null);
  const [mes, setMes] = useState(3);
  const [anio, setAnio] = useState(2026);

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

  useEffect(() => {
    cargarCurso();
  }, []);

  const NOMBRES_MESES = [
    "", "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
    "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
  ];

  function abrirReporte(tipo) {
    const base = import.meta.env.VITE_API_URL ?? "";
    let url = "";
    
    if (!cursoId) return;
    
    if (tipo === "balance") {
      url = `${base.replace(/\/$/, "")}/api/reportes/balance?curso_id=${cursoId}&mes=${mes}&anio=${anio}`;
    } else if (tipo === "deudores") {
      url = `${base.replace(/\/$/, "")}/api/reportes/deudores?curso_id=${cursoId}&anio=${anio}`;
    } else if (tipo === "cuotas") {
      url = `${base.replace(/\/$/, "")}/api/reportes/cuotas?curso_id=${cursoId}&anio=${anio}`;
    }
    
    window.open(url, "_blank");
  }

  return (
    <div className="min-h-screen pb-24">
      <header className="border-b border-primary/15 bg-surface shadow-sm">
        <div className="mx-auto flex max-w-5xl items-center justify-between px-4 py-4">
          <div>
            <h1 className="text-2xl font-bold text-primary">Reportes</h1>
            <p className="text-sm text-muted">Exportación de informes en PDF</p>
          </div>
          <div className="flex gap-3">
            <select
              value={mes}
              onChange={(e) => setMes(parseInt(e.target.value, 10))}
              className="rounded-lg border border-muted/40 px-3 py-2 outline-none ring-primary focus:ring-2"
            >
              {NOMBRES_MESES.slice(1).map((n, i) => (
                <option key={i + 1} value={i + 1}>{n}</option>
              ))}
            </select>
            <select
              value={anio}
              onChange={(e) => setAnio(parseInt(e.target.value, 10))}
              className="rounded-lg border border-muted/40 px-3 py-2 outline-none ring-primary focus:ring-2"
            >
              <option value={2025}>2025</option>
              <option value={2026}>2026</option>
              <option value={2027}>2027</option>
            </select>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-5xl space-y-6 px-4 py-6">
        <div className="grid gap-6 md:grid-cols-3">
          {/* Balance Mensual */}
          <div className="rounded-2xl border border-muted/20 bg-surface p-6 shadow-sm hover:shadow-md transition-shadow">
            <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-xl bg-primary/10 text-primary">
              <DollarSign size={24} />
            </div>
            <h2 className="mb-2 text-lg font-semibold text-primary">Balance Mensual</h2>
            <p className="mb-4 text-sm text-muted">
              Resumen de ingresos y egresos del período seleccionado, con saldo acumulado.
            </p>
            <button
              type="button"
              onClick={() => abrirReporte("balance")}
              className="w-full rounded-lg bg-primary px-4 py-2 font-medium text-white shadow hover:bg-primary/90"
            >
              Ver reporte
            </button>
          </div>

          {/* Nómina de Deudores */}
          <div className="rounded-2xl border border-muted/20 bg-surface p-6 shadow-sm hover:shadow-md transition-shadow">
            <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-xl bg-danger/10 text-danger">
              <Users size={24} />
            </div>
            <h2 className="mb-2 text-lg font-semibold text-primary">Nómina de Deudores</h2>
            <p className="mb-4 text-sm text-muted">
              Lista de alumnos con cuotas pendientes y montos adeudados al año seleccionado.
            </p>
            <button
              type="button"
              onClick={() => abrirReporte("deudores")}
              className="w-full rounded-lg bg-primary px-4 py-2 font-medium text-white shadow hover:bg-primary/90"
            >
              Ver reporte
            </button>
          </div>

          {/* Resumen de Cuotas */}
          <div className="rounded-2xl border border-muted/20 bg-surface p-6 shadow-sm hover:shadow-md transition-shadow">
            <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-xl bg-success/10 text-success">
              <Calendar size={24} />
            </div>
            <h2 className="mb-2 text-lg font-semibold text-primary">Resumen de Cuotas</h2>
            <p className="mb-4 text-sm text-muted">
              Matriz completa de pagos por alumno y mes, con porcentaje de cobranza.
            </p>
            <button
              type="button"
              onClick={() => abrirReporte("cuotas")}
              className="w-full rounded-lg bg-primary px-4 py-2 font-medium text-white shadow hover:bg-primary/90"
            >
              Ver reporte
            </button>
          </div>
        </div>

        <section className="rounded-2xl border border-muted/20 bg-surface p-6 shadow-sm">
          <h2 className="mb-4 font-semibold text-primary">Instrucciones</h2>
          <ul className="space-y-2 text-sm text-muted">
            <li className="flex items-start gap-2">
              <span className="text-primary">•</span>
              <span>Selecciona el mes y año para el reporte de balance mensual.</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-primary">•</span>
              <span>Los reportes se abren en una nueva pestaña en formato HTML imprimible.</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-primary">•</span>
              <span>Usa la función de impresión del navegador (Ctrl+P) para guardar como PDF.</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-primary">•</span>
              <span>Los reportes están optimizados para formato A4.</span>
            </li>
          </ul>
        </section>
      </main>
    </div>
  );
}
