"""Esquemas Pydantic v2."""
from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator, field_serializer


class MovimientoCrear(BaseModel):
    curso_id: str = Field(..., min_length=1)
    tipo: Literal["ingreso", "egreso"]
    monto: int = Field(..., gt=0)
    descripcion: str = Field(..., max_length=200, min_length=1)
    fecha: date | None = None

    @field_validator("monto")
    @classmethod
    def monto_entero(cls, v: int) -> int:
        if not isinstance(v, int):
            raise ValueError("El monto debe ser un entero en pesos chilenos.")
        return v


class MovimientoResponse(BaseModel):
    id: str
    curso_id: str
    tipo: str
    monto: int
    descripcion: str
    folio: str
    fecha: date
    anulado: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class CursoPublicoInfo(BaseModel):
    nombre: str
    colegio: str
    año: int


class MovimientoPublicoLista(BaseModel):
    """Últimos movimientos públicos: sin datos internos."""

    tipo: str
    monto: int
    descripcion: str
    fecha: date
    folio: str


class PublicEstadoResponse(BaseModel):
    curso: CursoPublicoInfo
    saldo: int
    total_ingresos: int
    total_egresos: int
    ultimos_movimientos: list[MovimientoPublicoLista]
    resumen_cuotas: dict | None = None


class HealthResponse(BaseModel):
    status: Literal["ok"] = "ok"


# Alumnos y Apoderados


class ApoderadoCrear(BaseModel):
    nombre: str = Field(..., min_length=1, max_length=100)
    apellido_paterno: str = Field(..., min_length=1, max_length=100)
    email: str | None = Field(None, max_length=255)
    telefono: str | None = Field(None, max_length=50)


class ApoderadoResponse(BaseModel):
    id: str
    alumno_id: str
    nombre: str
    apellido_paterno: str
    email: str | None
    telefono: str | None

    model_config = {"from_attributes": True}


class EstadoCuota(BaseModel):
    estado: Literal["al_dia", "debe_meses", "sin_cuotas"]
    meses_pendientes: int
    monto_pendiente: int


class AlumnoCrear(BaseModel):
    curso_id: str = Field(..., min_length=1)
    nombre: str = Field(..., min_length=1, max_length=100)
    apellido_paterno: str = Field(..., min_length=1, max_length=100)
    apellido_materno: str | None = Field(None, max_length=100)
    rut: str | None = Field(None, max_length=20)
    apoderado: ApoderadoCrear

    @field_validator("rut")
    @classmethod
    def validar_formato_rut(cls, v: str | None) -> str | None:
        if v is None:
            return None
        import re
        if not re.match(r"^\d{1,2}\.\d{3}\.\d{3}-[\dkK]$", v):
            raise ValueError("El RUT debe tener formato XX.XXX.XXX-X")
        return v


class AlumnoResponse(BaseModel):
    id: str
    curso_id: str
    nombre: str
    apellido_paterno: str
    apellido_materno: str | None
    rut: str | None
    activo: bool
    created_at: datetime
    apoderado: ApoderadoResponse | None
    estado_cuota: EstadoCuota

    @field_serializer("estado_cuota")
    def serialize_estado_cuota(self, value: EstadoCuota, _info):
        return value.model_dump()

    model_config = {"from_attributes": True}


class AlumnoActualizar(BaseModel):
    nombre: str | None = Field(None, min_length=1, max_length=100)
    apellido_paterno: str | None = Field(None, min_length=1, max_length=100)
    apellido_materno: str | None = Field(None, max_length=100)
    rut: str | None = Field(None, max_length=20)
    activo: bool | None = None
    apoderado: ApoderadoCrear | None = None

    @field_validator("rut")
    @classmethod
    def validar_formato_rut(cls, v: str | None) -> str | None:
        if v is None:
            return None
        import re
        if not re.match(r"^\d{1,2}\.\d{3}\.\d{3}-[\dkK]$", v):
            raise ValueError("El RUT debe tener formato XX.XXX.XXX-X")
        return v


