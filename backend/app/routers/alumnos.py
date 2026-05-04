"""Endpoints de gestión de alumnos y apoderados."""
import uuid
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Alumno, Apoderado, ConfigCuota, Curso, PagoCuota
from app.schemas import (
    AlumnoActualizar,
    AlumnoCrear,
    AlumnoResponse,
    ApoderadoCrear,
    ApoderadoResponse,
    EstadoCuota,
)

router = APIRouter(prefix="/api", tags=["alumnos"])


def _calcular_estado_cuota(alumno: Alumno, db: Session, año: int) -> EstadoCuota:
    """Calcula el estado de cuotas de un alumno para un año dado."""
    configs = db.execute(
        select(ConfigCuota).where(
            ConfigCuota.curso_id == alumno.curso_id,
            ConfigCuota.año == año,
        )
    ).scalars().all()

    if not configs:
        return EstadoCuota(estado="sin_cuotas", meses_pendientes=0, monto_pendiente=0)

    pagos = db.execute(
        select(PagoCuota).where(
            PagoCuota.alumno_id == alumno.id,
        )
    ).scalars().all()

    config_ids_pagados = {p.config_cuota_id for p in pagos}
    meses_pendientes = 0
    monto_pendiente = 0

    for config in configs:
        if config.id not in config_ids_pagados:
            meses_pendientes += 1
            monto_pendiente += config.monto

    if meses_pendientes == 0:
        return EstadoCuota(estado="al_dia", meses_pendientes=0, monto_pendiente=0)
    else:
        return EstadoCuota(
            estado="debe_meses",
            meses_pendientes=meses_pendientes,
            monto_pendiente=monto_pendiente,
        )


