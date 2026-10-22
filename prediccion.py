import sqlite3
from datetime import date, timedelta


def ventas_por_dia(nombre_db, producto_id):
    # Devuelve una lista con las piezas vendidas cada dia (0 si no vendio)
    conexion = sqlite3.connect(nombre_db)
    cursor = conexion.cursor()
    cursor.execute(
        "SELECT fecha, SUM(cantidad) FROM ventas WHERE producto_id = ? GROUP BY fecha",
        (producto_id,)
    )
    filas = cursor.fetchall()
    conexion.close()

    if len(filas) == 0:
        return []

    por_fecha = {}
    for fila in filas:
        por_fecha[fila[0]] = fila[1]

    primer_dia = date.fromisoformat(min(por_fecha))
    dia = primer_dia
    resultado = []
    while dia <= date.today():
        resultado.append(por_fecha.get(str(dia), 0))
        dia = dia + timedelta(days=1)
    return resultado


def promedio_movil(ventas, dias=7):
    ultimos = ventas[-dias:]
    if len(ultimos) == 0:
        return 0
    return sum(ultimos) / len(ultimos)


def dias_restantes(existencias, promedio_diario):
    if promedio_diario <= 0:
        return None
    return existencias / promedio_diario


def sugerir_reabasto(existencias, promedio_diario, dias_cubrir=7):
    necesarias = promedio_diario * dias_cubrir
    faltan = necesarias - existencias
    if faltan <= 0:
        return 0
    return round(faltan)