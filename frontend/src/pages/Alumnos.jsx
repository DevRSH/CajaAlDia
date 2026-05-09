import { useEffect, useState } from "react";
import { Edit, Trash2 } from "lucide-react";
import MontoDisplay from "../components/MontoDisplay.jsx";
import Toast from "../components/Toast.jsx";
import { actualizarAlumno, crearAlumno, eliminarAlumno, fetchAlumnos, getConfiguracion, getErrorMessage } from "../services/api.js";

function formatoMilesChilenos(num) {
  if (!num) return "0";
  return String(num).replace(/\B(?=(\d{3})+(?!\d))/g, ".");
}

export default function Alumnos() {
  const [cursoId, setCursoId] = useState(null);
  const [alumnos, setAlumnos] = useState([]);
  const [modal, setModal] = useState(false);
  const [modalDetalle, setModalDetalle] = useState(null);
  const [modalEdicion, setModalEdicion] = useState(false);
  const [alumnoEditando, setAlumnoEditando] = useState(null);
  const [modalEliminar, setModalEliminar] = useState(false);
  const [alumnoEliminar, setAlumnoEliminar] = useState(null);
  const [toast, setToast] = useState({ visible: false, mensaje: "", tipo: "error" });
  const [cargando, setCargando] = useState(false);

  // Formulario nuevo alumno
  const [nombre, setNombre] = useState("");
  const [apellidoPaterno, setApellidoPaterno] = useState("");
  const [apellidoMaterno, setApellidoMaterno] = useState("");
  const [rut, setRut] = useState("");
  const [apodNombre, setApodNombre] = useState("");
  const [apodApellido, setApodApellido] = useState("");
  const [apodEmail, setApodEmail] = useState("");
  const [apodTelefono, setApodTelefono] = useState("");

  // Formulario edición alumno
  const [editNombre, setEditNombre] = useState("");
  const [editApellidoPaterno, setEditApellidoPaterno] = useState("");
  const [editApellidoMaterno, setEditApellidoMaterno] = useState("");
  const [editRut, setEditRut] = useState("");
  const [editApodNombre, setEditApodNombre] = useState("");
  const [editApodApellido, setEditApodApellido] = useState("");
  const [editApodEmail, setEditApodEmail] = useState("");
  const [editApodTelefono, setEditApodTelefono] = useState("");

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
      const data = await fetchAlumnos(cursoId);
      setAlumnos(Array.isArray(data) ? data : []);
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
  }, [cursoId]);

  function mostrarToast(okMsg, errMsg) {
    if (errMsg) setToast({ visible: true, tipo: "error", mensaje: errMsg });
    else if (okMsg) setToast({ visible: true, tipo: "success", mensaje: okMsg });
  }

  function cerrarModal() {
    setModal(false);
    setNombre("");
    setApellidoPaterno("");
    setApellidoMaterno("");
    setRut("");
    setApodNombre("");
    setApodApellido("");
    setApodEmail("");
    setApodTelefono("");
    cargar();
  }

  async function guardar(ev) {
    ev.preventDefault();
    try {
      if (!nombre.trim() || !apellidoPaterno.trim()) {
        mostrarToast(null, "Nombre y apellido paterno son obligatorios.");
        return;
      }
      if (!apodNombre.trim() || !apodApellido.trim()) {
        mostrarToast(null, "Nombre y apellido del apoderado son obligatorios.");
        return;
      }
      setCargando(true);
      await crearAlumno({
        curso_id: cursoId,
        nombre: nombre.trim(),
        apellido_paterno: apellidoPaterno.trim(),
        apellido_materno: apellidoMaterno.trim() || null,
        rut: rut.trim() || null,
        apoderado: {
          nombre: apodNombre.trim(),
          apellido_paterno: apodApellido.trim(),
          email: apodEmail.trim() || null,
          telefono: apodTelefono.trim() || null,
        },
      });
      mostrarToast("Alumno creado correctamente.", null);
      cerrarModal();
    } catch (err) {
      mostrarToast(null, getErrorMessage(err));
    } finally {
      setCargando(false);
    }
  }

  function abrirDetalle(alumno) {
    setModalDetalle(alumno);
  }

  function abrirEdicion(alumno) {
    setAlumnoEditando(alumno);
    setEditNombre(alumno.nombre || "");
    setEditApellidoPaterno(alumno.apellido_paterno || "");
    setEditApellidoMaterno(alumno.apellido_materno || "");
    setEditRut(alumno.rut || "");
    setEditApodNombre(alumno.apoderado?.nombre || "");
    setEditApodApellido(alumno.apoderado?.apellido_paterno || "");
    setEditApodEmail(alumno.apoderado?.email || "");
    setEditApodTelefono(alumno.apoderado?.telefono || "");
    setModalEdicion(true);
  }

  function abrirEliminar(alumno) {
    setAlumnoEliminar(alumno);
    setModalEliminar(true);
  }

  function cerrarEdicion() {
    setModalEdicion(false);
    setAlumnoEditando(null);
    setEditNombre("");
    setEditApellidoPaterno("");
    setEditApellidoMaterno("");
    setEditRut("");
    setEditApodNombre("");
    setEditApodApellido("");
    setEditApodEmail("");
    setEditApodTelefono("");
  }

  async function guardarEdicion(ev) {
    ev.preventDefault();
    try {
      if (!editNombre.trim() || !editApellidoPaterno.trim()) {
        mostrarToast(null, "Nombre y apellido paterno son obligatorios.");
        return;
      }
      if (!editApodNombre.trim() || !editApodApellido.trim()) {
        mostrarToast(null, "Nombre y apellido del apoderado son obligatorios.");
        return;
      }
      setCargando(true);
      await actualizarAlumno(alumnoEditando.id, {
        nombre: editNombre.trim(),
        apellido_paterno: editApellidoPaterno.trim(),
        apellido_materno: editApellidoMaterno.trim() || null,
        rut: editRut.trim() || null,
        apoderado: {
          nombre: editApodNombre.trim(),
          apellido_paterno: editApodApellido.trim(),
          email: editApodEmail.trim() || null,
          telefono: editApodTelefono.trim() || null,
        },
      });
      mostrarToast("Alumno actualizado correctamente.", null);
      cerrarEdicion();
      cargar();
    } catch (err) {
      mostrarToast(null, getErrorMessage(err));
    } finally {
      setCargando(false);
    }
  }

  async function confirmarEliminar() {
    try {
      setCargando(true);
      const resultado = await eliminarAlumno(alumnoEliminar.id);
      if (resultado.advertencia) {
        mostrarToast(resultado.advertencia, null);
        setToast((t) => ({ ...t, tipo: "warning" }));
      } else {
        mostrarToast("Alumno eliminado correctamente.", null);
      }
      setModalEliminar(false);
      setAlumnoEliminar(null);
      cargar();
    } catch (err) {
      mostrarToast(null, getErrorMessage(err));
    } finally {
      setCargando(false);
    }
  }

  function nombreCompleto(alumno) {
    return `${alumno.apellido_paterno} ${alumno.apellido_materno || ""}, ${alumno.nombre}`.trim();
  }

  function estadoBadge(estado) {
    if (estado.estado === "al_dia") {
      return <span className="inline-flex rounded-full bg-green-100 px-2 py-0.5 text-xs font-semibold text-success">Al día</span>;
    }
    if (estado.estado === "debe_meses") {
      return (
        <span className="inline-flex rounded-full bg-red-100 px-2 py-0.5 text-xs font-semibold text-danger">
          Debe {estado.meses_pendientes} mes{estado.meses_pendientes > 1 ? "es" : ""} (${formatoMilesChilenos(estado.monto_pendiente)})
        </span>
      );
    }
    return <span className="inline-flex rounded-full bg-gray-100 px-2 py-0.5 text-xs font-semibold text-muted">Sin cuotas</span>;
  }

  return (
    <div className="min-h-screen w-full max-w-full overflow-x-hidden pb-24">
      {/* Header mobile-first */}
      <header className="min-h-[64px] border-b border-primary/15 bg-surface shadow-sm">
        <div className="mx-auto flex max-w-5xl flex-col items-start justify-between gap-3 px-4 py-4 sm:flex-row sm:items-center">
          <div className="min-w-0 flex-1">
            <h1 className="text-xl font-bold text-primary sm:text-2xl">Alumnos</h1>
            <p className="text-sm text-muted">Gestión de alumnos y apoderados</p>
          </div>
          <button
            type="button"
            onClick={() => setModal(true)}
            className="h-12 w-full rounded-xl bg-primary px-4 py-3 text-base font-medium text-white shadow hover:bg-primary/90 active:bg-primary/80 sm:w-auto"
          >
            + Agregar alumno
          </button>
        </div>
      </header>

      <main className="mx-auto max-w-5xl px-4 py-6">
        <section className="overflow-hidden rounded-2xl border border-muted/20 bg-surface shadow-sm">
          {/* Tabla scrollable horizontalmente */}
          <div className="overflow-x-auto">
            <table className="w-full min-w-[800px] text-left text-sm">
              <thead className="bg-bg text-muted">
                <tr>
                  <th className="px-4 py-3 font-semibold">Nombre completo</th>
                  <th className="px-4 py-3 font-semibold">RUT</th>
                  <th className="px-4 py-3 font-semibold">Email apoderado</th>
                  <th className="px-4 py-3 font-semibold">Teléfono</th>
                  <th className="px-4 py-3 font-semibold">Estado</th>
                  <th className="px-4 py-3 font-semibold">Acciones</th>
                </tr>
              </thead>
              <tbody>
                {alumnos.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="px-4 py-8 text-center text-muted">
                      No hay alumnos registrados.
                    </td>
                  </tr>
                ) : (
                  alumnos.map((a) => (
                    <tr
                      key={a.id}
                      className="cursor-pointer border-t border-muted/10 hover:bg-bg/80"
                      onClick={() => abrirDetalle(a)}
                    >
                      <td className="px-4 py-3 font-medium">{nombreCompleto(a)}</td>
                      <td className="px-4 py-3">{a.rut || "-"}</td>
                      <td className="px-4 py-3">{a.apoderado?.email || "-"}</td>
                      <td className="px-4 py-3">{a.apoderado?.telefono || "-"}</td>
                      <td className="px-4 py-3">{estadoBadge(a.estado_cuota)}</td>
                      <td className="px-4 py-3">
                        <div className="flex gap-2">
                          {/* Botones de acción con tamaño mínimo 40px para touch */}
                          <button
                            type="button"
                            onClick={(e) => {
                              e.stopPropagation();
                              abrirEdicion(a);
                            }}
                            className="flex h-10 w-10 items-center justify-center rounded p-1 text-muted hover:bg-bg hover:text-primary"
                            title="Editar"
                            aria-label="Editar alumno"
                          >
                            <Edit size={18} />
                          </button>
                          <button
                            type="button"
                            onClick={(e) => {
                              e.stopPropagation();
                              abrirEliminar(a);
                            }}
                            className="flex h-10 w-10 items-center justify-center rounded p-1 text-muted hover:bg-bg hover:text-danger"
                            title="Eliminar"
                            aria-label="Eliminar alumno"
                          >
                            <Trash2 size={18} />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </section>
      </main>

      {/* Modal nuevo alumno - full screen en mobile, centrado en desktop */}
      {modal && (
        <div className="fixed inset-0 z-40 flex items-start justify-center bg-black/40 p-0 sm:items-center sm:p-4">
          <div className="h-full w-full overflow-y-auto bg-surface p-4 shadow-xl sm:h-auto sm:max-h-[90vh] sm:max-w-lg sm:rounded-2xl sm:p-6">
            <h2 className="mb-4 text-xl font-bold text-primary">Nuevo alumno</h2>
            <form onSubmit={guardar} className="space-y-4">
              <div>
                <label className="mb-1 block text-sm font-medium text-muted">Nombre</label>
                <input
                  type="text"
                  value={nombre}
                  onChange={(e) => setNombre(e.target.value)}
                  className="w-full rounded-lg border border-muted/40 px-3 py-3 text-base outline-none ring-primary focus:ring-2"
                  placeholder="Nombre del alumno"
                />
              </div>
              <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
                <div>
                  <label className="mb-1 block text-sm font-medium text-muted">Apellido paterno</label>
                  <input
                    type="text"
                    value={apellidoPaterno}
                    onChange={(e) => setApellidoPaterno(e.target.value)}
                    className="w-full rounded-lg border border-muted/40 px-3 py-3 text-base outline-none ring-primary focus:ring-2"
                    placeholder="Apellido paterno"
                  />
                </div>
                <div>
                  <label className="mb-1 block text-sm font-medium text-muted">Apellido materno</label>
                  <input
                    type="text"
                    value={apellidoMaterno}
                    onChange={(e) => setApellidoMaterno(e.target.value)}
                    className="w-full rounded-lg border border-muted/40 px-3 py-3 text-base outline-none ring-primary focus:ring-2"
                    placeholder="Apellido materno (opcional)"
                  />
                </div>
              </div>
              <div>
                <label className="mb-1 block text-sm font-medium text-muted">RUT (opcional)</label>
                <input
                  type="text"
                  placeholder="XX.XXX.XXX-X"
                  value={rut}
                  onChange={(e) => setRut(e.target.value)}
                  className="w-full rounded-lg border border-muted/40 px-3 py-3 text-base outline-none ring-primary focus:ring-2"
                />
              </div>
              <div className="border-t border-muted/20 pt-4">
                <h3 className="mb-3 font-semibold text-primary">Apoderado</h3>
                <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
                  <div>
                    <label className="mb-1 block text-sm font-medium text-muted">Nombre</label>
                    <input
                      type="text"
                      value={apodNombre}
                      onChange={(e) => setApodNombre(e.target.value)}
                      className="w-full rounded-lg border border-muted/40 px-3 py-3 text-base outline-none ring-primary focus:ring-2"
                      placeholder="Nombre del apoderado"
                    />
                  </div>
                  <div>
                    <label className="mb-1 block text-sm font-medium text-muted">Apellido paterno</label>
                    <input
                      type="text"
                      value={apodApellido}
                      onChange={(e) => setApodApellido(e.target.value)}
                      className="w-full rounded-lg border border-muted/40 px-3 py-3 text-base outline-none ring-primary focus:ring-2"
                      placeholder="Apellido del apoderado"
                    />
                  </div>
                </div>
                <div className="mt-3 grid grid-cols-1 gap-3 sm:grid-cols-2">
                  <div>
                    <label className="mb-1 block text-sm font-medium text-muted">Email (opcional)</label>
                    <input
                      type="email"
                      value={apodEmail}
                      onChange={(e) => setApodEmail(e.target.value)}
                      className="w-full rounded-lg border border-muted/40 px-3 py-3 text-base outline-none ring-primary focus:ring-2"
                      placeholder="email@ejemplo.com"
                    />
                  </div>
                  <div>
                    <label className="mb-1 block text-sm font-medium text-muted">Teléfono (opcional)</label>
                    <input
                      type="tel"
                      value={apodTelefono}
                      onChange={(e) => setApodTelefono(e.target.value)}
                      className="w-full rounded-lg border border-muted/40 px-3 py-3 text-base outline-none ring-primary focus:ring-2"
                      placeholder="+569XXXXXXXX"
                    />
                  </div>
                </div>
              </div>
              {/* Botones full-width en mobile */}
              <div className="flex flex-col-reverse gap-2 pt-2 sm:flex-row sm:justify-end">
                <button
                  type="button"
                  className="h-12 rounded-lg px-4 py-3 font-medium text-muted hover:bg-bg"
                  onClick={cerrarModal}
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  disabled={cargando}
                  className="h-12 rounded-lg bg-primary px-5 py-3 font-medium text-white shadow hover:bg-primary/90 disabled:opacity-60"
                >
                  {cargando ? "Guardando..." : "Guardar"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal detalle alumno - full screen en mobile */}
      {modalDetalle && (
        <div className="fixed inset-0 z-40 flex items-start justify-center bg-black/40 p-0 sm:items-center sm:p-4">
          <div className="h-full w-full overflow-y-auto bg-surface p-4 shadow-xl sm:h-auto sm:max-h-[90vh] sm:max-w-lg sm:rounded-2xl sm:p-6">
            <h2 className="mb-4 text-lg font-bold text-primary sm:text-xl">{nombreCompleto(modalDetalle)}</h2>
            <div className="space-y-3 text-sm">
              <div>
                <span className="font-semibold text-muted">RUT:</span> {modalDetalle.rut || "-"}
              </div>
              <div>
                <span className="font-semibold text-muted">Estado:</span> {estadoBadge(modalDetalle.estado_cuota)}
              </div>
              <div className="border-t border-muted/20 pt-3">
                <h3 className="mb-2 font-semibold text-primary">Apoderado</h3>
                <div>
                  <span className="font-semibold text-muted">Nombre:</span>{" "}
                  {modalDetalle.apoderado
                    ? `${modalDetalle.apoderado.nombre} ${modalDetalle.apoderado.apellido_paterno}`
                    : "-"}
                </div>
                <div>
                  <span className="font-semibold text-muted">Email:</span> {modalDetalle.apoderado?.email || "-"}
                </div>
                <div>
                  <span className="font-semibold text-muted">Teléfono:</span> {modalDetalle.apoderado?.telefono || "-"}
                </div>
              </div>
            </div>
            <div className="mt-6 flex justify-end">
              <button
                type="button"
                className="h-12 w-full rounded-lg border border-muted/40 px-4 py-3 font-medium text-ink sm:w-auto"
                onClick={() => setModalDetalle(null)}
              >
                Cerrar
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Modal edición alumno - full screen en mobile */}
      {modalEdicion && (
        <div className="fixed inset-0 z-40 flex items-start justify-center bg-black/40 p-0 sm:items-center sm:p-4">
          <div className="h-full w-full overflow-y-auto bg-surface p-4 shadow-xl sm:h-auto sm:max-h-[90vh] sm:max-w-lg sm:rounded-2xl sm:p-6">
            <h2 className="mb-4 text-xl font-bold text-primary">Editar alumno</h2>
            <form onSubmit={guardarEdicion} className="space-y-4">
              <div>
                <label className="mb-1 block text-sm font-semibold text-muted">Nombre</label>
                <input
                  type="text"
                  value={editNombre}
                  onChange={(e) => setEditNombre(e.target.value)}
                  className="w-full rounded-lg border border-muted/40 px-3 py-2 outline-none ring-primary focus:ring-2"
                />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="mb-1 block text-sm font-semibold text-muted">Apellido paterno</label>
                  <input
                    type="text"
                    value={editApellidoPaterno}
                    onChange={(e) => setEditApellidoPaterno(e.target.value)}
                    className="w-full rounded-lg border border-muted/40 px-3 py-2 outline-none ring-primary focus:ring-2"
                  />
                </div>
                <div>
                  <label className="mb-1 block text-sm font-semibold text-muted">Apellido materno</label>
                  <input
                    type="text"
                    value={editApellidoMaterno}
                    onChange={(e) => setEditApellidoMaterno(e.target.value)}
                    className="w-full rounded-lg border border-muted/40 px-3 py-2 outline-none ring-primary focus:ring-2"
                  />
                </div>
              </div>
              <div>
                <label className="mb-1 block text-sm font-semibold text-muted">RUT (opcional)</label>
                <input
                  type="text"
                  placeholder="XX.XXX.XXX-X"
                  value={editRut}
                  onChange={(e) => setEditRut(e.target.value)}
                  className="w-full rounded-lg border border-muted/40 px-3 py-2 outline-none ring-primary focus:ring-2"
                />
              </div>
              <div className="border-t border-muted/20 pt-4">
                <h3 className="mb-3 font-semibold text-primary">Apoderado</h3>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="mb-1 block text-sm font-semibold text-muted">Nombre</label>
                    <input
                      type="text"
                      value={editApodNombre}
                      onChange={(e) => setEditApodNombre(e.target.value)}
                      className="w-full rounded-lg border border-muted/40 px-3 py-2 outline-none ring-primary focus:ring-2"
                    />
                  </div>
                  <div>
                    <label className="mb-1 block text-sm font-semibold text-muted">Apellido paterno</label>
                    <input
                      type="text"
                      value={editApodApellido}
                      onChange={(e) => setEditApodApellido(e.target.value)}
                      className="w-full rounded-lg border border-muted/40 px-3 py-2 outline-none ring-primary focus:ring-2"
                    />
                  </div>
                </div>
                <div className="mt-3 grid grid-cols-2 gap-3">
                  <div>
                    <label className="mb-1 block text-sm font-semibold text-muted">Email (opcional)</label>
                    <input
                      type="email"
                      value={editApodEmail}
                      onChange={(e) => setEditApodEmail(e.target.value)}
                      className="w-full rounded-lg border border-muted/40 px-3 py-2 outline-none ring-primary focus:ring-2"
                    />
                  </div>
                  <div>
                    <label className="mb-1 block text-sm font-semibold text-muted">Teléfono (opcional)</label>
                    <input
                      type="text"
                      value={editApodTelefono}
                      onChange={(e) => setEditApodTelefono(e.target.value)}
                      className="w-full rounded-lg border border-muted/40 px-3 py-2 outline-none ring-primary focus:ring-2"
                    />
                  </div>
                </div>
              </div>
              {/* Botones full-width en mobile */}
              <div className="flex flex-col-reverse gap-2 pt-2 sm:flex-row sm:justify-end">
                <button
                  type="button"
                  className="h-12 rounded-lg px-4 py-3 font-medium text-muted hover:bg-bg"
                  onClick={cerrarEdicion}
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  disabled={cargando}
                  className="h-12 rounded-lg bg-primary px-5 py-3 font-medium text-white shadow hover:bg-primary/90 disabled:opacity-60"
                >
                  {cargando ? "Guardando..." : "Guardar cambios"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal confirmar eliminación - full screen en mobile */}
      {modalEliminar && (
        <div className="fixed inset-0 z-40 flex items-start justify-center bg-black/40 p-0 sm:items-center sm:p-4">
          <div className="h-full w-full bg-surface p-4 shadow-xl sm:h-auto sm:max-w-md sm:rounded-2xl sm:p-6">
            <h2 className="mb-4 text-xl font-bold text-primary">Eliminar alumno</h2>
            <p className="mb-6 text-base">
              ¿Eliminar a <strong>{nombreCompleto(alumnoEliminar)}</strong>? Esta acción no se puede deshacer.
            </p>
            <div className="flex flex-col-reverse gap-2 sm:flex-row sm:justify-end">
              <button
                type="button"
                className="h-12 rounded-lg px-4 py-3 font-medium text-muted hover:bg-bg"
                onClick={() => {
                  setModalEliminar(false);
                  setAlumnoEliminar(null);
                }}
              >
                Cancelar
              </button>
              <button
                type="button"
                disabled={cargando}
                onClick={confirmarEliminar}
                className="h-12 rounded-lg bg-danger px-5 py-3 font-medium text-white shadow hover:bg-danger/90 disabled:opacity-60"
              >
                {cargando ? "Eliminando..." : "Eliminar"}
              </button>
            </div>
          </div>
        </div>
      )}

      <Toast
        visible={toast.visible}
        tipo={toast.tipo}
        mensaje={toast.mensaje}
        onClose={() => setToast((t) => ({ ...t, visible: false }))}
      />
    </div>
  );
}
