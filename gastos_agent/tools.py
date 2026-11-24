"""Herramientas del agente de gastos personales.

Cada herramienta devuelve un dict con la clave "status":
  - "ok"             -> la operación salió bien
  - "sin_resultados" -> la operación es válida pero no hay datos
  - "error"          -> argumentos inválidos o fallo interno (ver "mensaje")
"""

import json
from datetime import date, datetime
from pathlib import Path

ARCHIVO_DATOS = Path(__file__).parent / "gastos.json"

CATEGORIAS = ["comida", "transporte", "servicios", "salud", "ocio", "educacion", "otros"]


# ---------- helpers internos ----------

def _error(mensaje: str) -> dict:
    return {"status": "error", "mensaje": mensaje}


def _cargar() -> list:
    if not ARCHIVO_DATOS.exists():
        return []
    try:
        return json.loads(ARCHIVO_DATOS.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as e:
        raise RuntimeError(f"No se pudo leer el archivo de gastos: {e}")


def _guardar(gastos: list) -> None:
    ARCHIVO_DATOS.write_text(json.dumps(gastos, indent=2, ensure_ascii=False), encoding="utf-8")


def _validar_fecha(texto: str, formato: str = "%Y-%m-%d") -> bool:
    try:
        datetime.strptime(texto, formato)
        return True
    except (ValueError, TypeError):
        return False


def _normalizar_categoria(categoria: str) -> str:
    return (categoria or "").strip().lower()


# ---------- herramientas ----------

def registrar_gasto(descripcion: str, monto: float, categoria: str, fecha: str = "") -> dict:
    """Registra un nuevo gasto.

    Args:
        descripcion: Qué se compró o pagó (ej. "Supermercado").
        monto: Importe en pesos, mayor a 0.
        categoria: Una de: comida, transporte, servicios, salud, ocio, educacion, otros.
        fecha: Fecha en formato AAAA-MM-DD. Si se deja vacía se usa la fecha de hoy.

    Returns:
        dict con status y el gasto creado.
    """
    if not descripcion or not str(descripcion).strip():
        return _error("La descripción no puede estar vacía.")

    try:
        monto = float(monto)
    except (TypeError, ValueError):
        return _error(f"El monto '{monto}' no es un número válido.")
    if monto <= 0:
        return _error("El monto debe ser mayor a 0.")

    categoria = _normalizar_categoria(categoria)
    if categoria not in CATEGORIAS:
        return _error(f"Categoría inválida. Opciones: {', '.join(CATEGORIAS)}.")

    fecha = (fecha or "").strip() or date.today().isoformat()
    if not _validar_fecha(fecha):
        return _error("La fecha debe tener formato AAAA-MM-DD.")

    try:
        gastos = _cargar()
        nuevo = {
            "id": max((g["id"] for g in gastos), default=0) + 1,
            "descripcion": str(descripcion).strip(),
            "monto": round(monto, 2),
            "categoria": categoria,
            "fecha": fecha,
        }
        gastos.append(nuevo)
        _guardar(gastos)
    except RuntimeError as e:
        return _error(str(e))

    return {"status": "ok", "gasto": nuevo}


def buscar_gastos(categoria: str = "", desde: str = "", hasta: str = "") -> dict:
    """Busca gastos registrados, con filtros opcionales.

    Args:
        categoria: Filtra por categoría. Vacío = todas.
        desde: Fecha mínima AAAA-MM-DD (inclusive). Vacío = sin límite.
        hasta: Fecha máxima AAAA-MM-DD (inclusive). Vacío = sin límite.

    Returns:
        dict con status, cantidad y la lista de gastos encontrados.
    """
    categoria = _normalizar_categoria(categoria)
    if categoria and categoria not in CATEGORIAS:
        return _error(f"Categoría inválida. Opciones: {', '.join(CATEGORIAS)}.")
    for f in (desde, hasta):
        if f and not _validar_fecha(f):
            return _error(f"La fecha '{f}' debe tener formato AAAA-MM-DD.")
    if desde and hasta and desde > hasta:
        return _error("La fecha 'desde' no puede ser posterior a 'hasta'.")

    try:
        gastos = _cargar()
    except RuntimeError as e:
        return _error(str(e))

    encontrados = [
        g for g in gastos
        if (not categoria or g["categoria"] == categoria)
        and (not desde or g["fecha"] >= desde)
        and (not hasta or g["fecha"] <= hasta)
    ]
    if not encontrados:
        return {"status": "sin_resultados", "mensaje": "No se encontraron gastos con esos filtros."}

    return {"status": "ok", "cantidad": len(encontrados), "gastos": encontrados}


def resumen_gastos(mes: str = "") -> dict:
    """Calcula estadísticas de los gastos de un mes.

    Args:
        mes: Mes en formato AAAA-MM. Vacío = mes actual.

    Returns:
        dict con total, total por categoría, promedio y el mayor gasto del mes.
    """
    mes = (mes or "").strip() or date.today().strftime("%Y-%m")
    if not _validar_fecha(mes, "%Y-%m"):
        return _error("El mes debe tener formato AAAA-MM (ej. 2026-11).")

    try:
        gastos = [g for g in _cargar() if g["fecha"].startswith(mes)]
    except RuntimeError as e:
        return _error(str(e))

    if not gastos:
        return {"status": "sin_resultados", "mensaje": f"No hay gastos registrados en {mes}."}

    por_categoria: dict = {}
    for g in gastos:
        por_categoria[g["categoria"]] = round(por_categoria.get(g["categoria"], 0) + g["monto"], 2)

    total = round(sum(g["monto"] for g in gastos), 2)
    return {
        "status": "ok",
        "mes": mes,
        "total": total,
        "cantidad": len(gastos),
        "promedio": round(total / len(gastos), 2),
        "por_categoria": por_categoria,
        "mayor_gasto": max(gastos, key=lambda g: g["monto"]),
    }


def eliminar_gasto(id_gasto: int) -> dict:
    """Elimina un gasto por su ID.

    Args:
        id_gasto: ID numérico del gasto (se obtiene con buscar_gastos).

    Returns:
        dict con status y el gasto eliminado.
    """
    try:
        id_gasto = int(id_gasto)
    except (TypeError, ValueError):
        return _error(f"El ID '{id_gasto}' no es un número válido.")

    try:
        gastos = _cargar()
        restantes = [g for g in gastos if g["id"] != id_gasto]
        if len(restantes) == len(gastos):
            return _error(f"No existe un gasto con ID {id_gasto}.")
        _guardar(restantes)
    except RuntimeError as e:
        return _error(str(e))

    eliminado = next(g for g in gastos if g["id"] == id_gasto)
    return {"status": "ok", "eliminado": eliminado}
