# CajaAlDía

Sistema de gestión de caja chica para colegios, diseñado para administrar pagos de cuotas mensuales, movimientos financieros y comunicación con apoderados.

## 🎯 A quién va dirigido

CajaAlDía está diseñado para:

- **Profesores de curso** que necesitan administrar los pagos de cuotas de sus alumnos
- **Tesoreros de colegios** que requieren un sistema simple y eficiente para gestionar cobranzas
- **Administradores escolares** que buscan controlar los movimientos financieros de manera organizada
- **Pequeños establecimientos educativos** que necesitan una solución accesible sin complejidades

## ✨ Características Principales

### Gestión de Alumnos
- Registro completo de alumnos con información personal y de apoderados
- Edición y eliminación de alumnos (con soft delete para mantener historial)
- Visualización de estado de pagos por alumno
- Gestión de apoderados con contacto email y teléfono

### Gestión de Cuotas
- Configuración de cuotas mensuales con montos personalizables
- Matriz visual de estado de pagos por alumno y mes
- Registro de pagos con generación automática de comprobantes
- Notificaciones de pago a apoderados (simulado)
- Sistema de notificación de deuda a apoderados con morosidad

### Movimientos Financieros
- Registro de ingresos y egresos
- Historial completo de movimientos
- Visualización de saldo disponible en tiempo real
- Generación de folios únicos para cada transacción

### Panel Público
- Vista pública para consultar estado de cuenta por código de curso
- Acceso para apoderados sin necesidad de autenticación
- Visualización de saldo y últimos movimientos

### Reportes
- Reportes de ingresos y egresos
- Análisis de estado de pagos por curso
- Exportación de información (en desarrollo)

## 🚀 Tecnologías

### Backend
- **FastAPI** - Framework web moderno y rápido para Python
- **SQLAlchemy** - ORM para gestión de base de datos
- **Alembic** - Herramienta de migración de base de datos
- **SQLite** - Base de datos ligera para desarrollo (PostgreSQL en producción)

### Frontend
- **React** - Biblioteca JavaScript para interfaces de usuario
- **Vite** - Herramienta de build rápida y moderna
- **TailwindCSS** - Framework CSS para diseño responsivo
- **Lucide React** - Biblioteca de iconos
- **Axios** - Cliente HTTP para comunicación con API

## 📦 Instalación

### Requisitos Previos
- Python 3.12+
- Node.js 18+
- Git

### Instalación del Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # En Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Ejecutar migraciones de base de datos:
```bash
alembic upgrade head
```

Iniciar servidor de desarrollo:
```bash
uvicorn app.main:app --reload
```

El backend estará disponible en `http://localhost:8000`

### Instalación del Frontend

```bash
cd frontend
npm install
npm run dev
```

El frontend estará disponible en `http://localhost:5173`

## 📖 Uso

### Primeros Pasos

1. **Crear un curso**: Al iniciar la aplicación, se crea automáticamente un curso demo (4° Básico A) con 3 alumnos de ejemplo.
2. **Configurar cuotas**: Ve a la sección "Cuotas" y configura las cuotas mensuales con sus respectivos montos.
3. **Registrar pagos**: En la matriz de pagos, haz clic en los meses pendientes para registrar pagos.
4. **Ver movimientos**: En el Dashboard, puedes ver el saldo disponible y el historial de movimientos.
5. **Generar reportes**: Ve a la sección "Reportes" para ver ingresos, egresos y análisis.

### Gestión de Alumnos

1. Ve a la sección "Alumnos"
2. Haz clic en "Nuevo alumno" para registrar un nuevo estudiante
3. Completa los datos del alumno y del apoderado
4. Usa los botones de Editar (lápiz) y Eliminar (papelera) para gestionar alumnos existentes

### Notificación de Deuda

1. Ve a la sección "Cuotas"
2. Desplázate hacia abajo para ver la sección "Deudores"
3. Selecciona los alumnos a notificar con los checkboxes
4. Haz clic en "Notificar seleccionados" o "Notificar a todos los deudores"
5. El sistema generará notificaciones simuladas para los apoderados

## 🔧 Configuración

### Variables de Entorno (Opcional)

En desarrollo, el proyecto usa valores por defecto. Para producción, puedes configurar:

**Backend (.env):**
```
FRONTEND_URL=https://tu-frontend.com
DATABASE_URL=postgresql://usuario:password@host:puerto/database
```

**Frontend (.env):**
```
VITE_API_URL=https://tu-backend.com
```

## 🌐 Despliegue

El proyecto está preparado para desplegarse en Railway. Consulta la guía completa en [DESPLEGUE_RAILWAY.md](DESPLEGUE_RAILWAY.md) para instrucciones paso a paso.

### Despliegue en Railway

1. Conecta tu repositorio de GitHub a Railway
2. Crea un servicio para el backend desde el directorio `backend/`
3. Agrega una base de datos PostgreSQL
4. Crea un servicio para el frontend desde el directorio `frontend/`
5. Configura las variables de entorno
6. Despliega ambos servicios

## 📸 Capturas de Pantalla

*(Agrega capturas de pantalla de tu aplicación aquí)*

## 🤝 Contribución

Las contribuciones son bienvenidas. Si deseas contribuir:

1. Haz un fork del proyecto
2. Crea una rama para tu feature (`git checkout -b feature/nueva-caracteristica`)
3. Commit tus cambios (`git commit -m 'Agrega nueva característica'`)
4. Push a la rama (`git push origin feature/nueva-caracteristica`)
5. Abre un Pull Request

## 📄 Licencia

Este proyecto es de código abierto y está disponible bajo la Licencia MIT.

## 📞 Soporte

Si encuentras algún problema o tienes sugerencias, por favor abre un issue en el repositorio de GitHub.

## 🔮 Roadmap

- [ ] Autenticación de usuarios
- [ ] Múltiples cursos por usuario
- [ ] Exportación de reportes a PDF/Excel
- [ ] Integración con pasarelas de pago
- [ ] Móvil (PWA)
- [ ] Notificaciones por email reales
- [ ] Sistema de recordatorios automáticos

---

Desarrollado con ❤️ para simplificar la gestión financiera educativa.
