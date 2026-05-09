import { useEffect, useState } from "react";
import MontoDisplay from "../components/MontoDisplay.jsx";
import Toast from "../components/Toast.jsx";
import { fetchAlumnos, getConfiguracion } from "../services/api.js";
import {
  crearConfigCuota,
  crearCuotaEspecial,
  fetchConfigCuotas,
  fetchCuotasEspeciales,
  fetchDeudores,
  fetchEstadoCuotaEspecial,
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
  const [cursoId, setCursoId] = useState(null);
  const [anio, setAnio] = useState(2026);
  const [configs, setConfigs] = useState([]);
  const [estado, setEstado] = useState(null);
  const [deudores, setDeudores] = useState(null);
  const [selectedDeudores, setSelectedDeudores] = useState(new Set());
  const [toast, setToast] = useState({ visible: false, mensaje: "", tipo: "error" });
  const [cargando, setCargando] = useState(false);

  // Tabs: "curso" | "especiales"
  const [activeTab, setActiveTab] = useState("curso");

  // Formulario nueva config cuota curso
  const [mes, setMes] = useState(3);
  const [monto, setMonto] = useState("");
  const [descripcion, setDescripcion] = useState("");

  // Cuotas especiales
  const [cuotasEspeciales, setCuotasEspeciales] = useState([]);
  const [alumnos, setAlumnos] = useState([]);

  // Formulario cuota especial
  const [showFormEspecial, setShowFormEspecial] = useState(false);
  const [nombreEspecial, setNombreEspecial] = useState("");
  const [montoEspecial, setMontoEspecial] = useState("");
  const [descripcionEspecial, setDescripcionEspecial] = useState("");
  const [aplicaATodos, setAplicaATodos] = useState(true);
  const [alumnosSeleccionados, setAlumnosSeleccionados] = useState(new Set());

  // Detalle cuota especial
  const [cuotaEspecialSeleccionada, setCuotaEspecialSeleccionada] = useState(null);
  const [estadoCuotaEspecial, setEstadoCuotaEspecial] = useState(null);

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

  async function cargar() {
    if (!cursoId) return;
    try {
      const [cfgResponse, est, deud, alumnosData, especiales] = await Promise.all([
        fetchConfigCuotas(cursoId, anio),
        fetchEstadoCuotas(cursoId, anio),
        fetchDeudores(cursoId, anio),
        fetchAlumnos(cursoId),
        fetchCuotasEspeciales(cursoId, anio),
      ]);
      // La API ahora retorna { cuotas_curso, cuotas_especiales }
      setConfigs(Array.isArray(cfgResponse?.cuotas_curso) ? cfgResponse.cuotas_curso : []);
      setEstado(est);
      setDeudores(deud);
      setSelectedDeudores(new Set());
      setAlumnos(Array.isArray(alumnosData) ? alumnosData : []);
      setCuotasEspeciales(Array.isArray(especiales) ? especiales : []);
    } catch (err) {
      setToast({ visible: true, tipo: "error", mensaje: getErrorMessage(err) });
    }
  }

  useEffect(() => {
    cargarCurso();
  }, []);

  useEffect(() => {
    if (cursoId) {
      cargar();
    }
  }, [anio, cursoId]);

  // Funciones para cuotas especiales
  function onMontoEspecialChange(e) {
    const v = e.target.value.replace(/\D/g, "");
    setMontoEspecial(v ? formatoMilesChilenos(parseInt(v, 10)) : "");
  }

  function toggleAlumnoSeleccionado(alumnoId) {
    const newSet = new Set(alumnosSeleccionados);
    if (newSet.has(alumnoId)) {
      newSet.delete(alumnoId);
    } else {
      newSet.add(alumnoId);
    }
    setAlumnosSeleccionados(newSet);
  }

  async function crearCuotaEspecialSubmit(ev) {
    ev.preventDefault();
    try {
      const montoNum = parseInt(montoEspecial.replace(/\D/g, ""), 10);
      if (!montoNum || montoNum <= 0) {
        mostrarToast(null, "Ingrese un monto válido.");
        return;
      }
      if (!nombreEspecial.trim()) {
        mostrarToast(null, "El nombre de la cuota especial es obligatorio.");
        return;
      }
      setCargando(true);

      const alumnoIds = aplicaATodos ? null : Array.from(alumnosSeleccionados);

      await crearCuotaEspecial({
        curso_id: cursoId,
        anio,
        monto: montoNum,
        descripcion: descripcionEspecial.trim() || nombreEspecial.trim(),
        nombre_especial: nombreEspecial.trim(),
        alumno_ids: alumnoIds,
      });
      mostrarToast("Cuota especial creada correctamente.", null);
      setNombreEspecial("");
      setMontoEspecial("");
      setDescripcionEspecial("");
      setAplicaATodos(true);
      setAlumnosSeleccionados(new Set());
      setShowFormEspecial(false);
      cargar();
    } catch (err) {
      mostrarToast(null, getErrorMessage(err));
    } finally {
      setCargando(false);
    }
  }

  async function verDetalleCuotaEspecial(cuota) {
    try {
      setCargando(true);
      const estado = await fetchEstadoCuotaEspecial(cuota.id);
      setCuotaEspecialSeleccionada(cuota);
      setEstadoCuotaEspecial(estado);
    } catch (err) {
      mostrarToast(null, getErrorMessage(err));
    } finally {
      setCargando(false);
    }
  }

  async function registrarPagoEspecial(alumno) {
    if (!cuotaEspecialSeleccionada) return;
    const nombreAlumno = alumno.alumno?.nombre_completo || "Alumno";
    const confirmar = window.confirm(
      `¿Registrar pago de $${formatoMilesChilenos(cuotaEspecialSeleccionada.monto)} para ${nombreAlumno} - ${cuotaEspecialSeleccionada.nombre_especial}?`
    );
    if (!confirmar) return;

    try {
      setCargando(true);
      const resultado = await registrarPagoCuota({
        alumno_id: alumno.alumno.id,
        config_cuota_id: cuotaEspecialSeleccionada.id,
        fecha_pago: null,
      });
      mostrarToast("Pago registrado correctamente.", null);

      // Recargar el estado de la cuota especial
      const estado = await fetchEstadoCuotaEspecial(cuotaEspecialSeleccionada.id);
      setEstadoCuotaEspecial(estado);
      cargar();

      // Preguntar si desea enviar notificación
      const notificar = window.confirm("¿Deseas enviar una notificación por email al apoderado?");
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
        curso_id: cursoId,
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
      const resultado = await notificarDeuda(cursoId, anio, Array.from(selectedDeudores));
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
      const resultado = await notificarDeuda(cursoId, anio, null);
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
    <div className="min-h-screen w-full max-w-full overflow-x-hidden pb-24">
      {/* Header mobile-first */}
      <header className="min-h-[64px] border-b border-primary/15 bg-surface shadow-sm">
        <div className="mx-auto flex max-w-6xl flex-col items-start justify-between gap-3 px-4 py-4 sm:flex-row sm:items-center">
          <div className="min-w-0 flex-1">
            <h1 className="text-xl font-bold text-primary sm:text-2xl">Cuotas</h1>
            <p className="text-sm text-muted">Gestión de cuotas del curso</p>
          </div>
          <select
            value={anio}
            onChange={(e) => setAnio(parseInt(e.target.value, 10))}
            className="h-12 rounded-lg border border-muted/40 px-3 py-2 text-base outline-none ring-primary focus:ring-2"
          >
            <option value={2025}>2025</option>
            <option value={2026}>2026</option>
            <option value={2027}>2027</option>
          </select>
        </div>
      </header>

      <main className="mx-auto max-w-6xl space-y-6 px-4 py-6">
        {/* Tabs */}
        <div className="flex border-b border-muted/20">
          <button
            type="button"
            onClick={() => setActiveTab("curso")}
            className={`flex-1 px-4 py-3 text-center text-base font-medium sm:flex-none sm:px-6 ${
              activeTab === "curso"
                ? "border-b-2 border-primary text-primary"
                : "text-muted hover:text-ink"
            }`}
          >
            Cuotas del Curso
          </button>
          <button
            type="button"
            onClick={() => setActiveTab("especiales")}
            className={`flex-1 px-4 py-3 text-center text-base font-medium sm:flex-none sm:px-6 ${
              activeTab === "especiales"
                ? "border-b-2 border-primary text-primary"
                : "text-muted hover:text-ink"
            }`}
          >
            Cuotas Especiales
            {cuotasEspeciales.length > 0 && (
              <span className="ml-2 inline-flex rounded-full bg-primary/10 px-2 py-0.5 text-xs">
                {cuotasEspeciales.length}
              </span>
            )}
          </button>
        </div>

        {/* TAB 1: Cuotas del Curso */}
        {activeTab === "curso" && (
          <>
            {/* Configurar cuota */}
            <section className="rounded-2xl border border-muted/20 bg-surface p-4 shadow-sm sm:p-6">
              <h2 className="mb-4 font-semibold text-primary">Configurar cuota mensual</h2>
              <form onSubmit={crearConfig} className="flex flex-col gap-3 sm:flex-row sm:flex-wrap sm:items-end">
                <div>
                  <label className="mb-1 block text-sm font-medium text-muted">Mes</label>
                  <select
                    value={mes}
                    onChange={(e) => setMes(parseInt(e.target.value, 10))}
                    className="h-12 w-full rounded-lg border border-muted/40 px-3 py-2 text-base outline-none ring-primary focus:ring-2 sm:w-auto"
                  >
                    {NOMBRES_MESES.slice(1).map((n, i) => (
                      <option key={i + 1} value={i + 1}>{n}</option>
                    ))}
                  </select>
                </div>
                <div className="flex-1">
                  <label className="mb-1 block text-sm font-medium text-muted">Monto (CLP)</label>
                  <input
                    type="text"
                    inputMode="numeric"
                    placeholder="Ej: 15000"
                    value={monto}
                    onChange={onMontoChange}
                    className="h-12 w-full rounded-lg border border-muted/40 px-3 py-2 text-base outline-none ring-primary focus:ring-2"
                  />
                </div>
                <div className="flex-[2]">
                  <label className="mb-1 block text-sm font-medium text-muted">Descripción</label>
                  <input
                    type="text"
                    placeholder="Ej: Cuota marzo 2026"
                    value={descripcion}
                    onChange={(e) => setDescripcion(e.target.value)}
                    className="h-12 w-full rounded-lg border border-muted/40 px-3 py-2 text-base outline-none ring-primary focus:ring-2"
                  />
                </div>
                <button
                  type="submit"
                  disabled={cargando}
                  className="h-12 rounded-lg bg-primary px-5 py-3 font-medium text-white shadow hover:bg-primary/90 disabled:opacity-60"
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
                        <th className="px-4 py-3 font-semibold">Alumno</th>
                        {configs.map((c) => (
                          <th key={c.id} className="px-2 py-3 text-center font-semibold">
                            {NOMBRES_MESES[c.mes]}
                          </th>
                        ))}
                        <th className="px-4 py-3 text-center font-semibold">Pagado</th>
                        <th className="px-4 py-3 text-center font-semibold">Pendiente</th>
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
                            <td className="px-4 py-3 font-medium">{a.alumno.nombre_completo}</td>
                            {configs.map((c) => {
                              const mesEstado = a.meses.find((m) => m.mes === c.mes);
                              return celdaEstado(mesEstado, a.alumno, c);
                            })}
                            <td className="px-4 py-3 text-center">
                              <MontoDisplay monto={a.total_pagado} tipo="neutro" className="!text-success" />
                            </td>
                            <td className="px-4 py-3 text-center">
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
                  <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
                    <h2 className="font-semibold text-primary">Apoderados con deuda pendiente</h2>
                    <div className="flex flex-col gap-2 sm:flex-row">
                      <button
                        type="button"
                        onClick={notificarSeleccionados}
                        disabled={cargando || selectedDeudores.size === 0}
                        className="h-12 rounded-lg bg-primary px-4 py-3 text-sm font-medium text-white shadow hover:bg-primary/90 disabled:opacity-60"
                      >
                        Notificar seleccionados ({selectedDeudores.size})
                      </button>
                      <button
                        type="button"
                        onClick={notificarTodosDeudores}
                        disabled={cargando}
                        className="h-12 rounded-lg border border-primary px-4 py-3 text-sm font-medium text-primary hover:bg-primary/5 disabled:opacity-60"
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
                        <th className="px-4 py-3 font-semibold">
                          <input
                            type="checkbox"
                            checked={selectedDeudores.size === deudores.alumnos.length}
                            onChange={toggleSelectAllDeudores}
                            className="rounded border-muted/40 text-primary focus:ring-primary"
                          />
                        </th>
                        <th className="px-4 py-3 font-semibold">Nombre alumno</th>
                        <th className="px-4 py-3 font-semibold">Meses pendientes</th>
                        <th className="px-4 py-3 font-semibold">Monto total</th>
                      </tr>
                    </thead>
                    <tbody>
                      {deudores.alumnos.map((a) => (
                        <tr key={a.alumno.id} className="border-t border-muted/10">
                          <td className="px-4 py-3">
                            <input
                              type="checkbox"
                              checked={selectedDeudores.has(a.alumno.id)}
                              onChange={() => toggleDeudorSelection(a.alumno.id)}
                              className="rounded border-muted/40 text-primary focus:ring-primary"
                            />
                          </td>
                          <td className="px-4 py-3 font-medium">{a.alumno.nombre_completo}</td>
                          <td className="px-4 py-3">
                            {a.total_pendiente > 0 ? (
                              <span className="inline-flex rounded-full bg-red-100 px-2 py-1 text-xs font-semibold text-danger">
                                {a.meses.filter((m) => !m.pagado).length} mes(es)
                              </span>
                            ) : (
                              "-"
                            )}
                          </td>
                          <td className="px-4 py-3">
                            <MontoDisplay monto={a.total_pendiente} tipo="neutro" className="!text-danger" />
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </section>
            )}
          </>
        )}

        {/* TAB 2: Cuotas Especiales */}
        {activeTab === "especiales" && (
          <>
            {/* Botón crear cuota especial */}
            <div className="flex flex-col gap-3 sm:flex-row">
              <button
                type="button"
                onClick={() => setShowFormEspecial(!showFormEspecial)}
                className="h-12 w-full rounded-xl bg-primary px-6 py-3 font-medium text-white shadow hover:bg-primary/90 sm:w-auto"
              >
                {showFormEspecial ? "Cancelar" : "+ Crear cuota especial"}
              </button>
            </div>

            {/* Formulario cuota especial */}
            {showFormEspecial && (
              <section className="rounded-2xl border border-muted/20 bg-surface p-4 shadow-sm sm:p-6">
                <h2 className="mb-4 font-semibold text-primary">Nueva cuota especial</h2>
                <form onSubmit={crearCuotaEspecialSubmit} className="space-y-4">
                  <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
                    <div>
                      <label className="mb-1 block text-sm font-medium text-muted">Nombre *</label>
                      <input
                        type="text"
                        placeholder="Ej: Kermés Mes del Mar"
                        value={nombreEspecial}
                        onChange={(e) => setNombreEspecial(e.target.value)}
                        className="h-12 w-full rounded-lg border border-muted/40 px-3 py-3 text-base outline-none ring-primary focus:ring-2"
                        required
                      />
                    </div>
                    <div>
                      <label className="mb-1 block text-sm font-medium text-muted">Monto (CLP) *</label>
                      <input
                        type="text"
                        inputMode="numeric"
                        placeholder="Ej: 3000"
                        value={montoEspecial}
                        onChange={onMontoEspecialChange}
                        className="h-12 w-full rounded-lg border border-muted/40 px-3 py-3 text-base outline-none ring-primary focus:ring-2"
                        required
                      />
                    </div>
                  </div>
                  <div>
                    <label className="mb-1 block text-sm font-medium text-muted">Descripción (opcional)</label>
                    <input
                      type="text"
                      placeholder="Descripción de la cuota especial"
                      value={descripcionEspecial}
                      onChange={(e) => setDescripcionEspecial(e.target.value)}
                      className="h-12 w-full rounded-lg border border-muted/40 px-3 py-3 text-base outline-none ring-primary focus:ring-2"
                    />
                  </div>

                  {/* Selector de alumnos */}
                  <div>
                    <label className="mb-2 block text-sm font-medium text-muted">¿A quién aplica?</label>
                    <div className="space-y-2">
                      <label className="flex cursor-pointer items-center gap-2">
                        <input
                          type="radio"
                          checked={aplicaATodos}
                          onChange={() => setAplicaATodos(true)}
                          className="text-primary focus:ring-primary"
                        />
                        <span className="text-base">Todos los alumnos</span>
                      </label>
                      <label className="flex cursor-pointer items-center gap-2">
                        <input
                          type="radio"
                          checked={!aplicaATodos}
                          onChange={() => setAplicaATodos(false)}
                          className="text-primary focus:ring-primary"
                        />
                        <span className="text-base">Alumnos específicos</span>
                      </label>
                    </div>
                  </div>

                  {!aplicaATodos && (
                    <div className="max-h-60 overflow-y-auto rounded-lg border border-muted/20 bg-bg p-3">
                      <p className="mb-2 text-sm text-muted">Selecciona los alumnos:</p>
                      {alumnos.map((a) => (
                        <label key={a.id} className="flex cursor-pointer items-center gap-2 py-1">
                          <input
                            type="checkbox"
                            checked={alumnosSeleccionados.has(a.id)}
                            onChange={() => toggleAlumnoSeleccionado(a.id)}
                            className="rounded border-muted/40 text-primary focus:ring-primary"
                          />
                          <span className="text-base">
                            {a.apellido_paterno} {a.apellido_materno || ""}, {a.nombre}
                          </span>
                        </label>
                      ))}
                    </div>
                  )}

                  <div className="flex flex-col-reverse gap-2 pt-2 sm:flex-row">
                    <button
                      type="button"
                      onClick={() => setShowFormEspecial(false)}
                      className="h-12 rounded-lg px-4 py-3 font-medium text-muted hover:bg-bg"
                    >
                      Cancelar
                    </button>
                    <button
                      type="submit"
                      disabled={cargando || (!aplicaATodos && alumnosSeleccionados.size === 0)}
                      className="h-12 rounded-lg bg-primary px-5 py-3 font-medium text-white shadow hover:bg-primary/90 disabled:opacity-60"
                    >
                      {cargando ? "Guardando..." : "Crear cuota especial"}
                    </button>
                  </div>
                </form>
              </section>
            )}

            {/* Lista de cuotas especiales */}
            <section className="space-y-4">
              <h2 className="font-semibold text-primary">Cuotas especiales creadas</h2>
              {cuotasEspeciales.length === 0 ? (
                <div className="rounded-2xl border border-muted/20 bg-surface p-8 text-center text-muted">
                  No hay cuotas especiales creadas para este año.
                </div>
              ) : (
                <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
                  {cuotasEspeciales.map((cuota) => (
                    <div
                      key={cuota.id}
                      onClick={() => verDetalleCuotaEspecial(cuota)}
                      className="cursor-pointer rounded-2xl border border-muted/20 bg-surface p-4 shadow-sm transition-shadow hover:shadow-md sm:p-5"
                    >
                      <div className="flex items-start justify-between">
                        <div>
                          <h3 className="font-semibold text-primary">{cuota.nombre_especial}</h3>
                          <p className="mt-1 text-sm text-muted">{cuota.descripcion}</p>
                        </div>
                        <span className="rounded-full bg-accent/20 px-3 py-1 text-lg font-bold text-primary">
                          ${formatoMilesChilenos(cuota.monto)}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </section>

            {/* Detalle de cuota especial seleccionada */}
            {cuotaEspecialSeleccionada && estadoCuotaEspecial && (
              <section className="overflow-hidden rounded-2xl border border-muted/20 bg-surface shadow-sm">
                <div className="border-b border-muted/15 bg-bg px-4 py-3">
                  <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
                    <div>
                      <h2 className="font-semibold text-primary">{estadoCuotaEspecial.config_cuota.nombre_especial}</h2>
                      <p className="text-sm text-muted">
                        ${formatoMilesChilenos(estadoCuotaEspecial.config_cuota.monto)} cada una ·{" "}
                        {estadoCuotaEspecial.resumen.pagados} de {estadoCuotaEspecial.resumen.total_alumnos} pagados
                      </p>
                    </div>
                    <button
                      type="button"
                      onClick={() => {
                        setCuotaEspecialSeleccionada(null);
                        setEstadoCuotaEspecial(null);
                      }}
                      className="h-10 rounded-lg px-4 py-2 text-sm font-medium text-muted hover:bg-bg"
                    >
                      Cerrar detalle
                    </button>
                  </div>
                </div>
                <div className="overflow-x-auto">
                  <table className="w-full min-w-[400px] text-left text-sm">
                    <thead className="bg-bg text-muted">
                      <tr>
                        <th className="px-4 py-3 font-semibold">Alumno</th>
                        <th className="px-4 py-3 text-center font-semibold">Estado</th>
                        <th className="px-4 py-3 text-center font-semibold">Acción</th>
                      </tr>
                    </thead>
                    <tbody>
                      {estadoCuotaEspecial.alumnos.map((a) => (
                        <tr key={a.alumno.id} className="border-t border-muted/10">
                          <td className="px-4 py-3 font-medium">{a.alumno.nombre_completo}</td>
                          <td className="px-4 py-3 text-center">
                            {a.pagado ? (
                              <span className="inline-flex items-center gap-1 rounded-full bg-green-100 px-3 py-1 text-sm font-semibold text-success">
                                ✓ Pagado
                                {a.folio && <span className="text-xs">({a.folio})</span>}
                              </span>
                            ) : (
                              <span className="inline-flex rounded-full bg-red-100 px-3 py-1 text-sm font-semibold text-danger">
                                Pendiente
                              </span>
                            )}
                          </td>
                          <td className="px-4 py-3 text-center">
                            {!a.pagado && (
                              <button
                                type="button"
                                onClick={() => registrarPagoEspecial(a)}
                                className="h-10 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-white hover:bg-primary/90"
                              >
                                Registrar pago
                              </button>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                {/* Resumen */}
                <div className="grid grid-cols-2 gap-4 border-t border-muted/10 bg-bg p-4 sm:grid-cols-4">
                  <div className="text-center">
                    <p className="text-sm text-muted">Total alumnos</p>
                    <p className="text-xl font-bold text-primary">{estadoCuotaEspecial.resumen.total_alumnos}</p>
                  </div>
                  <div className="text-center">
                    <p className="text-sm text-muted">Pagados</p>
                    <p className="text-xl font-bold text-success">{estadoCuotaEspecial.resumen.pagados}</p>
                  </div>
                  <div className="text-center">
                    <p className="text-sm text-muted">Pendientes</p>
                    <p className="text-xl font-bold text-danger">{estadoCuotaEspecial.resumen.pendientes}</p>
                  </div>
                  <div className="text-center">
                    <p className="text-sm text-muted">Recaudado</p>
                    <p className="text-xl font-bold text-primary">
                      ${formatoMilesChilenos(estadoCuotaEspecial.resumen.total_recaudado)}
                    </p>
                  </div>
                </div>
              </section>
            )}
          </>
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
