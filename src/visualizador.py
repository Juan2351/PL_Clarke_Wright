"""Generador de grafos con PyVis para visualizar instancias CVRP y rutas de Clarke & Wright."""

from typing import Dict, List, Tuple
from pyvis.network import Network

from src.clarke_wright import ResultadoClarkeWright
from src.red_logistica import RedLogistica

COLOR_MENOR_COSTO = "#16A34A"  # Verde (ruta de menor distancia)
COLOR_MAYOR_COSTO = "#DC2626"  # Rojo (ruta de mayor distancia)
PALETA_INTERMEDIA: List[str] = [
    "#2563EB",  # Azul
    "#D97706",  # Ámbar
    "#7C3AED",  # Púrpura
    "#0891B2",  # Cian
]


def _normalizar_par(u: int, v: int) -> Tuple[int, int]:
    """Retorna la arista no dirigida en orden canónico (menor, mayor)."""
    return (u, v) if u <= v else (v, u)


def obtener_aristas_rutas_optimas(
    rutas_finales: List[List[int]],
) -> Dict[Tuple[int, int], int]:
    """Extrae un diccionario {(u, v): indice_vehiculo} para todas las aristas utilizadas en la solución."""
    aristas_activas: Dict[Tuple[int, int], int] = {}
    for idx_vehiculo, ruta in enumerate(rutas_finales, start=1):
        for k in range(len(ruta) - 1):
            par = _normalizar_par(ruta[k], ruta[k + 1])
            aristas_activas[par] = idx_vehiculo
    return aristas_activas


def calcular_colores_por_costo_ruta(
    red: RedLogistica,
    rutas_finales: List[List[int]],
) -> Tuple[Dict[int, str], Dict[int, str]]:
    """Asigna colores a cada ruta (1..k) según su costo (distancia total).

    - La ruta con menor distancia se pinta de VERDE (#16A34A).
    - La ruta con mayor distancia se pinta de ROJO (#DC2626).
    - Si hay rutas intermedias o empates, se asignan colores intermedios claros.

    Returns:
        Tupla (color_por_ruta, etiqueta_costo_por_ruta) indexada por número de vehículo (1..k).
    """
    num_rutas = len(rutas_finales)
    if num_rutas == 0:
        return {}, {}

    distancias = {
        idx: red.distancia_ruta(ruta)
        for idx, ruta in enumerate(rutas_finales, start=1)
    }

    if num_rutas == 1:
        return {1: COLOR_MENOR_COSTO}, {1: "Ruta única (Verde)"}

    # Ordenar índices de vehículo de menor a mayor distancia (desempate por índice)
    ordenados = sorted(distancias.keys(), key=lambda idx: (distancias[idx], idx))
    idx_min = ordenados[0]
    idx_max = ordenados[-1]

    colores: Dict[int, str] = {}
    etiquetas: Dict[int, str] = {}

    colores[idx_min] = COLOR_MENOR_COSTO
    etiquetas[idx_min] = "Menor costo (Verde)"

    colores[idx_max] = COLOR_MAYOR_COSTO
    etiquetas[idx_max] = "Mayor costo (Rojo)"

    for pos, idx in enumerate(ordenados[1:-1]):
        colores[idx] = PALETA_INTERMEDIA[pos % len(PALETA_INTERMEDIA)]
        etiquetas[idx] = "Costo intermedio (Azul)"

    return colores, etiquetas


