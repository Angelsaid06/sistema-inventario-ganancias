import os
import json
import sqlite3
from datetime import date, timedelta
import anthropic
from prediccion import ventas_por_dia, promedio_movil, dias_restantes, sugerir_reabasto

MODELO = "claude-haiku-5-5"


def crear_tabla_precios(nombre_db):
    conexion = sqlite3.connect(nombre_db)
    cursor = conexion.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS precios_proveedor (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            producto_id INTEGER NOT NULL,
            proveedor TEXT NOT NULL,
            precio_pieza REAL NOT NULL,
            fecha TEXT NOT NULL,
            FOREIGN KEY (producto_id) REFERENCES productos(id)
        )
    """)
    conexion.commit()
    conexion.close()


def registrar_precio(nombre_db, producto_id, proveedor, precio_pieza):
    if proveedor.strip() == "" or precio_pieza <= 0:
        return
    crear_tabla_precios(nombre_db)
    conexion = sqlite3.connect(nombre_db)
    cursor = conexion.cursor()
    cursor.execute(
        "INSERT INTO precios_proveedor (producto_id, proveedor, precio_pieza, fecha) VALUES (?, ?, ?, ?)",
        (producto_id, proveedor, precio_pieza, str(date.today()))
    )
    conexion.commit()
    conexion.close()


# ---------- Herramientas que consulta el asistente ----------

def ver_inventario(nombre_db):
    conexion = sqlite3.connect(nombre_db)
    cursor = conexion.cursor()
    cursor.execute("SELECT id, nombre, precio_venta, existencias FROM productos")
    filas = cursor.fetchall()

    lista = []
    for fila in filas:
        cursor.execute(
            "SELECT SUM(cantidad), SUM(costo_total) FROM compras WHERE producto_id = ?",
            (fila[0],)
        )
        compras = cursor.fetchone()
        if compras[0] is None or compras[0] == 0:
            costo = None
        else:
            costo = round(compras[1] / compras[0], 2)
        lista.append({
            "id": fila[0],
            "nombre": fila[1],
            "precio_venta": fila[2],
            "costo_promedio": costo,
            "existencias": fila[3],
        })
    conexion.close()
    return lista


def ventas_recientes(nombre_db, dias):
    desde = str(date.today() - timedelta(days=dias))
    conexion = sqlite3.connect(nombre_db)
    cursor = conexion.cursor()
    cursor.execute(
        "SELECT productos.nombre, SUM(ventas.cantidad) "
        "FROM ventas JOIN productos ON ventas.producto_id = productos.id "
        "WHERE ventas.fecha >= ? GROUP BY productos.nombre",
        (desde,)
    )
    filas = cursor.fetchall()
    conexion.close()

    lista = []
    for fila in filas:
        lista.append({"producto": fila[0], "piezas_vendidas": fila[1]})
    return lista


def prediccion_reabasto(nombre_db):
    resultado = []
    for producto in ver_inventario(nombre_db):
        ventas = ventas_por_dia(nombre_db, producto["id"])
        promedio = promedio_movil(ventas, 7)
        dias = dias_restantes(producto["existencias"], promedio)
        if dias is not None:
            dias = round(dias, 1)
        resultado.append({
            "producto": producto["nombre"],
            "existencias": producto["existencias"],
            "promedio_diario_7_dias": round(promedio, 1),
            "dias_que_le_quedan": dias,
            "reponer_para_7_dias": sugerir_reabasto(producto["existencias"], promedio, 7),
        })
    return resultado


def precios_proveedor(nombre_db):
    crear_tabla_precios(nombre_db)
    conexion = sqlite3.connect(nombre_db)
    cursor = conexion.cursor()
    cursor.execute(
        "SELECT productos.nombre, precios_proveedor.proveedor, "
        "precios_proveedor.precio_pieza, precios_proveedor.fecha "
        "FROM precios_proveedor JOIN productos ON precios_proveedor.producto_id = productos.id "
        "ORDER BY precios_proveedor.fecha DESC"
    )
    filas = cursor.fetchall()
    conexion.close()

    lista = []
    for fila in filas:
        lista.append({
            "producto": fila[0],
            "proveedor": fila[1],
            "precio_pieza": fila[2],
            "fecha": fila[3],
        })
    return lista


def ejecutar_herramienta(nombre, datos, nombre_db):
    if nombre == "ver_inventario":
        return ver_inventario(nombre_db)
    if nombre == "ventas_recientes":
        return ventas_recientes(nombre_db, datos.get("dias", 30))
    if nombre == "prediccion_reabasto":
        return prediccion_reabasto(nombre_db)
    if nombre == "precios_proveedor":
        return precios_proveedor(nombre_db)
    return {"error": "Herramienta desconocida"}


HERRAMIENTAS = [
    {
        "name": "ver_inventario",
        "description": "Devuelve cada producto con su precio de venta, costo promedio por pieza y existencias actuales.",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "ventas_recientes",
        "description": "Devuelve las piezas vendidas por producto en los ultimos N dias.",
        "input_schema": {
            "type": "object",
            "properties": {"dias": {"type": "integer", "description": "Cuantos dias hacia atras revisar"}},
            "required": ["dias"],
        },
    },
    {
        "name": "prediccion_reabasto",
        "description": "Estima, con el promedio de ventas de los ultimos 7 dias, cuantos dias le quedan a cada producto y cuantas piezas reponer para cubrir 7 dias.",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "precios_proveedor",
        "description": "Devuelve los precios por pieza que el dueno ha registrado de distintos proveedores o tiendas.",
        "input_schema": {"type": "object", "properties": {}},
    },
]


# ---------- Conversacion con Claude ----------

def leer_contexto():
    if os.path.exists("contexto.txt"):
        archivo = open("contexto.txt", encoding="utf-8")
        texto = archivo.read()
        archivo.close()
        return texto
    return ""


def armar_instrucciones():
    texto = (
        "Eres un asistente de compras para un negocio pequeno de botanas y dulces. "
        "Antes de recomendar, consulta los datos con las herramientas. "
        "Reglas: no inventes precios ni cifras. Si falta un dato (por ejemplo precios de proveedor "
        "o pocas ventas registradas), dilo claramente y pide ese dato. "
        "Explica tu razonamiento con los numeros de las herramientas. "
        "Entrega las recomendaciones como una lista de compra con cantidades. "
        "No puedes ejecutar compras: la decision final es del dueno. "
        "Responde en espanol y de forma breve."
    )
    contexto = leer_contexto()
    if contexto != "":
        texto = texto + "\n\nContexto del negocio:\n" + contexto
    return texto


def preguntar(pregunta, historial, nombre_db):
    cliente = anthropic.Anthropic()
    mensajes = historial + [{"role": "user", "content": pregunta}]

    for vuelta in range(6):
        respuesta = cliente.messages.create(
            model=MODELO,
            max_tokens=1000,
            system=armar_instrucciones(),
            tools=HERRAMIENTAS,
            messages=mensajes,
        )
        mensajes.append({"role": "assistant", "content": respuesta.content})

        if respuesta.stop_reason != "tool_use":
            texto = ""
            for bloque in respuesta.content:
                if bloque.type == "text":
                    texto = texto + bloque.text
            return texto, mensajes

        resultados = []
        for bloque in respuesta.content:
            if bloque.type == "tool_use":
                datos = ejecutar_herramienta(bloque.name, bloque.input, nombre_db)
                resultados.append({
                    "type": "tool_result",
                    "tool_use_id": bloque.id,
                    "content": json.dumps(datos),
                })
        mensajes.append({"role": "user", "content": resultados})

    return "No pude terminar la consulta, intenta de nuevo.", mensajes