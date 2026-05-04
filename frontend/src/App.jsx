import { Route, Routes } from "react-router-dom";
import Alumnos from "./pages/Alumnos.jsx";
import Comprobante from "./pages/Comprobante.jsx";
import Cuotas from "./pages/Cuotas.jsx";
import Dashboard from "./pages/Dashboard.jsx";
import PanelPublico from "./pages/PanelPublico.jsx";
import Reportes from "./pages/Reportes.jsx";
import Sidebar from "./components/Sidebar.jsx";

export default function App() {
  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <main className="flex-1 md:ml-64">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/alumnos" element={<Alumnos />} />
          <Route path="/cuotas" element={<Cuotas />} />
          <Route path="/reportes" element={<Reportes />} />
          <Route path="/comprobante/:id" element={<Comprobante />} />
          <Route path="/public/:codigo_curso" element={<PanelPublico />} />
        </Routes>
      </main>
    </div>
  );
}
