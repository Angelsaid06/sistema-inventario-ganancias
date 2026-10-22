import os
import sqlite3
import streamlit as st
import pandas as pd
from inventario import registrar_compra, registrar_venta, calcular_ganancia, registrar_gasto
from prediccion import ventas_por_dia, promedio_movil, dias_restantes, sugerir_reabasto

def obtener_productos():
    conexion = sqlite3.connect("inventario.db")
    cursor = conexion.cursor()
    cursor.execute("SELECT id, nombre, precio_venta, existencias FROM productos")
    filas = cursor.fetchall()
    conexion.close()
    return filas


def pagina_productos():
    st.header("Productos")
    productos = obtener_productos()

    # Alertas: productos con 5 piezas o menos
    for fila in productos:
        if fila[3] == 0:
            st.error(fila[1] + ": SIN existencias")
        elif fila[3] <= 5:
            st.warning(fila[1] + ": quedan solo " + str(fila[3]) + " piezas")

    tabla = []
    for fila in productos:
        tabla.append({"Producto": fila[1], "Precio": fila[2], "Existencias": fila[3]})
    st.table(tabla)


def pagina_venta():
    st.header("Registrar venta")
    productos = obtener_productos()
    nombres = []
    for fila in productos:
        nombres.append(fila[1])

    elegido = st.selectbox("Producto", nombres)
    posicion = nombres.index(elegido)
    producto_id = productos[posicion][0]
    existencias = productos[posicion][3]

    st.write("Existencias:", existencias)
    cantidad = st.number_input("Cantidad vendida", min_value=1, step=1)

    if st.button("Registrar venta"):
        if cantidad > existencias:
            st.error("No hay suficientes piezas")
        else:
            registrar_venta(producto_id, int(cantidad))
            st.success("Venta registrada")


def pagina_compra():
    st.header("Registrar compra")
    productos = obtener_productos()
    nombres = []
    for fila in productos:
        nombres.append(fila[1])

    elegido = st.selectbox("Producto", nombres)
    posicion = nombres.index(elegido)
    producto_id = productos[posicion][0]

    cantidad = st.number_input("Cantidad comprada", min_value=1, step=1)
    costo_total = st.number_input("Costo total", min_value=0.0, step=1.0)

    if st.button("Registrar compra"):
        registrar_compra(producto_id, int(cantidad), costo_total)
        st.success("Compra registrada")


def pagina_reporte():
    st.header("Reporte de ganancias")
    conexion = sqlite3.connect("inventario.db")
    cursor = conexion.cursor()
    cursor.execute("SELECT id, nombre FROM productos")
    productos = cursor.fetchall()

    tabla = []
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
            tabla.append({
                "Producto": producto[1],
                "Vendidas": piezas_vendidas,
                "Ingresos": round(ingresos, 2),
                "Costo": round(costo_vendido, 2),
                "Ganancia": round(ganancia, 2),
            })

        total_ingresos = total_ingresos + ingresos
        total_costos = total_costos + costo_vendido
    cursor.execute("SELECT SUM(monto) FROM gastos")
    total_gastos = cursor.fetchone()[0]
    if total_gastos is None:
        total_gastos = 0
    conexion.close()

    if len(tabla) > 0:
        st.table(tabla)
    else:
        st.write("Todavia no hay ventas registradas")

    st.write("Ingresos totales:", round(total_ingresos, 2))
    st.write("Costos totales:", round(total_costos, 2))
    st.write("Ganancia de ventas:", round(total_ingresos - total_costos, 2))
    st.write("Gastos extra:", round(total_gastos, 2))
    st.subheader("Ganancia neta: " + str(round(total_ingresos - total_costos - total_gastos, 2)))

def pagina_ventas_dia():
    st.header("Ventas por dia")
    conexion = sqlite3.connect("inventario.db")
    cursor = conexion.cursor()

    cursor.execute(
        "SELECT fecha, SUM(cantidad), SUM(cantidad * precio_unitario) "
        "FROM ventas GROUP BY fecha ORDER BY fecha"
    )
    por_dia = cursor.fetchall()

    cursor.execute(
        "SELECT productos.nombre, SUM(ventas.cantidad) "
        "FROM ventas JOIN productos ON ventas.producto_id = productos.id "
        "GROUP BY productos.nombre ORDER BY SUM(ventas.cantidad) DESC"
    )
    mas_vendidos = cursor.fetchall()
    conexion.close()

    if len(por_dia) == 0:
        st.write("Todavia no hay ventas registradas")
    else:
        tabla = []
        for fila in por_dia:
            tabla.append({"Fecha": fila[0], "Piezas": fila[1], "Ingresos": fila[2]})
        st.table(tabla)

        st.subheader("Productos mas vendidos")
        datos = pd.DataFrame(mas_vendidos, columns=["Producto", "Vendidas"])
        datos = datos.set_index("Producto")
        st.bar_chart(datos)
