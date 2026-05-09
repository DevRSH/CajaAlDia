import axios from "axios";

/**
 * Si VITE_API_URL está vacío, se usa mismo origen y el proxy de Vite reenvía a FastAPI en desarrollo.
 */
const baseURL = import.meta.env.VITE_API_URL ?? "";

export const api = axios.create({
  baseURL,
  headers: { "Content-Type": "application/json" },
});

// Interceptor de request: agrega token JWT a todas las peticiones
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("cajaaldia_token");
  if (token) {
    config.headers["Authorization"] = `Bearer ${token}`;
  }
  return config;
});

// Interceptor de response: si el servidor retorna 401, limpiar token y redirigir a /login
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error?.response?.status === 401) {
      const rutaActual = window.location.pathname;
      if (rutaActual !== "/login") {
        localStorage.removeItem("cajaaldia_token");
        localStorage.removeItem("cajaaldia_usuario");
        window.location.href = "/login";
      }
    }
    return Promise.reject(error);
  }
);

/**
 * Extrae mensaje de error del backend `{ detail }` o texto genérico.
 */
export function getErrorMessage(error) {
  try {
    const d = error?.response?.data?.detail;
    if (typeof d === "string") return d;
    if (Array.isArray(d)) {
      const primer = d[0];
      if (primer?.msg) return String(primer.msg);
    }
    if (typeof error?.message === "string" && error.message) return error.message;
    return "Ocurrió un error al contactar el servidor.";
  } catch (_) {
    return "Ocurrió un error desconocido.";
  }
}

// Auth

export async function login(email, password) {
  const { data } = await api.post("/api/auth/login", { email, password });
  return data;
}

export async function logout() {
  try {
    await api.post("/api/auth/logout");
  } catch (_) {
    // Si falla el logout en el servidor igual limpiamos localmente
  } finally {
    localStorage.removeItem("cajaaldia_token");
    localStorage.removeItem("cajaaldia_usuario");
  }
}

export async function getMe() {
  const { data } = await api.get("/api/auth/me");
  return data;
}

export async function cambiarPassword(passwordActual, passwordNuevo) {
  const { data } = await api.post("/api/auth/cambiar-password", {
    password_actual: passwordActual,
    password_nuevo: passwordNuevo,
  });
  return data;
}

export async function actualizarPerfil(nombre, email) {
  const { data } = await api.put("/api/auth/perfil", { nombre, email });
  return data;
}

export async function fetchEstadoPublico(codigoCurso) {
  const { data } = await api.get(`/api/public/${encodeURIComponent(codigoCurso)}`);
  return data;
}

export async function fetchMovimientos(cursoId, page = 1) {
  const { data } = await api.get("/api/movimientos", {
    params: { curso_id: cursoId, page },
  });
  return data;
}

export async function crearMovimiento(payload) {
  const { data } = await api.post("/api/movimientos", payload);
  return data;
}

/** URL absoluta al HTML del comprobante (iframe o nueva pestaña). */
export function getComprobanteUrl(movimientoId) {
  const base = import.meta.env.VITE_API_URL ?? "";
  if (base) {
    return `${base.replace(/\/$/, "")}/api/movimientos/${movimientoId}/comprobante`;
  }
  return `/api/movimientos/${movimientoId}/comprobante`;
}

// Alumnos

export async function fetchAlumnos(cursoId, año = null) {
  const params = { curso_id: cursoId };
  if (año !== null) params.año = año;
  const { data } = await api.get("/api/alumnos", { params });
  return data;
}

export async function crearAlumno(payload) {
  const { data } = await api.post("/api/alumnos", payload);
  return data;
}

export async function actualizarAlumno(alumnoId, payload) {
  const { data } = await api.put(`/api/alumnos/${alumnoId}`, payload);
  return data;
}

export async function eliminarAlumno(alumnoId) {
  const { data } = await api.delete(`/api/alumnos/${alumnoId}`);
  return data;
}

// Cuotas

export async function fetchConfigCuotas(cursoId, anio) {
  const { data } = await api.get("/api/cuotas/config", {
    params: { curso_id: cursoId, anio },
  });
  return data;
}

export async function crearConfigCuota(payload) {
  const { data } = await api.post("/api/cuotas/config", payload);
  return data;
}

export async function crearCuotaEspecial(data) {
  // Wrapper para crear cuota especial con tipo="especial"
  return crearConfigCuota({
    ...data,
    tipo: "especial",
    mes: 0, // Cuotas especiales usan mes=0
  });
}

export async function fetchCuotasEspeciales(cursoId, anio) {
  const response = await fetchConfigCuotas(cursoId, anio);
  // La API retorna { cuotas_curso, cuotas_especiales }
  return response?.cuotas_especiales || [];
}

export async function fetchEstadoCuotaEspecial(configCuotaId) {
  const { data } = await api.get(`/api/cuotas/especial/${configCuotaId}/estado`);
  return data;
}

export async function registrarPagoCuota(payload) {
  const response = await api.post("/api/cuotas/pago", payload);
  return response.data;
}

export async function notificarPagoCuota(pagoId) {
  const response = await api.post(`/api/cuotas/pago/${pagoId}/notificar`);
  return response.data;
}

export async function fetchEstadoCuotas(cursoId, anio) {
  const { data } = await api.get("/api/cuotas/estado", {
    params: { curso_id: cursoId, anio },
  });
  return data;
}

export async function fetchDeudores(cursoId, anio) {
  const { data } = await api.get("/api/cuotas/deudores", {
    params: { curso_id: cursoId, anio },
  });
  return data;
}

export async function notificarDeuda(cursoId, anio, alumnoIds) {
  const { data } = await api.post("/api/cuotas/notificar-deuda", {
    curso_id: cursoId,
    año: anio,
    alumno_ids: alumnoIds,
  });
  return data;
}

// Configuración

export async function getConfiguracion() {
  const { data } = await api.get("/api/configuracion");
  return data;
}

export async function crearCurso(data) {
  const { data: response } = await api.post("/api/configuracion/curso", data);
  return response;
}

export async function actualizarCurso(data) {
  const { data: response } = await api.put("/api/configuracion/curso", data);
  return response;
}

export async function resetearCurso() {
  const { data } = await api.delete("/api/configuracion/curso");
  return data;
}

// Historial notificaciones

export async function fetchHistorialNotificaciones(cursoId, page = 1, size = 20, tipo = null) {
  const params = { curso_id: cursoId, page, size };
  if (tipo) params.tipo = tipo;
  const { data } = await api.get("/api/cuotas/historial-notificaciones", { params });
  return data;
}
