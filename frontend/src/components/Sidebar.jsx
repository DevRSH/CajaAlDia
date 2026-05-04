import { useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { Calendar, Eye, FileText, Home, Menu, Users, X } from "lucide-react";
import logoUrl from "@assets/logo.png";

export default function Sidebar() {
  const [abierto, setAbierto] = useState(false);
  const location = useLocation();

  const navItems = [
    { path: "/", label: "Inicio", icon: Home },
    { path: "/cuotas", label: "Cuotas", icon: Calendar },
    { path: "/alumnos", label: "Alumnos", icon: Users },
    { path: "/reportes", label: "Reportes", icon: FileText },
    { path: "/public/4BA-2026", label: "Panel Público", icon: Eye },
  ];

  function activo(path) {
    return location.pathname === path;
  }

  return (
    <>
      {/* Hamburger button mobile */}
      <button
        type="button"
        onClick={() => setAbierto(true)}
        className="fixed left-4 top-4 z-50 rounded-lg bg-primary p-2 text-white shadow-lg md:hidden"
      >
        <Menu size={24} />
      </button>

      {/* Overlay mobile */}
      {abierto && (
        <div
          className="fixed inset-0 z-40 bg-black/50 md:hidden"
          onClick={() => setAbierto(false)}
        />
      )}

      {/* Sidebar */}
      <aside
        className={`fixed left-0 top-0 z-40 h-full w-64 border-r border-primary/15 bg-surface shadow-lg transition-transform duration-300 md:translate-x-0 ${
          abierto ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        <div className="flex h-full flex-col">
          {/* Header */}
          <div className="flex items-center justify-between border-b border-muted/20 px-4 py-4">
            <div className="flex items-center gap-3">
              <img src={logoUrl} alt="CajaAlDía" className="h-10 w-auto" />
              <span className="font-bold text-primary">CajaAlDía</span>
            </div>
            <button
              type="button"
              onClick={() => setAbierto(false)}
              className="rounded-lg p-1 text-muted hover:bg-bg md:hidden"
            >
              <X size={20} />
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
                  className={`flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors ${
                    activo(item.path)
                      ? "bg-primary/10 text-primary"
                      : "text-muted hover:bg-bg hover:text-ink"
                  }`}
                >
                  <Icon size={20} />
                  {item.label}
                </Link>
              );
            })}
          </nav>

          {/* Footer */}
          <div className="border-t border-muted/20 px-4 py-3">
            <p className="text-xs text-muted">Sprint 2 - Gestión de Cuotas</p>
          </div>
        </div>
      </aside>
    </>
  );
}
