import sqlite3
import streamlit as st
from inventario import registrar_compra, registrar_venta, calcular_ganancia


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

    conexion.close()

    if len(tabla) > 0:
        st.table(tabla)
    else:
        st.write("Todavia no hay ventas registradas")

    st.write("Ingresos totales:", round(total_ingresos, 2))
    st.write("Costos totales:", round(total_costos, 2))
    st.subheader("Ganancia total: " + str(round(total_ingresos - total_costos, 2)))


st.title("Inventario y ganancias")

pagina = st.sidebar.radio(
    "Menu",
    ["Productos", "Registrar venta", "Registrar compra", "Reporte de ganancias"]
)

if pagina == "Productos":
    pagina_productos()
elif pagina == "Registrar venta":
    pagina_venta()
elif pagina == "Registrar compra":
    pagina_compra()
else:
    pagina_reporte()