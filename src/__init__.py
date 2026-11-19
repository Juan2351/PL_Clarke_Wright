"""Paquete principal para la resolución del Problema de Enrutamiento de Vehículos con Capacidad (CVRP)
mediante el Algoritmo de Ahorros de Clarke & Wright.
"""

from src.red_logistica import RedLogistica
from src.clarke_wright import AhorroPar, ResultadoClarkeWright, resolver_clarke_wright

__all__ = [
    "RedLogistica",
    "AhorroPar",
    "ResultadoClarkeWright",
    "resolver_clarke_wright",
]