# Cuotas


class ConfigCuotaCrear(BaseModel):
    curso_id: str = Field(..., min_length=1)
    anio: int = Field(..., ge=2000, le=2100)
    mes: int = Field(..., ge=1, le=12)
    monto: int = Field(..., gt=0)
    descripcion: str = Field(..., min_length=1, max_length=200)


class ConfigCuotaResponse(BaseModel):
    id: str
    curso_id: str
    año: int
    mes: int
    monto: int
    descripcion: str

    model_config = {"from_attributes": True}


class PagoCuotaCrear(BaseModel):
    alumno_id: str = Field(..., min_length=1)
    config_cuota_id: str = Field(..., min_length=1)
    fecha_pago: date | None = None


class PagoCuotaResponse(BaseModel):
    id: str
    alumno_id: str
    config_cuota_id: str
    movimiento_id: str
    fecha_pago: date
    created_at: datetime

    model_config = {"from_attributes": True}


class MesEstadoCuota(BaseModel):
    mes: int
    descripcion: str
    monto: int
    pagado: bool
    fecha_pago: date | None
    folio: str | None


class AlumnoEstadoCuota(BaseModel):
    alumno: dict
    meses: list[MesEstadoCuota]
    total_pagado: int
    total_pendiente: int


class CuotaEstadoResponse(BaseModel):
    curso: dict
    año: int
    alumnos: list[AlumnoEstadoCuota]


class PagoCuotaConMovimiento(BaseModel):
    pago: PagoCuotaResponse
    movimiento: MovimientoResponse
    folio: str


class NotificacionResponse(BaseModel):
    enviado: bool
    destinatario: str
    asunto: str
    mensaje: str


# Notificación de deuda


class NotificacionDeudaRequest(BaseModel):
    curso_id: str = Field(..., min_length=1)
    año: int = Field(..., ge=2000, le=2100)
    alumno_ids: list[str] | None = None


class NotificacionDeudaDetalle(BaseModel):
    alumno: str
    email: str | None
    meses_pendientes: int
    monto_total: int


class NotificacionDeudaResponse(BaseModel):
    notificados: int
    sin_email: int
    detalle: list[NotificacionDeudaDetalle]


# Configuración del curso


class Directiva(BaseModel):
    tesorera: str = Field(..., min_length=1, max_length=255)
    presidenta: str | None = Field(None, max_length=255)
    secretaria: str | None = Field(None, max_length=255)


class CursoCrear(BaseModel):
    codigo: str = Field(..., min_length=1, max_length=64)
    nombre: str = Field(..., min_length=1, max_length=255)
    colegio: str = Field(..., min_length=1, max_length=255)
    año: int = Field(..., ge=2000, le=2100)
    directiva: Directiva

    @field_validator("codigo")
    @classmethod
    def codigo_sin_espacios(cls, v: str) -> str:
        if " " in v:
            raise ValueError("El código no puede contener espacios.")
        return v


class CursoActualizar(BaseModel):
    codigo: str | None = Field(None, max_length=64)
    nombre: str | None = Field(None, max_length=255)
    colegio: str | None = Field(None, max_length=255)
    año: int | None = Field(None, ge=2000, le=2100)
    directiva: Directiva | None = None

    @field_validator("codigo")
    @classmethod
    def codigo_sin_espacios(cls, v: str | None) -> str | None:
        if v is not None and " " in v:
            raise ValueError("El código no puede contener espacios.")
        return v


class CursoResponse(BaseModel):
    id: str
    codigo: str
    nombre: str
    colegio: str
    año: int
    directiva_tesorera: str | None
    directiva_presidenta: str | None
    directiva_secretaria: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class ConfiguracionResponse(BaseModel):
    configurada: bool
    curso: CursoResponse | None
