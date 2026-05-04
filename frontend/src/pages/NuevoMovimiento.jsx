import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import FolioTag from "../components/FolioTag.jsx";
import MontoDisplay from "../components/MontoDisplay.jsx";
import { crearMovimiento, getConfiguracion, getErrorMessage } from "../services/api.js";

function fechaHoyInput() {
  const d = new Date();
  const z = (n) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${z(d.getMonth() + 1)}-${z(d.getDate())}`;
}

/** Solo dígitos → entero CLP positivo */
function parseMontoEntero(raw) {
  const d = raw.replace(/\D/g, "");
  if (!d) return 0;
  const n = parseInt(d, 10);
  return Number.isFinite(n) ? n : 0;
}

/** Formato de miles para el input visible (solo lectura efectiva con máscara) */
function formatoMilesChilenos(num) {
  if (!num) return "";
  return String(num).replace(/\B(?=(\d{3})+(?!\d))/g, ".");
}

/**
 * Modal de nuevo movimiento (ingreso/egreso).
 */
export default function NuevoMovimiento({ abierto, onCerrar, onExitoGlobal }) {
  const navigate = useNavigate();
  const [cursoId, setCursoId] = useState(null);

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
  const [tipo, setTipo] = useState("ingreso");
  const [montoStr, setMontoStr] = useState("");
  const [descripcion, setDescripcion] = useState("");
  const [fecha, setFecha] = useState(fechaHoyInput());
  const [cargando, setCargando] = useState(false);
  const [creado, setCreado] = useState(null);

  useEffect(() => {
    if (abierto) {
      setTipo("ingreso");
      setMontoStr("");
      setDescripcion("");
      setFecha(fechaHoyInput());
      setCreado(null);
      setCargando(false);
    }
  }, [abierto]);

  if (!abierto) return null;

  const monto = parseMontoEntero(montoStr);
  const restantes = 200 - descripcion.length;

  async function guardar(ev) {
    ev.preventDefault();
    try {
      if (monto <= 0) {
        onExitoGlobal?.(null, getErrorMessage({ message: "Ingrese un monto válido mayor a cero." }));
        return;
      }
      if (!descripcion.trim()) {
        onExitoGlobal?.(null, "La descripción es obligatoria.");
        return;
      }
      setCargando(true);
      if (!cursoId) {
        onExitoGlobal?.(null, "No hay curso configurado.");
        return;
      }
      const resp = await crearMovimiento({
        curso_id: cursoId,
        tipo,
        monto,
        descripcion: descripcion.trim(),
        fecha: fecha || undefined,
      });
      setCreado(resp);
      onExitoGlobal?.("Movimiento registrado correctamente.", null);
    } catch (err) {
      try {
        onExitoGlobal?.(null, getErrorMessage(err));
      } catch {
        onExitoGlobal?.(null, "No se pudo guardar el movimiento.");
      }
    } finally {
      setCargando(false);
    }
  }

  function onMontoChange(e) {
    const v = parseMontoEntero(e.target.value);
    setMontoStr(v ? formatoMilesChilenos(v) : "");
  }

  return (
    <div className="fixed inset-0 z-40 flex items-center justify-center bg-black/40 p-4">
      <div className="max-h-[90vh] w-full max-w-lg overflow-y-auto rounded-2xl bg-surface p-6 shadow-xl">
        {!creado ? (
          <form onSubmit={guardar} className="space-y-4">
            <h2 className="text-xl font-bold text-primary">Nuevo movimiento</h2>

            <div className="grid grid-cols-2 gap-3">
              <label
                className={`flex cursor-pointer items-center justify-center rounded-xl border-2 p-4 text-center font-semibold ${
                  tipo === "ingreso"
                    ? "border-success bg-green-50 text-success"
                    : "border-muted/30 hover:border-success/50"
                }`}
              >
                <input
                  type="radio"
                  name="tipo"
                  className="sr-only"
                  checked={tipo === "ingreso"}
                  onChange={() => setTipo("ingreso")}
                />
                INGRESO
              </label>
              <label
                className={`flex cursor-pointer items-center justify-center rounded-xl border-2 p-4 text-center font-semibold ${
                  tipo === "egreso" ? "border-danger bg-red-50 text-danger" : "border-muted/30 hover:border-danger/50"
                }`}
              >
                <input
                  type="radio"
                  name="tipo"
                  className="sr-only"
                  checked={tipo === "egreso"}
                  onChange={() => setTipo("egreso")}
                />
                EGRESO
              </label>
            </div>

            <div>
              <label className="mb-1 block text-sm font-semibold text-muted">Monto (CLP)</label>
              <input
                type="text"
                inputMode="numeric"
                placeholder="Ej: 25000"
                value={montoStr}
                onChange={onMontoChange}
                className="w-full rounded-lg border border-muted/40 px-3 py-3 text-lg outline-none ring-primary focus:ring-2"
              />
              <p className="mt-1 text-sm text-muted">
                Vista previa:{" "}
                <MontoDisplay monto={monto || 0} tipo={monto ? tipo : "neutro"} />
              </p>
            </div>

            <div>
              <div className="mb-1 flex justify-between">
                <label className="text-sm font-semibold text-muted">Descripción</label>
                <span className="text-xs text-muted">{restantes}</span>
              </div>
              <textarea
                maxLength={200}
                rows={3}
                value={descripcion}
                onChange={(e) => setDescripcion(e.target.value)}
                className="w-full rounded-lg border border-muted/40 px-3 py-2 outline-none ring-primary focus:ring-2"
              />
            </div>

            <div>
              <label className="mb-1 block text-sm font-semibold text-muted">Fecha</label>
              <input
                type="date"
                value={fecha}
                onChange={(e) => setFecha(e.target.value)}
                className="w-full rounded-lg border border-muted/40 px-3 py-2 outline-none ring-primary focus:ring-2"
              />
            </div>

            <div className="flex justify-end gap-2 pt-2">
              <button
                type="button"
                className="rounded-lg px-4 py-2 font-medium text-muted hover:bg-bg"
                onClick={onCerrar}
              >
                Cancelar
              </button>
              <button
                type="submit"
                disabled={cargando}
                className="rounded-lg bg-primary px-5 py-2 font-medium text-white shadow hover:bg-primary/90 disabled:opacity-60"
              >
                {cargando ? "Guardando..." : "Guardar"}
              </button>
            </div>
          </form>
        ) : (
          <div className="space-y-4">
            <h2 className="text-xl font-bold text-success">¡Movimiento guardado!</h2>
            <p className="text-sm text-muted">Folio generado:</p>
            <FolioTag folio={creado.folio} />
            <div className="flex flex-wrap gap-2 pt-2">
              <button
                type="button"
                className="rounded-lg bg-primary px-4 py-2 font-medium text-white"
                onClick={() => navigate(`/comprobante/${creado.id}`)}
              >
                Ver comprobante
              </button>
              <button
                type="button"
                className="rounded-lg border border-muted/40 px-4 py-2 font-medium text-ink"
                onClick={onCerrar}
              >
                Volver al dashboard
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
