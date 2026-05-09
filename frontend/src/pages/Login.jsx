import { useState } from "react";
import { useNavigate } from "react-router-dom";
import logoUrl from "@assets/logo.png";
import { getErrorMessage, login } from "../services/api.js";

export default function Login() {
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [cargando, setCargando] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setCargando(true);
    try {
      const datos = await login(email.trim(), password);
      localStorage.setItem("cajaaldia_token", datos.token);
      localStorage.setItem("cajaaldia_usuario", JSON.stringify(datos.usuario));
      navigate("/", { replace: true });
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setCargando(false);
    }
  }

  return (
    <div className="flex min-h-screen w-full items-center justify-center bg-[#E3F2FD] px-4 py-12">
      <div className="w-full max-w-md rounded-2xl bg-white p-8 shadow-xl">
        <div className="mb-8 text-center">
          <img src={logoUrl} alt="CajaAlDía" className="mx-auto h-16 w-auto" />
          <h1 className="mt-4 text-2xl font-bold text-primary">Bienvenida a CajaAlDía</h1>
          <p className="mt-1 text-sm text-muted">Ingresa con tu cuenta para continuar</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-5">
          <div>
            <label htmlFor="email" className="mb-1 block text-sm font-medium text-ink">
              Correo electrónico
            </label>
            <input
              type="email"
              id="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              autoComplete="email"
              className="w-full rounded-lg border border-muted/30 px-4 py-3 text-base focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20"
              placeholder="tesorera@cajaaldia.cl"
            />
          </div>

          <div>
            <label htmlFor="password" className="mb-1 block text-sm font-medium text-ink">
              Contraseña
            </label>
            <input
              type="password"
              id="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              autoComplete="current-password"
              className="w-full rounded-lg border border-muted/30 px-4 py-3 text-base focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20"
              placeholder="••••••••"
            />
          </div>

          {error && (
            <div className="rounded-lg border border-danger/30 bg-red-50 px-4 py-3 text-sm text-danger">
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={cargando}
            className="h-12 w-full rounded-xl bg-primary text-base font-semibold text-white shadow-md hover:bg-primary/90 disabled:opacity-50"
          >
            {cargando ? "Ingresando..." : "Ingresar"}
          </button>
        </form>

        <p className="mt-6 text-center text-xs text-muted">
          CajaAlDía · La plata del curso, siempre a la vista.
        </p>
      </div>
    </div>
  );
}
