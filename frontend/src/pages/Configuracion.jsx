import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import logoUrl from "@assets/logo.png";
import Toast from "../components/Toast.jsx";
import { actualizarCurso, crearCurso, getConfiguracion, getErrorMessage, resetearCurso } from "../services/api.js";

export default function Configuracion() {
  const navigate = useNavigate();
  const [modo, setModo] = useState("crear"); // "crear" | "editar"
  const [cargando, setCargando] = useState(true);
  const [guardando, setGuardando] = useState(false);
  const [toast, setToast] = useState({ visible: false, mensaje: "", tipo: "error" });
  const [modalReset, setModalReset] = useState(false);
  const [textoConfirmacion, setTextoConfirmacion] = useState("");

  const [formData, setFormData] = useState({
    codigo: "",
    nombre: "",
    colegio: "",
    año: new Date().getFullYear(),
    directiva: {
      tesorera: "",
      presidenta: "",
      secretaria: "",
    },
  });

  async function cargarConfiguracion() {
    try {
      const config = await getConfiguracion();
      if (config.configurada && config.curso) {
        setModo("editar");
        setFormData({
          codigo: config.curso.codigo,
          nombre: config.curso.nombre,
          colegio: config.curso.colegio,
          año: config.curso.año,
          directiva: {
            tesorera: config.curso.directiva_tesorera || "",
            presidenta: config.curso.directiva_presidenta || "",
            secretaria: config.curso.directiva_secretaria || "",
          },
        });
      }
    } catch (err) {
      setToast({ visible: true, tipo: "error", mensaje: getErrorMessage(err) });
    } finally {
      setCargando(false);
    }
  }

  useEffect(() => {
    cargarConfiguracion();
  }, []);

  function handleChange(e) {
    const { name, value } = e.target;
    if (name.startsWith("directiva_")) {
      const campo = name.replace("directiva_", "");
      setFormData((prev) => ({
        ...prev,
        directiva: { ...prev.directiva, [campo]: value },
      }));
    } else {
      setFormData((prev) => ({ ...prev, [name]: value }));
    }
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setGuardando(true);

    try {
      if (modo === "crear") {
        await crearCurso(formData);
        setToast({ visible: true, tipo: "success", mensaje: "Curso creado exitosamente." });
        setTimeout(() => navigate("/"), 1000);
      } else {
        await actualizarCurso(formData);
        setToast({ visible: true, tipo: "success", mensaje: "Curso actualizado exitosamente." });
      }
    } catch (err) {
      setToast({ visible: true, tipo: "error", mensaje: getErrorMessage(err) });
    } finally {
      setGuardando(false);
    }
  }

  function handleVolver() {
    navigate("/");
  }

  function handleAbrirModalReset() {
    setModalReset(true);
    setTextoConfirmacion("");
  }

  function handleCerrarModalReset() {
    setModalReset(false);
    setTextoConfirmacion("");
  }

  async function handleReset() {
    if (textoConfirmacion !== "RESETEAR") return;
    setGuardando(true);
    try {
      await resetearCurso();
      setToast({ visible: true, tipo: "success", mensaje: "Curso reseteado exitosamente." });
      setTimeout(() => window.location.reload(), 1000);
    } catch (err) {
      setToast({ visible: true, tipo: "error", mensaje: getErrorMessage(err) });
    } finally {
      setGuardando(false);
    }
  }

  if (cargando) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-[#E3F2FD]">
        <div className="text-center">
          <img src={logoUrl} alt="CajaAlDía" className="mx-auto h-20 w-auto animate-pulse" />
          <p className="mt-4 text-muted">Cargando...</p>
        </div>
      </div>
    );
  }

  if (modo === "crear") {
    return (
      <div className="flex min-h-screen items-center justify-center bg-[#E3F2FD] p-4">
        <div className="w-full max-w-lg rounded-2xl bg-white p-8 shadow-xl">
          <div className="mb-6 text-center">
            <img src={logoUrl} alt="CajaAlDía" className="mx-auto h-16 w-auto" />
            <h1 className="mt-4 text-2xl font-bold text-primary">¡Bienvenida!</h1>
            <h2 className="mt-2 text-xl font-semibold text-primary">Configura tu curso</h2>
            <p className="mt-2 text-muted">Solo necesitas unos minutos para comenzar</p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <h3 className="mb-3 font-semibold text-primary">Datos del Curso</h3>
              <div className="space-y-4">
                <div>
                  <label htmlFor="nombre" className="mb-1 block text-sm font-medium text-ink">
                    Nombre del curso *
                  </label>
                  <input
                    type="text"
                    id="nombre"
                    name="nombre"
                    value={formData.nombre}
                    onChange={handleChange}
                    required
                    className="w-full rounded-lg border border-muted/30 px-4 py-2.5 focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20"
                    placeholder="Ej: 4° Básico A"
                  />
                </div>

                <div>
                  <label htmlFor="codigo" className="mb-1 block text-sm font-medium text-ink">
                    Código único *
                  </label>
                  <input
                    type="text"
                    id="codigo"
                    name="codigo"
                    value={formData.codigo}
                    onChange={handleChange}
                    required
                    className="w-full rounded-lg border border-muted/30 px-4 py-2.5 focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20"
                    placeholder="Ej: 4BA-2026"
                  />
                  <p className="mt-1 text-xs text-muted">Este código se usa para el panel público</p>
                </div>

                <div>
                  <label htmlFor="colegio" className="mb-1 block text-sm font-medium text-ink">
                    Nombre del colegio *
                  </label>
                  <input
                    type="text"
                    id="colegio"
                    name="colegio"
                    value={formData.colegio}
                    onChange={handleChange}
                    required
                    className="w-full rounded-lg border border-muted/30 px-4 py-2.5 focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20"
                  />
                </div>

                <div>
                  <label htmlFor="año" className="mb-1 block text-sm font-medium text-ink">
                    Año *
                  </label>
                  <input
                    type="number"
                    id="año"
                    name="año"
                    value={formData.año}
                    onChange={handleChange}
                    required
                    min="2000"
                    max="2100"
                    className="w-full rounded-lg border border-muted/30 px-4 py-2.5 focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20"
                  />
                </div>
              </div>
            </div>

            <div>
              <h3 className="mb-3 font-semibold text-primary">Directiva</h3>
              <div className="space-y-4">
                <div>
                  <label htmlFor="directiva_tesorera" className="mb-1 block text-sm font-medium text-ink">
                    Nombre de la Tesorera *
                  </label>
                  <input
                    type="text"
                    id="directiva_tesorera"
                    name="directiva_tesorera"
                    value={formData.directiva.tesorera}
                    onChange={handleChange}
                    required
                    className="w-full rounded-lg border border-muted/30 px-4 py-2.5 focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20"
                  />
                </div>

                <div>
                  <label htmlFor="directiva_presidenta" className="mb-1 block text-sm font-medium text-ink">
                    Nombre de la Presidenta (opcional)
                  </label>
                  <input
                    type="text"
                    id="directiva_presidenta"
                    name="directiva_presidenta"
                    value={formData.directiva.presidenta}
                    onChange={handleChange}
                    className="w-full rounded-lg border border-muted/30 px-4 py-2.5 focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20"
                  />
                </div>

                <div>
                  <label htmlFor="directiva_secretaria" className="mb-1 block text-sm font-medium text-ink">
                    Nombre de la Secretaria (opcional)
                  </label>
                  <input
                    type="text"
                    id="directiva_secretaria"
                    name="directiva_secretaria"
                    value={formData.directiva.secretaria}
                    onChange={handleChange}
                    className="w-full rounded-lg border border-muted/30 px-4 py-2.5 focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20"
                  />
                </div>
              </div>
            </div>

            <button
              type="submit"
              disabled={guardando}
              className="w-full rounded-xl bg-[#0D47A1] px-6 py-4 text-lg font-medium text-white shadow-lg hover:bg-[#0D47A1]/90 disabled:opacity-50"
            >
              {guardando ? "Guardando..." : "Guardar configuración"}
            </button>
          </form>

          <Toast
            visible={toast.visible}
            tipo={toast.tipo}
            mensaje={toast.mensaje}
            onClose={() => setToast((t) => ({ ...t, visible: false }))}
          />
        </div>
      </div>
    );
  }

  // Modo EDITAR
  return (
    <div className="min-h-screen bg-bg pb-24">
      <header className="border-b border-primary/15 bg-surface shadow-sm">
        <div className="mx-auto max-w-5xl px-4 py-4">
          <h1 className="text-2xl font-bold text-primary">Configuración del Curso</h1>
          <p className="text-muted">Edita los datos de tu curso y directiva</p>
        </div>
      </header>

      <main className="mx-auto max-w-5xl space-y-6 px-4 py-6">
        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="overflow-hidden rounded-2xl border border-muted/20 bg-surface p-6 shadow-sm">
            <h3 className="mb-4 font-semibold text-primary">Datos del Curso</h3>
            <div className="grid gap-4 md:grid-cols-2">
              <div>
                <label htmlFor="nombre" className="mb-1 block text-sm font-medium text-ink">
                  Nombre del curso *
                </label>
                <input
                  type="text"
                  id="nombre"
                  name="nombre"
                  value={formData.nombre}
                  onChange={handleChange}
                  required
                  className="w-full rounded-lg border border-muted/30 px-4 py-2.5 focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20"
                />
              </div>

              <div>
                <label htmlFor="codigo" className="mb-1 block text-sm font-medium text-ink">
                  Código único *
                </label>
                <input
                  type="text"
                  id="codigo"
                  name="codigo"
                  value={formData.codigo}
                  onChange={handleChange}
                  required
                  className="w-full rounded-lg border border-muted/30 px-4 py-2.5 focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20"
                />
                <p className="mt-1 text-xs text-muted">Este código se usa para el panel público</p>
              </div>

              <div>
                <label htmlFor="colegio" className="mb-1 block text-sm font-medium text-ink">
                  Nombre del colegio *
                </label>
                <input
                  type="text"
                  id="colegio"
                  name="colegio"
                  value={formData.colegio}
                  onChange={handleChange}
                  required
                  className="w-full rounded-lg border border-muted/30 px-4 py-2.5 focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20"
                />
              </div>

              <div>
                <label htmlFor="año" className="mb-1 block text-sm font-medium text-ink">
                  Año *
                </label>
                <input
                  type="number"
                  id="año"
                  name="año"
                  value={formData.año}
                  onChange={handleChange}
                  required
                  min="2000"
                  max="2100"
                  className="w-full rounded-lg border border-muted/30 px-4 py-2.5 focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20"
                />
              </div>
            </div>
          </div>

          <div className="overflow-hidden rounded-2xl border border-muted/20 bg-surface p-6 shadow-sm">
            <h3 className="mb-4 font-semibold text-primary">Directiva</h3>
            <div className="grid gap-4 md:grid-cols-3">
              <div>
                <label htmlFor="directiva_tesorera" className="mb-1 block text-sm font-medium text-ink">
                  Tesorera *
                </label>
                <input
                  type="text"
                  id="directiva_tesorera"
                  name="directiva_tesorera"
                  value={formData.directiva.tesorera}
                  onChange={handleChange}
                  required
                  className="w-full rounded-lg border border-muted/30 px-4 py-2.5 focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20"
                />
              </div>

              <div>
                <label htmlFor="directiva_presidenta" className="mb-1 block text-sm font-medium text-ink">
                  Presidenta (opcional)
                </label>
                <input
                  type="text"
                  id="directiva_presidenta"
                  name="directiva_presidenta"
                  value={formData.directiva.presidenta}
                  onChange={handleChange}
                  className="w-full rounded-lg border border-muted/30 px-4 py-2.5 focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20"
                />
              </div>

              <div>
                <label htmlFor="directiva_secretaria" className="mb-1 block text-sm font-medium text-ink">
                  Secretaria (opcional)
                </label>
                <input
                  type="text"
                  id="directiva_secretaria"
                  name="directiva_secretaria"
                  value={formData.directiva.secretaria}
                  onChange={handleChange}
                  className="w-full rounded-lg border border-muted/30 px-4 py-2.5 focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20"
                />
              </div>
            </div>
          </div>

          <div className="flex gap-4">
            <button
              type="submit"
              disabled={guardando}
              className="rounded-xl bg-primary px-6 py-3 font-medium text-white shadow-lg hover:bg-primary/90 disabled:opacity-50"
            >
              {guardando ? "Guardando..." : "Guardar cambios"}
            </button>
            <button
              type="button"
              onClick={handleVolver}
              className="rounded-xl border border-muted/30 px-6 py-3 font-medium text-ink hover:bg-bg"
            >
              Volver
            </button>
          </div>

          <button
            type="button"
            onClick={handleAbrirModalReset}
            className="w-full rounded-xl border-2 border-danger px-6 py-3 font-medium text-danger hover:bg-danger/5"
          >
            Resetear y comenzar de nuevo
          </button>
        </form>

        <Toast
          visible={toast.visible}
          tipo={toast.tipo}
          mensaje={toast.mensaje}
          onClose={() => setToast((t) => ({ ...t, visible: false }))}
        />

        {modalReset && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
            <div className="w-full max-w-md rounded-2xl bg-surface p-6 shadow-xl md:rounded-2xl">
              <h3 className="mb-2 text-xl font-bold text-danger">¿Estás segura?</h3>
              <p className="mb-4 text-muted">Se eliminarán TODOS los datos del curso y no se podrán recuperar.</p>
              <div className="mb-4">
                <label htmlFor="confirmacion" className="mb-1 block text-sm font-medium text-ink">
                  Escribe <span className="font-bold">RESETEAR</span> para confirmar
                </label>
                <input
                  type="text"
                  id="confirmacion"
                  value={textoConfirmacion}
                  onChange={(e) => setTextoConfirmacion(e.target.value)}
                  className="w-full rounded-lg border border-muted/30 px-4 py-2.5 focus:border-danger focus:outline-none focus:ring-2 focus:ring-danger/20"
                  placeholder="RESETEAR"
                />
              </div>
              <div className="flex gap-3">
                <button
                  type="button"
                  onClick={handleCerrarModalReset}
                  className="flex-1 rounded-xl border border-muted/30 px-4 py-3 font-medium text-ink hover:bg-bg"
                >
                  Cancelar
                </button>
                <button
                  type="button"
                  onClick={handleReset}
                  disabled={textoConfirmacion !== "RESETEAR" || guardando}
                  className="flex-1 rounded-xl bg-danger px-4 py-3 font-medium text-white hover:bg-danger/90 disabled:opacity-50"
                >
                  {guardando ? "Reseteando..." : "Confirmar"}
                </button>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
