import { useEffect, useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { Calendar, Eye, FileText, Home, Menu, Settings, Users, X } from "lucide-react";
import logoUrl from "@assets/logo.png";
import { getConfiguracion } from "../services/api.js";

export default function Sidebar() {
  const [abierto, setAbierto] = useState(false);
  const [curso, setCurso] = useState(null);
  const location = useLocation();

  useEffect(() => {
    async function cargarCurso() {
      try {
        const config = await getConfiguracion();
        if (config.configurada && config.curso) {
          setCurso(config.curso);
        }
      } catch (err) {
        console.error("Error al cargar curso:", err);
      }
    }
    cargarCurso();
  }, []);

  const navItems = [
    { path: "/", label: "Inicio", icon: Home },
    { path: "/cuotas", label: "Cuotas", icon: Calendar },
    { path: "/alumnos", label: "Alumnos", icon: Users },
    { path: "/reportes", label: "Reportes", icon: FileText },
    { path: `/public/${curso?.codigo || ""}`, label: "Panel Público", icon: Eye },
  ];

  function activo(path) {
    return location.pathname === path;
  }

  return (
    <>
      {/* Hamburger button mobile - 48px mínimo para touch */}
      <button
        type="button"
        onClick={() => setAbierto(true)}
        className="fixed left-4 top-4 z-50 flex h-12 w-12 items-center justify-center rounded-lg bg-primary p-2 text-white shadow-lg md:hidden"
        aria-label="Abrir menú"
      >
        <Menu size={24} />
      </button>

      {/* Overlay mobile con transición suave */}
      <div
        className={`fixed inset-0 z-40 bg-black/50 transition-opacity duration-300 md:hidden ${
          abierto ? "opacity-100" : "pointer-events-none opacity-0"
        }`}
        onClick={() => setAbierto(false)}
      />

      {/* Sidebar */}
      <aside
        className={`fixed left-0 top-0 z-50 h-full w-64 border-r border-primary/15 bg-surface shadow-xl transition-transform duration-300 ease-out md:translate-x-0 ${
          abierto ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        <div className="flex h-full flex-col">
          {/* Header - altura mínima 64px en mobile */}
          <div className="flex h-16 items-center justify-between border-b border-muted/20 px-4">
            <div className="flex items-center gap-3">
              <img src={logoUrl} alt="CajaAlDía" className="h-10 w-auto" />
              <div className="flex flex-col">
                <span className="font-bold text-primary">CajaAlDía</span>
                {curso && (
                  <span className="text-xs text-muted line-clamp-1">{curso.nombre}</span>
                )}
              </div>
            </div>
            <button
              type="button"
              onClick={() => setAbierto(false)}
              className="flex h-10 w-10 items-center justify-center rounded-lg text-muted hover:bg-bg md:hidden"
              aria-label="Cerrar menú"
            >
              <X size={24} />
            </button>
          </div>

          {/* Navigation */}
          <nav className="flex-1 space-y-1 px-3 py-4">
            {navItems.map((item) => {
              const Icon = item.icon;
              return (
                <Link
                  key={item.path}
                  to={item.path}
                  onClick={() => setAbierto(false)}
                  className={`flex min-h-[48px] items-center gap-3 rounded-lg px-3 py-3 text-base font-medium transition-colors ${
                    activo(item.path)
                      ? "bg-primary/10 text-primary"
                      : "text-muted hover:bg-bg hover:text-ink"
                  }`}
                >
                  <Icon size={22} />
                  {item.label}
                </Link>
              );
            })}
          </nav>

          {/* Footer */}
          <div className="border-t border-muted/20 px-4 py-3">
            {curso && (
              <div className="space-y-1">
                <p className="text-xs font-medium text-muted">{curso.nombre}</p>
                <p className="text-xs text-muted">{curso.colegio}</p>
                <p className="text-xs text-muted">Tesorera: {curso.directiva_tesorera || "—"}</p>
              </div>
            )}
            <Link
              to="/configuracion"
              onClick={() => setAbierto(false)}
              className="mt-3 flex items-center gap-2 text-xs text-muted hover:text-ink transition-colors"
            >
              <Settings size={14} />
              Configuración
            </Link>
          </div>
        </div>
      </aside>
    </>
  );
}
