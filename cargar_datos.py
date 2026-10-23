import sqlite3


def cargar_ejemplo(nombre_db="inventario.db"):
    conexion = sqlite3.connect(nombre_db)
    cursor = conexion.cursor()

    # nombre, precio de venta, costo por pieza, piezas en inventario
    productos = [
        ["Galletas", 15, 8, 20],
        ["Papitas", 12, 7, 15],
        ["Chocolate", 10, 6, 25],
        ["Gomitas", 8, 4, 30],
        ["Refresco", 18, 11, 12],
    ]

    for producto in productos:
        cursor.execute(
            "INSERT INTO productos (nombre, precio_venta, existencias) VALUES (?, ?, ?)",
            (producto[0], producto[1], producto[3])
        )
        producto_id = cursor.lastrowid
        cursor.execute(
            "INSERT INTO compras (producto_id, cantidad, costo_total, fecha) VALUES (?, ?, ?, date('now'))",
            (producto_id, producto[3], producto[2] * producto[3])
        )

    conexion.commit()
    conexion.close()


if __name__ == "__main__":
    cargar_ejemplo()
    print("Datos cargados")