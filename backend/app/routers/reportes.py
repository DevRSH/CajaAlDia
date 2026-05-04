"""Endpoints de reportes HTML imprimibles."""
import html
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import HTMLResponse
from sqlalchemy import extract, func, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Alumno, ConfigCuota, Curso, Movimiento, PagoCuota

router = APIRouter(prefix="/api", tags=["reportes"])


def _html_reporte_base(title: str, content: str) -> str:
    """Plantilla base para reportes HTML."""
    return f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="utf-8" />
  <title>{title}</title>
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
    .header {{
      display: flex;
      align-items: center;
      gap: 16px;
      margin-bottom: 32px;
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
    .subtitle {{ color: var(--muted); font-size: 0.85rem; margin: 0; }}
    table {{
      width: 100%;
      border-collapse: collapse;
      margin: 24px 0;
    }}
    th {{
      background: var(--bg);
      color: var(--primary);
      font-weight: 600;
      padding: 12px 8px;
      text-align: left;
      border-bottom: 2px solid var(--primary);
    }}
    td {{
      padding: 10px 8px;
      border-bottom: 1px solid #E5E7EB;
    }}
    .resumen {{
      background: var(--bg);
      padding: 16px;
      border-radius: 8px;
      margin: 24px 0;
    }}
    .resumen-item {{
      display: flex;
      justify-content: space-between;
      padding: 8px 0;
    }}
    .resumen-label {{ font-weight: 600; color: var(--muted); }}
    .resumen-value {{ font-weight: 700; }}
    .success {{ color: var(--success); }}
    .danger {{ color: var(--danger); }}
    .primary {{ color: var(--primary); }}
    .footer {{
      margin-top: 32px;
      padding-top: 16px;
      border-top: 1px solid #E5E7EB;
      text-align: center;
      font-size: 0.85rem;
      color: var(--muted);
    }}
    @media print {{
      body {{ background: white; padding: 0; }}
      .page {{ padding: 0; max-width: 100%; }}
      @page {{
        size: A4;
        margin: 15mm;
      }}
    }}
  </style>
</head>
<body>
  <div class="page">
    {content}
    <div class="footer">
      Generado por CajaAlDía — cajaaldia.cl
    </div>
  </div>
</body>
</html>
"""


@router.get("/reportes/balance", response_class=HTMLResponse)
def reporte_balance(
    curso_id: str = Query(..., description="UUID del curso"),
    mes: int = Query(..., ge=1, le=12, description="Mes"),
    anio: int = Query(..., ge=2000, le=2100, description="Año"),
    db: Session = Depends(get_db),
):
    """Reporte de balance mensual en HTML imprimible."""
    try:
        curso = db.execute(select(Curso).where(Curso.id == curso_id)).scalar_one_or_none()
        if curso is None:
            raise HTTPException(status_code=404, detail="No se encontró el curso indicado.")

        # Movimientos del mes
        movimientos = db.execute(
            select(Movimiento)
            .where(
                Movimiento.curso_id == curso_id,
                Movimiento.anulado == False,
                extract('month', Movimiento.fecha) == mes,
                extract('year', Movimiento.fecha) == anio,
            )
            .order_by(Movimiento.fecha.asc())
        ).scalars().all()

        ingresos = [m for m in movimientos if m.tipo == "ingreso"]
        egresos = [m for m in movimientos if m.tipo == "egreso"]

        total_ingresos = sum(m.monto for m in ingresos)
        total_egresos = sum(m.monto for m in egresos)
        saldo_periodo = total_ingresos - total_egresos

        # Saldo acumulado hasta fin del mes
        movimientos_acumulados = db.execute(
            select(Movimiento)
            .where(
                Movimiento.curso_id == curso_id,
                Movimiento.anulado.is_(False),
                Movimiento.fecha <= date(anio, mes, 28).replace(day=31),
            )
        ).scalars().all()
        
        saldo_acumulado = sum(m.monto if m.tipo == "ingreso" else -m.monto for m in movimientos_acumulados)

        nombre_mes = ["", "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
                      "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"][mes]

        def format_monto(n):
            return f"{n:,}".replace(",", ".")

        # Logo SVG
        logo_svg = """<svg width="40" height="40" viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">
            <rect width="48" height="48" rx="8" fill="#0D47A1"/>
            <path d="M12 24L20 32L36 16" stroke="#FFC107" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>"""

        # Tabla de ingresos
        filas_ingresos = "\n".join(
            f"<tr><td>{m.fecha}</td><td>{html.escape(m.descripcion)}</td><td>{html.escape(m.folio)}</td><td class='success'>${format_monto(m.monto)}</td></tr>"
            for m in ingresos
        ) or "<tr><td colspan='4' class='text-muted'>Sin ingresos</td></tr>"

        # Tabla de egresos
        filas_egresos = "\n".join(
            f"<tr><td>{m.fecha}</td><td>{html.escape(m.descripcion)}</td><td>{html.escape(m.folio)}</td><td class='danger'>${format_monto(m.monto)}</td></tr>"
            for m in egresos
        ) or "<tr><td colspan='4' class='text-muted'>Sin egresos</td></tr>"

        content = f"""
    <div class="header">
      <div class="logo">{logo_svg}</div>
      <div class="title">
        <h1>Balance Mensual</h1>
        <p class="subtitle">{html.escape(curso.nombre)} — {nombre_mes} {anio}</p>
      </div>
    </div>

    <h2>Ingresos</h2>
    <table>
      <thead>
        <tr><th>Fecha</th><th>Descripción</th><th>Folio</th><th>Monto</th></tr>
      </thead>
      <tbody>{filas_ingresos}</tbody>
    </table>

    <h2>Egresos</h2>
    <table>
      <thead>
        <tr><th>Fecha</th><th>Descripción</th><th>Folio</th><th>Monto</th></tr>
      </thead>
      <tbody>{filas_egresos}</tbody>
    </table>

    <div class="resumen">
      <div class="resumen-item">
        <span class="resumen-label">Total ingresos</span>
        <span class="resumen-value success">${format_monto(total_ingresos)}</span>
      </div>
      <div class="resumen-item">
        <span class="resumen-label">Total egresos</span>
        <span class="resumen-value danger">${format_monto(total_egresos)}</span>
      </div>
      <div class="resumen-item">
        <span class="resumen-label">Saldo del período</span>
        <span class="resumen-value primary">${format_monto(saldo_periodo)}</span>
      </div>
      <div class="resumen-item">
        <span class="resumen-label">Saldo acumulado</span>
        <span class="resumen-value primary">${format_monto(saldo_acumulado)}</span>
      </div>
    </div>
"""

        return HTMLResponse(content=_html_reporte_base(f"Balance {nombre_mes} {anio}", content))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al generar reporte de balance: {e!s}") from e


@router.get("/reportes/deudores", response_class=HTMLResponse)
def reporte_deudores(
    curso_id: str = Query(..., description="UUID del curso"),
    anio: int = Query(..., ge=2000, le=2100, description="Año"),
    db: Session = Depends(get_db),
):
    """Reporte de nómina de deudores en HTML imprimible."""
    try:
        curso = db.execute(select(Curso).where(Curso.id == curso_id)).scalar_one_or_none()
        if curso is None:
            raise HTTPException(status_code=404, detail="No se encontró el curso indicado.")

        # Obtener estado de cuotas
        configs = db.execute(
            select(ConfigCuota).where(
                ConfigCuota.curso_id == curso_id,
                ConfigCuota.año == anio,
            )
        ).scalars().all()

        alumnos = db.execute(
            select(Alumno)
            .where(Alumno.curso_id == curso_id, Alumno.activo.is_(True))
            .order_by(Alumno.apellido_paterno.asc())
        ).scalars().all()

        pagos = db.execute(
            select(PagoCuota)
            .join(ConfigCuota, PagoCuota.config_cuota_id == ConfigCuota.id)
            .where(ConfigCuota.curso_id == curso_id, ConfigCuota.año == anio)
        ).scalars().all()

        pagos_map = {(p.alumno_id, p.config_cuota_id): p for p in pagos}

        deudores = []
        total_adeudado = 0

        for alumno in alumnos:
            nombre_completo = f"{alumno.apellido_paterno} {alumno.apellido_materno or ''}, {alumno.nombre}".strip()
            meses_adeudados = []
            monto_adeudado = 0

            for config in configs:
                pago = pagos_map.get((alumno.id, config.id))
                if pago is None:
                    meses_adeudados.append(config.descripcion)
                    monto_adeudado += config.monto

            if meses_adeudados:
                deudores.append({
                    "nombre": nombre_completo,
                    "meses": ", ".join(meses_adeudados),
                    "monto": monto_adeudado,
                })
                total_adeudado += monto_adeudado

        def format_monto(n):
            return f"{n:,}".replace(",", ".")

        logo_svg = """<svg width="40" height="40" viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">
            <rect width="48" height="48" rx="8" fill="#0D47A1"/>
            <path d="M12 24L20 32L36 16" stroke="#FFC107" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>"""

        filas_deudores = "\n".join(
            f"<tr><td>{html.escape(d['nombre'])}</td><td>{html.escape(d['meses'])}</td><td class='danger'>${format_monto(d['monto'])}</td></tr>"
            for d in deudores
        ) or "<tr><td colspan='3' class='text-muted'>No hay deudores</td></tr>"

        content = f"""
    <div class="header">
      <div class="logo">{logo_svg}</div>
      <div class="title">
        <h1>Nómina de Deudores</h1>
        <p class="subtitle">{html.escape(curso.nombre)} — Año {anio}</p>
      </div>
    </div>

    <table>
      <thead>
        <tr><th>Alumno</th><th>Meses adeudados</th><th>Total adeudado</th></tr>
      </thead>
      <tbody>{filas_deudores}</tbody>
    </table>

    <div class="resumen">
      <div class="resumen-item">
        <span class="resumen-label">Total general adeudado</span>
        <span class="resumen-value danger">${format_monto(total_adeudado)}</span>
      </div>
    </div>
"""

        return HTMLResponse(content=_html_reporte_base(f"Deudores {anio}", content))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al generar reporte de deudores: {e!s}") from e


@router.get("/reportes/cuotas", response_class=HTMLResponse)
def reporte_cuotas(
    curso_id: str = Query(..., description="UUID del curso"),
    anio: int = Query(..., ge=2000, le=2100, description="Año"),
    db: Session = Depends(get_db),
):
    """Reporte de resumen de cuotas en HTML imprimible."""
    try:
        curso = db.execute(select(Curso).where(Curso.id == curso_id)).scalar_one_or_none()
        if curso is None:
            raise HTTPException(status_code=404, detail="No se encontró el curso indicado.")

        configs = db.execute(
            select(ConfigCuota)
            .where(ConfigCuota.curso_id == curso_id, ConfigCuota.año == anio)
            .order_by(ConfigCuota.mes.asc())
        ).scalars().all()

        alumnos = db.execute(
            select(Alumno)
            .where(Alumno.curso_id == curso_id, Alumno.activo.is_(True))
            .order_by(Alumno.apellido_paterno.asc())
        ).scalars().all()

        pagos = db.execute(
            select(PagoCuota)
            .join(ConfigCuota, PagoCuota.config_cuota_id == ConfigCuota.id)
            .where(ConfigCuota.curso_id == curso_id, ConfigCuota.año == anio)
        ).scalars().all()

        pagos_map = {(p.alumno_id, p.config_cuota_id): p for p in pagos}

        # Calcular estadísticas por mes
        meses_stats = []
        total_recaudado = 0
        total_esperado = 0

        for config in configs:
            pagados = sum(1 for p in pagos if p.config_cuota_id == config.id)
            total_alumnos = len(alumnos)
            porcentaje = (pagados / total_alumnos * 100) if total_alumnos > 0 else 0
            recaudado = sum(p.config_cuota.monto for p in pagos if p.config_cuota_id == config.id)
            esperado = config.monto * total_alumnos

            meses_stats.append({
                "mes": config.mes,
                "descripcion": config.descripcion,
                "pagados": pagados,
                "total": total_alumnos,
                "porcentaje": round(porcentaje, 1),
                "recaudado": recaudado,
                "esperado": esperado,
            })

            total_recaudado += recaudado
            total_esperado += esperado

        def format_monto(n):
            return f"{n:,}".replace(",", ".")

        logo_svg = """<svg width="40" height="40" viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">
            <rect width="48" height="48" rx="8" fill="#0D47A1"/>
            <path d="M12 24L20 32L36 16" stroke="#FFC107" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>"""

        filas_meses = "\n".join(
            f"<tr><td>{s['mes']}</td><td>{html.escape(s['descripcion'])}</td><td>{s['pagados']}/{s['total']}</td>"
            f"<td>{s['porcentaje']}%</td><td class='success'>${format_monto(s['recaudado'])}</td><td>${format_monto(s['esperado'])}</td></tr>"
            for s in meses_stats
        ) or "<tr><td colspan='6' class='text-muted'>Sin meses configurados</td></tr>"

        # Matriz simplificada
        filas_matriz = []
        for alumno in alumnos:
            nombre_completo = f"{alumno.apellido_paterno} {alumno.apellido_materno or ''}, {alumno.nombre}".strip()
            celdas = []
            for config in configs:
                pago = pagos_map.get((alumno.id, config.id))
                if pago:
                    celdas.append(f"<td class='success'>✓ {pago.fecha_pago}</td>")
                else:
                    celdas.append("<td class='danger'>-</td>")
            filas_matriz.append(f"<tr><td>{html.escape(nombre_completo)}</td>{''.join(celdas)}</tr>")

        matriz_html = ""
        if configs:
            header_meses = "".join(f"<th>{c.mes}</th>" for c in configs)
            matriz_html = f"""
    <h3>Matriz de Pagos</h3>
    <table>
      <thead>
        <tr><th>Alumno</th>{header_meses}</tr>
      </thead>
      <tbody>{''.join(filas_matriz)}</tbody>
    </table>
"""

        content = f"""
    <div class="header">
      <div class="logo">{logo_svg}</div>
      <div class="title">
        <h1>Resumen de Cuotas</h1>
        <p class="subtitle">{html.escape(curso.nombre)} — Año {anio}</p>
      </div>
    </div>

    <h2>Cobranza por Mes</h2>
    <table>
      <thead>
        <tr><th>Mes</th><th>Descripción</th><th>Pagados/Total</th><th>% Cobranza</th><th>Recaudado</th><th>Esperado</th></tr>
      </thead>
      <tbody>{filas_meses}</tbody>
    </table>

    {matriz_html}

    <div class="resumen">
      <div class="resumen-item">
        <span class="resumen-label">Total recaudado</span>
        <span class="resumen-value success">${format_monto(total_recaudado)}</span>
      </div>
      <div class="resumen-item">
        <span class="resumen-label">Total esperado</span>
        <span class="resumen-value primary">${format_monto(total_esperado)}</span>
      </div>
      <div class="resumen-item">
        <span class="resumen-label">% Cobranza global</span>
        <span class="resumen-value primary">{round(total_recaudado / total_esperado * 100, 1) if total_esperado > 0 else 0}%</span>
      </div>
    </div>
"""

        return HTMLResponse(content=_html_reporte_base(f"Cuotas {anio}", content))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al generar reporte de cuotas: {e!s}") from e
