import os
import sqlite3
import streamlit as st
import pandas as pd
from datetime import date
from inventario import registrar_compra, registrar_venta, registrar_gasto, listar_productos, resumen_ganancias, agregar_producto, ultimas_ventas, cancelar_venta, ultimas_compras, cancelar_compra, ultimos_gastos, cancelar_gasto
from prediccion import ventas_por_dia, promedio_movil, dias_restantes, sugerir_reabasto, comparar_modelos
from asistente import preguntar, crear_tabla_precios, registrar_precio, precios_proveedor, evaluar_recomendaciones, resumen_evaluacion
from database import crear_tablas
from cargar_datos import cargar_ejemplo

st.set_page_config(page_title="Inventario y ganancias", page_icon="🛒")

# Si no existe la base de datos, se crea vacia
if not os.path.exists("inventario.db"):
    crear_tablas()


def pagina_productos():
    st.header("Productos")

    with st.expander("Agregar producto"):
        nombre = st.text_input("Nombre")
        precio = st.number_input("Precio de venta", min_value=0.0, step=0.5)
        if st.button("Guardar producto"):
            if nombre.strip() == "" or precio <= 0:
                st.error("Escribe un nombre y un precio mayor a 0")
            else:
                agregar_producto(nombre, precio)
                st.success("Producto agregado")

    productos = listar_productos()

    if len(productos) == 0:
        st.info("Bienvenido. Aun no tienes productos: agrega el primero arriba, o carga unos de ejemplo para explorar la app.")
        if st.button("Cargar datos de ejemplo"):
            cargar_ejemplo()
            st.rerun()
        return

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
    productos = listar_productos()
    if len(productos) == 0:
        st.write("Primero agrega productos en la seccion Productos")
        return

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

    aviso = st.session_state.pop("aviso", None)
    if aviso is not None:
        st.success(aviso)

    productos = listar_productos()
    if len(productos) == 0:
        st.write("Primero agrega productos en la seccion Productos")
        return

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

    st.subheader("Ultimas compras")
    compras = ultimas_compras(5)
    if len(compras) == 0:
        st.write("Todavia no hay compras")
    for compra in compras:
        columna1, columna2 = st.columns([3, 1])
        columna1.write(str(compra[2]) + " x " + compra[1] + "  ($" + str(compra[3]) + " en total)  " + compra[4])
        if columna2.button("Cancelar", key="cancelar_compra_" + str(compra[0])):
            if cancelar_compra(compra[0]):
                st.session_state.aviso = "Compra cancelada: " + compra[1]
                st.rerun()
            else:
                st.error("No se puede cancelar: ya se vendieron piezas de esa compra")


def contenido_ganancias():
    resumen = resumen_ganancias()

    if len(resumen["filas"]) > 0:
        tabla = []
        for fila in resumen["filas"]:
            tabla.append({
                "Producto": fila["producto"],
                "Vendidas": fila["vendidas"],
                "Ingresos": fila["ingresos"],
                "Costo": fila["costo"],
                "Ganancia": fila["ganancia"],
            })
        st.table(tabla)
        grafica = pd.DataFrame(tabla).set_index("Producto")[["Ganancia"]]
        st.subheader("Ganancia por producto")
        st.bar_chart(grafica)
    else:
        st.write("Todavia no hay ventas registradas")

    st.write("Ingresos totales:", round(resumen["ingresos"], 2))
    st.write("Costos totales:", round(resumen["costos"], 2))
    st.write("Ganancia de ventas:", round(resumen["ganancia_ventas"], 2))
    st.write("Gastos extra:", round(resumen["gastos"], 2))
    st.subheader("Ganancia neta: " + str(round(resumen["ganancia_neta"], 2)))


