"""Implementación del Algoritmo de Ahorros de Clarke & Wright (1964) para el CVRP."""

from dataclasses import dataclass
from typing import Dict, List, Tuple

from src.red_logistica import RedLogistica


@dataclass(frozen=True)
class AhorroPar:
    """Representa el ahorro S_ij obtenido al unir los clientes i y j en una misma ruta.

    Attributes:
        nodo_i (int): Identificador del primer cliente (i < j).
        nodo_j (int): Identificador del segundo cliente (j > i).
        ahorro (float): Valor del ahorro S_ij = d_0i + d_0j - d_ij.
    """

    nodo_i: int
    nodo_j: int
    ahorro: float


@dataclass
class ResultadoClarkeWright:
    """Contiene los resultados completos y trazabilidad del Algoritmo de Clarke & Wright.

    Attributes:
        ahorros_ordenados (List[AhorroPar]): Lista de ahorros S_ij ordenada de forma descendente.
        rutas_finales (List[List[int]]): Lista de rutas finales [0, ..., 0].
        distancia_total (float): Distancia total acumulada de las rutas finales.
        distancia_inicial (float): Distancia total inicial con rutas individuales [0, i, 0].
        ahorro_total (float): Ahorro total efectivo logrado (distancia_inicial - distancia_total).
        trazabilidad_fusiones (List[str]): Registro paso a paso de la evaluación de cada ahorro.
    """

    ahorros_ordenados: List[AhorroPar]
    rutas_finales: List[List[int]]
    distancia_total: float
    distancia_inicial: float
    ahorro_total: float
    trazabilidad_fusiones: List[str]

    def __getitem__(self, item: str) -> object:
        """Permite acceso tipo diccionario además del acceso por atributos de dataclass."""
        return getattr(self, item)

    def to_dict(self) -> Dict[str, object]:
        """Convierte el resultado a un diccionario estándar."""
        return {
            "ahorros_ordenados": self.ahorros_ordenados,
            "rutas_finales": self.rutas_finales,
            "distancia_total": self.distancia_total,
            "distancia_inicial": self.distancia_inicial,
            "ahorro_total": self.ahorro_total,
            "trazabilidad_fusiones": self.trazabilidad_fusiones,
        }


def calcular_ahorros(red: RedLogistica) -> List[AhorroPar]:
    """Calcula la lista de ahorros S_ij = d_0i + d_0j - d_ij para todo par i < j y la ordena descendentemente.

    Args:
        red: Instancia de RedLogistica validada.

    Returns:
        Lista de objetos AhorroPar ordenada en orden estrictamente descendente por ahorro
        (desempatando de forma determinista por par (i, j) ascendente).
    """
    ahorros: List[AhorroPar] = []
    clientes = red.clientes
    d0 = red.deposito

    for idx_i, i in enumerate(clientes):
        for j in clientes[idx_i + 1 :]:
            s_ij = red.distancia(d0, i) + red.distancia(d0, j) - red.distancia(i, j)
            ahorros.append(AhorroPar(nodo_i=i, nodo_j=j, ahorro=s_ij))

    ahorros.sort(key=lambda par: (-par.ahorro, par.nodo_i, par.nodo_j))
    return ahorros


def _es_extremo(seq_clientes: List[int], nodo: int) -> bool:
    """Verifica si un cliente se encuentra en un extremo conectado directamente al depósito."""
    return len(seq_clientes) > 0 and (
        seq_clientes[0] == nodo or seq_clientes[-1] == nodo
    )


def _fusionar_secuencias(
    seq_a: List[int], nodo_a: int, seq_b: List[int], nodo_b: int
) -> List[int]:
    """Fusiona dos secuencias internas de clientes conectando directamente nodo_a con nodo_b.

    Como las distancias son simétricas, si nodo_a no está al final de seq_a o nodo_b no está al
    inicio de seq_b, se invierte la sub-ruta correspondiente para que la conexión ocurra extremo con extremo.
    """
    ruta_izq = list(seq_a)
    ruta_der = list(seq_b)

    if ruta_izq[-1] != nodo_a:
        ruta_izq.reverse()

    if ruta_der[0] != nodo_b:
        ruta_der.reverse()

    return ruta_izq + ruta_der


