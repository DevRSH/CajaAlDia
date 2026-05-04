"""Construcción del folio según reglas de negocio."""


def segmento_codigo_para_folio(codigo_curso: str, año_movimiento: int) -> str:
    """
    Si el código termina en -{año} (ej. 4BA-2026 con año 2026), se usa la parte previa
    para coincidir con folios del tipo CAD-2026-4BA-0001.
    """
    suffix = f"-{año_movimiento}"
    if codigo_curso.endswith(suffix):
        return codigo_curso[: -len(suffix)]
    return codigo_curso


def construir_folio(año: int, codigo_curso: str, secuencia: int) -> str:
    """Formato: CAD-{año}-{segmento}-{secuencia:04d}."""
    mid = segmento_codigo_para_folio(codigo_curso, año)
    return f"CAD-{año}-{mid}-{secuencia:04d}"