def pagina_gastos():
    st.header("Gastos extra")
    descripcion = st.text_input("Descripcion (ejemplo: bolsas, transporte)")
    monto = st.number_input("Monto", min_value=0.0, step=1.0)

    if st.button("Registrar gasto"):
        if descripcion == "":
            st.error("Escribe una descripcion")
        else:
            registrar_gasto(descripcion, monto)
            st.success("Gasto registrado")

    conexion = sqlite3.connect("inventario.db")
    cursor = conexion.cursor()
    cursor.execute("SELECT fecha, descripcion, monto FROM gastos ORDER BY fecha DESC")
    filas = cursor.fetchall()
    conexion.close()

    if len(filas) > 0:
        tabla = []
        for fila in filas:
            tabla.append({"Fecha": fila[0], "Descripcion": fila[1], "Monto": fila[2]})
        st.table(tabla)
def pagina_mes():
    st.header("Reporte por mes")
    conexion = sqlite3.connect("inventario.db")
    cursor = conexion.cursor()

    cursor.execute(
        "SELECT substr(fecha, 1, 7), SUM(cantidad), SUM(cantidad * precio_unitario) "
        "FROM ventas GROUP BY substr(fecha, 1, 7) ORDER BY 1"
    )
    por_mes = cursor.fetchall()

    cursor.execute(
        "SELECT ventas.fecha, productos.nombre, ventas.cantidad, ventas.precio_unitario "
        "FROM ventas JOIN productos ON ventas.producto_id = productos.id "
        "ORDER BY ventas.fecha"
    )
    todas = cursor.fetchall()
    conexion.close()

    if len(por_mes) == 0:
        st.write("Todavia no hay ventas registradas")
    else:
        tabla = []
        for fila in por_mes:
            tabla.append({"Mes": fila[0], "Piezas": fila[1], "Ingresos": fila[2]})
        st.table(tabla)

        datos = pd.DataFrame(
            todas, columns=["Fecha", "Producto", "Cantidad", "Precio unitario"]
        )
        csv = datos.to_csv(index=False)
        st.download_button("Descargar ventas en CSV", csv, "ventas.csv", "text/csv")
def pagina_prediccion():
    st.header("Prediccion de reabastecimiento")
    fuente = st.radio("Datos", ["Mis datos", "Datos de demo (inventados)"])

    if fuente == "Mis datos":
        nombre_db = "inventario.db"
    else:
        nombre_db = "demo.db"

    if not os.path.exists(nombre_db):
        st.write("No se encontro la base. Para la demo corre: py generar_demo.py")
        return

    conexion = sqlite3.connect(nombre_db)
    cursor = conexion.cursor()
    cursor.execute("SELECT id, nombre, existencias FROM productos")
    productos = cursor.fetchall()
    conexion.close()

    tabla = []
    for producto in productos:
        ventas = ventas_por_dia(nombre_db, producto[0])
        promedio = promedio_movil(ventas, 7)
        dias = dias_restantes(producto[2], promedio)
        sugerido = sugerir_reabasto(producto[2], promedio, 7)

        if dias is None:
            texto_dias = "sin ventas recientes"
        else:
            texto_dias = str(round(dias, 1))

        tabla.append({
            "Producto": producto[1],
            "Existencias": producto[2],
            "Promedio diario (7 dias)": round(promedio, 1),
            "Dias que le quedan": texto_dias,
            "Reponer (para 7 dias)": sugerido,
        })

    st.table(tabla)
    st.caption("Estimacion basada en el promedio de los ultimos 7 dias; no es una garantia.")
st.title("Inventario y ganancias")

pagina = st.sidebar.radio(
    "Menu",
    ["Productos", "Registrar venta", "Registrar compra", "Gastos", "Reporte de ganancias", "Ventas por dia", "Reporte por mes"]
)

if pagina == "Productos":
    pagina_productos()
elif pagina == "Registrar venta":
    pagina_venta()
elif pagina == "Registrar compra":
    pagina_compra()
elif pagina == "Gastos":
    pagina_gastos()
elif pagina == "Reporte de ganancias":
    pagina_reporte()
elif pagina == "Ventas por dia":
    pagina_ventas_dia()
else:
    pagina_mes()