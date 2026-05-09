"""Servicio de envío de emails con Resend."""
import logging
import os

logger = logging.getLogger(__name__)

RESEND_API_KEY = os.getenv("RESEND_API_KEY", "")
FRONTEND_URL = os.getenv("FRONTEND_URL", "https://cajaaldia.up.railway.app")

# Remitente: usar dominio propio si está configurado, de lo contrario onboarding@resend.dev
FROM_EMAIL = os.getenv("EMAIL_FROM", "CajaAlDía <onboarding@resend.dev>")

# Colores del branding
COLOR_AZUL = "#0D47A1"
COLOR_AMARILLO = "#FFC107"
COLOR_VERDE = "#16A34A"
COLOR_ROJO = "#DC2626"
COLOR_GRIS = "#6B7280"


def _html_comprobante(
    destinatario_nombre: str,
    alumno_nombre: str,
    mes_año: str,
    monto: int,
    folio: str,
    verification_url: str,
) -> str:
    """Genera el HTML del comprobante de pago."""
    monto_fmt = f"${monto:,}".replace(",", ".")
    return f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Comprobante de pago - {mes_año}</title>
</head>
<body style="margin:0;padding:0;background-color:#E3F2FD;font-family:Arial,Helvetica,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background-color:#E3F2FD;padding:32px 16px;">
    <tr>
      <td align="center">
        <table width="600" cellpadding="0" cellspacing="0" style="max-width:600px;width:100%;background:#ffffff;border-radius:12px;overflow:hidden;box-shadow:0 4px 16px rgba(0,0,0,0.08);">
          <!-- Cabecera -->
          <tr>
            <td style="background-color:{COLOR_AZUL};padding:24px 32px;text-align:center;">
              <div style="font-size:28px;font-weight:700;color:#ffffff;letter-spacing:-0.5px;">
                Caja<span style="color:{COLOR_AMARILLO};">AlDía</span>
              </div>
              <div style="font-size:13px;color:rgba(255,255,255,0.8);margin-top:4px;">
                La plata del curso, siempre a la vista.
              </div>
            </td>
          </tr>
          <!-- Cuerpo -->
          <tr>
            <td style="padding:32px;">
              <!-- Saludo -->
              <p style="margin:0 0 8px 0;font-size:16px;color:#111827;">
                Estimado/a <strong>{destinatario_nombre}</strong>,
              </p>
              <p style="margin:0 0 24px 0;font-size:15px;color:#374151;">
                Se ha registrado el siguiente pago de cuota escolar:
              </p>
              <!-- Folio destacado -->
              <div style="background-color:#E3F2FD;border:2px solid {COLOR_AZUL};border-radius:8px;padding:12px 20px;margin-bottom:24px;text-align:center;">
                <div style="font-size:11px;color:{COLOR_GRIS};text-transform:uppercase;letter-spacing:0.08em;margin-bottom:4px;">Folio</div>
                <div style="font-family:monospace;font-size:20px;font-weight:700;color:{COLOR_AZUL};">{folio}</div>
              </div>
              <!-- Tabla de datos -->
              <table width="100%" cellpadding="0" cellspacing="0" style="border-collapse:collapse;margin-bottom:24px;">
                <tr style="border-bottom:1px solid #E5E7EB;">
                  <td style="padding:12px 0;font-size:13px;color:{COLOR_GRIS};width:40%;">Alumno/a</td>
                  <td style="padding:12px 0;font-size:14px;font-weight:600;color:#111827;">{alumno_nombre}</td>
                </tr>
                <tr style="border-bottom:1px solid #E5E7EB;">
                  <td style="padding:12px 0;font-size:13px;color:{COLOR_GRIS};">Período</td>
                  <td style="padding:12px 0;font-size:14px;font-weight:600;color:#111827;">{mes_año}</td>
                </tr>
                <tr>
                  <td style="padding:12px 0;font-size:13px;color:{COLOR_GRIS};">Monto pagado</td>
                  <td style="padding:12px 0;font-size:22px;font-weight:700;color:{COLOR_VERDE};">{monto_fmt}</td>
                </tr>
              </table>
              <!-- Link verificación -->
              <div style="background-color:#F0FDF4;border:1px solid #BBF7D0;border-radius:8px;padding:16px;margin-bottom:24px;">
                <p style="margin:0 0 8px 0;font-size:13px;color:#166534;font-weight:600;">✓ Comprobante verificable</p>
                <p style="margin:0 0 8px 0;font-size:13px;color:#15803D;">
                  Puedes verificar este pago en el panel público del curso:
                </p>
                <a href="{verification_url}" style="display:inline-block;color:{COLOR_AZUL};font-size:13px;word-break:break-all;">{verification_url}</a>
              </div>
            </td>
          </tr>
          <!-- Pie -->
          <tr>
            <td style="background-color:#F9FAFB;border-top:1px solid #E5E7EB;padding:20px 32px;text-align:center;">
              <p style="margin:0;font-size:12px;color:{COLOR_GRIS};">
                Este es un correo automático de CajaAlDía. Por favor no respondas a este mensaje.
              </p>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""


