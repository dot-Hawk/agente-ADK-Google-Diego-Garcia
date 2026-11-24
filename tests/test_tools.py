import pytest

from gastos_agent import tools


@pytest.fixture(autouse=True)
def archivo_temporal(tmp_path, monkeypatch):
    """Cada test usa su propio archivo de datos vacío."""
    monkeypatch.setattr(tools, "ARCHIVO_DATOS", tmp_path / "gastos.json")


# ---------- registrar_gasto ----------

def test_registrar_gasto_valido():
    r = tools.registrar_gasto("Supermercado", 1500, "comida", "2026-11-01")
    assert r["status"] == "ok"
    assert r["gasto"]["id"] == 1
    assert r["gasto"]["monto"] == 1500.0


def test_registrar_gasto_sin_fecha_usa_hoy():
    r = tools.registrar_gasto("Colectivo", 800, "transporte")
    assert r["status"] == "ok"
    assert len(r["gasto"]["fecha"]) == 10


@pytest.mark.parametrize("monto", [0, -10, "abc", None])
def test_registrar_gasto_monto_invalido(monto):
    r = tools.registrar_gasto("Algo", monto, "otros")
    assert r["status"] == "error"


def test_registrar_gasto_descripcion_vacia():
    assert tools.registrar_gasto("   ", 100, "otros")["status"] == "error"


def test_registrar_gasto_categoria_invalida():
    r = tools.registrar_gasto("Algo", 100, "viajes espaciales")
    assert r["status"] == "error"
    assert "comida" in r["mensaje"]


def test_registrar_gasto_fecha_invalida():
    assert tools.registrar_gasto("Algo", 100, "otros", "31/12/2026")["status"] == "error"


def test_categoria_no_distingue_mayusculas():
    assert tools.registrar_gasto("Pizza", 100, "  COMIDA ")["gasto"]["categoria"] == "comida"


# ---------- buscar_gastos ----------

def test_buscar_sin_datos_devuelve_sin_resultados():
    assert tools.buscar_gastos()["status"] == "sin_resultados"


def test_buscar_por_categoria_y_fechas():
    tools.registrar_gasto("Super", 1000, "comida", "2026-10-05")
    tools.registrar_gasto("Pizza", 500, "comida", "2026-11-05")
    tools.registrar_gasto("Nafta", 2000, "transporte", "2026-11-06")

    r = tools.buscar_gastos(categoria="comida", desde="2026-11-01")
    assert r["status"] == "ok"
    assert r["cantidad"] == 1
    assert r["gastos"][0]["descripcion"] == "Pizza"


def test_buscar_rango_invertido_es_error():
    r = tools.buscar_gastos(desde="2026-12-01", hasta="2026-01-01")
    assert r["status"] == "error"


def test_buscar_categoria_invalida_es_error():
    assert tools.buscar_gastos(categoria="xyz")["status"] == "error"


# ---------- resumen_gastos ----------

def test_resumen_del_mes():
    tools.registrar_gasto("Super", 1000, "comida", "2026-11-05")
    tools.registrar_gasto("Pizza", 500, "comida", "2026-11-10")
    tools.registrar_gasto("Nafta", 2000, "transporte", "2026-11-06")
    tools.registrar_gasto("Viejo", 9999, "otros", "2026-10-01")

    r = tools.resumen_gastos("2026-11")
    assert r["status"] == "ok"
    assert r["total"] == 3500.0
    assert r["por_categoria"] == {"comida": 1500.0, "transporte": 2000.0}
    assert r["mayor_gasto"]["descripcion"] == "Nafta"


def test_resumen_mes_invalido():
    assert tools.resumen_gastos("noviembre")["status"] == "error"


def test_resumen_sin_datos():
    assert tools.resumen_gastos("2026-11")["status"] == "sin_resultados"


# ---------- eliminar_gasto ----------

def test_eliminar_gasto_existente():
    tools.registrar_gasto("Super", 1000, "comida", "2026-11-05")
    assert tools.eliminar_gasto(1)["status"] == "ok"
    assert tools.buscar_gastos()["status"] == "sin_resultados"


def test_eliminar_gasto_inexistente():
    assert tools.eliminar_gasto(42)["status"] == "error"


def test_eliminar_id_invalido():
    assert tools.eliminar_gasto("uno")["status"] == "error"


# ---------- archivo corrupto ----------

def test_archivo_corrupto_no_rompe():
    tools.ARCHIVO_DATOS.write_text("esto no es json")
    assert tools.buscar_gastos()["status"] == "error"
