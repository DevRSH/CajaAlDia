"""Endpoints de autenticación: login, logout, me, cambiar-password."""
import logging
import os
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from threading import Lock

from fastapi import APIRouter, Depends, HTTPException, Request
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Usuario

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth", tags=["auth"])

# Configuración JWT
JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret-CHANGE-IN-PRODUCTION")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_HOURS = 8

# Hashing de contraseñas
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Rate limiting simple en memoria: ip -> lista de timestamps de fallos
_fallos: dict[str, list[datetime]] = defaultdict(list)
_fallos_lock = Lock()
MAX_FALLOS = 5
VENTANA_SEGUNDOS = 300  # 5 minutos

# Set de tokens invalidados (logout)
_tokens_invalidos: set[str] = set()


def verificar_rate_limit(ip: str) -> None:
    """Lanza 429 si la IP superó el máximo de intentos fallidos."""
    ahora = datetime.now(timezone.utc)
    with _fallos_lock:
        # Limpiar intentos fuera de la ventana
        _fallos[ip] = [t for t in _fallos[ip] if (ahora - t).total_seconds() < VENTANA_SEGUNDOS]
        if len(_fallos[ip]) >= MAX_FALLOS:
            raise HTTPException(
                status_code=429,
                detail="Demasiados intentos fallidos. Espera 5 minutos antes de volver a intentar.",
            )


def registrar_fallo(ip: str) -> None:
    """Registra un intento fallido para la IP."""
    with _fallos_lock:
        _fallos[ip].append(datetime.now(timezone.utc))


def limpiar_fallos(ip: str) -> None:
    """Limpia el registro de fallos tras login exitoso."""
    with _fallos_lock:
        _fallos[ip] = []


def crear_token(usuario_id: str, email: str, rol: str) -> str:
    """Genera un JWT con expiración de JWT_EXPIRE_HOURS horas."""
    expira = datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRE_HOURS)
    payload = {
        "sub": usuario_id,
        "email": email,
        "rol": rol,
        "exp": expira,
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decodificar_token(token: str) -> dict:
    """Decodifica y valida el JWT. Lanza HTTPException 401 si es inválido."""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Token inválido o expirado.")


def get_current_user(request: Request, db: Session = Depends(get_db)) -> Usuario:
    """Dependencia FastAPI: extrae y valida el token Bearer del header Authorization."""
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Se requiere autenticación.")
    token = auth.removeprefix("Bearer ").strip()
    if token in _tokens_invalidos:
        raise HTTPException(status_code=401, detail="La sesión ha sido cerrada.")
    payload = decodificar_token(token)
    usuario_id = payload.get("sub")
    if not usuario_id:
        raise HTTPException(status_code=401, detail="Token inválido.")
    usuario = db.execute(select(Usuario).where(Usuario.id == usuario_id)).scalar_one_or_none()
    if usuario is None or not usuario.activo:
        raise HTTPException(status_code=401, detail="Usuario no encontrado o inactivo.")
    return usuario


@router.post("/login")
def login(body: dict, request: Request, db: Session = Depends(get_db)):
    """Autentica con email y contraseña. Retorna JWT con duración de 8 horas."""
    email = body.get("email", "").strip().lower()
    password = body.get("password", "")
    if not email or not password:
        raise HTTPException(status_code=400, detail="Email y contraseña son obligatorios.")

    ip = request.client.host if request.client else "unknown"
    verificar_rate_limit(ip)

    usuario = db.execute(
        select(Usuario).where(Usuario.email == email, Usuario.activo.is_(True))
    ).scalar_one_or_none()

    if usuario is None or not pwd_context.verify(password, usuario.password_hash):
        registrar_fallo(ip)
        logger.warning("Intento de login fallido para email=%s ip=%s", email, ip)
        raise HTTPException(status_code=401, detail="Credenciales incorrectas.")

    limpiar_fallos(ip)
    token = crear_token(usuario.id, usuario.email, usuario.rol)
    logger.info("Login exitoso: email=%s rol=%s", usuario.email, usuario.rol)

    return {
        "token": token,
        "usuario": {
            "nombre": usuario.nombre,
            "email": usuario.email,
            "rol": usuario.rol,
        },
    }


@router.post("/logout")
def logout(request: Request, current_user: Usuario = Depends(get_current_user)):
    """Invalida el token actual."""
    auth = request.headers.get("Authorization", "")
    token = auth.removeprefix("Bearer ").strip()
    _tokens_invalidos.add(token)
    logger.info("Logout: email=%s", current_user.email)
    return {"mensaje": "Sesión cerrada correctamente."}


@router.get("/me")
def me(current_user: Usuario = Depends(get_current_user)):
    """Retorna los datos del usuario autenticado."""
    return {
        "id": current_user.id,
        "nombre": current_user.nombre,
        "email": current_user.email,
        "rol": current_user.rol,
    }


@router.put("/perfil")
def actualizar_perfil(
    body: dict,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """Actualiza nombre y/o email del usuario autenticado."""
    nombre = body.get("nombre", "").strip()
    email = body.get("email", "").strip().lower()

    if not nombre and not email:
        raise HTTPException(status_code=400, detail="Debes proporcionar al menos nombre o email.")

    if nombre:
        current_user.nombre = nombre
    if email:
        # Verificar que el email no esté en uso por otro usuario
        existente = db.execute(
            select(Usuario).where(Usuario.email == email, Usuario.id != current_user.id)
        ).scalar_one_or_none()
        if existente is not None:
            raise HTTPException(status_code=400, detail="Ese email ya está en uso por otro usuario.")
        current_user.email = email

    db.commit()
    logger.info("Perfil actualizado: id=%s", current_user.id)
    return {
        "nombre": current_user.nombre,
        "email": current_user.email,
        "rol": current_user.rol,
    }


@router.post("/cambiar-password")
def cambiar_password(
    body: dict,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """Cambia la contraseña del usuario autenticado."""
    password_actual = body.get("password_actual", "")
    password_nuevo = body.get("password_nuevo", "")

    if not password_actual or not password_nuevo:
        raise HTTPException(status_code=400, detail="Debes proporcionar la contraseña actual y la nueva.")

    if len(password_nuevo) < 8:
        raise HTTPException(status_code=400, detail="La nueva contraseña debe tener al menos 8 caracteres.")

    if not pwd_context.verify(password_actual, current_user.password_hash):
        raise HTTPException(status_code=401, detail="La contraseña actual es incorrecta.")

    current_user.password_hash = pwd_context.hash(password_nuevo)
    db.commit()
    logger.info("Contraseña actualizada: email=%s", current_user.email)
    return {"mensaje": "Contraseña actualizada correctamente."}
