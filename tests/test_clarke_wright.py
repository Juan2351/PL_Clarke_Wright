"""Suite de pruebas unitarias para la red logística y el Algoritmo de Clarke & Wright."""

from typing import Dict, List
import pytest

from src.clarke_wright import resolver_clarke_wright
from src.red_logistica import RedLogistica


@pytest.fixture
def datos_caso_estudio() -> Dict[str, object]:
    """Proporciona los datos del caso de estudio analítico."""
    return {
        "demandas": {1: 4.0, 2: 3.0, 3: 5.0, 4: 3.0},
        "capacidad": 10.0,
        "distancias": [
            [0.0, 10.0, 12.0, 15.0, 8.0],
            [10.0, 0.0, 6.0, 14.0, 12.0],
            [12.0, 6.0, 0.0, 9.0, 15.0],
            [15.0, 14.0, 9.0, 0.0, 10.0],
            [8.0, 12.0, 15.0, 10.0, 0.0],
        ],
    }


def _normalizar_ruta(ruta: List[int]) -> List[int]:
    """Normaliza la orientación de una ruta simétrica [0, ..., 0] para comparaciones deterministas."""
    if len(ruta) > 3 and ruta[1] > ruta[-2]:
        return [ruta[0]] + list(reversed(ruta[1:-1])) + [ruta[-1]]
    return ruta


def test_convergencia_caso_manual(datos_caso_estudio: Dict[str, object]) -> None:
    """Valida la convergencia exacta contra el caso de estudio analítico manual."""
    red = RedLogistica(
        demandas=datos_caso_estudio["demandas"],  # type: ignore[arg-type]
        capacidad_vehiculo=datos_caso_estudio["capacidad"],  # type: ignore[arg-type]
        matriz_distancias=datos_caso_estudio["distancias"],  # type: ignore[arg-type]
    )

    resultado = resolver_clarke_wright(red)

    # Verificar ahorros ordenados esperados: S_23=18, S_12=16, S_34=13, S_13=11, S_14=6, S_24=5
    pares_ahorros = [
        (item.nodo_i, item.nodo_j, item.ahorro)
        for item in resultado.ahorros_ordenados
    ]
    assert pares_ahorros == [
        (2, 3, 18.0),
        (1, 2, 16.0),
        (3, 4, 13.0),
        (1, 3, 11.0),
        (1, 4, 6.0),
        (2, 4, 5.0),
    ]

    # Verificar distancia inicial, distancia final (66.0) y ahorro total (24.0)
    assert resultado.distancia_inicial == pytest.approx(90.0)
    assert resultado.distancia_total == pytest.approx(66.0)
    assert resultado.ahorro_total == pytest.approx(24.0)

    # Verificar rutas finales óptimas: [[0, 2, 3, 0], [0, 1, 4, 0]]
    assert resultado.rutas_finales == [[0, 2, 3, 0], [0, 1, 4, 0]]
    rutas_normalizadas = sorted(
        [_normalizar_ruta(r) for r in resultado.rutas_finales]
    )
    assert rutas_normalizadas == [[0, 1, 4, 0], [0, 2, 3, 0]]


def test_rechazo_demanda_supera_capacidad(
    datos_caso_estudio: Dict[str, object],
) -> None:
    """Valida que se lance un ValueError cuando la demanda individual q_i supera la capacidad Q."""
    demandas_invalidas = {1: 4.0, 2: 11.0, 3: 5.0, 4: 3.0}

    with pytest.raises(ValueError, match="supera la capacidad máxima"):
        RedLogistica(
            demandas=demandas_invalidas,
            capacidad_vehiculo=10.0,
            matriz_distancias=datos_caso_estudio["distancias"],  # type: ignore[arg-type]
        )


def test_rechazo_distancias_negativas(datos_caso_estudio: Dict[str, object]) -> None:
    """Valida que se lance un ValueError ante la presencia de distancias negativas en la matriz."""
    matriz_negativa = [
        [0.0, 10.0, 12.0, 15.0, 8.0],
        [10.0, 0.0, -6.0, 14.0, 12.0],
        [12.0, -6.0, 0.0, 9.0, 15.0],
        [15.0, 14.0, 9.0, 0.0, 10.0],
        [8.0, 12.0, 15.0, 10.0, 0.0],
    ]

    with pytest.raises(ValueError, match="no pueden ser negativas"):
        RedLogistica(
            demandas=datos_caso_estudio["demandas"],  # type: ignore[arg-type]
            capacidad_vehiculo=10.0,
            matriz_distancias=matriz_negativa,
        )


def test_rechazo_matriz_asimetrica_o_no_cuadrada(
    datos_caso_estudio: Dict[str, object],
) -> None:
    """Valida que se lance un ValueError si la matriz no es simétrica o no es cuadrada."""
    matriz_asimetrica = [
        [0.0, 99.0, 12.0, 15.0, 8.0],
        [10.0, 0.0, 6.0, 14.0, 12.0],
        [12.0, 6.0, 0.0, 9.0, 15.0],
        [15.0, 14.0, 9.0, 0.0, 10.0],
        [8.0, 12.0, 15.0, 10.0, 0.0],
    ]

    with pytest.raises(ValueError, match="simétrica"):
        RedLogistica(
            demandas=datos_caso_estudio["demandas"],  # type: ignore[arg-type]
            capacidad_vehiculo=10.0,
            matriz_distancias=matriz_asimetrica,
        )

    matriz_no_cuadrada = [
        [0.0, 10.0],
        [10.0, 0.0, 5.0],
    ]

    with pytest.raises(ValueError, match="cuadrada"):
        RedLogistica(
            demandas={1: 4.0},
            capacidad_vehiculo=10.0,
            matriz_distancias=matriz_no_cuadrada,
        )
