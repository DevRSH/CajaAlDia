"""Endpoints de gestión de cuotas y pagos."""
import uuid
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.folio_util import construir_folio
from app.models import Alumno, Apoderado, ConfigCuota, Curso, FolioSecuencia, Movimiento, NotificacionEmail, PagoCuota
from app.schemas import (
    AlumnoEstadoCuota,
    ConfigCuotaCrear,
    ConfigCuotaResponse,
    CuotaEstadoResponse,
    EstadoCuota,
    MesEstadoCuota,
    NotificacionDeudaDetalle,
    NotificacionDeudaRequest,
    NotificacionDeudaResponse,
    NotificacionResponse,
    MovimientoResponse,
    PagoCuotaConMovimiento,
    PagoCuotaCrear,
    PagoCuotaResponse,
)

router = APIRouter(prefix="/api", tags=["cuotas"])

MAX_FOLIO_RETRIES = 8


@router.post("/cuotas/config", response_model=ConfigCuotaResponse)
def crear_config_cuota(
    body: ConfigCuotaCrear,
    db: Session = Depends(get_db),
):
    """Crea una configuración de cuota mensual para un curso."""
    try:
        curso = db.execute(select(Curso).where(Curso.id == body.curso_id)).scalar_one_or_none()
        if curso is None:
            raise HTTPException(status_code=404, detail="No se encontró el curso indicado.")

        config = ConfigCuota(
            id=str(uuid.uuid4()),
            curso_id=body.curso_id,
            año=body.anio,
            mes=body.mes,
            monto=body.monto,
            descripcion=body.descripcion.strip(),
        )
        db.add(config)
        db.commit()
        db.refresh(config)
        return config
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Ya existe una configuración de cuota para este mes y año."
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al crear configuración de cuota: {e!s}") from e


@router.get("/cuotas/config", response_model=list[ConfigCuotaResponse])
def listar_config_cuotas(
    curso_id: str = Query(..., description="UUID del curso"),
    anio: int = Query(..., description="Año"),
    db: Session = Depends(get_db),
):
    """Lista las configuraciones de cuota de un curso para un año."""
    try:
        curso = db.execute(select(Curso).where(Curso.id == curso_id)).scalar_one_or_none()
        if curso is None:
            raise HTTPException(status_code=404, detail="No se encontró el curso indicado.")

        configs = db.execute(
            select(ConfigCuota)
            .where(ConfigCuota.curso_id == curso_id, ConfigCuota.año == anio)
            .order_by(ConfigCuota.mes.asc())
        ).scalars().all()
        return list(configs)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al listar configuraciones: {e!s}") from e


