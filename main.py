"""Script principal que ejecuta el caso de estudio analítico del Algoritmo de Clarke & Wright (CVRP)."""

from src.clarke_wright import resolver_clarke_wright
from src.red_logistica import RedLogistica


def construir_caso_estudio() -> RedLogistica:
    """Construye la instancia del caso de estudio analítico con 1 depósito y 4 clientes."""
    demandas = {
        1: 4.0,
        2: 3.0,
        3: 5.0,
        4: 3.0,
    }
    capacidad_q = 10.0
    matriz_distancias = [
        [0.0, 10.0, 12.0, 15.0, 8.0],
        [10.0, 0.0, 6.0, 14.0, 12.0],
        [12.0, 6.0, 0.0, 9.0, 15.0],
        [15.0, 14.0, 9.0, 0.0, 10.0],
        [8.0, 12.0, 15.0, 10.0, 0.0],
    ]
    return RedLogistica(
        demandas=demandas,
        capacidad_vehiculo=capacidad_q,
        matriz_distancias=matriz_distancias,
    )


def main() -> None:
    """Punto de entrada principal para resolver e imprimir el caso de estudio en consola."""
    red = construir_caso_estudio()
    resultado = resolver_clarke_wright(red)

    print("=" * 72)
    print("  ALGORITMO DE CLARKE & WRIGHT (SAVINGS) - CASO DE ESTUDIO CVRP")
    print("=" * 72)
    print(f"Depósito central        : Nodo {red.deposito}")
    print(f"Clientes                : {red.clientes}")
    print(f"Demandas (q_i)          : {red.demandas}")
    print(f"Capacidad vehículo (Q)  : {red.capacidad_vehiculo:.1f}")
    print("-" * 72)

    print("\n1. TABLA DE AHORROS ORDENADOS (S_ij = d_0i + d_0j - d_ij):")
    for idx, item in enumerate(resultado.ahorros_ordenados, start=1):
        d_0i = red.distancia(0, item.nodo_i)
        d_0j = red.distancia(0, item.nodo_j)
        d_ij = red.distancia(item.nodo_i, item.nodo_j)
        print(
            f"   {idx}. Par ({item.nodo_i}, {item.nodo_j}): "
            f"{d_0i:.1f} + {d_0j:.1f} - {d_ij:.1f} = {item.ahorro:.1f}"
        )

    print("\n2. TRAZABILIDAD DE FUSIÓN DE RUTAS:")
    for paso in resultado.trazabilidad_fusiones:
        print(f"   - {paso}")

    print("\n3. RESUMEN DE SOLUCIÓN ÓPTIMA:")
    print(f"   Rutas óptimas     : {resultado.rutas_finales}")
    for idx, ruta in enumerate(resultado.rutas_finales, start=1):
        carga = red.demanda_ruta(ruta)
        dist = red.distancia_ruta(ruta)
        print(
            f"     * Vehículo {idx}: {ruta} | Carga: {carga:.1f}/{red.capacidad_vehiculo:.1f} | Distancia: {dist:.1f}"
        )
    print(f"   Distancia inicial : {resultado.distancia_inicial:.1f}")
    print(f"   Distancia total   : {resultado.distancia_total:.1f}")
    print(f"   Ahorro total      : {resultado.ahorro_total:.1f}")
    print("=" * 72)


if __name__ == "__main__":
    main()
