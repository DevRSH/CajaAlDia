"""Modelos ORM."""
import uuid
from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.sqlite import CHAR
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Usuario(Base):
    """Usuario del sistema (tesorera, directiva, admin)."""

    __tablename__ = "usuarios"
    __table_args__ = (UniqueConstraint("email", name="uq_usuarios_email"),)

    id: Mapped[str] = mapped_column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    nombre: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    rol: Mapped[str] = mapped_column(String(50), nullable=False, default="tesorera")
    activo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.utcnow())


class Curso(Base):
    __tablename__ = "cursos"
    __table_args__ = (UniqueConstraint("codigo", name="uq_cursos_codigo"),)

    id: Mapped[str] = mapped_column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    codigo: Mapped[str] = mapped_column(String(64), nullable=False)
    nombre: Mapped[str] = mapped_column(String(255), nullable=False)
    colegio: Mapped[str] = mapped_column(String(255), nullable=False)
    año: Mapped[int] = mapped_column(Integer, nullable=False)
    directiva_tesorera: Mapped[str] = mapped_column(String(255), nullable=True)
    directiva_tesorera_email: Mapped[str] = mapped_column(String(255), nullable=True)
    directiva_presidenta: Mapped[str] = mapped_column(String(255), nullable=True)
    directiva_presidenta_email: Mapped[str] = mapped_column(String(255), nullable=True)
    directiva_secretaria: Mapped[str] = mapped_column(String(255), nullable=True)
    directiva_secretaria_email: Mapped[str] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.utcnow())

    movimientos: Mapped[list["Movimiento"]] = relationship(
        back_populates="curso",
        cascade="all, delete-orphan",
    )

    folio_rows: Mapped[list["FolioSecuencia"]] = relationship(
        back_populates="curso",
        cascade="all, delete-orphan",
    )

    alumnos: Mapped[list["Alumno"]] = relationship(
        back_populates="curso",
        cascade="all, delete-orphan",
    )


class FolioSecuencia(Base):
    """Contador atómico por curso y año para generar folios sin duplicados."""

    __tablename__ = "folio_secuencia"
    __table_args__ = (UniqueConstraint("curso_id", "año", name="uq_folio_seq_curso_año"),)

    id: Mapped[str] = mapped_column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    curso_id: Mapped[str] = mapped_column(CHAR(36), ForeignKey("cursos.id", ondelete="CASCADE"), nullable=False)
    año: Mapped[int] = mapped_column(Integer, nullable=False)
    ultimo_numero: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    curso: Mapped["Curso"] = relationship(back_populates="folio_rows")


class Movimiento(Base):
    __tablename__ = "movimientos"

    __table_args__ = (UniqueConstraint("folio", name="uq_movimientos_folio"),)

    id: Mapped[str] = mapped_column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    curso_id: Mapped[str] = mapped_column(CHAR(36), ForeignKey("cursos.id", ondelete="CASCADE"), nullable=False)
    tipo: Mapped[str] = mapped_column(String(16), nullable=False)  # ingreso | egreso
    monto: Mapped[int] = mapped_column(Integer, nullable=False)
    descripcion: Mapped[str] = mapped_column(String(200), nullable=False)
    folio: Mapped[str] = mapped_column(String(64), nullable=False)
    fecha: Mapped[date] = mapped_column(Date, nullable=False)
    anulado: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.utcnow())

    curso: Mapped["Curso"] = relationship(back_populates="movimientos")
    pagos_cuota: Mapped[list["PagoCuota"]] = relationship(back_populates="movimiento")


class Alumno(Base):
    __tablename__ = "alumnos"

    id: Mapped[str] = mapped_column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    curso_id: Mapped[str] = mapped_column(CHAR(36), ForeignKey("cursos.id", ondelete="CASCADE"), nullable=False)
    nombre: Mapped[str] = mapped_column(String(100), nullable=False)
    apellido_paterno: Mapped[str] = mapped_column(String(100), nullable=False)
    apellido_materno: Mapped[str] = mapped_column(String(100), nullable=True)
    rut: Mapped[str] = mapped_column(String(20), nullable=True)
    activo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.utcnow())

    curso: Mapped["Curso"] = relationship(back_populates="alumnos")
    apoderado: Mapped["Apoderado"] = relationship(back_populates="alumno", uselist=False)
    pagos_cuota: Mapped[list["PagoCuota"]] = relationship(back_populates="alumno")


class Apoderado(Base):
    __tablename__ = "apoderados"

    id: Mapped[str] = mapped_column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    alumno_id: Mapped[str] = mapped_column(CHAR(36), ForeignKey("alumnos.id", ondelete="CASCADE"), nullable=False, unique=True)
    nombre: Mapped[str] = mapped_column(String(100), nullable=False)
    apellido_paterno: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=True)
    telefono: Mapped[str] = mapped_column(String(50), nullable=True)

    alumno: Mapped["Alumno"] = relationship(back_populates="apoderado")


