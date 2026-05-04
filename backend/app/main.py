"""Aplicación FastAPI CajaAlDía."""
import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.database import SessionLocal
from app.models import Alumno, Apoderado, Curso
from app.routers import alumnos, cuotas, movimientos, public, reportes
from app.schemas import HealthResponse

logger = logging.getLogger(__name__)

# UUID fijo sincronizado con el seed del curso demo (frontend puede hardcodear el mismo).
CURSO_DEMO_ID = "c0ffee00-0000-4000-a001-000000000001"


def seed_curso_demo() -> None:
    """Crea el curso de demostración si no existe (idempotente)."""
    db = SessionLocal()
    try:
        existente_por_codigo = db.execute(
            select(Curso).where(Curso.codigo == "4BA-2026")
        ).scalar_one_or_none()
        if existente_por_codigo is not None:
            return
        existe_id = db.execute(select(Curso).where(Curso.id == CURSO_DEMO_ID)).scalar_one_or_none()
        if existe_id is not None:
            return
        curso = Curso(
            id=CURSO_DEMO_ID,
            codigo="4BA-2026",
            nombre="4° Básico A",
            colegio="Colegio Demo",
            año=2026,
        )
        db.add(curso)
        db.commit()
    except IntegrityError:
        db.rollback()
        logger.warning("Seed curso demo: código o id ya existente, se omite.")
    except Exception as e:
        db.rollback()
        logger.exception("Seed curso demo falló: %s", e)
    finally:
        db.close()


def seed_alumnos_demo() -> None:
    """Crea 3 alumnos demo con sus apoderados para el curso 4BA-2026 (idempotente)."""
    db = SessionLocal()
    try:
        curso = db.execute(select(Curso).where(Curso.id == CURSO_DEMO_ID)).scalar_one_or_none()
        if curso is None:
            return

        # Verificar si ya existen alumnos
        existentes = db.execute(
            select(Alumno).where(Alumno.curso_id == CURSO_DEMO_ID)
        ).scalar_one_or_none()
        if existentes is not None:
            return

        # Datos de los 3 alumnos demo
        alumnos_data = [
            {
                "nombre": "María José",
                "apellido_paterno": "García",
                "apellido_materno": "González",
                "rut": "21.456.789-3",
                "apoderado": {
                    "nombre": "Ana María",
                    "apellido_paterno": "González",
                    "apellido_materno": "Torres",
                    "email": "ana.gonzalez@gmail.com",
                    "telefono": "+56912345678",
                },
            },
            {
                "nombre": "Juan Ignacio",
                "apellido_paterno": "Pérez",
                "apellido_materno": "Silva",
                "rut": "21.789.012-5",
                "apoderado": {
                    "nombre": "Carlos Eduardo",
                    "apellido_paterno": "Silva",
                    "apellido_materno": "Rojas",
                    "email": "carlos.silva@gmail.com",
                    "telefono": "+56987654321",
                },
            },
            {
                "nombre": "Sofía Valentina",
                "apellido_paterno": "Morales",
                "apellido_materno": "Castro",
                "rut": "21.234.567-8",
                "apoderado": {
                    "nombre": "Patricia",
                    "apellido_paterno": "Castro",
                    "apellido_materno": "Muñoz",
                    "email": "patricia.castro@gmail.com",
                    "telefono": "+56956789012",
                },
            },
        ]

        for data in alumnos_data:
            import uuid
            alumno = Alumno(
                id=str(uuid.uuid4()),
                curso_id=CURSO_DEMO_ID,
                nombre=data["nombre"],
                apellido_paterno=data["apellido_paterno"],
                apellido_materno=data["apellido_materno"],
                rut=data["rut"],
                activo=True,
            )
            db.add(alumno)
            db.flush()

            apod = data["apoderado"]
            apoderado = Apoderado(
                id=str(uuid.uuid4()),
                alumno_id=alumno.id,
                nombre=apod["nombre"],
                apellido_paterno=apod["apellido_paterno"],
                email=apod["email"],
                telefono=apod["telefono"],
            )
            db.add(apoderado)

        db.commit()
        logger.info("Seed alumnos demo: 3 alumnos creados exitosamente.")
    except IntegrityError:
        db.rollback()
        logger.warning("Seed alumnos demo: datos ya existentes, se omite.")
    except Exception as e:
        db.rollback()
        logger.exception("Seed alumnos demo falló: %s", e)
    finally:
        db.close()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Arranque: datos iniciales (solo en desarrollo)."""
    # Solo ejecutar seeding en desarrollo si SEED_DEMO_DATA=true
    if os.getenv("SEED_DEMO_DATA", "false").lower() == "true":
        seed_curso_demo()
        seed_alumnos_demo()
    yield


app = FastAPI(title="CajaAlDía", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        # Vite usa el siguiente puerto libre si 5173 está ocupado
        "http://localhost:5174",
        "http://127.0.0.1:5174",
        # Railway frontend (se configurará dinámicamente)
        os.getenv("FRONTEND_URL", "*"),
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(RequestValidationError)
async def validation_es(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Unifica errores de validación con mensaje claro."""
    errores = exc.errors()
    if errores:
        primero = errores[0]
        msg = primero.get("msg", "Datos inválidos.")
        if msg == "Field required":
            loc = ".".join(str(x) for x in primero.get("loc", []) if x != "body")
            msg = f"Falta el campo obligatorio: {loc}." if loc else "Faltan datos obligatorios."
    else:
        msg = "Datos inválidos."
    return JSONResponse(status_code=422, content={"detail": msg})


@app.exception_handler(Exception)
async def error_generico(request: Request, exc: Exception) -> JSONResponse:
    """Errores no controlados (no debe tragar HTTPException)."""
    if isinstance(exc, HTTPException):
        detail = exc.detail
        if not isinstance(detail, str):
            detail = str(detail)
        return JSONResponse(status_code=exc.status_code, content={"detail": detail})

    logger.exception("Error no controlado: %s", exc)
    return JSONResponse(
        status_code=500,
        content={"detail": "Ocurrió un error interno. Intente más tarde."},
    )


@app.get("/health", response_model=HealthResponse)
def health() -> dict:
    return {"status": "ok"}


app.include_router(movimientos.router)
app.include_router(public.router)
app.include_router(alumnos.router)
app.include_router(cuotas.router)
app.include_router(reportes.router)