def contenido_dia():
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

        diario = pd.DataFrame(por_dia, columns=["Fecha", "Piezas", "Ingresos"]).set_index("Fecha")
        st.subheader("Ingresos por dia")
        st.line_chart(diario[["Ingresos"]])

        st.subheader("Productos mas vendidos")
        datos = pd.DataFrame(mas_vendidos, columns=["Producto", "Vendidas"])
        datos = datos.set_index("Producto")
        st.bar_chart(datos)


def pagina_gastos():
    st.header("Gastos extra")

    aviso = st.session_state.pop("aviso", None)
    if aviso is not None:
        st.success(aviso)

    descripcion = st.text_input("Descripcion (ejemplo: bolsas, transporte)")
    monto = st.number_input("Monto", min_value=0.0, step=1.0)

    if st.button("Registrar gasto"):
        if descripcion == "":
            st.error("Escribe una descripcion")
        else:
            registrar_gasto(descripcion, monto)
            st.success("Gasto registrado")

    st.subheader("Ultimos gastos")
    gastos = ultimos_gastos(10)
    if len(gastos) == 0:
        st.write("Todavia no hay gastos")
    for gasto in gastos:
        columna1, columna2 = st.columns([3, 1])
        columna1.write(gasto[1] + "  ($" + str(gasto[2]) + ")  " + gasto[3])
        if columna2.button("Cancelar", key="cancelar_gasto_" + str(gasto[0])):
            cancelar_gasto(gasto[0])
            st.session_state.aviso = "Gasto cancelado: " + gasto[1]
            st.rerun()


def contenido_mes():
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


def pagina_reportes():
    st.header("Reportes")
    pestana1, pestana2, pestana3 = st.tabs(["Ganancias", "Por dia", "Por mes"])
    with pestana1:
        contenido_ganancias()
    with pestana2:
        contenido_dia()
    with pestana3:
        contenido_mes()


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

    st.subheader("Que tan bien predice cada metodo")
    comparacion = []
    for producto in productos:
        ventas = ventas_por_dia(nombre_db, producto[0])
        resultado = comparar_modelos(ventas)
        if resultado is None:
            comparacion.append({
                "Producto": producto[1],
                "Error promedio simple": "faltan datos",
                "Error modelo ML": "faltan datos",
            })
        else:
            comparacion.append({
                "Producto": producto[1],
                "Error promedio simple": round(resultado[0], 2),
                "Error modelo ML": round(resultado[1], 2),
            })
    st.table(comparacion)
    st.caption("Error = diferencia promedio entre las piezas reales y las predichas por dia, medida en los ultimos dias que el modelo no vio al entrenar. Menor es mejor.")


def pagina_precios():
    st.header("Precios de proveedores")
    crear_tabla_precios("inventario.db")
    productos = listar_productos()
    if len(productos) == 0:
        st.write("Primero agrega productos en la seccion Productos")
        return

    nombres = []
    for fila in productos:
        nombres.append(fila[1])

    elegido = st.selectbox("Producto", nombres)
    producto_id = productos[nombres.index(elegido)][0]
    proveedor = st.text_input("Proveedor o tienda")
    precio = st.number_input("Precio por pieza", min_value=0.0, step=0.5)

    if st.button("Guardar precio"):
        if proveedor == "" or precio <= 0:
            st.error("Escribe el proveedor y un precio mayor a 0")
        else:
            registrar_precio("inventario.db", producto_id, proveedor, precio)
            st.success("Precio guardado")

    lista = precios_proveedor("inventario.db")
    if len(lista) > 0:
        st.table(lista)


