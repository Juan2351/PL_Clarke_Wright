# Algoritmo de Ahorros de Clarke & Wright (CVRP)

Implementación modular en Python del **Algoritmo de Ahorros de Clarke & Wright (1964)** (*Savings Algorithm*) para la resolución del **Problema de Enrutamiento de Vehículos con Capacidad (CVRP - Capacitated Vehicle Routing Problem)**.

---

## Fundamento Matemático

Dado un depósito central (nodo $0$) y un conjunto de $n$ clientes $\{1, 2, \dots, n\}$ con demandas conocidas $q_i$, una flota homogénea de vehículos con capacidad máxima $Q$, y una matriz de distancias simétricas $d_{ij}$:

1. **Solución inicial**: Se parte de $n$ rutas individuales de ida y vuelta $[0, i, 0]$ con costo total inicial:
   $$D_{\text{inicial}} = \sum_{i=1}^{n} 2 \cdot d_{0i}$$

2. **Cálculo de ahorros**: Para cada par de clientes $(i, j)$ con $i < j$, el ahorro $S_{ij}$ obtenido al consolidar ambos clientes en una sola ruta en lugar de atenderlos en rutas separadas está dado por:
   $$S_{ij} = d_{0i} + d_{0j} - d_{ij}$$

3. **Ordenamiento**: Los pares $(i, j)$ se ordenan de forma estrictamente descendente según su ahorro $S_{ij} > 0$.

4. **Fusión iterativa (Versión Paralela)**: Se evalúa cada par $(i, j)$ en orden y se fusionan sus rutas si y solo si se cumplen tres condiciones:
   - **(a) Rutas distintas**: $i$ y $j$ no pertenecen actualmente a la misma ruta.
   - **(b) Nodos extremos**: Tanto $i$ como $j$ están conectados directamente al depósito $0$ (son el primer o último cliente de sus respectivas rutas).
   - **(c) Factibilidad de capacidad**: La suma de las demandas de ambas rutas no excede la capacidad máxima del vehículo ($Q_{\text{ruta}(i)} + Q_{\text{ruta}(j)} \le Q$).

---

## Estructura del Proyecto

```text
.
├── src/
│   ├── __init__.py          # Exportación de la interfaz pública del paquete
│   ├── red_logistica.py     # Clase RedLogistica y validación de invariantes del CVRP
│   └── clarke_wright.py     # Algoritmo de Clarke & Wright y estructuras de resultados
├── tests/
│   └── test_clarke_wright.py # Suite de pruebas unitarias con pytest
├── main.py                  # Script ejecutable con el caso de estudio analítico
├── .gitignore               # Exclusiones de archivos temporales y caché de Python
└── README.md                # Documentación del proyecto
```

---

## Requisitos e Instalación

- **Python** $\ge 3.10$
- **pytest** (para ejecutar la suite de pruebas unitarias)

```bash
pip install pytest
```

---

## Uso y Caso de Estudio

Para ejecutar el caso de estudio analítico incluido ($4$ clientes, capacidad $Q = 10$):

```bash
python main.py
```

### Salida en Consola

```text
========================================================================
  ALGORITMO DE CLARKE & WRIGHT (SAVINGS) - CASO DE ESTUDIO CVRP
========================================================================
Depósito central        : Nodo 0
Clientes                : [1, 2, 3, 4]
Demandas (q_i)          : {1: 4.0, 2: 3.0, 3: 5.0, 4: 3.0}
Capacidad vehículo (Q)  : 10.0
------------------------------------------------------------------------

1. TABLA DE AHORROS ORDENADOS (S_ij = d_0i + d_0j - d_ij):
   1. Par (2, 3): 12.0 + 15.0 - 9.0 = 18.0
   2. Par (1, 2): 10.0 + 12.0 - 6.0 = 16.0
   3. Par (3, 4): 15.0 + 8.0 - 10.0 = 13.0
   4. Par (1, 3): 10.0 + 15.0 - 14.0 = 11.0
   5. Par (1, 4): 10.0 + 8.0 - 12.0 = 6.0
   6. Par (2, 4): 12.0 + 8.0 - 15.0 = 5.0

2. TRAZABILIDAD DE FUSIÓN DE RUTAS:
   - Par (2, 3) | S_23 = 18.0: FUSIONADO -> Ruta [0, 2, 3, 0] (Carga: 8.0/10.0).
   - Par (1, 2) | S_12 = 16.0: Rechazado (demanda combinada 12.0 > Q = 10.0).
   - Par (3, 4) | S_34 = 13.0: Rechazado (demanda combinada 11.0 > Q = 10.0).
   - Par (1, 3) | S_13 = 11.0: Rechazado (demanda combinada 12.0 > Q = 10.0).
   - Par (1, 4) | S_14 = 6.0: FUSIONADO -> Ruta [0, 1, 4, 0] (Carga: 7.0/10.0).
   - Par (2, 4) | S_24 = 5.0: Rechazado (demanda combinada 15.0 > Q = 10.0).

3. RESUMEN DE SOLUCIÓN ÓPTIMA:
   Rutas óptimas     : [[0, 2, 3, 0], [0, 1, 4, 0]]
     * Vehículo 1: [0, 2, 3, 0] | Carga: 8.0/10.0 | Distancia: 36.0
     * Vehículo 2: [0, 1, 4, 0] | Carga: 7.0/10.0 | Distancia: 30.0
   Distancia inicial : 90.0
   Distancia total   : 66.0
   Ahorro total      : 24.0
========================================================================
```

---

## Ejecución de Pruebas

Para ejecutar la suite de pruebas automatizadas:

```bash
python -m pytest -v
```

Las pruebas verifican:
1. **Convergencia exacta** contra el caso de estudio manual (`distancia_total == 66.0`, `ahorro_total == 24.0` y rutas `[[0, 2, 3, 0], [0, 1, 4, 0]]`).
2. **Validación de capacidad**: Lanzamiento de `ValueError` cuando la demanda individual de un cliente supera $Q$ ($q_i > Q$).
3. **Validación de no negatividad y simetría**: Lanzamiento de `ValueError` ante distancias negativas ($d_{ij} < 0$) o matrices asimétricas/no cuadradas.
