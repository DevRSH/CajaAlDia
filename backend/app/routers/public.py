"""Vista pública por código de curso (sin autenticación)."""
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Alumno, ConfigCuota, Curso, Movimiento, PagoCuota
from app.schemas import CursoPublicoInfo, MovimientoPublicoLista, PublicEstadoResponse

router = APIRouter(prefix="/api", tags=["public"])


@router.get("/public/{codigo_curso}", response_model=PublicEstadoResponse)
def estado_publico(
    codigo_curso: str,
    db: Session = Depends(get_db),
) -> PublicEstadoResponse:
    try:
        codigo = codigo_curso.strip()
        curso = db.execute(select(Curso).where(Curso.codigo == codigo)).scalar_one_or_none()
        if curso is None:
            raise HTTPException(status_code=404, detail="Código de curso no encontrado.")

        base = (
            select(Movimiento)
            .where(
                Movimiento.curso_id == curso.id,
                Movimiento.anulado.is_(False),
            )
        )

        total_ingresos = db.scalar(
            select(func.coalesce(func.sum(Movimiento.monto), 0)).where(
                Movimiento.curso_id == curso.id,
                Movimiento.anulado.is_(False),
                Movimiento.tipo == "ingreso",
            )
        )
        total_egresos = db.scalar(
            select(func.coalesce(func.sum(Movimiento.monto), 0)).where(
                Movimiento.curso_id == curso.id,
                Movimiento.anulado.is_(False),
                Movimiento.tipo == "egreso",
            )
        )

        ti = int(total_ingresos or 0)
        te = int(total_egresos or 0)
        saldo = ti - te

        ultimos = db.execute(
            base.order_by(Movimiento.fecha.desc(), Movimiento.created_at.desc()).limit(10)
        ).scalars().all()

        # Calcular resumen de cuotas
        año_actual = curso.año
        configs = db.execute(
            select(ConfigCuota).where(
                ConfigCuota.curso_id == curso.id,
                ConfigCuota.año == año_actual,
            )
        ).scalars().all()

        alumnos = db.execute(
            select(Alumno).where(
                Alumno.curso_id == curso.id,
                Alumno.activo.is_(True),
            )
        ).scalars().all()

        pagos = db.execute(
            select(PagoCuota)
            .join(ConfigCuota, PagoCuota.config_cuota_id == ConfigCuota.id)
            .where(ConfigCuota.curso_id == curso.id, ConfigCuota.año == año_actual)
        ).scalars().all()

        total_alumnos = len(alumnos)
        al_dia = 0
        con_deuda = 0

        for alumno in alumnos:
            pagos_alumno = [p for p in pagos if p.alumno_id == alumno.id]
            meses_pagados = len(pagos_alumno)
            meses_config = len(configs)
            
            if meses_config == 0:
                continue
            
            if meses_pagados >= meses_config:
                al_dia += 1
            else:
                con_deuda += 1

        porcentaje_al_dia = (al_dia / total_alumnos * 100) if total_alumnos > 0 else 0

        resumen_cuotas = {
            "total_alumnos": total_alumnos,
            "al_dia": al_dia,
            "con_deuda": con_deuda,
            "porcentaje_al_dia": round(porcentaje_al_dia, 1),
        }

        return PublicEstadoResponse(
            curso=CursoPublicoInfo(nombre=curso.nombre, colegio=curso.colegio, año=curso.año),
            saldo=saldo,
            total_ingresos=ti,
            total_egresos=te,
            ultimos_movimientos=[
                MovimientoPublicoLista(
                    tipo=m.tipo,
                    monto=m.monto,
                    descripcion=m.descripcion,
                    fecha=m.fecha,
                    folio=m.folio,
                )
                for m in ultimos
            ],
            resumen_cuotas=resumen_cuotas,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al obtener el estado público: {e!s}",
        ) from e
