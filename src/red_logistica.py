"""Módulo que define la estructura de datos, validaciones y persistencia JSON de la red logística para el CVRP."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Sequence


class RedLogistica:
    """Representa una red logística para el Problema de Enrutamiento de Vehículos con Capacidad (CVRP).

    Almacena el depósito central (nodo 0), los clientes (1..n), sus demandas individuales,
    la capacidad homogénea de la flota de vehículos y la matriz de distancias simétricas.

    Attributes:
        deposito (int): Identificador del nodo depósito (siempre 0).
        capacidad_vehiculo (float): Capacidad máxima homogénea Q de cada vehículo.
        demandas (Dict[int, float]): Diccionario que mapea cada cliente i (1..n) a su demanda q_i.
        matriz_distancias (List[List[float]]): Matriz cuadrada y simétrica (n+1)x(n+1) de distancias d_ij.
        clientes (List[int]): Lista ordenada de identificadores de clientes [1, 2, ..., n].
        nombre (str): Nombre descriptivo de la instancia de la red logística.
    """

    def __init__(
        self,
        demandas: Dict[int, float] | Dict[str, float] | Sequence[float],
        capacidad_vehiculo: float,
        matriz_distancias: Sequence[Sequence[float]],
        nombre: str = "Red Logística CVRP",
    ) -> None:
        """Inicializa y valida la red logística.

        Args:
            demandas: Diccionario {cliente_id: demanda} para clientes 1..n, o secuencia de demandas
                donde el índice corresponde a los clientes 1..n (o 0..n si incluye el depósito con demanda 0).
            capacidad_vehiculo: Capacidad máxima Q de cada vehículo (Q > 0).
            matriz_distancias: Matriz cuadrada (n+1)x(n+1) con las distancias entre todos los nodos (0..n).
            nombre: Nombre opcional de la instancia.

        Raises:
            ValueError: Si la capacidad no es positiva, si la matriz no es cuadrada o simétrica,
                si existen distancias negativas, o si la demanda de algún cliente supera la capacidad Q
                o es negativa.
        """
        if capacidad_vehiculo <= 0:
            raise ValueError(
                f"La capacidad del vehículo Q debe ser estrictamente positiva (recibido: {capacidad_vehiculo})."
            )

        self.deposito: int = 0
        self.nombre: str = nombre
        self.capacidad_vehiculo: float = float(capacidad_vehiculo)
        self.matriz_distancias: List[List[float]] = [
            [float(valor) for valor in fila] for fila in matriz_distancias
        ]

        num_nodos = len(self.matriz_distancias)
        if num_nodos < 2:
            raise ValueError(
                "La matriz de distancias debe contener al menos el depósito (nodo 0) y un cliente (nodo 1)."
            )

        self._validar_matriz_distancias(num_nodos)
        self.demandas: Dict[int, float] = self._procesar_y_validar_demandas(
            demandas, num_nodos - 1
        )
        self.clientes: List[int] = sorted(self.demandas.keys())

    def _validar_matriz_distancias(self, num_nodos: int) -> None:
        """Valida que la matriz de distancias sea cuadrada, no negativa y simétrica."""
        for i, fila in enumerate(self.matriz_distancias):
            if len(fila) != num_nodos:
                raise ValueError(
                    f"La matriz de distancias debe ser cuadrada. "
                    f"Se esperaban {num_nodos} columnas en la fila {i}, pero se encontraron {len(fila)}."
                )
            for j, d_ij in enumerate(fila):
                if d_ij < 0:
                    raise ValueError(
                        f"Las distancias no pueden ser negativas. Se encontró d_({i},{j}) = {d_ij}."
                    )
                if i == j and d_ij != 0.0:
                    raise ValueError(
                        f"La diagonal principal de la matriz de distancias debe ser 0. "
                        f"Se encontró d_({i},{i}) = {d_ij}."
                    )

        tol = 1e-9
        for i in range(num_nodos):
            for j in range(i + 1, num_nodos):
                if abs(self.matriz_distancias[i][j] - self.matriz_distancias[j][i]) > tol:
                    raise ValueError(
                        f"La matriz de distancias debe ser simétrica. "
                        f"d_({i},{j}) = {self.matriz_distancias[i][j]} != d_({j},{i}) = {self.matriz_distancias[j][i]}."
                    )

    def _procesar_y_validar_demandas(
        self,
        demandas: Dict[int, float] | Dict[str, float] | Sequence[float],
        num_clientes: int,
    ) -> Dict[int, float]:
        """Normaliza y valida que las demandas de los clientes estén dentro del rango permitido (0 <= q_i <= Q)."""
        demandas_dict: Dict[int, float] = {}

        if isinstance(demandas, dict):
            demandas_int: Dict[int, float] = {
                int(k): float(v) for k, v in demandas.items()
            }
            clientes_esperados = set(range(1, num_clientes + 1))
            claves = set(demandas_int.keys()) - {0}
            if claves != clientes_esperados:
                raise ValueError(
                    f"Las claves de demandas deben corresponder exactamente a los clientes 1..{num_clientes}. "
                    f"Recibido: {sorted(claves)}."
                )
            for cliente_id in range(1, num_clientes + 1):
                demandas_dict[cliente_id] = float(demandas_int[cliente_id])
        else:
            if len(demandas) == num_clientes:
                for idx, val in enumerate(demandas, start=1):
                    demandas_dict[idx] = float(val)
            elif len(demandas) == num_clientes + 1:
                for idx in range(1, num_clientes + 1):
                    demandas_dict[idx] = float(demandas[idx])
            else:
                raise ValueError(
                    f"La cantidad de demandas ({len(demandas)}) no coincide con el número de clientes ({num_clientes})."
                )

        for cliente_id, q_i in demandas_dict.items():
            if q_i < 0:
                raise ValueError(
                    f"La demanda del cliente {cliente_id} no puede ser negativa (q_{cliente_id} = {q_i})."
                )
            if q_i > self.capacidad_vehiculo:
                raise ValueError(
                    f"La demanda del cliente {cliente_id} (q_{cliente_id} = {q_i}) supera "
                    f"la capacidad máxima del vehículo (Q = {self.capacidad_vehiculo})."
                )

        return demandas_dict

    def distancia(self, nodo_origen: int, nodo_destino: int) -> float:
        """Retorna la distancia d_ij entre dos nodos de la red."""
        return self.matriz_distancias[nodo_origen][nodo_destino]

    def demanda_ruta(self, ruta: Sequence[int]) -> float:
        """Calcula la demanda total acumulada de los clientes visitados en una ruta."""
        return sum(self.demandas.get(nodo, 0.0) for nodo in ruta if nodo != self.deposito)

    def distancia_ruta(self, ruta: Sequence[int]) -> float:
        """Calcula la distancia total recorrida en una secuencia de nodos."""
        if len(ruta) < 2:
            return 0.0
        return sum(
            self.matriz_distancias[ruta[k]][ruta[k + 1]] for k in range(len(ruta) - 1)
        )

    def a_diccionario(self) -> Dict[str, Any]:
        """Serializa la red logística a un diccionario compatible con JSON."""
        return {
            "nombre": self.nombre,
            "deposito": self.deposito,
            "capacidad_vehiculo": self.capacidad_vehiculo,
            "demandas": {str(k): v for k, v in self.demandas.items()},
            "matriz_distancias": self.matriz_distancias,
        }

    @classmethod
    def desde_diccionario(cls, datos: Dict[str, Any]) -> RedLogistica:
        """Construye una instancia de RedLogistica a partir de un diccionario."""
        if "capacidad_vehiculo" not in datos or "demandas" not in datos or "matriz_distancias" not in datos:
            raise ValueError(
                "El diccionario JSON debe contener las claves 'capacidad_vehiculo', 'demandas' y 'matriz_distancias'."
            )
        return cls(
            demandas=datos["demandas"],
            capacidad_vehiculo=float(datos["capacidad_vehiculo"]),
            matriz_distancias=datos["matriz_distancias"],
            nombre=str(datos.get("nombre", "Red Logística CVRP")),
        )

    @classmethod
    def cargar_desde_json(cls, ruta_archivo: str | Path) -> RedLogistica:
        """Carga una topología de red logística desde un archivo JSON."""
        ruta = Path(ruta_archivo)
        with ruta.open("r", encoding="utf-8") as archivo:
            datos = json.load(archivo)
        return cls.desde_diccionario(datos)

    def guardar_en_json(self, ruta_archivo: str | Path) -> None:
        """Exporta la red logística actual a un archivo JSON."""
        ruta = Path(ruta_archivo)
        ruta.parent.mkdir(parents=True, exist_ok=True)
        with ruta.open("w", encoding="utf-8") as archivo:
            json.dump(self.a_diccionario(), archivo, indent=2, ensure_ascii=False)
