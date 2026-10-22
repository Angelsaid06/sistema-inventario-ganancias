import sqlite3
from prediccion import ventas_por_dia, comparar_modelos

nombre_db = "demo.db"

conexion = sqlite3.connect(nombre_db)
cursor = conexion.cursor()
cursor.execute("SELECT id, nombre FROM productos")
productos = cursor.fetchall()
conexion.close()

for producto in productos:
    ventas = ventas_por_dia(nombre_db, producto[0])
    resultado = comparar_modelos(ventas)
    if resultado is None:
        print(producto[1], ": faltan datos (se necesitan al menos 30 dias)")
    else:
        print(producto[1], "| error promedio simple:", round(resultado[0], 2),
              "| error modelo:", round(resultado[1], 2))