def pagina_asistente():
    st.header("Asistente de compras")

    if os.environ.get("ANTHROPIC_API_KEY") is None:
        st.info("El asistente esta desactivado en esta demo publica. Para probarlo, clona el repositorio y configura tu propia clave (mira el README).")
        return

    fuente = st.radio("Datos", ["Mis datos", "Datos de demo (inventados)"])
    if fuente == "Mis datos":
        nombre_db = "inventario.db"
    else:
        nombre_db = "demo.db"

    if not os.path.exists(nombre_db):
        st.write("No se encontro la base. Para la demo corre: py generar_demo.py")
        return

    if "chat" not in st.session_state:
        st.session_state.chat = []
        st.session_state.mensajes_api = []

    if st.button("Nueva conversacion"):
        st.session_state.chat = []
        st.session_state.mensajes_api = []
        st.rerun()

    for mensaje in st.session_state.chat:
        with st.chat_message(mensaje["rol"]):
            st.write(mensaje["texto"])

    pregunta = st.chat_input("Ejemplo: que compro este fin de semana con 500 pesos?")
    if pregunta:
        st.session_state.chat.append({"rol": "user", "texto": pregunta})
        try:
            with st.spinner("Pensando..."):
                texto, mensajes = preguntar(pregunta, st.session_state.mensajes_api, nombre_db)
            st.session_state.mensajes_api = mensajes
            st.session_state.chat.append({"rol": "assistant", "texto": texto})
        except Exception as error:
            st.session_state.chat.append({"rol": "assistant", "texto": "Error: " + str(error)})
        st.rerun()


def pagina_evaluacion():
    st.header("Evaluacion de las recomendaciones")
    evaluadas, pendientes = evaluar_recomendaciones("inventario.db", 7)
    st.write("Recomendaciones esperando sus 7 dias:", pendientes)

    resumen = resumen_evaluacion(evaluadas)
    if resumen is None:
        st.write("Todavia no hay recomendaciones con 7 dias cumplidos.")
        return

    st.write("Recomendaciones evaluadas:", resumen["n"])
    st.write("Error promedio del asistente (piezas):", resumen["error_asistente"])
    st.write("Error promedio de la regla simple (piezas):", resumen["error_regla"])
    st.write("Veces que lo sugerido alcanzo para la demanda: " + str(resumen["porcentaje_alcanzo"]) + "%")
    st.table(evaluadas)
    st.caption("Error = |existencias + piezas sugeridas - piezas vendidas en los 7 dias siguientes|. Menor es mejor. Si un producto se agota, la demanda real se subestima.")


def pagina_inicio():
    st.header("Inicio")

    # Accesos rapidos
    columna_a, columna_b = st.columns(2)
    columna_a.page_link(p_venta_rapida, label="Venta rapida", icon="⚡")
    columna_b.page_link(p_productos, label="Productos", icon="📦")
    columna_c, columna_d = st.columns(2)
    columna_c.page_link(p_compra, label="Registrar compra", icon="🛒")
    columna_d.page_link(p_reportes, label="Reportes", icon="📊")

    productos = listar_productos()
    if len(productos) == 0:
        st.info("Aun no hay productos. Agrega el primero en la seccion Productos.")
        return

    resumen = resumen_ganancias()

    conexion = sqlite3.connect("inventario.db")
    cursor = conexion.cursor()
    cursor.execute(
        "SELECT SUM(cantidad), SUM(cantidad * precio_unitario) FROM ventas WHERE fecha = ?",
        (str(date.today()),)
    )
    hoy = cursor.fetchone()
    cursor.execute(
        "SELECT fecha, SUM(cantidad * precio_unitario) FROM ventas "
        "GROUP BY fecha ORDER BY fecha DESC LIMIT 14"
    )
    por_dia = cursor.fetchall()
    conexion.close()

    piezas_hoy = hoy[0]
    ingresos_hoy = hoy[1]
    if piezas_hoy is None:
        piezas_hoy = 0
        ingresos_hoy = 0

    por_agotarse = 0
    for fila in productos:
        if fila[3] <= 5:
            por_agotarse = por_agotarse + 1

    columna1, columna2 = st.columns(2)
    columna1.metric("Ventas de hoy", "$" + str(round(ingresos_hoy, 2)))
    columna2.metric("Piezas vendidas hoy", piezas_hoy)

    columna3, columna4 = st.columns(2)
    columna3.metric("Ganancia neta total", "$" + str(round(resumen["ganancia_neta"], 2)))
    columna4.metric("Productos por agotarse", por_agotarse)

    if len(por_dia) > 0:
        por_dia.reverse()
        datos = pd.DataFrame(por_dia, columns=["Fecha", "Ingresos"])
        datos = datos.set_index("Fecha")
        st.subheader("Ingresos de los ultimos dias")
        st.bar_chart(datos)