@router.post("/alumnos", response_model=AlumnoResponse)
def crear_alumno(
    body: AlumnoCrear,
    db: Session = Depends(get_db),
):
    """Crea un alumno con su apoderado en una sola transacción."""
    try:
        curso = db.execute(select(Curso).where(Curso.id == body.curso_id)).scalar_one_or_none()
        if curso is None:
            raise HTTPException(status_code=404, detail="No se encontró el curso indicado.")

        alumno = Alumno(
            id=str(uuid.uuid4()),
            curso_id=body.curso_id,
            nombre=body.nombre.strip(),
            apellido_paterno=body.apellido_paterno.strip(),
            apellido_materno=body.apellido_materno.strip() if body.apellido_materno else None,
            rut=body.rut.strip() if body.rut else None,
            activo=True,
        )
        db.add(alumno)
        db.flush()

        apoderado = Apoderado(
            id=str(uuid.uuid4()),
            alumno_id=alumno.id,
            nombre=body.apoderado.nombre.strip(),
            apellido_paterno=body.apoderado.apellido_paterno.strip(),
            email=body.apoderado.email.strip() if body.apoderado.email else None,
            telefono=body.apoderado.telefono.strip() if body.apoderado.telefono else None,
        )
        db.add(apoderado)
        db.commit()
        db.refresh(alumno)
        db.refresh(apoderado)

        # Calcular estado de cuotas para el año actual
        año_actual = date.today().year
        estado_cuota = _calcular_estado_cuota(alumno, db, año_actual)

        # Construir respuesta manual
        return AlumnoResponse(
            id=alumno.id,
            curso_id=alumno.curso_id,
            nombre=alumno.nombre,
            apellido_paterno=alumno.apellido_paterno,
            apellido_materno=alumno.apellido_materno,
            rut=alumno.rut,
            activo=alumno.activo,
            created_at=alumno.created_at,
            apoderado=ApoderadoResponse(
                id=apoderado.id,
                alumno_id=apoderado.alumno_id,
                nombre=apoderado.nombre,
                apellido_paterno=apoderado.apellido_paterno,
                email=apoderado.email,
                telefono=apoderado.telefono,
            ),
            estado_cuota=estado_cuota,
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al crear el alumno: {e!s}") from e


@router.get("/alumnos", response_model=list[AlumnoResponse])
def listar_alumnos(
    curso_id: str = Query(..., description="UUID del curso"),
    año: int | None = Query(None, description="Año para calcular estado de cuotas (default: actual)"),
    db: Session = Depends(get_db),
):
    """Lista todos los alumnos del curso ordenados por apellido paterno."""
    try:
        curso = db.execute(select(Curso).where(Curso.id == curso_id)).scalar_one_or_none()
        if curso is None:
            raise HTTPException(status_code=404, detail="No se encontró el curso indicado.")

        alumnos = db.execute(
            select(Alumno)
            .where(Alumno.curso_id == curso_id)
            .order_by(Alumno.apellido_paterno.asc())
        ).scalars().all()

        año_calculo = año if año is not None else date.today().year
        resultado = []

        for alumno in alumnos:
            estado_cuota = _calcular_estado_cuota(alumno, db, año_calculo)
            apoderado = db.execute(
                select(Apoderado).where(Apoderado.alumno_id == alumno.id)
            ).scalar_one_or_none()

            apoderado_resp = None
            if apoderado:
                apoderado_resp = ApoderadoResponse(
                    id=apoderado.id,
                    alumno_id=apoderado.alumno_id,
                    nombre=apoderado.nombre,
                    apellido_paterno=apoderado.apellido_paterno,
                    email=apoderado.email,
                    telefono=apoderado.telefono,
                )

            resultado.append(
                AlumnoResponse(
                    id=alumno.id,
                    curso_id=alumno.curso_id,
                    nombre=alumno.nombre,
                    apellido_paterno=alumno.apellido_paterno,
                    apellido_materno=alumno.apellido_materno,
                    rut=alumno.rut,
                    activo=alumno.activo,
                    created_at=alumno.created_at,
                    apoderado=apoderado_resp,
                    estado_cuota=estado_cuota,
                )
            )

        return resultado
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al listar alumnos: {e!s}") from e


@router.put("/alumnos/{alumno_id}", response_model=AlumnoResponse)
def actualizar_alumno(
    alumno_id: str,
    body: AlumnoActualizar,
    db: Session = Depends(get_db),
):
    """Actualiza datos del alumno y/o apoderado."""
    try:
        alumno = db.execute(select(Alumno).where(Alumno.id == alumno_id)).scalar_one_or_none()
        if alumno is None:
            raise HTTPException(status_code=404, detail="No se encontró el alumno indicado.")

        # Actualizar campos del alumno si se proporcionan
        if body.nombre is not None:
            alumno.nombre = body.nombre.strip()
        if body.apellido_paterno is not None:
            alumno.apellido_paterno = body.apellido_paterno.strip()
        if body.apellido_materno is not None:
            alumno.apellido_materno = body.apellido_materno.strip() if body.apellido_materno else None
        if body.rut is not None:
            alumno.rut = body.rut.strip() if body.rut else None
        if body.activo is not None:
            alumno.activo = body.activo

        # Actualizar apoderado si se proporciona
        if body.apoderado is not None:
            apoderado = db.execute(
                select(Apoderado).where(Apoderado.alumno_id == alumno.id)
            ).scalar_one_or_none()

            if apoderado is None:
                apoderado = Apoderado(
                    id=str(uuid.uuid4()),
                    alumno_id=alumno.id,
                    nombre=body.apoderado.nombre.strip(),
                    apellido_paterno=body.apoderado.apellido_paterno.strip(),
                    email=body.apoderado.email.strip() if body.apoderado.email else None,
                    telefono=body.apoderado.telefono.strip() if body.apoderado.telefono else None,
                )
                db.add(apoderado)
            else:
                apoderado.nombre = body.apoderado.nombre.strip()
                apoderado.apellido_paterno = body.apoderado.apellido_paterno.strip()
                apoderado.email = body.apoderado.email.strip() if body.apoderado.email else None
                apoderado.telefono = body.apoderado.telefono.strip() if body.apoderado.telefono else None

        db.commit()
        db.refresh(alumno)

        # Recargar apoderado
        apoderado = db.execute(
            select(Apoderado).where(Apoderado.alumno_id == alumno.id)
        ).scalar_one_or_none()

        # Calcular estado de cuotas
        año_actual = date.today().year
        estado_cuota = _calcular_estado_cuota(alumno, db, año_actual)

        apoderado_resp = None
        if apoderado:
            apoderado_resp = ApoderadoResponse(
                id=apoderado.id,
                alumno_id=apoderado.alumno_id,
                nombre=apoderado.nombre,
                apellido_paterno=apoderado.apellido_paterno,
                email=apoderado.email,
                telefono=apoderado.telefono,
            )

        return AlumnoResponse(
            id=alumno.id,
            curso_id=alumno.curso_id,
            nombre=alumno.nombre,
            apellido_paterno=alumno.apellido_paterno,
            apellido_materno=alumno.apellido_materno,
            rut=alumno.rut,
            activo=alumno.activo,
            created_at=alumno.created_at,
            apoderado=apoderado_resp,
            estado_cuota=estado_cuota,
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al actualizar el alumno: {e!s}") from e


@router.delete("/alumnos/{alumno_id}")
def eliminar_alumno(
    alumno_id: str,
    db: Session = Depends(get_db),
):
    """Soft delete: marca activo=False. Retorna advertencia si tiene pagos registrados."""
    try:
        alumno = db.execute(select(Alumno).where(Alumno.id == alumno_id)).scalar_one_or_none()
        if alumno is None:
            raise HTTPException(status_code=404, detail="No se encontró el alumno indicado.")

        # Contar pagos del alumno
        result = db.execute(
            select(func.count()).where(PagoCuota.alumno_id == alumno_id)
        )
        pagos_count = result.scalar()

        # Soft delete
        alumno.activo = False
        db.commit()

        advertencia = None
        if pagos_count > 0:
            advertencia = f"El alumno tiene {pagos_count} pago(s) registrado(s)."

        return {"eliminado": True, "advertencia": advertencia}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al eliminar el alumno: {e!s}") from e
