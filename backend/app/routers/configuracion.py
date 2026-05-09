"""Endpoints de configuración inicial del curso."""
import os
import uuid
from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import delete, select
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.database import get_db
from app.models import (
    Alumno,
    Apoderado,
    ConfigCuota,
    Curso,
    FolioSecuencia,
    Movimiento,
    NotificacionEmail,
    PagoCuota,
    Usuario,
)
from app.routers.auth import get_current_user
from app.schemas import ConfiguracionResponse, CursoActualizar, CursoCrear, CursoResponse

router = APIRouter(prefix="/api", tags=["configuracion"])


@router.get("/configuracion", response_model=ConfiguracionResponse)
def obtener_configuracion(db: Session = Depends(get_db)):
    """Retorna el estado de configuración de la aplicación."""
    try:
        result = db.execute(select(Curso).limit(1))
        curso = result.scalars().first()
        if curso is None:
            return ConfiguracionResponse(configurada=False, curso=None)
        return ConfiguracionResponse(configurada=True, curso=curso)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener configuración: {e!s}") from e


@router.post("/configuracion/curso", response_model=CursoResponse)
def crear_curso_configuracion(
    body: CursoCrear,
    db: Session = Depends(get_db),
    _usuario: Usuario = Depends(get_current_user),
):
    """Crea el curso inicial. Solo permitido si no existe ningún curso."""
    try:
        # Verificar si ya existe un curso
        result = db.execute(select(Curso).limit(1))
        existente = result.scalars().first()
        if existente is not None:
            raise HTTPException(
                status_code=400,
                detail="El curso ya está configurado. Use el endpoint de actualización.",
            )

        curso = Curso(
            id=str(uuid.uuid4()),
            codigo=body.codigo.strip(),
            nombre=body.nombre.strip(),
            colegio=body.colegio.strip(),
            año=body.año,
            directiva_tesorera=body.directiva.tesorera.strip(),
            directiva_tesorera_email=body.directiva.tesorera_email.strip() if body.directiva.tesorera_email else None,
            directiva_presidenta=body.directiva.presidenta.strip() if body.directiva.presidenta else None,
            directiva_presidenta_email=body.directiva.presidenta_email.strip() if body.directiva.presidenta_email else None,
            directiva_secretaria=body.directiva.secretaria.strip() if body.directiva.secretaria else None,
            directiva_secretaria_email=body.directiva.secretaria_email.strip() if body.directiva.secretaria_email else None,
        )
        db.add(curso)
        db.commit()
        db.refresh(curso)
        return curso
    except HTTPException:
        raise
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="El código del curso ya existe.") from None
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al crear el curso: {e!s}") from e


@router.put("/configuracion/curso", response_model=CursoResponse)
def actualizar_curso_configuracion(
    body: CursoActualizar,
    db: Session = Depends(get_db),
    _usuario: Usuario = Depends(get_current_user),
):
    """Actualiza los datos del curso existente."""
    try:
        result = db.execute(select(Curso).limit(1))
        curso = result.scalars().first()
        if curso is None:
            raise HTTPException(status_code=404, detail="No existe un curso configurado.")

        # Actualizar campos si se proporcionan
        if body.codigo is not None:
            curso.codigo = body.codigo.strip()
        if body.nombre is not None:
            curso.nombre = body.nombre.strip()
        if body.colegio is not None:
            curso.colegio = body.colegio.strip()
        if body.año is not None:
            curso.año = body.año
        if body.directiva is not None:
            curso.directiva_tesorera = body.directiva.tesorera.strip()
            curso.directiva_tesorera_email = body.directiva.tesorera_email.strip() if body.directiva.tesorera_email else None
            curso.directiva_presidenta = body.directiva.presidenta.strip() if body.directiva.presidenta else None
            curso.directiva_presidenta_email = body.directiva.presidenta_email.strip() if body.directiva.presidenta_email else None
            curso.directiva_secretaria = body.directiva.secretaria.strip() if body.directiva.secretaria else None
            curso.directiva_secretaria_email = body.directiva.secretaria_email.strip() if body.directiva.secretaria_email else None

        db.commit()
        db.refresh(curso)
        return curso
    except HTTPException:
        raise
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="El código del curso ya existe.") from None
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al actualizar el curso: {e!s}") from e


@router.delete("/configuracion/curso")
def resetear_curso_configuracion(
    db: Session = Depends(get_db),
    _usuario: Usuario = Depends(get_current_user),
):
    """Elimina el curso y todos sus datos asociados. Solo permitido si ALLOW_RESET=true."""
    if os.getenv("ALLOW_RESET", "false").lower() != "true":
        raise HTTPException(status_code=403, detail="Reset no permitido en este entorno.")

    try:
        result = db.execute(select(Curso).limit(1))
        curso = result.scalars().first()
        if curso is None:
            raise HTTPException(status_code=404, detail="No existe un curso configurado.")

        # Eliminar en orden respetando foreign keys
        # 1. notificaciones_email (depende de pagos_cuotas)
        db.execute(delete(NotificacionEmail))
        # 2. pagos_cuotas (depende de movimientos y config_cuotas)
        db.execute(delete(PagoCuota))
        # 3. config_cuotas (depende de cursos)
        db.execute(delete(ConfigCuota))
        # 4. movimientos (depende de cursos)
        db.execute(delete(Movimiento))
        # 5. folio_secuencia (depende de cursos)
        db.execute(delete(FolioSecuencia))
        # 6. apoderados (depende de alumnos)
        db.execute(delete(Apoderado))
        # 7. alumnos (depende de cursos)
        db.execute(delete(Alumno))
        # 8. curso
        db.execute(delete(Curso).where(Curso.id == curso.id))

        db.commit()
        return {"reseteado": True}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al resetear el curso: {e!s}") from e
