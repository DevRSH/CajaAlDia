# Guía de Despliegue en Railway

Esta guía explica paso a paso cómo desplegar CajaAlDía en Railway.

## Preparativos

He preparado los siguientes archivos para facilitar el despliegue:

**Backend:**
- `backend/railway.json` - Configuración de Railway para FastAPI
- `backend/.env.example` - Ejemplo de variables de entorno
- `backend/requirements.txt` - Actualizado con `psycopg2-binary` para PostgreSQL
- `backend/app/database.py` - Configurado para usar PostgreSQL en producción
- `backend/app/main.py` - CORS configurado para Railway

**Frontend:**
- `frontend/railway.json` - Configuración de Railway para Vite/React

## Paso 1: Crear cuenta en Railway

1. Ve a [railway.app](https://railway.app)
2. Regístrate o inicia sesión
3. Conecta tu repositorio de GitHub (sube el código primero)

## Paso 2: Desplegar el Backend (FastAPI + PostgreSQL)

### 2.1 Crear proyecto Railway

1. En Railway, haz clic en "New Project"
2. Selecciona "Deploy from GitHub repo"
3. Selecciona tu repositorio
4. Configura el root directory: `backend`

### 2.2 Agregar Base de Datos PostgreSQL

1. En tu proyecto Railway, haz clic en "+ New Service"
2. Selecciona "Database"
3. Elige "PostgreSQL"
4. Railway creará una base de datos PostgreSQL automáticamente

### 2.3 Configurar Variables de Entorno

1. En el servicio del backend, ve a la pestaña "Variables"
2. Agrega la siguiente variable:
   - `FRONTEND_URL`: La URL de tu frontend (la obtendrás después de desplegar el frontend)

### 2.4 Ejecutar Migraciones

Railway necesita ejecutar las migraciones de Alembic al iniciar. Agrega esto en el comando de inicio:

1. En la pestaña "Settings" del servicio backend
2. En "Build Command", agrega:
   ```
   pip install -r requirements.txt && alembic upgrade head
   ```
3. En "Start Command", deja:
   ```
   uvicorn app.main:app --host 0.0.0.0 --port $PORT
   ```

### 2.5 Desplegar

1. Haz clic en "Deploy"
2. Railway construirá y desplegará el backend
3. Copia la URL del backend (terminará en `.railway.app`)

## Paso 3: Desplegar el Frontend (Vite/React)

### 3.1 Crear Servicio Frontend

1. En el mismo proyecto Railway, haz clic en "+ New Service"
2. Selecciona "Deploy from GitHub repo"
3. Selecciona el mismo repositorio
4. Configura el root directory: `frontend`

### 3.2 Configurar Variable de Entorno

1. En el servicio del frontend, ve a la pestaña "Variables"
2. Agrega la variable:
   - `VITE_API_URL`: La URL de tu backend (del Paso 2.5)

### 3.3 Desplegar

1. Haz clic en "Deploy"
2. Railway construirá y desplegará el frontend
3. Copia la URL del frontend

## Paso 4: Conectar Backend y Frontend

1. Vuelve al servicio del backend
2. En "Variables", actualiza `FRONTEND_URL` con la URL del frontend
3. Haz redeploy del backend

## Paso 5: Actualizar CORS en el Backend

El archivo `backend/app/main.py` ya está configurado para leer `FRONTEND_URL` desde las variables de entorno, así que no necesitas hacer cambios adicionales.

## Paso 6: Verificar el Despliegue

1. Abre la URL del frontend en tu navegador
2. Verifica que puedas ver la aplicación
3. Intenta crear un alumno, registrar un pago, etc.
4. Verifica que todo funcione correctamente

## Notas Importantes

- **Base de datos**: Railway usa PostgreSQL en producción, mientras que local usas SQLite. Las migraciones de Alembic se ejecutan automáticamente al desplegar.
- **CORS**: El backend está configurado para aceptar solicitudes desde la URL del frontend configurada en `FRONTEND_URL`.
- **Variables de entorno**: Asegúrate de configurar correctamente `VITE_API_URL` en el frontend y `FRONTEND_URL` en el backend.
- **Dominios personalizados**: Si quieres usar un dominio personalizado, configúralo en Railway y actualiza las variables de entorno correspondientes.

## Solución de Problemas

### Error de conexión a base de datos
- Verifica que la variable `DATABASE_URL` esté configurada correctamente (Railway la configura automáticamente)
- Asegúrate de que el servicio PostgreSQL esté ejecutándose

### Error de CORS
- Verifica que `FRONTEND_URL` esté configurada con la URL correcta del frontend
- Asegúrate de que no haya slashes extra al final de la URL

### Error de migraciones
- Verifica que el comando de build incluya `alembic upgrade head`
- Revisa los logs de Railway para ver si las migraciones se ejecutaron correctamente

## Comandos Útiles

### Desplegar cambios
```bash
git add .
git commit -m "mensaje"
git push
# Railway detectará los cambios y redeployará automáticamente
```

### Ver logs
- En Railway, ve a la pestaña "Deployments" de cada servicio
- Haz clic en un deployment para ver los logs

### Reiniciar servicios
- En Railway, ve a la pestaña "Settings" del servicio
- Haz clic en "Redeploy"