def pagina_venta_rapida():
    st.header("Venta rapida")
    st.caption("Toca un producto para registrar 1 pieza vendida.")

    mensaje = st.session_state.pop("ultima_venta", None)
    if mensaje is not None:
        st.success(mensaje)

    productos = listar_productos()
    if len(productos) == 0:
        st.write("Primero agrega productos en la seccion Productos")
        return

    for fila in productos:
        texto = fila[1] + "  ($" + str(fila[2]) + ")  -  quedan " + str(fila[3])
        if st.button(texto, key="rapida_" + str(fila[0]), disabled=(fila[3] == 0)):
            registrar_venta(fila[0], 1)
            st.session_state.ultima_venta = "Vendido: " + fila[1]
            st.rerun()

    st.subheader("Ultimas ventas")
    ventas = ultimas_ventas(5)
    if len(ventas) == 0:
        st.write("Todavia no hay ventas")
    for venta in ventas:
        columna1, columna2 = st.columns([3, 1])
        columna1.write(str(venta[2]) + " x " + venta[1] + "  ($" + str(venta[3]) + " c/u)  " + venta[4])
        if columna2.button("Cancelar", key="cancelar_" + str(venta[0])):
            cancelar_venta(venta[0])
            st.session_state.ultima_venta = "Venta cancelada: " + venta[1]
            st.rerun()


# ---------- Estilos y menu ----------

ESTILOS = """
<style>
div.stButton > button {
    border-radius: 14px;
    border: none;
    padding: 0.6rem 1.2rem;
    font-weight: 600;
    color: white;
    background: linear-gradient(135deg, #1D9E75, #14B8A6);
}
div.stButton > button:hover {
    color: white;
    filter: brightness(1.08);
}
div.stButton > button:disabled {
    background: #D1D5DB;
    color: #6B7280;
}
div[data-testid="stMetric"] {
    background: #F0F7F4;
    border-radius: 16px;
    padding: 14px 16px;
}
a[data-testid="stPageLink-NavLink"] {
    background: #F0F7F4;
    border-radius: 14px;
    padding: 0.7rem 1rem;
    font-weight: 600;
}
</style>
"""
st.markdown(ESTILOS, unsafe_allow_html=True)

p_inicio = st.Page(pagina_inicio, title="Inicio", icon="🏠", default=True)
p_venta_rapida = st.Page(pagina_venta_rapida, title="Venta rapida", icon="⚡")
p_venta = st.Page(pagina_venta, title="Registrar venta", icon="🧾")
p_productos = st.Page(pagina_productos, title="Productos", icon="📦")
p_compra = st.Page(pagina_compra, title="Registrar compra", icon="🛒")
p_gastos = st.Page(pagina_gastos, title="Gastos", icon="💸")
p_precios = st.Page(pagina_precios, title="Precios de proveedores", icon="🏷️")
p_reportes = st.Page(pagina_reportes, title="Reportes", icon="📊")
p_prediccion = st.Page(pagina_prediccion, title="Prediccion", icon="🔮")
p_asistente = st.Page(pagina_asistente, title="Asistente", icon="🤖")
p_evaluacion = st.Page(pagina_evaluacion, title="Evaluacion", icon="📈")

navegacion = st.navigation({
    "Principal": [p_inicio, p_venta_rapida, p_venta],
    "Inventario": [p_productos, p_compra, p_gastos, p_precios],
    "Reportes": [p_reportes],
    "Inteligencia": [p_prediccion, p_asistente, p_evaluacion],
})
navegacion.run()