def construir_red_pyvis(
    red: RedLogistica,
    resultado: ResultadoClarkeWright,
    mostrar_aristas_inactivas: bool = False,
    altura_px: int = 440,
) -> Network:
    """Construye la red PyVis con el depósito legible, los clientes y las rutas coloreadas por costo."""
    net = Network(
        height=f"{altura_px}px",
        width="100%",
        directed=False,
        bgcolor="#FFFFFF",
        font_color="#0F172A",
    )

    colores_ruta, etiquetas_ruta = calcular_colores_por_costo_ruta(
        red, resultado.rutas_finales
    )

    vehiculo_de_cliente: Dict[int, int] = {}
    for idx_vehiculo, ruta in enumerate(resultado.rutas_finales, start=1):
        for nodo in ruta:
            if nodo != red.deposito:
                vehiculo_de_cliente[nodo] = idx_vehiculo

    # Depósito con fondo claro y texto oscuro perfectamente legible
    net.add_node(
        red.deposito,
        label="Depósito (0)",
        title=f"Depósito Central (Nodo 0) | Capacidad Q = {red.capacidad_vehiculo:.1f}",
        color={
            "background": "#FEF3C7",
            "border": "#D97706",
            "highlight": {"background": "#FDE68A", "border": "#B45309"},
        },
        shape="box",
        borderWidth=2,
        margin=10,
        font={"size": 15, "color": "#0F172A", "face": "Segoe UI, sans-serif", "bold": True},
    )

    for cliente in red.clientes:
        q_i = red.demandas[cliente]
        idx_v = vehiculo_de_cliente.get(cliente, 1)
        color_v = colores_ruta.get(idx_v, COLOR_MENOR_COSTO)
        etiqueta_v = etiquetas_ruta.get(idx_v, "")

        net.add_node(
            cliente,
            label=f"Cliente {cliente}\n(q={q_i:g})",
            title=(
                f"Cliente {cliente} | Demanda: {q_i:.1f} | "
                f"Ruta {idx_v} ({etiqueta_v})"
            ),
            color={
                "background": "#FFFFFF",
                "border": color_v,
                "highlight": {"background": "#F8FAFC", "border": color_v},
            },
            shape="dot",
            size=20,
            borderWidth=3,
            font={"size": 13, "color": "#0F172A", "face": "Segoe UI, sans-serif"},
        )

    aristas_optimas = obtener_aristas_rutas_optimas(resultado.rutas_finales)
    nodos_totales = [red.deposito] + red.clientes

    for idx_u, u in enumerate(nodos_totales):
        for v in nodos_totales[idx_u + 1 :]:
            par = _normalizar_par(u, v)
            dist = red.distancia(u, v)

            if par in aristas_optimas:
                idx_v = aristas_optimas[par]
                color_arista = colores_ruta.get(idx_v, COLOR_MENOR_COSTO)
                etiqueta_v = etiquetas_ruta.get(idx_v, "")
                net.add_edge(
                    u,
                    v,
                    label=f"{dist:g}",
                    title=f"Ruta {idx_v} ({etiqueta_v}): ({u}, {v}) | Distancia = {dist:.1f}",
                    color=color_arista,
                    width=3.8,
                    font={"size": 13, "color": "#0F172A", "background": "#FFFFFF"},
                )
            elif mostrar_aristas_inactivas:
                net.add_edge(
                    u,
                    v,
                    label=f"{dist:g}",
                    title=f"Arco no utilizado ({u}, {v}) | Distancia = {dist:.1f}",
                    color="#CBD5E1",
                    width=1.0,
                    dashes=True,
                    font={"size": 10, "color": "#94A3B8"},
                )

    net.set_options(
        """
        {
          "physics": {
            "enabled": true,
            "solver": "forceAtlas2Based",
            "forceAtlas2Based": {
              "gravitationalConstant": -85,
              "centralGravity": 0.015,
              "springLength": 150,
              "springConstant": 0.07
            },
            "stabilization": {
              "iterations": 120
            }
          },
          "interaction": {
            "hover": true,
            "navigationButtons": false
          }
        }
        """
    )

    return net


def generar_html_red(
    red: RedLogistica,
    resultado: ResultadoClarkeWright,
    mostrar_aristas_inactivas: bool = False,
    altura_px: int = 440,
) -> str:
    """Genera el HTML del grafo PyVis."""
    net = construir_red_pyvis(
        red=red,
        resultado=resultado,
        mostrar_aristas_inactivas=mostrar_aristas_inactivas,
        altura_px=altura_px,
    )
    return net.generate_html()
