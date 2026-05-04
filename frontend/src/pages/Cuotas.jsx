import { useEffect, useState } from "react";
import MontoDisplay from "../components/MontoDisplay.jsx";
import Toast from "../components/Toast.jsx";
import { CURSO_DEMO_ID } from "../constants.js";
import {
  crearConfigCuota,
  fetchConfigCuotas,
  fetchDeudores,
  fetchEstadoCuotas,
  getErrorMessage,
  notificarDeuda,
  notificarPagoCuota,
  registrarPagoCuota,
} from "../services/api.js";

function formatoMilesChilenos(num) {
  if (!num) return "0";
  return String(num).replace(/\B(?=(\d{3})+(?!\d))/g, ".");
}

const NOMBRES_MESES = [
  "", "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
  "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
];

export default function Cuotas() {
  const [anio, setAnio] = useState(2026);
  const [configs, setConfigs] = useState([]);
  const [estado, setEstado] = useState(null);
  const [deudores, setDeudores] = useState(null);
  const [selectedDeudores, setSelectedDeudores] = useState(new Set());
  const [toast, setToast] = useState({ visible: false, mensaje: "", tipo: "error" });
  const [cargando, setCargando] = useState(false);

  // Formulario nueva config
  const [mes, setMes] = useState(3);
  const [monto, setMonto] = useState("");
  const [descripcion, setDescripcion] = useState("");

  async function cargar() {
    try {
      const [cfg, est, deud] = await Promise.all([
        fetchConfigCuotas(CURSO_DEMO_ID, anio),
        fetchEstadoCuotas(CURSO_DEMO_ID, anio),
        fetchDeudores(CURSO_DEMO_ID, anio),
      ]);
      setConfigs(Array.isArray(cfg) ? cfg : []);
      setEstado(est);
      setDeudores(deud);
      setSelectedDeudores(new Set());
    } catch (err) {
      setToast({ visible: true, tipo: "error", mensaje: getErrorMessage(err) });
    }
  }

  useEffect(() => {
    cargar();
  }, [anio]);

  function mostrarToast(okMsg, errMsg) {
    if (errMsg) setToast({ visible: true, tipo: "error", mensaje: errMsg });
    else if (okMsg) setToast({ visible: true, tipo: "success", mensaje: okMsg });
  }

  async function crearConfig(ev) {
    ev.preventDefault();
    try {
      const montoNum = parseInt(monto.replace(/\D/g, ""), 10);
      if (!montoNum || montoNum <= 0) {
        mostrarToast(null, "Ingrese un monto válido.");
        return;
      }
      if (!descripcion.trim()) {
        mostrarToast(null, "La descripción es obligatoria.");
        return;
      }
      setCargando(true);
      await crearConfigCuota({
        curso_id: CURSO_DEMO_ID,
        anio,
        mes,
        monto: montoNum,
        descripcion: descripcion.trim(),
      });
      mostrarToast("Configuración creada.", null);
      setMes(3);
      setMonto("");
      setDescripcion("");
      cargar();
    } catch (err) {
      mostrarToast(null, getErrorMessage(err));
    } finally {
      setCargando(false);
    }
  }

  function onMontoChange(e) {
    const v = e.target.value.replace(/\D/g, "");
    setMonto(v ? formatoMilesChilenos(parseInt(v, 10)) : "");
  }

  async function registrarPago(alumno, config) {
    const nombreAlumno = alumno.nombre_completo;
    const confirmar = window.confirm(
      `¿Registrar pago de $${formatoMilesChilenos(config.monto)} para ${nombreAlumno} - ${NOMBRES_MESES[config.mes]} ${anio}?`
    );
    if (!confirmar) return;

    try {
      setCargando(true);
      const resultado = await registrarPagoCuota({
        alumno_id: alumno.id,
        config_cuota_id: config.id,
        fecha_pago: null,
      });
      mostrarToast("Pago registrado correctamente.", null);
      cargar();

      // Preguntar si desea enviar notificación
      const notificar = window.confirm(
        "¿Deseas enviar una notificación por email al apoderado?"
      );
      if (notificar && resultado.pago?.id) {
        try {
          await notificarPagoCuota(resultado.pago.id);
          mostrarToast("Notificación enviada correctamente.", null);
        } catch (err) {
          mostrarToast(null, getErrorMessage(err));
        }
      }
    } catch (err) {
      mostrarToast(null, getErrorMessage(err));
    } finally {
      setCargando(false);
    }
  }

  function celdaEstado(mesEstado, alumno, config) {
    if (!mesEstado) {
      return <td className="border border-muted/10 bg-gray-50 px-2 py-2 text-center text-muted">-</td>;
    }
    if (mesEstado.pagado) {
      return (
        <td className="border border-muted/10 bg-green-50 px-2 py-2 text-center">
          <span className="text-success">✓</span>
        </td>
      );
    }
    return (
      <td
        className="cursor-pointer border border-muted/10 bg-red-50 px-2 py-2 text-center hover:bg-red-100"
        onClick={() => registrarPago(alumno, config)}
      >
        <span className="text-danger font-semibold">$</span>
      </td>
    );
  }

  function toggleDeudorSelection(alumnoId) {
    const newSelection = new Set(selectedDeudores);
    if (newSelection.has(alumnoId)) {
      newSelection.delete(alumnoId);
    } else {
      newSelection.add(alumnoId);
    }
    setSelectedDeudores(newSelection);
  }

  function toggleSelectAllDeudores() {
    if (selectedDeudores.size === deudores?.alumnos?.length) {
      setSelectedDeudores(new Set());
    } else {
      setSelectedDeudores(new Set(deudores.alumnos.map((a) => a.alumno.id)));
    }
  }

  async function notificarSeleccionados() {
    try {
      if (selectedDeudores.size === 0) {
        mostrarToast(null, "Selecciona al menos un alumno para notificar.");
        return;
      }
      setCargando(true);
      const resultado = await notificarDeuda(CURSO_DEMO_ID, anio, Array.from(selectedDeudores));
      mostrarToast(
        `Se notificó a ${resultado.notificados} apoderados. ${resultado.sin_email} apoderados sin email registrado.`,
        null
      );
      cargar();
    } catch (err) {
      mostrarToast(null, getErrorMessage(err));
    } finally {
      setCargando(false);
    }
  }

  async function notificarTodosDeudores() {
    try {
      setCargando(true);
      const resultado = await notificarDeuda(CURSO_DEMO_ID, anio, null);
      mostrarToast(
        `Se notificó a ${resultado.notificados} apoderados. ${resultado.sin_email} apoderados sin email registrado.`,
        null
      );
      cargar();
    } catch (err) {
      mostrarToast(null, getErrorMessage(err));
    } finally {
      setCargando(false);
    }
  }

  return (
    <div className="min-h-screen pb-24">
      <header className="border-b border-primary/15 bg-surface shadow-sm">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-4">
          <div>
            <h1 className="text-2xl font-bold text-primary">Cuotas</h1>
            <p className="text-sm text-muted">Gestión de cuotas mensuales</p>
          </div>
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
      </header>

      <main className="mx-auto max-w-6xl space-y-6 px-4 py-6">
        {/* Configurar cuota */}
        <section className="rounded-2xl border border-muted/20 bg-surface p-6 shadow-sm">
          <h2 className="mb-4 font-semibold text-primary">Configurar cuota mensual</h2>
          <form onSubmit={crearConfig} className="flex flex-wrap items-end gap-3">
            <div>
              <label className="mb-1 block text-sm font-semibold text-muted">Mes</label>
              <select
                value={mes}
                onChange={(e) => setMes(parseInt(e.target.value, 10))}
                className="rounded-lg border border-muted/40 px-3 py-2 outline-none ring-primary focus:ring-2"
              >
                {NOMBRES_MESES.slice(1).map((n, i) => (
                  <option key={i + 1} value={i + 1}>{n}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="mb-1 block text-sm font-semibold text-muted">Monto (CLP)</label>
              <input
                type="text"
                inputMode="numeric"
                placeholder="Ej: 15000"
                value={monto}
                onChange={onMontoChange}
                className="w-40 rounded-lg border border-muted/40 px-3 py-2 outline-none ring-primary focus:ring-2"
              />
            </div>
            <div>
              <label className="mb-1 block text-sm font-semibold text-muted">Descripción</label>
              <input
                type="text"
                placeholder="Ej: Cuota marzo 2026"
                value={descripcion}
                onChange={(e) => setDescripcion(e.target.value)}
                className="w-64 rounded-lg border border-muted/40 px-3 py-2 outline-none ring-primary focus:ring-2"
              />
            </div>
            <button
              type="submit"
              disabled={cargando}
              className="rounded-lg bg-primary px-5 py-2 font-medium text-white shadow hover:bg-primary/90 disabled:opacity-60"
            >
              {cargando ? "Guardando..." : "Configurar"}
            </button>
          </form>
        </section>

        {/* Matriz de estado */}
        {estado && (
          <section className="overflow-hidden rounded-2xl border border-muted/20 bg-surface shadow-sm">
            <h2 className="border-b border-muted/15 bg-bg px-4 py-3 font-semibold text-primary">
              Estado de pagos - {anio}
            </h2>
            <div className="overflow-x-auto">
              <table className="w-full min-w-[900px] text-left text-sm">
                <thead className="bg-bg text-muted">
                  <tr>
                    <th className="px-4 py-2 font-semibold">Alumno</th>
                    {configs.map((c) => (
                      <th key={c.id} className="px-2 py-2 text-center font-semibold">
                        {NOMBRES_MESES[c.mes]}
                      </th>
                    ))}
                    <th className="px-4 py-2 text-center font-semibold">Pagado</th>
                    <th className="px-4 py-2 text-center font-semibold">Pendiente</th>
                  </tr>
                </thead>
                <tbody>
                  {estado.alumnos.length === 0 ? (
                    <tr>
                      <td colSpan={configs.length + 3} className="px-4 py-8 text-center text-muted">
                        No hay alumnos registrados.
                      </td>
                    </tr>
                  ) : (
                    estado.alumnos.map((a) => (
                      <tr key={a.alumno.id} className="border-t border-muted/10">
                        <td className="px-4 py-2 font-medium">{a.alumno.nombre_completo}</td>
                        {configs.map((c) => {
                          const mesEstado = a.meses.find((m) => m.mes === c.mes);
                          return celdaEstado(mesEstado, a.alumno, c);
                        })}
                        <td className="px-4 py-2 text-center">
                          <MontoDisplay monto={a.total_pagado} tipo="neutro" className="!text-success" />
                        </td>
                        <td className="px-4 py-2 text-center">
                          <MontoDisplay monto={a.total_pendiente} tipo="neutro" className="!text-danger" />
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </section>
        )}

        {/* Sección Deudores */}
        {deudores && deudores.alumnos.length > 0 && (
          <section className="overflow-hidden rounded-2xl border border-muted/20 bg-surface shadow-sm">
            <div className="border-b border-muted/15 bg-bg px-4 py-3">
              <div className="flex items-center justify-between">
                <h2 className="font-semibold text-primary">Apoderados con deuda pendiente</h2>
                <div className="flex gap-2">
                  <button
                    type="button"
                    onClick={notificarSeleccionados}
                    disabled={cargando || selectedDeudores.size === 0}
                    className="rounded-lg bg-primary px-4 py-2 text-sm font-medium text-white shadow hover:bg-primary/90 disabled:opacity-60"
                  >
                    Notificar seleccionados ({selectedDeudores.size})
                  </button>
                  <button
                    type="button"
                    onClick={notificarTodosDeudores}
                    disabled={cargando}
                    className="rounded-lg border border-primary px-4 py-2 text-sm font-medium text-primary hover:bg-primary/5 disabled:opacity-60"
                  >
                    Notificar a todos los deudores
                  </button>
                </div>
              </div>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full min-w-[600px] text-left text-sm">
                <thead className="bg-bg text-muted">
                  <tr>
                    <th className="px-4 py-2 font-semibold">
                      <input
                        type="checkbox"
                        checked={selectedDeudores.size === deudores.alumnos.length}
                        onChange={toggleSelectAllDeudores}
                        className="rounded border-muted/40 text-primary focus:ring-primary"
                      />
                    </th>
                    <th className="px-4 py-2 font-semibold">Nombre alumno</th>
                    <th className="px-4 py-2 font-semibold">Meses pendientes</th>
                    <th className="px-4 py-2 font-semibold">Monto total</th>
                    <th className="px-4 py-2 font-semibold">Email apoderado</th>
                  </tr>
                </thead>
                <tbody>
                  {deudores.alumnos.map((a) => (
                    <tr key={a.alumno.id} className="border-t border-muted/10">
                      <td className="px-4 py-2">
                        <input
                          type="checkbox"
                          checked={selectedDeudores.has(a.alumno.id)}
                          onChange={() => toggleDeudorSelection(a.alumno.id)}
                          className="rounded border-muted/40 text-primary focus:ring-primary"
                        />
                      </td>
                      <td className="px-4 py-2 font-medium">{a.alumno.nombre_completo}</td>
                      <td className="px-4 py-2">
                        {a.total_pendiente > 0 ? (
                          <span className="inline-flex rounded-full bg-red-100 px-2 py-0.5 text-xs font-semibold text-danger">
                            {a.meses.filter((m) => !m.pagado).length} mes(es)
                          </span>
                        ) : (
                          "-"
                        )}
                      </td>
                      <td className="px-4 py-2">
                        <MontoDisplay monto={a.total_pendiente} tipo="neutro" className="!text-danger" />
                      </td>
                      <td className="px-4 py-2 text-muted">-</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        )}
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
