import sqlite3
from datetime import date


def agregar_producto(nombre, precio_venta):
    if nombre.strip() == "" or precio_venta <= 0:
        print("Nombre o precio invalido")
        return
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
    if cantidad <= 0 or costo_total < 0:
        print("Cantidad o costo invalido")
        return
    conexion = sqlite3.connect("inventario.db")
    cursor = conexion.cursor()
    cursor.execute("SELECT id FROM productos WHERE id = ?", (producto_id,))
    if cursor.fetchone() is None:
        print("Ese producto no existe")
        conexion.close()
        return
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
    if cantidad <= 0:
        print("La cantidad debe ser mayor a 0")
        return
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
def calcular_ganancia(piezas_compradas, costo_compras, piezas_vendidas, ingresos):
    if piezas_compradas > 0:
        costo_promedio = costo_compras / piezas_compradas
    else:
        costo_promedio = 0

    costo_vendido = costo_promedio * piezas_vendidas
    ganancia = ingresos - costo_vendido
    return costo_vendido, ganancia


def registrar_gasto(descripcion, monto):
    if descripcion.strip() == "" or monto <= 0:
        print("Descripcion o monto invalido")
        return
    conexion = sqlite3.connect("inventario.db")
    cursor = conexion.cursor()
    cursor.execute(
        "INSERT INTO gastos (descripcion, monto, fecha) VALUES (?, ?, ?)",
        (descripcion, monto, str(date.today()))
    )
    conexion.commit()
    conexion.close()
    print("Gasto registrado")
def pedir_entero(texto):
    while True:
        try:
            return int(input(texto))
        except ValueError:
            print("Escribe un numero entero")


def pedir_decimal(texto):
    while True:
        try:
            return float(input(texto))
        except ValueError:
            print("Escribe un numero valido")

def listar_productos(nombre_db="inventario.db"):
    conexion = sqlite3.connect(nombre_db)
    cursor = conexion.cursor()
    cursor.execute("SELECT id, nombre, precio_venta, existencias FROM productos")
    filas = cursor.fetchall()
    conexion.close()
    return filas


def ver_productos():
    print("")
    for fila in listar_productos():
        print(fila[0], "-", fila[1], "| precio:", fila[2], "| existencias:", fila[3])
    print("")


def resumen_ganancias(nombre_db="inventario.db"):
    conexion = sqlite3.connect(nombre_db)
    cursor = conexion.cursor()

    cursor.execute("SELECT id, nombre FROM productos")
    productos = cursor.fetchall()

    filas = []
    total_ingresos = 0
    total_costos = 0

    for producto in productos:
        cursor.execute(
            "SELECT SUM(cantidad), SUM(costo_total) FROM compras WHERE producto_id = ?",
            (producto[0],)
        )
        compras = cursor.fetchone()
        cursor.execute(
            "SELECT SUM(cantidad), SUM(cantidad * precio_unitario) FROM ventas WHERE producto_id = ?",
            (producto[0],)
        )
        ventas = cursor.fetchone()

        piezas_compradas = compras[0]
        costo_compras = compras[1]
        piezas_vendidas = ventas[0]
        ingresos = ventas[1]

        if piezas_compradas is None:
            piezas_compradas = 0
            costo_compras = 0
        if piezas_vendidas is None:
            piezas_vendidas = 0
            ingresos = 0

        costo_vendido, ganancia = calcular_ganancia(
            piezas_compradas, costo_compras, piezas_vendidas, ingresos
        )

        if piezas_vendidas > 0:
            filas.append({
                "producto": producto[1],
                "vendidas": piezas_vendidas,
                "ingresos": round(ingresos, 2),
                "costo": round(costo_vendido, 2),
                "ganancia": round(ganancia, 2),
            })

        total_ingresos = total_ingresos + ingresos
        total_costos = total_costos + costo_vendido

    cursor.execute("SELECT SUM(monto) FROM gastos")
    total_gastos = cursor.fetchone()[0]
    if total_gastos is None:
        total_gastos = 0

    conexion.close()

    return {
        "filas": filas,
        "ingresos": total_ingresos,
        "costos": total_costos,
        "gastos": total_gastos,
        "ganancia_ventas": total_ingresos - total_costos,
        "ganancia_neta": total_ingresos - total_costos - total_gastos,
    }


def reporte_ganancias():
    resumen = resumen_ganancias()
    print("")
    for fila in resumen["filas"]:
        print(fila["producto"], "| vendidas:", fila["vendidas"], "| ingresos:", fila["ingresos"],
              "| costo:", fila["costo"], "| ganancia:", fila["ganancia"])
    print("")
    print("TOTAL ingresos:", round(resumen["ingresos"], 2))
    print("TOTAL costos:", round(resumen["costos"], 2))
    print("Ganancia de ventas:", round(resumen["ganancia_ventas"], 2))
    print("Gastos extra:", round(resumen["gastos"], 2))
    print("GANANCIA NETA:", round(resumen["ganancia_neta"], 2))
    print("")

def ultimas_ventas(limite=10, nombre_db="inventario.db"):
    conexion = sqlite3.connect(nombre_db)
    cursor = conexion.cursor()
    cursor.execute(
        "SELECT ventas.id, productos.nombre, ventas.cantidad, ventas.precio_unitario, ventas.fecha "
        "FROM ventas JOIN productos ON ventas.producto_id = productos.id "
        "ORDER BY ventas.id DESC LIMIT ?",
        (limite,)
    )
    filas = cursor.fetchall()
    conexion.close()
    return filas


def cancelar_venta(venta_id, nombre_db="inventario.db"):
    conexion = sqlite3.connect(nombre_db)
    cursor = conexion.cursor()

    cursor.execute("SELECT producto_id, cantidad FROM ventas WHERE id = ?", (venta_id,))
    venta = cursor.fetchone()
    if venta is None:
        conexion.close()
        print("Esa venta no existe")
        return False

    # Regresamos las piezas al inventario y borramos la venta
    cursor.execute(
        "UPDATE productos SET existencias = existencias + ? WHERE id = ?",
        (venta[1], venta[0])
    )
    cursor.execute("DELETE FROM ventas WHERE id = ?", (venta_id,))
    conexion.commit()
    conexion.close()
    print("Venta cancelada")
    return True
def menu():
    opcion = ""
    while opcion != "7":
        print("1. Ver productos")
        print("2. Agregar producto")
        print("3. Registrar compra")
        print("4. Registrar venta")
        print("5. Reporte de ganancias")
        print("6. Registrar gasto")
        print("7. Salir")
        opcion = input("Elige una opcion: ")

        if opcion == "1":
            ver_productos()
        elif opcion == "2":
            nombre = input("Nombre: ")
            precio = pedir_decimal("Precio de venta: ")
            agregar_producto(nombre, precio)
        elif opcion == "3":
            ver_productos()
            producto_id = pedir_entero("ID del producto: ")
            cantidad = pedir_entero("Cantidad comprada: ")
            costo_total = pedir_decimal("Costo total: ")
            registrar_compra(producto_id, cantidad, costo_total)
        elif opcion == "4":
            ver_productos()
            producto_id = pedir_entero("ID del producto: ")
            cantidad = pedir_entero("Cantidad vendida: ")
            registrar_venta(producto_id, cantidad)
        elif opcion == "5":
            reporte_ganancias()
        elif opcion == "6":
            descripcion = input("Descripcion del gasto: ")
            monto = pedir_decimal("Monto: ")
            registrar_gasto(descripcion, monto)


if __name__ == "__main__":
    menu()