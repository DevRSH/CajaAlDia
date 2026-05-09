"""Aplicación FastAPI CajaAlDía."""
import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.database import SessionLocal
from app.models import Alumno, Apoderado, ConfigCuota, Curso, Usuario
from app.routers import alumnos, auth, configuracion, cuotas, movimientos, public, reportes
from app.schemas import HealthResponse

logger = logging.getLogger(__name__)


def run_migrations() -> None:
    """Ejecuta migraciones Alembic pendientes (upgrade head)."""
    try:
        from alembic.config import Config
        from alembic import command

        alembic_cfg = Config(str(Path(__file__).resolve().parent.parent / "alembic.ini"))
        command.upgrade(alembic_cfg, "head")
        logger.info("Migraciones ejecutadas correctamente.")
    except Exception as e:
        logger.exception("Error ejecutando migraciones: %s", e)

# UUID fijo sincronizado con el seed del curso demo (solo usado si CURSO_DEMO=true)
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
            directiva_tesorera="Tesorera Demo",
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


def seed_cuota_especial_demo() -> None:
    """Crea una cuota especial de demo 'Kermés Demo' para todos los alumnos."""
    db = SessionLocal()
    try:
        # Verificar si ya existe cuota especial de demo
        existente = db.execute(
            select(ConfigCuota).where(
                ConfigCuota.curso_id == CURSO_DEMO_ID,
                ConfigCuota.tipo == "especial",
                ConfigCuota.nombre_especial == "Kermés Demo",
            )
        ).scalar_one_or_none()
        if existente:
            return

        # Verificar que exista el curso demo
        curso = db.execute(select(Curso).where(Curso.id == CURSO_DEMO_ID)).scalar_one_or_none()
        if curso is None:
            return

        # Crear cuota especial demo
        import uuid
        config = ConfigCuota(
            id=str(uuid.uuid4()),
            curso_id=CURSO_DEMO_ID,
            año=2026,
            mes=0,  # 0 para cuotas especiales
            monto=3000,
            descripcion="Cuota especial para la Kermés de demostración",
            tipo="especial",
            nombre_especial="Kermés Demo",
        )
        db.add(config)
        db.commit()
        logger.info("Seed cuota especial demo: 'Kermés Demo' de $3.000 creada exitosamente.")
    except IntegrityError:
        db.rollback()
        logger.warning("Seed cuota especial demo: ya existe, se omite.")
    except Exception as e:
        db.rollback()
        logger.exception("Seed cuota especial demo falló: %s", e)
    finally:
        db.close()


def seed_usuario_inicial() -> None:
    """Crea el usuario tesorera inicial si no existe ningún usuario (idempotente)."""
    from passlib.context import CryptContext
    db = SessionLocal()
    try:
        existente = db.execute(select(Usuario)).scalar_one_or_none()
        if existente is not None:
            return
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        usuario = Usuario(
            nombre="Tesorera",
            email="tesorera@cajaaldia.cl",
            password_hash=pwd_context.hash("CajaAlDia2026"),
            rol="tesorera",
            activo=True,
        )
        db.add(usuario)
        db.commit()
        logger.info("Usuario inicial creado: tesorera@cajaaldia.cl / CajaAlDia2026")
    except Exception as e:
        db.rollback()
        logger.exception("Seed usuario inicial falló: %s", e)
    finally:
        db.close()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Arranque: verificar si existe curso. Si no, la app muestra pantalla de configuración."""
    run_migrations()
    seed_usuario_inicial()
    # Solo ejecutar seeding si CURSO_DEMO=true (desarrollo local con datos demo)
    if os.getenv("CURSO_DEMO", "false").lower() == "true":
        seed_curso_demo()
        seed_alumnos_demo()
        seed_cuota_especial_demo()
    yield


app = FastAPI(title="CajaAlDía", lifespan=lifespan)

_frontend_url = os.getenv("FRONTEND_URL", "")
_origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:5174",
    "http://127.0.0.1:5174",
]
if _frontend_url:
    _origins.append(_frontend_url.rstrip("/"))
else:
    _origins.append("*")

app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
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


app.include_router(auth.router)
app.include_router(movimientos.router)
app.include_router(public.router)
app.include_router(alumnos.router)
app.include_router(cuotas.router)
app.include_router(reportes.router)
app.include_router(configuracion.router)