class ConfigCuota(Base):
    __tablename__ = "config_cuotas"

    # Unique constraint diferente para cuotas curso vs especiales
    __table_args__ = (
        UniqueConstraint("curso_id", "año", "mes", name="uq_config_cuotas_curso_año_mes"),
    )

    id: Mapped[str] = mapped_column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    curso_id: Mapped[str] = mapped_column(CHAR(36), ForeignKey("cursos.id", ondelete="CASCADE"), nullable=False)
    año: Mapped[int] = mapped_column(Integer, nullable=False)
    mes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)  # 0 para especiales, 1-12 para curso
    monto: Mapped[int] = mapped_column(Integer, nullable=False)
    descripcion: Mapped[str] = mapped_column(String(200), nullable=False)
    tipo: Mapped[str] = mapped_column(String(20), nullable=False, default="curso")  # "curso" | "especial"
    nombre_especial: Mapped[str | None] = mapped_column(String(200), nullable=True)  # Solo para tipo="especial"
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.utcnow())

    curso: Mapped["Curso"] = relationship()
    pagos: Mapped[list["PagoCuota"]] = relationship(back_populates="config_cuota")
    alumnos_especiales: Mapped[list["CuotaEspecialAlumno"]] = relationship(
        back_populates="config_cuota",
        cascade="all, delete-orphan",
    )


class CuotaEspecialAlumno(Base):
    """Tabla pivot para cuotas especiales: si no hay filas para una ConfigCuota,
    significa que aplica a TODOS los alumnos."""

    __tablename__ = "cuota_especial_alumnos"

    __table_args__ = (
        UniqueConstraint("config_cuota_id", "alumno_id", name="uq_cuota_especial_alumno"),
    )

    id: Mapped[str] = mapped_column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    config_cuota_id: Mapped[str] = mapped_column(
        CHAR(36), ForeignKey("config_cuotas.id", ondelete="CASCADE"), nullable=False
    )
    alumno_id: Mapped[str] = mapped_column(
        CHAR(36), ForeignKey("alumnos.id", ondelete="CASCADE"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.utcnow())

    config_cuota: Mapped["ConfigCuota"] = relationship(back_populates="alumnos_especiales")
    alumno: Mapped["Alumno"] = relationship()


class PagoCuota(Base):
    __tablename__ = "pagos_cuotas"

    __table_args__ = (UniqueConstraint("alumno_id", "config_cuota_id", name="uq_pagos_cuotas_alumno_config"),)

    id: Mapped[str] = mapped_column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    alumno_id: Mapped[str] = mapped_column(CHAR(36), ForeignKey("alumnos.id", ondelete="CASCADE"), nullable=False)
    config_cuota_id: Mapped[str] = mapped_column(CHAR(36), ForeignKey("config_cuotas.id", ondelete="CASCADE"), nullable=False)
    movimiento_id: Mapped[str] = mapped_column(CHAR(36), ForeignKey("movimientos.id", ondelete="CASCADE"), nullable=False)
    fecha_pago: Mapped[date] = mapped_column(Date, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.utcnow())

    alumno: Mapped["Alumno"] = relationship(back_populates="pagos_cuota")
    config_cuota: Mapped["ConfigCuota"] = relationship(back_populates="pagos")
    movimiento: Mapped["Movimiento"] = relationship(back_populates="pagos_cuota")
    notificaciones: Mapped[list["NotificacionEmail"]] = relationship(
        back_populates="pago_cuota",
        cascade="all, delete-orphan",
    )


class NotificacionEmail(Base):
    """Registro de notificaciones enviadas a apoderados."""

    __tablename__ = "notificaciones_email"

    id: Mapped[str] = mapped_column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    pago_cuota_id: Mapped[str] = mapped_column(CHAR(36), ForeignKey("pagos_cuotas.id", ondelete="CASCADE"), nullable=True)
    tipo: Mapped[str] = mapped_column(String(20), nullable=False, default="pago")
    email_destinatario: Mapped[str] = mapped_column(String(255), nullable=False)
    alumno_nombre: Mapped[str] = mapped_column(String(255), nullable=True)
    asunto: Mapped[str] = mapped_column(String(255), nullable=False)
    mensaje: Mapped[str] = mapped_column(String(500), nullable=False)
    estado: Mapped[str] = mapped_column(String(50), nullable=False, default="simulado")
    error_detalle: Mapped[str] = mapped_column(Text, nullable=True)
    enviado_en: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.utcnow())

    pago_cuota: Mapped["PagoCuota"] = relationship(back_populates="notificaciones")
