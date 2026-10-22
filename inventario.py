import sqlite3
from datetime import date


def ver_productos():
    conexion = sqlite3.connect("inventario.db")
    cursor = conexion.cursor()
    cursor.execute("SELECT id, nombre, precio_venta, existencias FROM productos")
    filas = cursor.fetchall()
    conexion.close()

    print("")
    for fila in filas:
        print(fila[0], "-", fila[1], "| precio:", fila[2], "| existencias:", fila[3])
    print("")


def agregar_producto(nombre, precio_venta):
    conexion = sqlite3.connect("inventario.db")
    cursor = conexion.cursor()
    cursor.execute(
        "INSERT INTO productos (nombre, precio_venta, existencias) VALUES (?, ?, 0)",
        (nombre, precio_venta)
    )
    conexion.commit()
    conexion.close()
    print("Producto agregado")


def registrar_compra(producto_id, cantidad, costo_total):
    conexion = sqlite3.connect("inventario.db")
    cursor = conexion.cursor()
    cursor.execute(
        "INSERT INTO compras (producto_id, cantidad, costo_total, fecha) VALUES (?, ?, ?, ?)",
        (producto_id, cantidad, costo_total, str(date.today()))
    )
    cursor.execute(
        "UPDATE productos SET existencias = existencias + ? WHERE id = ?",
        (cantidad, producto_id)
    )
    conexion.commit()
    conexion.close()
    print("Compra registrada")


def registrar_venta(producto_id, cantidad):
    conexion = sqlite3.connect("inventario.db")
    cursor = conexion.cursor()

    cursor.execute(
        "SELECT precio_venta, existencias FROM productos WHERE id = ?",
        (producto_id,)
    )
    resultado = cursor.fetchone()

    if resultado is None:
        print("Ese producto no existe")
    elif resultado[1] < cantidad:
        print("No hay suficientes piezas, solo quedan", resultado[1])
    else:
        precio = resultado[0]
        cursor.execute(
            "INSERT INTO ventas (producto_id, cantidad, precio_unitario, fecha) VALUES (?, ?, ?, ?)",
            (producto_id, cantidad, precio, str(date.today()))
        )
        cursor.execute(
            "UPDATE productos SET existencias = existencias - ? WHERE id = ?",
            (cantidad, producto_id)
        )
        conexion.commit()
        print("Venta registrada")

    conexion.close()


def menu():
    opcion = ""
    while opcion != "5":
        print("1. Ver productos")
        print("2. Agregar producto")
        print("3. Registrar compra")
        print("4. Registrar venta")
        print("5. Salir")
        opcion = input("Elige una opcion: ")

        if opcion == "1":
            ver_productos()
        elif opcion == "2":
            nombre = input("Nombre: ")
            precio = float(input("Precio de venta: "))
            agregar_producto(nombre, precio)
        elif opcion == "3":
            ver_productos()
            producto_id = int(input("ID del producto: "))
            cantidad = int(input("Cantidad comprada: "))
            costo_total = float(input("Costo total: "))
            registrar_compra(producto_id, cantidad, costo_total)
        elif opcion == "4":
            ver_productos()
            producto_id = int(input("ID del producto: "))
            cantidad = int(input("Cantidad vendida: "))
            registrar_venta(producto_id, cantidad)


menu()