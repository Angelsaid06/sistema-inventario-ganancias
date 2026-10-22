import sqlite3
from database import crear_tablas
from inventario import calcular_ganancia, registrar_compra, registrar_venta


def test_ganancia_refrescos():
    # Compro 24 a $240 (a $10 c/u), vendo 10 y cobro $150
    costo, ganancia = calcular_ganancia(24, 240, 10, 150)
    assert costo == 100
    assert ganancia == 50


def test_costo_promedio_con_dos_compras():
    # 10 piezas a $100 y 10 piezas a $140: costo promedio $12
    # Vendo 5 y cobro $100
    costo, ganancia = calcular_ganancia(20, 240, 5, 100)
    assert costo == 60
    assert ganancia == 40


def test_sin_compras_ni_ventas():
    costo, ganancia = calcular_ganancia(0, 0, 0, 0)
    assert costo == 0
    assert ganancia == 0

def preparar_base(tmp_path, monkeypatch):
    # Trabaja en una carpeta temporal para no tocar el inventario.db real
    monkeypatch.chdir(tmp_path)
    crear_tablas()
    conexion = sqlite3.connect("inventario.db")
    cursor = conexion.cursor()
    cursor.execute(
        "INSERT INTO productos (nombre, precio_venta, existencias) VALUES ('Refresco', 15, 0)"
    )
    conexion.commit()
    conexion.close()


def leer_existencias():
    conexion = sqlite3.connect("inventario.db")
    cursor = conexion.cursor()
    cursor.execute("SELECT existencias FROM productos WHERE id = 1")
    existencias = cursor.fetchone()[0]
    conexion.close()
    return existencias


def test_compra_suma_existencias(tmp_path, monkeypatch):
    preparar_base(tmp_path, monkeypatch)
    registrar_compra(1, 24, 240)
    assert leer_existencias() == 24


def test_venta_resta_existencias(tmp_path, monkeypatch):
    preparar_base(tmp_path, monkeypatch)
    registrar_compra(1, 24, 240)
    registrar_venta(1, 10)
    assert leer_existencias() == 14


def test_venta_sin_suficientes_piezas(tmp_path, monkeypatch):
    preparar_base(tmp_path, monkeypatch)
    registrar_compra(1, 5, 50)
    registrar_venta(1, 10)
    assert leer_existencias() == 5