def resolver_clarke_wright(red: RedLogistica) -> ResultadoClarkeWright:
    """Ejecuta el Algoritmo Paralelo de Ahorros de Clarke & Wright sobre una red logística.

    Pasos del algoritmo:
      1. Calcula S_ij = d_0i + d_0j - d_ij para todo par i < j.
      2. Ordena los pares en orden descendente de ahorro S_ij.
      3. Parte de n rutas individuales [0, i, 0] y fusiona iterativamente aquellas que:
         (a) pertenezcan a rutas distintas,
         (b) ambos nodos i y j sean extremos adyacentes al depósito 0 en sus rutas actuales,
         (c) la suma de demandas de ambas rutas no supere la capacidad Q (y el ahorro sea >= 0).

    Args:
        red: Instancia de RedLogistica con los datos del problema CVRP.

    Returns:
        ResultadoClarkeWright con ahorros_ordenados, rutas_finales, distancia_total,
        distancia_inicial, ahorro_total y trazabilidad_fusiones.
    """
    ahorros_ordenados = calcular_ahorros(red)

    # Representamos internamente cada ruta activa por su secuencia de clientes (sin los 0 de los extremos)
    rutas_internas: Dict[int, List[int]] = {i: [i] for i in red.clientes}
    demanda_por_ruta: Dict[int, float] = {i: red.demandas[i] for i in red.clientes}
    ruta_de_cliente: Dict[int, int] = {i: i for i in red.clientes}

    distancia_inicial = sum(
        2.0 * red.distancia(red.deposito, i) for i in red.clientes
    )

    trazabilidad: List[str] = []

    for par in ahorros_ordenados:
        i, j, s_ij = par.nodo_i, par.nodo_j, par.ahorro

        if s_ij <= 0:
            trazabilidad.append(
                f"Par ({i}, {j}) | S_{i}{j} = {s_ij:.1f}: Omitido (ahorro no positivo)."
            )
            continue

        id_ruta_i = ruta_de_cliente[i]
        id_ruta_j = ruta_de_cliente[j]

        # Condición (a): i y j deben estar en rutas distintas
        if id_ruta_i == id_ruta_j:
            trazabilidad.append(
                f"Par ({i}, {j}) | S_{i}{j} = {s_ij:.1f}: Rechazado (nodos ya están en la misma ruta)."
            )
            continue

        seq_i = rutas_internas[id_ruta_i]
        seq_j = rutas_internas[id_ruta_j]

        # Condición (b): ambos nodos deben ser extremos conectados directamente al depósito 0
        if not (_es_extremo(seq_i, i) and _es_extremo(seq_j, j)):
            trazabilidad.append(
                f"Par ({i}, {j}) | S_{i}{j} = {s_ij:.1f}: Rechazado (al menos un nodo ya es interior)."
            )
            continue

        # Condición (c): la demanda combinada no debe superar la capacidad Q
        nueva_demanda = demanda_por_ruta[id_ruta_i] + demanda_por_ruta[id_ruta_j]
        if nueva_demanda > red.capacidad_vehiculo:
            trazabilidad.append(
                f"Par ({i}, {j}) | S_{i}{j} = {s_ij:.1f}: Rechazado "
                f"(demanda combinada {nueva_demanda:.1f} > Q = {red.capacidad_vehiculo:.1f})."
            )
            continue

        # Fusión factible: unir rutas extremo con extremo
        nueva_seq = _fusionar_secuencias(seq_i, i, seq_j, j)
        del rutas_internas[id_ruta_i]
        del rutas_internas[id_ruta_j]
        rutas_internas[id_ruta_i] = nueva_seq
        demanda_por_ruta[id_ruta_i] = nueva_demanda

        for nodo in seq_j:
            ruta_de_cliente[nodo] = id_ruta_i

        del demanda_por_ruta[id_ruta_j]

        ruta_formateada = [red.deposito] + nueva_seq + [red.deposito]
        trazabilidad.append(
            f"Par ({i}, {j}) | S_{i}{j} = {s_ij:.1f}: FUSIONADO -> Ruta {ruta_formateada} "
            f"(Carga: {nueva_demanda:.1f}/{red.capacidad_vehiculo:.1f})."
        )

    rutas_finales: List[List[int]] = [
        [red.deposito] + seq + [red.deposito] for seq in rutas_internas.values()
    ]

    distancia_total = sum(red.distancia_ruta(ruta) for ruta in rutas_finales)
    ahorro_total = distancia_inicial - distancia_total

    return ResultadoClarkeWright(
        ahorros_ordenados=ahorros_ordenados,
        rutas_finales=rutas_finales,
        distancia_total=distancia_total,
        distancia_inicial=distancia_inicial,
        ahorro_total=ahorro_total,
        trazabilidad_fusiones=trazabilidad,
    )
