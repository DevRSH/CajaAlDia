"""Endpoints de gestión de cuotas y pagos."""
import os
import uuid
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.folio_util import construir_folio
from app.models import (
    Alumno,
    Apoderado,
    ConfigCuota,
    Curso,
    CuotaEspecialAlumno,
    FolioSecuencia,
    Movimiento,
    NotificacionEmail,
    PagoCuota,
    Usuario,
)
from app.routers.auth import get_current_user
from app.services import email_service
from app.schemas import (
    AlumnoEstadoCuota,
    ConfigCuotaCrear,
    ConfigCuotaResponse,
    ConfigCuotasListResponse,
    CuotaEspecialAlumnoResponse,
    CuotaEspecialEstado,
    CuotaEstadoCompletoResponse,
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
    _usuario: Usuario = Depends(get_current_user),
):
    """Crea una configuración de cuota mensual o especial para un curso."""
    try:
        curso = db.execute(select(Curso).where(Curso.id == body.curso_id)).scalar_one_or_none()
        if curso is None:
            raise HTTPException(status_code=404, detail="No se encontró el curso indicado.")

        # Para cuotas especiales, verificar si ya existe una con el mismo nombre
        if body.tipo == "especial":
            existente = db.execute(
                select(ConfigCuota).where(
                    ConfigCuota.curso_id == body.curso_id,
                    ConfigCuota.año == body.anio,
                    ConfigCuota.tipo == "especial",
                    ConfigCuota.nombre_especial == body.nombre_especial,
                )
            ).scalar_one_or_none()
            if existente:
                raise HTTPException(
                    status_code=409,
                    detail=f"Ya existe una cuota especial con el nombre '{body.nombre_especial}' para este año."
                )

        config = ConfigCuota(
            id=str(uuid.uuid4()),
            curso_id=body.curso_id,
            año=body.anio,
            mes=body.mes if body.mes is not None else 0,
            monto=body.monto,
            descripcion=body.descripcion.strip(),
            tipo=body.tipo,
            nombre_especial=body.nombre_especial.strip() if body.nombre_especial else None,
        )
        db.add(config)
        db.flush()  # Para obtener el ID antes de commit

        # Si hay alumno_ids específicos, crear las relaciones en la tabla pivot
        if body.tipo == "especial" and body.alumno_ids:
            for alumno_id in body.alumno_ids:
                # Verificar que el alumno existe y pertenece al curso
                alumno = db.execute(
                    select(Alumno).where(Alumno.id == alumno_id, Alumno.curso_id == body.curso_id)
                ).scalar_one_or_none()
                if alumno is None:
                    raise HTTPException(
                        status_code=404,
                        detail=f"No se encontró el alumno con ID {alumno_id} en este curso."
                    )

                rel = CuotaEspecialAlumno(
                    id=str(uuid.uuid4()),
                    config_cuota_id=config.id,
                    alumno_id=alumno_id,
                )
                db.add(rel)

        db.commit()
        db.refresh(config)
        return config
    except HTTPException:
        db.rollback()
        raise
    except IntegrityError as e:
        db.rollback()
        # Si es cuota de curso, puede ser el unique constraint
        if body.tipo == "curso":
            raise HTTPException(
                status_code=409,
                detail="Ya existe una configuración de cuota para este mes y año."
            )
        raise HTTPException(status_code=409, detail=f"Error de integridad: {str(e)}")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al crear configuración de cuota: {e!s}") from e


