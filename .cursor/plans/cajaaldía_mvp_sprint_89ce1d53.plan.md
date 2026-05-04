---
name: CajaAlDía MVP Sprint
overview: Bootstrap completo de backend FastAPI+SQLite+SQLAlchemy+Alembic y frontend Vite+React+Tailwind+Axios, con seed idempotente del curso demo, folio único atómico compatible con SQLite, vistas tesorera/pública y comprobante HTML imprimible.
todos:
  - id: backend-bootstrap
    content: Crear backend FastAPI (main/database/models/schemas), CORS/health/lifespan seed UUID fijo para 4BA-2026, routers movimientos+public+y comprobante HTML seguro
    status: pending
  - id: folio-atomico-sqlite
    content: Implementar tabla FolioSecuencia + transacción atómica + UNIQUE folio + reintentos; filtros anulado=false en agregados/listas
    status: pending
  - id: alembic-migracion
    content: Configurar Alembic + migración inicial de tablas/índices/constraints
    status: pending
  - id: frontend-bootstrap
    content: Crear Vite+React+Tailwind+Axios+react-router; variables CSS branding + Inter; layout páginas y componentes MontoDisplay/FolioTag/Toast
    status: pending
  - id: integracion-dev
    content: Alinear contrato API, manejo de errores en español, proxy/env VITE_API_URL, prueba manual end-to-end descrita por el usuario
    status: pending
isProject: false
---

# Plan: CajaAlDía (MVP Sprint)

## Contexto del repo (estado actual)
- [`backend/`](backend/) y [`frontend/`](frontend/) están **vacíos**; solo existe branding en [`assets/logo.png`](assets/logo.png).
- La implementación será **desde cero**, respetando el árbol de carpetas y endpoints que pediste.

## Decisiones técnicas (para cumplir reglas críticas con SQLite)
- **Folio único + “lock”**: SQLite no ofrece `SELECT FOR UPDATE` como Postgres. Para cumplir la intención (sin duplicados bajo concurrencia razonable), usar **transacción** + tabla contador `FolioSecuencia` con fila por `(curso_id, año)` y operación atómica:
  - `UPDATE folio_secuencia SET ultimo = ultimo + 1 WHERE ... RETURNING ultimo` (o equivalente vía SQLAlchemy `text()`), dentro de la misma transacción que inserta `Movimiento`.
  - **Constraint** `UNIQUE` en `movimientos.folio` + manejo de colisión con **reintento** (defensa en profundidad).
- **Formato de folio**: construir `CAD-{año}-{codigo_curso}-{secuencia:04d}` usando el `Curso.codigo` tal como está almacenado (p.ej. `4BA-2026`) y el `año` del movimiento (o del curso; quedará alineado con tu ejemplo `CAD-2026-4BA-0001`).
- **Anulación**: `Movimiento.anulado: bool` default `False`; **no** exponer delete; en listados/agregados del MVP considerar **solo movimientos no anulados** salvo que explícitamente quieras ver anulados (default: ocultos).
- **Errores**: `HTTPException` y/o handler global para que **siempre** sea coherente con FastAPI: `{"detail": "..." }` en español.
- **CORS**: `CORSMiddleware` con `http://localhost:5173` (y `http://127.0.0.1:5173` como extra seguro en dev).

## Backend: archivos y responsabilidades
Crear exactamente la estructura pedida:
- [`backend/app/main.py`](backend/app/main.py)
  - App FastAPI, include routers, CORS, `GET /health` → `{"status":"ok"}`.
  - **Lifespan**: seed idempotente del curso demo (ver abajo).
- [`backend/app/database.py`](backend/app/database.py)
  - Engine SQLite local (p.ej. `sqlite:///./cajaaldia.db`), `SessionLocal`, `Base`, helpers de sesión.
- [`backend/app/models.py`](backend/app/models.py)
  - Modelos SQLAlchemy 2.x: `Curso`, `Movimiento`, `FolioSecuencia` (contador).
  - Tipos: UUID strings en SQLite (CHAR(36)) o tipo nativo compatible; montos **int**; índices: `uniq_curso_codigo`, `uniq_movimiento_folio`, FKs con integridad referencial.
- [`backend/app/routers/movimientos.py`](backend/app/routers/movimientos.py)
  - `POST /api/movimientos` (crea movimiento + folio).
  - `GET /api/movimientos?curso_id=...&page=1` (20 por página; default `page=1`; orden `fecha DESC, created_at DESC`).
  - `GET /api/movimientos/{id}/comprobante` (**HTML imprimible** con CSS `@media print`; escapar HTML en descripción).
- [`backend/app/schemas.py`](backend/app/schemas.py) (archivo extra mínimo para orden)
  - Pydantic v2: payloads/respuestas, validaciones (tipo enum, `monto > 0`, `descripcion` max 200, fecha opcional default hoy en servidor si no viene).
- [`backend/app/routers/public.py`](backend/app/routers/public.py)
  - `GET /api/public/{codigo_curso}`
  - Respuesta conforme spec + `ultimos_movimientos`: **sin ids internos**, sin `created_at`; incluir solo campos “públicos” (fecha, tipo, monto formateado no es necesario en backend; el front formatea) — devolver-enteros como int.
  - Ignorar movimientos `anulado=true`.