def _html_deuda(
    destinatario_nombre: str,
    alumno_nombre: str,
    meses_pendientes: int,
    monto_total: int,
    curso_nombre: str,
    panel_url: str,
) -> str:
    """Genera el HTML de notificación de deuda."""
    monto_fmt = f"${monto_total:,}".replace(",", ".")
    meses_txt = "mes pendiente" if meses_pendientes == 1 else "meses pendientes"
    return f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Estado de cuenta - {curso_nombre}</title>
</head>
<body style="margin:0;padding:0;background-color:#E3F2FD;font-family:Arial,Helvetica,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background-color:#E3F2FD;padding:32px 16px;">
    <tr>
      <td align="center">
        <table width="600" cellpadding="0" cellspacing="0" style="max-width:600px;width:100%;background:#ffffff;border-radius:12px;overflow:hidden;box-shadow:0 4px 16px rgba(0,0,0,0.08);">
          <!-- Cabecera -->
          <tr>
            <td style="background-color:{COLOR_AZUL};padding:24px 32px;text-align:center;">
              <div style="font-size:28px;font-weight:700;color:#ffffff;letter-spacing:-0.5px;">
                Caja<span style="color:{COLOR_AMARILLO};">AlDía</span>
              </div>
              <div style="font-size:13px;color:rgba(255,255,255,0.8);margin-top:4px;">
                Estado de cuenta — {curso_nombre}
              </div>
            </td>
          </tr>
          <!-- Cuerpo -->
          <tr>
            <td style="padding:32px;">
              <p style="margin:0 0 8px 0;font-size:16px;color:#111827;">
                Estimado/a <strong>{destinatario_nombre}</strong>,
              </p>
              <p style="margin:0 0 24px 0;font-size:15px;color:#374151;">
                Le informamos que <strong>{alumno_nombre}</strong> tiene cuotas pendientes de pago.
              </p>
              <!-- Alerta de deuda -->
              <div style="background-color:#FEF2F2;border:2px solid #FECACA;border-radius:8px;padding:20px;margin-bottom:24px;text-align:center;">
                <div style="font-size:13px;color:#991B1B;margin-bottom:8px;font-weight:600;">Deuda pendiente</div>
                <div style="font-size:36px;font-weight:700;color:{COLOR_ROJO};">{monto_fmt}</div>
                <div style="font-size:13px;color:#B91C1C;margin-top:4px;">{meses_pendientes} {meses_txt}</div>
              </div>
              <p style="margin:0 0 16px 0;font-size:14px;color:#374151;">
                Por favor regularice su situación a la brevedad para evitar problemas con la gestión del curso.
              </p>
              <!-- Link panel público -->
              <div style="text-align:center;margin-bottom:24px;">
                <a href="{panel_url}" style="display:inline-block;background-color:{COLOR_AZUL};color:#ffffff;text-decoration:none;padding:12px 28px;border-radius:8px;font-size:14px;font-weight:600;">
                  Ver estado en panel público
                </a>
              </div>
            </td>
          </tr>
          <!-- Pie -->
          <tr>
            <td style="background-color:#F9FAFB;border-top:1px solid #E5E7EB;padding:20px 32px;text-align:center;">
              <p style="margin:0;font-size:12px;color:{COLOR_GRIS};">
                Este es un correo automático de CajaAlDía. Por favor no respondas a este mensaje.
              </p>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""


def enviar_comprobante_pago(
    destinatario_email: str,
    destinatario_nombre: str,
    alumno_nombre: str,
    mes_año: str,
    monto: int,
    folio: str,
    verification_url: str,
) -> bool:
    """Envía comprobante de pago. Retorna True si fue exitoso, False si falló.
    Nunca lanza excepción — el pago ya fue registrado, el email es secundario.
    """
    if not RESEND_API_KEY:
        logger.warning("RESEND_API_KEY no configurada. Email simulado para %s", destinatario_email)
        return False

    try:
        import resend
        resend.api_key = RESEND_API_KEY
        resend.Emails.send({
            "from": FROM_EMAIL,
            "to": [destinatario_email],
            "subject": f"Comprobante de pago - {mes_año}",
            "html": _html_comprobante(
                destinatario_nombre, alumno_nombre, mes_año, monto, folio, verification_url
            ),
        })
        logger.info("Comprobante enviado a %s folio=%s", destinatario_email, folio)
        return True
    except Exception as exc:
        logger.error("Error al enviar comprobante a %s: %s", destinatario_email, exc)
        return False


def enviar_notificacion_deuda(
    destinatario_email: str,
    destinatario_nombre: str,
    alumno_nombre: str,
    meses_pendientes: int,
    monto_total: int,
    curso_nombre: str,
    panel_url: str,
) -> bool:
    """Envía notificación de deuda. Retorna True si fue exitoso, False si falló."""
    if not RESEND_API_KEY:
        logger.warning("RESEND_API_KEY no configurada. Email deuda simulado para %s", destinatario_email)
        return False

    try:
        import resend
        resend.api_key = RESEND_API_KEY
        resend.Emails.send({
            "from": FROM_EMAIL,
            "to": [destinatario_email],
            "subject": f"Estado de cuenta - {curso_nombre}",
            "html": _html_deuda(
                destinatario_nombre, alumno_nombre, meses_pendientes, monto_total, curso_nombre, panel_url
            ),
        })
        logger.info("Notificación deuda enviada a %s", destinatario_email)
        return True
    except Exception as exc:
        logger.error("Error al enviar deuda a %s: %s", destinatario_email, exc)
        return False
