\# Sistema de inventario y ganancias
![Tests](https://github.com/Angelsaid06/sistema-inventario-ganancias/actions/workflows/tests.yml/badge.svg)


Programa en Python para llevar el inventario de un negocio pequeño: registra productos, compras y ventas, actualiza las existencias automáticamente y calcula la ganancia real por producto.



Nació de una necesidad real: vendo botanas en mi universidad y quería saber cuánto gano de verdad, sin llevar las cuentas a mano en Excel y poder administrarme bien, espero que en un futuro no muy lejano poderle implementar IA y hacerlo un buen Software.



\## Funciones



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



\## Limitaciones y mejoras futuras



- La ganancia usa costo promedio por pieza (no distingue lotes con distinto costo)
- Falta validar datos inválidos en el modo consola
- Todavía no hay reporte por mes ni exportar a Excel
- Pendiente publicar la app en línea

## Capturas

![Reporte de ganancias](imagenes/reporte.png)

