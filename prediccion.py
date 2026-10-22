import sqlite3
from sklearn.linear_model import LinearRegression
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

def armar_datos(ventas):
    # Para cada dia (desde el octavo) arma: promedio de los 7 dias anteriores + dia de la semana
    hoy = date.today()
    filas = []
    objetivos = []
    baseline = []
    for i in range(7, len(ventas)):
        fecha = hoy - timedelta(days=len(ventas) - 1 - i)
        previo = sum(ventas[i - 7:i]) / 7
        fila = [previo]
        for dia in range(7):
            if fecha.weekday() == dia:
                fila.append(1)
            else:
                fila.append(0)
        filas.append(fila)
        objetivos.append(ventas[i])
        baseline.append(previo)
    return filas, objetivos, baseline


def error_promedio(reales, predichos):
    total = 0
    for i in range(len(reales)):
        total = total + abs(reales[i] - predichos[i])
    return total / len(reales)


def comparar_modelos(ventas):
    # Devuelve (error del promedio simple, error del modelo), o None si hay pocos datos
    if len(ventas) < 30:
        return None

    filas, objetivos, baseline = armar_datos(ventas)
    corte = int(len(filas) * 0.8)

    modelo = LinearRegression()
    modelo.fit(filas[:corte], objetivos[:corte])
    predichos = modelo.predict(filas[corte:])

    error_base = error_promedio(objetivos[corte:], baseline[corte:])
    error_modelo = error_promedio(objetivos[corte:], predichos)
    return error_base, error_modelo