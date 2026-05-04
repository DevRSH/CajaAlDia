"""Endpoints de movimientos y comprobante."""
import html
import uuid
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import HTMLResponse
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.folio_util import construir_folio
from app.models import Curso, FolioSecuencia, Movimiento
from app.schemas import MovimientoCrear, MovimientoResponse

router = APIRouter(prefix="/api", tags=["movimientos"])

MAX_FOLIO_RETRIES = 8
PAGE_SIZE = 20


@router.post("/movimientos", response_model=MovimientoResponse)
def crear_movimiento(
    body: MovimientoCrear,
    db: Session = Depends(get_db),
):
    try:
        curso = db.execute(select(Curso).where(Curso.id == body.curso_id)).scalar_one_or_none()
        if curso is None:
            raise HTTPException(status_code=404, detail="No se encontró el curso indicado.")

        fecha_mov = body.fecha if body.fecha is not None else date.today()
        año = fecha_mov.year

        # Asegurar fila de secuencia para (curso, año)
        seq_row = db.execute(
            select(FolioSecuencia).where(
                FolioSecuencia.curso_id == curso.id,
                FolioSecuencia.año == año,
            )
        ).scalar_one_or_none()
        if seq_row is None:
            seq_row = FolioSecuencia(
                id=str(uuid.uuid4()),
                curso_id=curso.id,
                año=año,
                ultimo_numero=0,
            )
            db.add(seq_row)
            db.flush()

        for _ in range(MAX_FOLIO_RETRIES):
            try:
                # Incremento atómico (compatible con concurrencia en SQLite)
                resultado = db.execute(
                    text(
                        "UPDATE folio_secuencia SET ultimo_numero = ultimo_numero + 1 "
                        "WHERE curso_id = :cid AND año = :anio RETURNING ultimo_numero"
                    ),
                    {"cid": curso.id, "anio": año},
                )
                secuencia = resultado.scalar_one()
                folio = construir_folio(año, curso.codigo, secuencia)

                mov = Movimiento(
                    id=str(uuid.uuid4()),
                    curso_id=curso.id,
                    tipo=body.tipo,
                    monto=int(body.monto),
                    descripcion=body.descripcion.strip(),
                    folio=folio,
                    fecha=fecha_mov,
                    anulado=False,
                )
                db.add(mov)
                db.commit()
                db.refresh(mov)
                return mov
            except IntegrityError:
                db.rollback()
                # Reabrir fila de secuencia tras rollback
                seq_row = db.execute(
                    select(FolioSecuencia).where(
                        FolioSecuencia.curso_id == curso.id,
                        FolioSecuencia.año == año,
                    )
                ).scalar_one_or_none()
                if seq_row is None:
                    seq_row = FolioSecuencia(
                        id=str(uuid.uuid4()),
                        curso_id=curso.id,
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
        try:
            db.rollback()
        except Exception:
            pass
        raise HTTPException(
            status_code=500,
            detail=f"Error al crear el movimiento: {e!s}",
        ) from e


@router.get("/movimientos", response_model=list[MovimientoResponse])
def listar_movimientos(
    curso_id: str = Query(..., description="UUID del curso"),
    page: int = Query(1, ge=1),
    db: Session = Depends(get_db),
) -> list[Movimiento]:
    try:
        curso = db.execute(select(Curso).where(Curso.id == curso_id)).scalar_one_or_none()
        if curso is None:
            raise HTTPException(status_code=404, detail="No se encontró el curso indicado.")

        offset = (page - 1) * PAGE_SIZE
        rows = db.execute(
            select(Movimiento)
            .where(
                Movimiento.curso_id == curso_id,
                Movimiento.anulado.is_(False),
            )
            .order_by(Movimiento.fecha.desc(), Movimiento.created_at.desc())
            .offset(offset)
            .limit(PAGE_SIZE)
        ).scalars().all()
        return list(rows)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al listar movimientos: {e!s}") from e


def _html_comprobante(mov: Movimiento, curso: Curso) -> str:
    safe_desc = html.escape(mov.descripcion)
    safe_folio = html.escape(mov.folio)
    safe_curso = html.escape(curso.nombre)
    safe_colegio = html.escape(curso.colegio)
    safe_codigo = html.escape(curso.codigo)
    tipo_txt = "Ingreso" if mov.tipo == "ingreso" else "Egreso"
    fecha_str = mov.fecha.isoformat()
    monto_str = f"{mov.monto:,}".replace(",", ".")
    
    # Logo SVG embebido
    logo_svg = """<svg width="48" height="48" viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">
        <rect width="48" height="48" rx="8" fill="#0D47A1"/>
        <path d="M12 24L20 32L36 16" stroke="#FFC107" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/>
        <text x="24" y="42" text-anchor="middle" fill="white" font-size="8" font-weight="bold">Caja</text>
    </svg>"""
    
    return f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="utf-8" />
  <title>Comprobante {safe_folio}</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
  <style>
    :root {{
      --primary: #0D47A1;
      --accent: #FFC107;
      --success: #16A34A;
      --danger: #DC2626;
      --text: #111827;
      --muted: #6B7280;
      --surface: #FFFFFF;
      --bg: #E3F2FD;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      font-family: 'Inter', system-ui, sans-serif;
      color: var(--text);
      background: var(--bg);
      margin: 0;
      padding: 24px;
    }}
    .page {{
      max-width: 210mm;
      margin: 0 auto;
      background: white;
      padding: 20mm;
    }}
    .comprobante {{
      border: 2px solid var(--primary);
      border-radius: 12px;
      padding: 32px;
      margin-bottom: 24px;
      background: var(--surface);
    }}
    .header {{
      display: flex;
      align-items: center;
      gap: 16px;
      margin-bottom: 24px;
      padding-bottom: 16px;
      border-bottom: 2px solid var(--primary);
    }}
    .logo {{ flex-shrink: 0; }}
    .title {{ flex: 1; }}
    h1 {{
      color: var(--primary);
      font-size: 1.5rem;
      margin: 0 0 4px 0;
      font-weight: 700;
    }}
    .tagline {{ color: var(--muted); font-size: 0.85rem; margin: 0; }}
    .folio {{
      font-family: 'Inter', monospace;
      background: var(--bg);
      border: 2px solid var(--primary);
      padding: 8px 16px;
      border-radius: 8px;
      display: inline-block;
      font-weight: 600;
      font-size: 0.9rem;
      color: var(--primary);
      margin-bottom: 24px;
    }}
    dl {{ margin: 24px 0; }}
    dt {{ color: var(--muted); font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.05em; margin-top: 16px; font-weight: 600; }}
    dd {{ margin: 4px 0 0 0; font-size: 1rem; font-weight: 500; }}
    .monto {{ font-size: 2rem; font-weight: 700; }}
    .ingreso {{ color: var(--success); }}
    .egreso {{ color: var(--danger); }}
    .registrado-por {{
      margin-top: 24px;
      padding-top: 16px;
      border-top: 1px solid #E5E7EB;
      font-size: 0.85rem;
      color: var(--muted);
    }}
    .qr-section {{
      margin-top: 24px;
      padding: 16px;
      background: var(--bg);
      border-radius: 8px;
      text-align: center;
    }}
    .qr-text {{
      font-size: 0.75rem;
      color: var(--muted);
      font-family: monospace;
    }}
    .copy-label {{
      text-align: center;
      font-size: 0.75rem;
      color: var(--muted);
      text-transform: uppercase;
      letter-spacing: 0.1em;
      margin-top: 8px;
    }}
    @media print {{
      body {{ background: white; padding: 0; }}
      .page {{ padding: 0; max-width: 100%; }}
      .comprobante {{ page-break-inside: avoid; border: 2px solid var(--primary); }}
      @page {{
        size: A4;
        margin: 15mm;
      }}
    }}
  </style>
</head>
<body>
  <div class="page">
    <!-- Copia para apoderado -->
    <div class="comprobante">
      <div class="header">
        <div class="logo">{logo_svg}</div>
        <div class="title">
          <h1>CajaAlDía</h1>
          <p class="tagline">La plata del curso, siempre a la vista.</p>
        </div>
      </div>
      <p class="folio">{safe_folio}</p>
      <dl>
        <dt>Curso</dt>
        <dd>{safe_curso}</dd>
        <dt>Colegio</dt>
        <dd>{safe_colegio}</dd>
        <dt>Fecha</dt>
        <dd>{fecha_str}</dd>
        <dt>Tipo</dt>
        <dd>{tipo_txt}</dd>
        <dt>Descripción</dt>
        <dd>{safe_desc}</dd>
        <dt>Monto (CLP)</dt>
        <dd class="monto {'ingreso' if mov.tipo == 'ingreso' else 'egreso'}">$ {monto_str}</dd>
      </dl>
      <div class="registrado-por">
        Registrado por: Tesorera del Curso
      </div>
      <div class="qr-section">
        <div class="qr-text">Verificar en: cajaaldia.cl/public/{safe_codigo}</div>
      </div>
      <div class="copy-label">Copia para apoderado</div>
    </div>

    <!-- Copia para archivo -->
    <div class="comprobante">
      <div class="header">
        <div class="logo">{logo_svg}</div>
        <div class="title">
          <h1>CajaAlDía</h1>
          <p class="tagline">La plata del curso, siempre a la vista.</p>
        </div>
      </div>
      <p class="folio">{safe_folio}</p>
      <dl>
        <dt>Curso</dt>
        <dd>{safe_curso}</dd>
        <dt>Colegio</dt>
        <dd>{safe_colegio}</dd>
        <dt>Fecha</dt>
        <dd>{fecha_str}</dd>
        <dt>Tipo</dt>
        <dd>{tipo_txt}</dd>
        <dt>Descripción</dt>
        <dd>{safe_desc}</dd>
        <dt>Monto (CLP)</dt>
        <dd class="monto {'ingreso' if mov.tipo == 'ingreso' else 'egreso'}">$ {monto_str}</dd>
      </dl>
      <div class="registrado-por">
        Registrado por: Tesorera del Curso
      </div>
      <div class="qr-section">
        <div class="qr-text">Verificar en: cajaaldia.cl/public/{safe_codigo}</div>
      </div>
      <div class="copy-label">Copia para archivo</div>
    </div>
  </div>
</body>
</html>
"""


@router.get("/movimientos/{movimiento_id}/comprobante", response_class=HTMLResponse)
def comprobante_movimiento(
    movimiento_id: str,
    db: Session = Depends(get_db),
) -> HTMLResponse:
    try:
        mov = db.execute(select(Movimiento).where(Movimiento.id == movimiento_id)).scalar_one_or_none()
        if mov is None or mov.anulado:
            raise HTTPException(status_code=404, detail="No se encontró el comprobante.")

        curso = db.execute(select(Curso).where(Curso.id == mov.curso_id)).scalar_one_or_none()
        if curso is None:
            raise HTTPException(status_code=404, detail="No se encontró el curso del movimiento.")

        html_body = _html_comprobante(mov, curso)
        return HTMLResponse(content=html_body)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al generar comprobante: {e!s}") from e