### Seeds
- En `lifespan`/startup (después de asegurar tablas migradas): upsert/buscar por `codigo="4BA-2026"` y crear si no existe:
  - `nombre="4° Básico A"`, `colegio="Colegio Demo"`, `año=2026`
- Para que el frontend pueda “hardcodear” `curso_id` estable: **fijar UUID constante del curso seed** en código (único lugar) y reutilizarlo en el seed (create-if-missing por `codigo`, y si existe validar mismo id).

## Alembic
- [`backend/requirements.txt`](backend/requirements.txt): `fastapi`, `uvicorn[standard]`, `sqlalchemy`, `alembic`, `pydantic` v2.
- [`backend/alembic.ini`](backend/alembic.ini) + [`backend/alembic/env.py`](backend/alembic/env.py) apuntando a metadata de `models.py`.
- Migration inicial creando tablas + constraints + tabla `folio_secuencia`.

## Frontend: archivos y responsabilidades
Bootstrap Vite React JS (como especificaste: `main.jsx`/`App.jsx`):
- [`frontend/package.json`](frontend/package.json): React 18, Vite, Tailwind v3, Axios.
- **`react-router-dom`**: rutas `/` dashboard, `/comprobante/:id`, `/public/:codigo_curso` (routing no es librería de UI; alternativa sin router aumenta código y bugs).
- [`frontend/vite.config.js`](frontend/vite.config.js): `server.port=5173` (default) y **proxy** opcional `/api` → `http://127.0.0.1:8000` para evitar preflights molestos en dev (opcional pero recomendado).
- Tailwind [`frontend/tailwind.config.js`](frontend/tailwind.config.js) + [`frontend/postcss.config.js`](frontend/postcss.config.js).
- Branding/global:
  - [`frontend/index.html`](frontend/index.html): `<link>` a Google Fonts **Inter**.
  - [`frontend/src/index.css`](frontend/src/index.css): `@tailwind` + variables CSS EXACTAS + estilos base (fondo `#E3F2FD`, texto, etc.).
- [`frontend/src/services/api.js`](frontend/src/services/api.js)
  - `axios.create({ baseURL: import.meta.env.VITE_API_URL || '' })`.
  - Funciones: `health`, `crearMovimiento`, `listarMovimientos`, `getPublicEstado`, `getComprobanteUrl`/`fetchComprobanteHTML`.
  - Captura de errores: leer `err.response?.data?.detail` (string o lista) → mensaje español estable.
- Componentes solicitados:
  - [`frontend/src/components/MontoDisplay.jsx`](frontend/src/components/MontoDisplay.jsx): siempre `Intl.NumberFormat('es-CL',{style:'currency',currency:'CLP'})` + prefijos/signos por `tipo`.
  - [`frontend/src/components/FolioTag.jsx`](frontend/src/components/FolioTag.jsx): monospace + copiar clipboard + feedback 2s.
  - [`frontend/src/components/Toast.jsx`](frontend/src/components/Toast.jsx): stack/simple state.
- Páginas solicitadas:
  - [`frontend/src/pages/Dashboard.jsx`](frontend/src/pages/Dashboard.jsx): logo [`assets/logo.png`](assets/logo.png) (import desde `../../../../assets/logo.png` o copiar symlink—se elegirá import relativo válido para Vite), tarjetas de saldos, tabla últimos movimientos, CTA principal.
    - Obtener KPIs **sin endpoint extra**: combinando `GET /api/movimientos?curso_id=...` (página 1) + opcionalmente `GET /api/public/{codigo}` para saldo consolidado rápido, o calcular desde lista si paginas>1… **Para saldo correcto MVP**: preferir **`GET /api/public/{codigo}` con `saldo`** para KPIs grandes y paralelamente tabla con `movimientos` paginados.
    - Mantener `codigo_curso="4BA-2026"` y `CURSO_UUID` constante hardcode igual al backend seed.
  - [`frontend/src/pages/NuevoMovimiento.jsx`](frontend/src/pages/NuevoMovimiento.jsx): implementado como **modal controlado desde Dashboard** (per spec), inputs y validaciones (enteros CLP).
  - [`frontend/src/pages/Comprobante.jsx`](frontend/src/pages/Comprobante.jsx): `iframe srcDoc` **o** `iframe src` al endpoint `/api/movimientos/{id}/comprobante`; botón imprimir `window.print()`.
  - [`frontend/src/pages/PanelPublico.jsx`](frontend/src/pages/PanelPublico.jsx): ruta pública, layout simple, últimos 10, texto pie.

## Flujo de verificación (el “acceptance” del sprint)
- Arrancar backend+frontend con tus comandos.
- En `5173`: dashboard saldo 0.
- Crear ingreso 25000 con descripción dada → folio `CAD-2026-4BA-0001` (ajustar si el parser de código requiere normalización; se validará contra el seed).
- Abrir comprobante e imprimir.
- Abrir `/public/4BA-2026` y ver el movimiento.

## Comandos finales (los que te dejaré documentados)
- Backend:
  - `cd backend && python -m venv .venv && source .venv/bin/activate`
  - `pip install -r requirements.txt`
  - `alembic upgrade head`
  - `uvicorn app.main:app --reload`
- Frontend:
  - `cd frontend && npm install`
  - `npm run dev`
- Opcional recomendado: `VITE_API_URL=http://127.0.0.1:8000 npm run dev` si no usamos proxy.

