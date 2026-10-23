import sqlite3
from database import crear_tablas
from inventario import calcular_ganancia, registrar_compra, registrar_venta
from prediccion import promedio_movil, dias_restantes, sugerir_reabasto
from prediccion import comparar_modelos
from asistente import ver_inventario, ejecutar_herramienta
from datetime import date, timedelta
from asistente import guardar_recomendacion, evaluar_recomendaciones, resumen_evaluacion
from inventario import resumen_ganancias
from inventario import cancelar_venta, ultimas_ventas



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

def test_promedio_movil():
    assert promedio_movil([2, 4, 6], 7) == 4


def test_dias_restantes():
    assert dias_restantes(10, 2) == 5
    assert dias_restantes(10, 0) is None


def test_sugerir_reabasto():
    assert sugerir_reabasto(5, 2, 7) == 9
    assert sugerir_reabasto(50, 2, 7) == 0

def test_comparar_modelos_con_pocos_datos():
    assert comparar_modelos([1, 2, 3]) is None

def test_compra_con_cantidad_negativa_no_cambia_nada(tmp_path, monkeypatch):
    preparar_base(tmp_path, monkeypatch)
    registrar_compra(1, -5, 50)
    assert leer_existencias() == 0


def test_compra_de_producto_que_no_existe(tmp_path, monkeypatch):
    preparar_base(tmp_path, monkeypatch)
    registrar_compra(99, 5, 50)
    assert leer_existencias() == 0


def test_venta_con_cantidad_cero(tmp_path, monkeypatch):
    preparar_base(tmp_path, monkeypatch)
    registrar_compra(1, 5, 50)
    registrar_venta(1, 0)
    assert leer_existencias() == 5

def test_ver_inventario_calcula_costo_promedio(tmp_path, monkeypatch):
    preparar_base(tmp_path, monkeypatch)
    registrar_compra(1, 10, 100)
    inventario = ver_inventario("inventario.db")
    assert inventario[0]["existencias"] == 10
    assert inventario[0]["costo_promedio"] == 10


def test_herramienta_desconocida():
    resultado = ejecutar_herramienta("no_existe", {}, "inventario.db")
    assert "error" in resultado


def test_recomendacion_de_hoy_esta_pendiente(tmp_path, monkeypatch):
    preparar_base(tmp_path, monkeypatch)
    registrar_compra(1, 10, 100)
    guardar_recomendacion("inventario.db", 1, 5)
    evaluadas, pendientes = evaluar_recomendaciones("inventario.db", 7)
    assert pendientes == 1
    assert evaluadas == []


def test_evaluar_con_ventas_posteriores(tmp_path, monkeypatch):
    preparar_base(tmp_path, monkeypatch)
    registrar_compra(1, 10, 100)
    guardar_recomendacion("inventario.db", 1, 5)

    manana = str(date.today() + timedelta(days=1))
    conexion = sqlite3.connect("inventario.db")
    conexion.execute(
        "INSERT INTO ventas (producto_id, cantidad, precio_unitario, fecha) VALUES (1, 12, 15, ?)",
        (manana,)
    )
    conexion.commit()
    conexion.close()

    en_diez_dias = date.today() + timedelta(days=10)
    evaluadas, pendientes = evaluar_recomendaciones("inventario.db", 7, en_diez_dias)
    assert evaluadas[0]["vendido_en_7_dias"] == 12
    assert evaluadas[0]["error_asistente"] == 3
    assert evaluadas[0]["alcanzo"] is True


def test_resumen_sin_datos():
    assert resumen_evaluacion([]) is None

def test_resumen_ganancias(tmp_path, monkeypatch):
    preparar_base(tmp_path, monkeypatch)
    registrar_compra(1, 24, 240)
    registrar_venta(1, 10)
    resumen = resumen_ganancias()
    assert resumen["ingresos"] == 150
    assert resumen["costos"] == 100
    assert resumen["ganancia_neta"] == 50

def test_cancelar_venta_regresa_las_piezas(tmp_path, monkeypatch):
    preparar_base(tmp_path, monkeypatch)
    registrar_compra(1, 10, 100)
    registrar_venta(1, 3)
    assert leer_existencias() == 7

    venta_id = ultimas_ventas(1)[0][0]
    assert cancelar_venta(venta_id) is True
    assert leer_existencias() == 10
    assert ultimas_ventas(1) == []


def test_cancelar_venta_que_no_existe(tmp_path, monkeypatch):
    preparar_base(tmp_path, monkeypatch)
    assert cancelar_venta(99) is False