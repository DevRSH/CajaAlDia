import { useState } from "react";
import { useNavigate } from "react-router-dom";
import logoUrl from "@assets/logo.png";

export default function AccesoPublico() {
  const navigate = useNavigate();
  const [codigo, setCodigo] = useState("");
  const [error, setError] = useState("");

  function handleSubmit(e) {
    e.preventDefault();
    if (!codigo.trim()) {
      setError("Por favor ingresa el código del curso");
      return;
    }
    navigate(`/public/${codigo.trim()}`);
  }

  function handleKeyDown(e) {
    if (e.key === "Enter") {
      handleSubmit(e);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-[#E3F2FD]">
      <div className="w-full max-w-md rounded-2xl bg-white p-8 shadow-lg">
        <div className="mb-8 text-center">
          <img src={logoUrl} alt="CajaAlDía" className="mx-auto h-16 w-auto" />
        </div>
        
        <h1 className="mb-6 text-center text-2xl font-bold text-primary">
          Consulta el estado de la caja del curso
        </h1>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label htmlFor="codigo" className="mb-2 block text-sm font-medium text-muted">
              Ingresa el código del curso
            </label>
            <input
              id="codigo"
              type="text"
              value={codigo}
              onChange={(e) => {
                setCodigo(e.target.value);
                setError("");
              }}
              onKeyDown={handleKeyDown}
              placeholder="Ej: 4BA-2026"
              className="w-full rounded-lg border border-muted/40 px-4 py-3 outline-none ring-primary focus:ring-2"
              autoFocus
            />
            <p className="mt-2 text-xs text-muted">
              El código te lo entrega la directiva del curso
            </p>
            {error && (
              <p className="mt-2 text-sm text-danger">{error}</p>
            )}
          </div>

          <button
            type="submit"
            className="w-full rounded-lg bg-primary px-4 py-3 font-semibold text-white transition-colors hover:bg-primary/90"
          >
            Consultar
          </button>
        </form>
      </div>
    </div>
  );
}
