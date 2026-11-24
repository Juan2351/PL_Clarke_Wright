"""Paquete principal para la resolución del Problema de Enrutamiento de Vehículos con Capacidad (CVRP)
mediante el Algoritmo de Ahorros de Clarke & Wright.
"""

from src.red_logistica import RedLogistica
from src.clarke_wright import AhorroPar, ResultadoClarkeWright, resolver_clarke_wright
from src.visualizador import (
    COLOR_MAYOR_COSTO,
    COLOR_MENOR_COSTO,
    calcular_colores_por_costo_ruta,
    construir_red_pyvis,
    generar_html_red,
    obtener_aristas_rutas_optimas,
)

__all__ = [
    "RedLogistica",
    "AhorroPar",
    "ResultadoClarkeWright",
    "resolver_clarke_wright",
    "COLOR_MAYOR_COSTO",
    "COLOR_MENOR_COSTO",
    "calcular_colores_por_costo_ruta",
    "construir_red_pyvis",
    "generar_html_red",
    "obtener_aristas_rutas_optimas",
]
