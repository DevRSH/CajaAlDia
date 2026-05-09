import { useEffect, useState } from "react";
import { Navigate, Route, Routes, useLocation } from "react-router-dom";
import logoUrl from "@assets/logo.png";
import AccesoPublico from "./pages/AccesoPublico.jsx";
import Alumnos from "./pages/Alumnos.jsx";
import Comprobante from "./pages/Comprobante.jsx";
import Configuracion from "./pages/Configuracion.jsx";
import Cuotas from "./pages/Cuotas.jsx";
import Dashboard from "./pages/Dashboard.jsx";
import PanelPublico from "./pages/PanelPublico.jsx";
import Reportes from "./pages/Reportes.jsx";
import Sidebar from "./components/Sidebar.jsx";
import { getConfiguracion } from "./services/api.js";

function ConfiguracionChecker({ children }) {
  const [configurada, setConfigurada] = useState(null);
  const [cargando, setCargando] = useState(true);
  const location = useLocation();

  useEffect(() => {
    async function verificarConfiguracion() {
      try {
        const config = await getConfiguracion();
        console.log('Configuracion:', config);
        setConfigurada(config.configurada);
      } catch (err) {
        console.error("Error al verificar configuración:", err);
        setConfigurada(false);
      } finally {
        setCargando(false);
      }
    }
    verificarConfiguracion();
  }, [location.pathname]);

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

  if (!configurada && location.pathname !== "/configuracion") {
    return <Navigate to="/configuracion" replace />;
  }

  return children;
}

export default function App() {
  return (
    <Routes>
      <Route path="/public" element={<AccesoPublico />} />
      <Route path="/public/:codigo_curso" element={<PanelPublico />} />
      <Route
        path="/*"
        element={
          <ConfiguracionChecker>
            <Routes>
              <Route path="/configuracion" element={<Configuracion />} />
              <Route
                path="/*"
                element={
                  <div className="flex min-h-screen w-full max-w-full overflow-x-hidden">
                    <Sidebar />
                    <main className="flex-1 w-full md:ml-64">
                      <Routes>
                        <Route path="/" element={<Dashboard />} />
                        <Route path="/alumnos" element={<Alumnos />} />
                        <Route path="/cuotas" element={<Cuotas />} />
                        <Route path="/reportes" element={<Reportes />} />
                        <Route path="/comprobante/:id" element={<Comprobante />} />
                        <Route path="/configuracion" element={<Configuracion />} />
                      </Routes>
                    </main>
                  </div>
                }
              />
            </Routes>
          </ConfiguracionChecker>
        }
      />
    </Routes>
  );
}
