from inventario import calcular_ganancia


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