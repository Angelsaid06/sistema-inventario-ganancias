import sqlite3

conexion = sqlite3.connect("inventario.db")
cursor = conexion.cursor()

productos = [
    ["Galletas", 20, 9, 28],
    ["Papitas 18gr", 10, 5, 12],
    ["Gansitos", 10, 6, 45],
    ["Barritas Marinela", 15, 7, 20],
    ["Chocolate Muibon", 10, 5.8, 40],
    ["Gomitas", 8, 3.5, 40],
    ["Mini brownies", 15, 10.6, 54],
    ["Papitas 40gr", 20, 11, 10],
    ["Cheetos 40gr", 15, 11, 0],
    ["Churrumais 36gr", 15, 11, 2],
    ["Cheetos Pop 36gr", 15, 11, 1],
]

for producto in productos:
    nombre = producto[0]
    precio = producto[1]
    costo = producto[2]
    piezas = producto[3]

    cursor.execute(
        "INSERT INTO productos (nombre, precio_venta, existencias) VALUES (?, ?, ?)",
        (nombre, precio, piezas)
    )

    # El id del producto que acabamos de insertar
    producto_id = cursor.lastrowid

    # Si hay piezas, registramos la compra con su costo total
    if piezas > 0:
        costo_total = costo * piezas
        cursor.execute(
            "INSERT INTO compras (producto_id, cantidad, costo_total, fecha) VALUES (?, ?, ?, ?)",
            (producto_id, piezas, costo_total, "2026-10-21")
        )

conexion.commit()
conexion.close()
print("Datos cargados")