@router.post("/cuotas/pago/{pago_id}/notificar", response_model=NotificacionResponse)
def notificar_pago(
    pago_id: str,
    db: Session = Depends(get_db),
):
    """Simula el envío de una notificación de pago al apoderado."""
    print(f"DEBUG: notificar_pago llamado con pago_id={pago_id}")
    try:
        pago = db.execute(select(PagoCuota).where(PagoCuota.id == pago_id)).scalar_one_or_none()
        if pago is None:
            raise HTTPException(status_code=404, detail="No se encontró el pago indicado.")

        alumno = db.execute(select(Alumno).where(Alumno.id == pago.alumno_id)).scalar_one_or_none()
        if alumno is None:
            raise HTTPException(status_code=404, detail="No se encontró el alumno del pago.")

        apoderado = db.execute(select(Apoderado).where(Apoderado.alumno_id == alumno.id)).scalar_one_or_none()
        if apoderado is None or not apoderado.email:
            raise HTTPException(status_code=400, detail="El alumno no tiene apoderado con email registrado.")

        config = db.execute(select(ConfigCuota).where(ConfigCuota.id == pago.config_cuota_id)).scalar_one_or_none()
        if config is None:
            raise HTTPException(status_code=404, detail="No se encontró la configuración de cuota.")

        # Crear registro de notificación (simulado)
        notif = NotificacionEmail(
            id=str(uuid.uuid4()),
            pago_cuota_id=pago.id,
            email_destinatario=apoderado.email,
            asunto=f"Comprobante de pago - CajaAlDía",
            mensaje=f"Se ha registrado el pago de cuota {config.mes}/{config.año} por ${config.monto}.",
            estado="simulado",
        )
        db.add(notif)
        db.commit()

        return NotificacionResponse(
            enviado=True,
            destinatario=apoderado.email,
            asunto="Comprobante de pago - CajaAlDía",
            mensaje=f"Se ha registrado el pago de cuota {config.mes}/{config.año}",
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al enviar notificación: {e!s}") from e


@router.post("/cuotas/pago", response_model=PagoCuotaConMovimiento)
def registrar_pago_cuota(
    body: PagoCuotaCrear,
    db: Session = Depends(get_db),
):
    """Registra un pago de cuota creando el movimiento correspondiente."""
    try:
        alumno = db.execute(select(Alumno).where(Alumno.id == body.alumno_id)).scalar_one_or_none()
        if alumno is None:
            raise HTTPException(status_code=404, detail="No se encontró el alumno indicado.")

        config = db.execute(
            select(ConfigCuota).where(ConfigCuota.id == body.config_cuota_id)
        ).scalar_one_or_none()
        if config is None:
            raise HTTPException(status_code=404, detail="No se encontró la configuración de cuota.")

        # Verificar que el alumno pertenezca al mismo curso de la config
        if alumno.curso_id != config.curso_id:
            raise HTTPException(
                status_code=400,
                detail="El alumno no pertenece al curso de la configuración de cuota."
            )

        fecha_pago = body.fecha_pago if body.fecha_pago is not None else date.today()
        año = fecha_pago.year

        # Asegurar fila de secuencia para (curso, año)
        seq_row = db.execute(
            select(FolioSecuencia).where(
                FolioSecuencia.curso_id == alumno.curso_id,
                FolioSecuencia.año == año,
            )
        ).scalar_one_or_none()
        if seq_row is None:
            seq_row = FolioSecuencia(
                id=str(uuid.uuid4()),
                curso_id=alumno.curso_id,
                año=año,
                ultimo_numero=0,
            )
            db.add(seq_row)
            db.flush()

        # Descripción automática: "Cuota {mes}/{año} - {apellido_paterno}"
        descripcion = f"Cuota {config.mes}/{config.año} - {alumno.apellido_paterno}"

        for _ in range(MAX_FOLIO_RETRIES):
            try:
                # Incremento atómico
                resultado = db.execute(
                    text(
                        "UPDATE folio_secuencia SET ultimo_numero = ultimo_numero + 1 "
                        "WHERE curso_id = :cid AND año = :anio RETURNING ultimo_numero"
                    ),
                    {"cid": alumno.curso_id, "anio": año},
                )
                secuencia = resultado.scalar_one()
                folio = construir_folio(año, config.curso.codigo if config.curso else "", secuencia)

                # Crear movimiento de ingreso
                mov = Movimiento(
                    id=str(uuid.uuid4()),
                    curso_id=alumno.curso_id,
                    tipo="ingreso",
                    monto=config.monto,
                    descripcion=descripcion,
                    folio=folio,
                    fecha=fecha_pago,
                    anulado=False,
                )
                db.add(mov)
                db.flush()

                # Crear pago de cuota
                pago = PagoCuota(
                    id=str(uuid.uuid4()),
                    alumno_id=alumno.id,
                    config_cuota_id=config.id,
                    movimiento_id=mov.id,
                    fecha_pago=fecha_pago,
                )
                db.add(pago)
                db.commit()
                db.refresh(pago)
                db.refresh(mov)

                return PagoCuotaConMovimiento(
                    pago=PagoCuotaResponse(
                        id=pago.id,
                        alumno_id=pago.alumno_id,
                        config_cuota_id=pago.config_cuota_id,
                        movimiento_id=pago.movimiento_id,
                        fecha_pago=pago.fecha_pago,
                        created_at=pago.created_at,
                    ),
                    movimiento=MovimientoResponse(
                        id=mov.id,
                        curso_id=mov.curso_id,
                        tipo=mov.tipo,
                        monto=mov.monto,
                        descripcion=mov.descripcion,
                        folio=mov.folio,
                        fecha=mov.fecha,
                        anulado=mov.anulado,
                        created_at=mov.created_at,
                    ),
                    folio=folio,
                )
            except IntegrityError:
                db.rollback()
                # Reabrir fila de secuencia tras rollback
                seq_row = db.execute(
                    select(FolioSecuencia).where(
                        FolioSecuencia.curso_id == alumno.curso_id,
                        FolioSecuencia.año == año,
                    )
                ).scalar_one_or_none()
                if seq_row is None:
                    seq_row = FolioSecuencia(
                        id=str(uuid.uuid4()),
                        curso_id=alumno.curso_id,
                        año=año,
                        ultimo_numero=0,
                    )
                    db.add(seq_row)
                    db.flush()
                continue

        raise HTTPException(
            status_code=409,
            detail="No se pudo asignar un folio único. Intente nuevamente.",
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al registrar pago de cuota: {e!s}") from e


@router.get("/cuotas/estado", response_model=CuotaEstadoResponse)
def estado_cuotas(
    curso_id: str = Query(..., description="UUID del curso"),
    anio: int = Query(..., description="Año"),
    db: Session = Depends(get_db),
):
    """Retorna la matriz de estado de cuotas por alumno y mes."""
    try:
        curso = db.execute(select(Curso).where(Curso.id == curso_id)).scalar_one_or_none()
        if curso is None:
            raise HTTPException(status_code=404, detail="No se encontró el curso indicado.")

        # Obtener configuraciones del año
        configs = db.execute(
            select(ConfigCuota)
            .where(ConfigCuota.curso_id == curso_id, ConfigCuota.año == anio)
            .order_by(ConfigCuota.mes.asc())
        ).scalars().all()

        # Obtener alumnos activos ordenados por apellido
        alumnos = db.execute(
            select(Alumno)
            .where(Alumno.curso_id == curso_id, Alumno.activo.is_(True))
            .order_by(Alumno.apellido_paterno.asc())
        ).scalars().all()

        # Obtener todos los pagos del curso para este año
        pagos = db.execute(
            select(PagoCuota)
            .join(ConfigCuota, PagoCuota.config_cuota_id == ConfigCuota.id)
            .where(ConfigCuota.curso_id == curso_id, ConfigCuota.año == anio)
        ).scalars().all()

        # Crear mapa de pagos: (alumno_id, config_cuota_id) -> pago
        pagos_map = {(p.alumno_id, p.config_cuota_id): p for p in pagos}

        alumnos_estado = []
        for alumno in alumnos:
            nombre_completo = f"{alumno.apellido_paterno} {alumno.apellido_materno or ''}, {alumno.nombre}".strip()
            meses_estado = []
            total_pagado = 0
            total_pendiente = 0

            for config in configs:
                pago = pagos_map.get((alumno.id, config.id))
                pagado = pago is not None

                if pagado:
                    total_pagado += config.monto
                else:
                    total_pendiente += config.monto

                meses_estado.append(
                    MesEstadoCuota(
                        mes=config.mes,
                        descripcion=config.descripcion,
                        monto=config.monto,
                        pagado=pagado,
                        fecha_pago=pago.fecha_pago if pago else None,
                        folio=pago.movimiento.folio if pago else None,
                    )
                )

            alumnos_estado.append(
                AlumnoEstadoCuota(
                    alumno={"id": alumno.id, "nombre_completo": nombre_completo},
                    meses=meses_estado,
                    total_pagado=total_pagado,
                    total_pendiente=total_pendiente,
                )
            )

        return CuotaEstadoResponse(
            curso={"id": curso.id, "nombre": curso.nombre, "codigo": curso.codigo},
            año=anio,
            alumnos=alumnos_estado,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener estado de cuotas: {e!s}") from e


@router.get("/cuotas/deudores", response_model=CuotaEstadoResponse)
def listar_deudores(
    curso_id: str = Query(..., description="UUID del curso"),
    anio: int = Query(..., description="Año"),
    db: Session = Depends(get_db),
):
    """Retorna solo alumnos con cuotas pendientes, ordenados por monto pendiente descendente."""
    try:
        curso = db.execute(select(Curso).where(Curso.id == curso_id)).scalar_one_or_none()
        if curso is None:
            raise HTTPException(status_code=404, detail="No se encontró el curso indicado.")

        # Obtener configuraciones del año
        configs = db.execute(
            select(ConfigCuota)
            .where(ConfigCuota.curso_id == curso_id, ConfigCuota.año == anio)
            .order_by(ConfigCuota.mes.asc())
        ).scalars().all()

        # Obtener alumnos activos
        alumnos = db.execute(
            select(Alumno)
            .where(Alumno.curso_id == curso_id, Alumno.activo.is_(True))
            .order_by(Alumno.apellido_paterno.asc())
        ).scalars().all()

        # Obtener pagos
        pagos = db.execute(
            select(PagoCuota)
            .join(ConfigCuota, PagoCuota.config_cuota_id == ConfigCuota.id)
            .where(ConfigCuota.curso_id == curso_id, ConfigCuota.año == anio)
        ).scalars().all()

        pagos_map = {(p.alumno_id, p.config_cuota_id): p for p in pagos}

        alumnos_con_deuda = []
        for alumno in alumnos:
            nombre_completo = f"{alumno.apellido_paterno} {alumno.apellido_materno or ''}, {alumno.nombre}".strip()
            meses_estado = []
            total_pagado = 0
            total_pendiente = 0

            for config in configs:
                pago = pagos_map.get((alumno.id, config.id))
                pagado = pago is not None

                if pagado:
                    total_pagado += config.monto
                else:
                    total_pendiente += config.monto

                meses_estado.append(
                    MesEstadoCuota(
                        mes=config.mes,
                        descripcion=config.descripcion,
                        monto=config.monto,
                        pagado=pagado,
                        fecha_pago=pago.fecha_pago if pago else None,
                        folio=pago.movimiento.folio if pago else None,
                    )
                )

            # Solo incluir si tiene deuda
            if total_pendiente > 0:
                alumnos_con_deuda.append(
                    AlumnoEstadoCuota(
                        alumno={"id": alumno.id, "nombre_completo": nombre_completo},
                        meses=meses_estado,
                        total_pagado=total_pagado,
                        total_pendiente=total_pendiente,
                    )
                )

        # Ordenar por total_pendiente descendente
        alumnos_con_deuda.sort(key=lambda x: x.total_pendiente, reverse=True)

        return CuotaEstadoResponse(
            curso={"id": curso.id, "nombre": curso.nombre, "codigo": curso.codigo},
            año=anio,
            alumnos=alumnos_con_deuda,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al listar deudores: {e!s}") from e


@router.post("/cuotas/notificar-deuda", response_model=NotificacionDeudaResponse)
def notificar_deuda(
    body: NotificacionDeudaRequest,
    db: Session = Depends(get_db),
):
    """Envía notificaciones de deuda a apoderados (simulado)."""
    try:
        curso = db.execute(select(Curso).where(Curso.id == body.curso_id)).scalar_one_or_none()
        if curso is None:
            raise HTTPException(status_code=404, detail="No se encontró el curso indicado.")

        # Obtener configuraciones del año
        configs = db.execute(
            select(ConfigCuota)
            .where(ConfigCuota.curso_id == body.curso_id, ConfigCuota.año == body.año)
            .order_by(ConfigCuota.mes.asc())
        ).scalars().all()

        if not configs:
            raise HTTPException(status_code=400, detail="No hay configuraciones de cuota para este año.")

        # Obtener alumnos a notificar
        if body.alumno_ids is None:
            # Notificar a todos los deudores
            alumnos = db.execute(
                select(Alumno)
                .where(Alumno.curso_id == body.curso_id, Alumno.activo.is_(True))
                .order_by(Alumno.apellido_paterno.asc())
            ).scalars().all()
        else:
            # Notificar solo a los alumnos especificados
            alumnos = db.execute(
                select(Alumno)
                .where(Alumno.id.in_(body.alumno_ids), Alumno.activo.is_(True))
            ).scalars().all()

        # Obtener pagos para calcular deuda
        pagos = db.execute(
            select(PagoCuota)
            .join(ConfigCuota, PagoCuota.config_cuota_id == ConfigCuota.id)
            .where(ConfigCuota.curso_id == body.curso_id, ConfigCuota.año == body.año)
        ).scalars().all()

        pagos_map = {(p.alumno_id, p.config_cuota_id): p for p in pagos}

        detalle = []
        notificados = 0
        sin_email = 0

        for alumno in alumnos:
            # Calcular deuda
            meses_pendientes = 0
            monto_total = 0

            for config in configs:
                pago = pagos_map.get((alumno.id, config.id))
                if pago is None:
                    meses_pendientes += 1
                    monto_total += config.monto

            # Solo notificar si tiene deuda
            if meses_pendientes == 0:
                continue

            # Obtener apoderado
            apoderado = db.execute(
                select(Apoderado).where(Apoderado.alumno_id == alumno.id)
            ).scalar_one_or_none()

            if apoderado is None or not apoderado.email:
                sin_email += 1
                detalle.append(
                    NotificacionDeudaDetalle(
                        alumno=f"{alumno.apellido_paterno} {alumno.apellido_materno or ''}, {alumno.nombre}".strip(),
                        email=None,
                        meses_pendientes=meses_pendientes,
                        monto_total=monto_total,
                    )
                )
                continue

            # Crear notificación
            nombre_completo_alumno = f"{alumno.apellido_paterno} {alumno.apellido_materno or ''}, {alumno.nombre}".strip()
            nombre_apoderado = f"{apoderado.nombre} {apoderado.apellido_paterno}".strip()
            
            notif = NotificacionEmail(
                id=str(uuid.uuid4()),
                pago_cuota_id=None,
                tipo="deuda",
                email_destinatario=apoderado.email,
                asunto="Estado de cuenta - CajaAlDía",
                mensaje=f"Estimado/a {nombre_apoderado}, le informamos que {nombre_completo_alumno} tiene {meses_pendientes} mes(es) pendiente(s) por un total de ${monto_total}. Por favor regularice su situación.",
                estado="simulado",
            )
            db.add(notif)
            notificados += 1

            detalle.append(
                NotificacionDeudaDetalle(
                    alumno=nombre_completo_alumno,
                    email=apoderado.email,
                    meses_pendientes=meses_pendientes,
                    monto_total=monto_total,
                )
            )

        db.commit()

        return NotificacionDeudaResponse(
            notificados=notificados,
            sin_email=sin_email,
            detalle=detalle,
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al notificar deuda: {e!s}") from e
