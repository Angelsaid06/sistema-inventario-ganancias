import os
import random
import sqlite3
from datetime import date, timedelta
from database import crear_tablas

NOMBRE_DB = "demo.db"

if os.path.exists(NOMBRE_DB):
    os.remove(NOMBRE_DB)
crear_tablas(NOMBRE_DB)

random.seed(1)
conexion = sqlite3.connect(NOMBRE_DB)
cursor = conexion.cursor()

# nombre, precio de venta, costo, ventas promedio por dia entre semana, piezas que quedan
productos = [
    ["Gansitos", 10, 6, 5, 12],
    ["Galletas", 20, 9, 3, 4],
    ["Gomitas", 8, 3.5, 6, 30],
]

dias = 60
hoy = date.today()

for producto in productos:
    nombre = producto[0]
    precio = producto[1]
    costo = producto[2]
    media = producto[3]
    restante = producto[4]

    cursor.execute(
        "INSERT INTO productos (nombre, precio_venta, existencias) VALUES (?, ?, ?)",
        (nombre, precio, restante)
    )
    producto_id = cursor.lastrowid

    total_vendido = 0
    for atras in range(dias, 0, -1):
        fecha = hoy - timedelta(days=atras - 1)
        # Sabado y domingo no hay clases: casi no se vende
        if fecha.weekday() >= 5:
            base = 1
        else:
            base = media
        cantidad = random.randint(max(0, base - 2), base + 2)
        if cantidad > 0:
            cursor.execute(
                "INSERT INTO ventas (producto_id, cantidad, precio_unitario, fecha) VALUES (?, ?, ?, ?)",
                (producto_id, cantidad, precio, str(fecha))
            )
            total_vendido = total_vendido + cantidad

    comprada = total_vendido + restante
    cursor.execute(
        "INSERT INTO compras (producto_id, cantidad, costo_total, fecha) VALUES (?, ?, ?, ?)",
        (producto_id, comprada, costo * comprada, str(hoy - timedelta(days=dias)))
    )

conexion.commit()
conexion.close()
print("Base de demo creada: demo.db")