@router.get("/cuotas/config", response_model=ConfigCuotasListResponse)
def listar_config_cuotas(
    curso_id: str = Query(..., description="UUID del curso"),
    anio: int = Query(..., description="Año"),
    db: Session = Depends(get_db),
):
    """Lista las configuraciones de cuota de un curso para un año, separadas por tipo."""
    try:
        curso = db.execute(select(Curso).where(Curso.id == curso_id)).scalar_one_or_none()
        if curso is None:
            raise HTTPException(status_code=404, detail="No se encontró el curso indicado.")

        # Cuotas de curso (tipo="curso")
        cuotas_curso = db.execute(
            select(ConfigCuota)
            .where(
                ConfigCuota.curso_id == curso_id,
                ConfigCuota.año == anio,
                ConfigCuota.tipo == "curso",
            )
            .order_by(ConfigCuota.mes.asc())
        ).scalars().all()

        # Cuotas especiales (tipo="especial")
        cuotas_especiales = db.execute(
            select(ConfigCuota)
            .where(
                ConfigCuota.curso_id == curso_id,
                ConfigCuota.año == anio,
                ConfigCuota.tipo == "especial",
            )
            .order_by(ConfigCuota.created_at.desc())
        ).scalars().all()

        return ConfigCuotasListResponse(
            cuotas_curso=[ConfigCuotaResponse.model_validate(c) for c in cuotas_curso],
            cuotas_especiales=[ConfigCuotaResponse.model_validate(c) for c in cuotas_especiales],
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al listar configuraciones: {e!s}") from e


@router.post("/cuotas/pago/{pago_id}/notificar", response_model=NotificacionResponse)
def notificar_pago(
    pago_id: str,
    db: Session = Depends(get_db),
    _usuario: Usuario = Depends(get_current_user),
):
    """Envía (o reenvía) el comprobante de pago al apoderado."""
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

        frontend_url = os.getenv("FRONTEND_URL", "https://cajaaldia.up.railway.app")
        curso = db.execute(select(Curso).where(Curso.id == config.curso_id)).scalar_one_or_none()
        verification_url = f"{frontend_url}/public/{curso.codigo if curso else ''}"
        mes_año = f"{config.mes}/{config.año}" if config.mes else str(config.año)
        nombre_completo_alumno = f"{alumno.apellido_paterno} {alumno.apellido_materno or ''}, {alumno.nombre}".strip()
        nombre_apoderado = f"{apoderado.nombre} {apoderado.apellido_paterno}".strip()

        exitoso = email_service.enviar_comprobante_pago(
            destinatario_email=apoderado.email,
            destinatario_nombre=nombre_apoderado,
            alumno_nombre=nombre_completo_alumno,
            mes_año=mes_año,
            monto=config.monto,
            folio=pago.movimiento.folio if pago.movimiento else "",
            verification_url=verification_url,
        )

        estado = "enviado" if exitoso else "fallido"
        error_det = None if exitoso else "Error al comunicarse con Resend."

        notif = NotificacionEmail(
            id=str(uuid.uuid4()),
            pago_cuota_id=pago.id,
            tipo="pago",
            email_destinatario=apoderado.email,
            alumno_nombre=nombre_completo_alumno,
            asunto=f"Comprobante de pago - {mes_año}",
            mensaje=f"Comprobante de pago {mes_año} por ${config.monto}.",
            estado=estado,
            error_detalle=error_det,
        )
        db.add(notif)
        db.commit()

        return NotificacionResponse(
            enviado=exitoso,
            destinatario=apoderado.email,
            asunto=f"Comprobante de pago - {mes_año}",
            mensaje=f"Se ha registrado el pago de cuota {mes_año}",
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
    _usuario: Usuario = Depends(get_current_user),
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

                # Enviar comprobante por email (no bloquea el pago)
                apoderado = db.execute(
                    select(Apoderado).where(Apoderado.alumno_id == alumno.id)
                ).scalar_one_or_none()
                if apoderado and apoderado.email:
                    frontend_url = os.getenv("FRONTEND_URL", "https://cajaaldia.up.railway.app")
                    verification_url = f"{frontend_url}/public/{config.curso.codigo if config.curso else ''}"
                    mes_año = f"{config.mes}/{config.año}" if config.mes else str(config.año)
                    nombre_completo_alumno = f"{alumno.apellido_paterno} {alumno.apellido_materno or ''}, {alumno.nombre}".strip()
                    nombre_apoderado = f"{apoderado.nombre} {apoderado.apellido_paterno}".strip()
                    exitoso = email_service.enviar_comprobante_pago(
                        destinatario_email=apoderado.email,
                        destinatario_nombre=nombre_apoderado,
                        alumno_nombre=nombre_completo_alumno,
                        mes_año=mes_año,
                        monto=config.monto,
                        folio=folio,
                        verification_url=verification_url,
                    )
                    estado_email = "enviado" if exitoso else "fallido"
                    error_det = None if exitoso else "Error al comunicarse con Resend."
                    notif = NotificacionEmail(
                        id=str(uuid.uuid4()),
                        pago_cuota_id=pago.id,
                        tipo="pago",
                        email_destinatario=apoderado.email,
                        alumno_nombre=nombre_completo_alumno,
                        asunto=f"Comprobante de pago - {mes_año}",
                        mensaje=f"Comprobante de pago {mes_año} por ${config.monto}.",
                        estado=estado_email,
                        error_detalle=error_det,
                    )
                    db.add(notif)
                    db.commit()

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
    """Retorna la matriz de estado de cuotas por alumno y mes, incluyendo cuotas especiales."""
    try:
        curso = db.execute(select(Curso).where(Curso.id == curso_id)).scalar_one_or_none()
        if curso is None:
            raise HTTPException(status_code=404, detail="No se encontró el curso indicado.")

        # Obtener configuraciones del año (solo cuotas de curso tipo="curso")
        configs = db.execute(
            select(ConfigCuota)
            .where(
                ConfigCuota.curso_id == curso_id,
                ConfigCuota.año == anio,
                ConfigCuota.tipo == "curso",
            )
            .order_by(ConfigCuota.mes.asc())
        ).scalars().all()

        # Obtener cuotas especiales del año
        configs_especiales = db.execute(
            select(ConfigCuota)
            .where(
                ConfigCuota.curso_id == curso_id,
                ConfigCuota.año == anio,
                ConfigCuota.tipo == "especial",
            )
        ).scalars().all()

        # Obtener alumnos específicos para cada cuota especial
        alumnos_especiales_map = {}  # config_cuota_id -> set(alumno_ids)
        for config_esp in configs_especiales:
            rels = db.execute(
                select(CuotaEspecialAlumno.alumno_id).where(
                    CuotaEspecialAlumno.config_cuota_id == config_esp.id
                )
            ).scalars().all()
            if rels:
                alumnos_especiales_map[config_esp.id] = set(rels)
            # Si no hay filas, aplica a todos

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

            # Cuotas del curso
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


@router.get("/cuotas/historial-notificaciones")
def historial_notificaciones(
    curso_id: str = Query(..., description="UUID del curso"),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    tipo: str | None = Query(None, description="Filtrar por tipo: pago | deuda"),
    db: Session = Depends(get_db),
):
    """Lista el historial de notificaciones de email para el curso, ordenado por fecha desc."""
    try:
        # Obtener todos los pago_cuota_ids del curso
        pagos_ids = db.execute(
            select(PagoCuota.id)
            .join(ConfigCuota, PagoCuota.config_cuota_id == ConfigCuota.id)
            .where(ConfigCuota.curso_id == curso_id)
        ).scalars().all()

        # Notificaciones de deuda (pago_cuota_id=NULL) y de pago del curso
        stmt = select(NotificacionEmail).where(
            (NotificacionEmail.pago_cuota_id.in_(pagos_ids)) |
            (NotificacionEmail.pago_cuota_id.is_(None))
        )
        if tipo:
            stmt = stmt.where(NotificacionEmail.tipo == tipo)
        stmt = stmt.order_by(NotificacionEmail.enviado_en.desc())

        offset = (page - 1) * size
        notifs = db.execute(stmt.offset(offset).limit(size)).scalars().all()

        resultado = []
        for n in notifs:
            resultado.append({
                "id": n.id,
                "pago_cuota_id": n.pago_cuota_id,
                "tipo": n.tipo,
                "email_destinatario": n.email_destinatario,
                "alumno_nombre": n.alumno_nombre,
                "asunto": n.asunto,
                "estado": n.estado,
                "error_detalle": n.error_detalle,
                "enviado_en": n.enviado_en.isoformat() if n.enviado_en else None,
            })

        return {"page": page, "size": size, "items": resultado}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener historial: {e!s}") from e


@router.post("/cuotas/notificar-deuda", response_model=NotificacionDeudaResponse)
def notificar_deuda(
    body: NotificacionDeudaRequest,
    db: Session = Depends(get_db),
    _usuario: Usuario = Depends(get_current_user),
):
    """Envía notificaciones de deuda a apoderados."""
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
            
            frontend_url = os.getenv("FRONTEND_URL", "https://cajaaldia.up.railway.app")
            panel_url = f"{frontend_url}/public/{curso.codigo}"

            exitoso = email_service.enviar_notificacion_deuda(
                destinatario_email=apoderado.email,
                destinatario_nombre=nombre_apoderado,
                alumno_nombre=nombre_completo_alumno,
                meses_pendientes=meses_pendientes,
                monto_total=monto_total,
                curso_nombre=curso.nombre,
                panel_url=panel_url,
            )
            estado_email = "enviado" if exitoso else "fallido"
            error_det = None if exitoso else "Error al comunicarse con Resend."

            notif = NotificacionEmail(
                id=str(uuid.uuid4()),
                pago_cuota_id=None,
                tipo="deuda",
                email_destinatario=apoderado.email,
                alumno_nombre=nombre_completo_alumno,
                asunto=f"Estado de cuenta - {curso.nombre}",
                mensaje=f"Estimado/a {nombre_apoderado}, {nombre_completo_alumno} tiene {meses_pendientes} mes(es) pendiente(s) por un total de ${monto_total}.",
                estado=estado_email,
                error_detalle=error_det,
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


@router.get("/cuotas/especial/{config_cuota_id}/estado")
def estado_cuota_especial(
    config_cuota_id: str,
    db: Session = Depends(get_db),
):
    """Retorna el estado de pago de una cuota específica por alumno."""
    try:
        config = db.execute(
            select(ConfigCuota).where(ConfigCuota.id == config_cuota_id)
        ).scalar_one_or_none()
        if config is None:
            raise HTTPException(status_code=404, detail="No se encontró la cuota indicada.")

        # Obtener alumnos a los que aplica la cuota
        alumnos_especiales = db.execute(
            select(CuotaEspecialAlumno.alumno_id).where(
                CuotaEspecialAlumno.config_cuota_id == config_cuota_id
            )
        ).scalars().all()

        # Si hay alumnos específicos, solo esos; si no, todos los del curso
        if alumnos_especiales:
            alumnos = db.execute(
                select(Alumno)
                .where(Alumno.id.in_(alumnos_especiales), Alumno.activo.is_(True))
                .order_by(Alumno.apellido_paterno.asc())
            ).scalars().all()
        else:
            alumnos = db.execute(
                select(Alumno)
                .where(Alumno.curso_id == config.curso_id, Alumno.activo.is_(True))
                .order_by(Alumno.apellido_paterno.asc())
            ).scalars().all()

        # Obtener pagos para esta cuota
        pagos = db.execute(
            select(PagoCuota).where(PagoCuota.config_cuota_id == config_cuota_id)
        ).scalars().all()
        pagos_map = {p.alumno_id: p for p in pagos}

        resultado = []
        total_pagado = 0
        total_pendiente = 0
        pagados_count = 0
        pendientes_count = 0

        for alumno in alumnos:
            nombre_completo = f"{alumno.apellido_paterno} {alumno.apellido_materno or ''}, {alumno.nombre}".strip()
            pago = pagos_map.get(alumno.id)
            pagado = pago is not None

            if pagado:
                total_pagado += config.monto
                pagados_count += 1
            else:
                total_pendiente += config.monto
                pendientes_count += 1

            resultado.append(
                {
                    "alumno": {"id": alumno.id, "nombre_completo": nombre_completo},
                    "pagado": pagado,
                    "fecha_pago": pago.fecha_pago if pago else None,
                    "folio": pago.movimiento.folio if pago else None,
                }
            )

        return {
            "config_cuota": {
                "id": config.id,
                "nombre_especial": config.nombre_especial,
                "monto": config.monto,
                "descripcion": config.descripcion,
            },
            "alumnos": resultado,
            "resumen": {
                "total_alumnos": len(alumnos),
                "pagados": pagados_count,
                "pendientes": pendientes_count,
                "total_recaudado": total_pagado,
                "total_pendiente": total_pendiente,
            },
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener estado de cuota especial: {e!s}") from e
