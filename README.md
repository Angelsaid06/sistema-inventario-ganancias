\# Sistema de inventario y ganancias
![Tests](https://github.com/Angelsaid06/sistema-inventario-ganancias/actions/workflows/tests.yml/badge.svg)


Programa en Python para llevar el inventario de un negocio pequeño: registra productos, compras y ventas, actualiza las existencias automáticamente y calcula la ganancia real por producto.



Nació de una necesidad real: vendo botanas en mi universidad y quería saber cuánto gano de verdad, sin llevar las cuentas a mano en Excel y poder administrarme bien, espero que en un futuro no muy lejano poderle implementar IA y hacerlo un buen Software.



\## Funciones


- Reporte de ventas por mes y exportación a CSV
- Agregar y consultar productos
- Registrar compras (suman existencias)
- Registrar ventas (restan existencias y avisan si no alcanza)
- Registrar gastos extra (bolsas, transporte, etc.)
- Alertas de productos con pocas piezas o sin existencias
- Reporte de ingresos, costos, ganancia de ventas y ganancia neta
- Ventas por día y gráfica de productos más vendidos
- Interfaz web con Streamlit y modo consola
- Pruebas automáticas del cálculo de ganancias



\## Requisitos



\- Python 3

\- pytest (solo para correr las pruebas)



\## Cómo ejecutarlo



1\. Clona el repositorio:

```

\&#x20;  git clone https://github.com/Angelsaid06/sistema-inventario-ganancias.git

\&#x20;  cd sistema-inventario-ganancias

```

2\. Crea la base de datos y carga los datos de ejemplo:

```

\&#x20;  py database.py

\&#x20;  py cargar\\\_datos.py

```

3\. Inicia el programa:

```

\&#x20;  py inventario.py

```



\## Ejemplo



Compro 24 refrescos en $240 y vendo 10 a $15 cada uno:



\- Ingresos: $150

\- Costo de lo vendido: $100

\- Ganancia: $50



\## Cómo se calcula la ganancia



Se usa el costo promedio por pieza: costo total comprado entre piezas compradas. La ganancia es lo que cobraste menos ese costo por las piezas vendidas.



\## Pruebas



```

py -m pip install pytest

py -m pytest

```

## Predicción de reabastecimiento

La app estima cuántos días le quedan a cada producto y cuántas piezas conviene reponer, a partir del historial de ventas.

**Etapa 1: línea base.** Promedio de ventas de los últimos 7 días. Con eso se calcula cuántos días dura el inventario y cuántas piezas reponer para cubrir 7 días.

**Etapa 2: modelo de Machine Learning.** Regresión lineal (scikit-learn) que predice las ventas del día usando el promedio de los 7 días anteriores y el día de la semana. Se entrena con el 80% de los días y se evalúa con el 20% final, que no vio al entrenar. Se compara contra la línea base con el error absoluto promedio (piezas por día).

**Resultados con datos de demo (60 días, inventados):**

| Producto | Error promedio simple | Error modelo ML |
|---|---|---|
| Gansitos | 1.95 | 1.54 |
| Galletas | 1.09 | 0.93 |
| Gomitas | 2.13 | 1.17 |

**Cómo interpretarlo:** los datos de demo los generé con un patrón de ventas bajas en fin de semana, así que que el modelo gane era esperable. Estos resultados solo comprueban que el sistema de evaluación funciona. No demuestran que el modelo sea mejor con ventas reales. Además, la evaluación usa pocos días (unos 11), por lo que las diferencias pequeñas pueden ser casualidad. Con datos reales se necesitan al menos 30 días de historial; si el modelo no mejora al promedio simple, ese también es un resultado válido.

Para generar la demo y evaluar: `py generar_demo.py` y `py evaluar.py`.

\## Limitaciones y mejoras futuras


- El modelo de predicción aún no se ha validado con ventas reales.
- La ganancia usa costo promedio por pieza (no distingue lotes con distinto costo)
- Falta validar datos inválidos en el modo consola
- Pendiente publicar la app en línea

## Capturas

![Reporte de ganancias](imagenes/reporte.png)

