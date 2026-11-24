# CVRP - Algoritmo de Ahorros de Clarke & Wright

Implementación en Python de la heurística de ahorros de **Clarke & Wright (1964)** para el Problema de Enrutamiento de Vehículos con Capacidad (*Capacitated Vehicle Routing Problem* - CVRP).

## Modelo del Problema

Se tiene un depósito central (nodo `0`) y $n$ clientes $\{1, \dots, n\}$ con demandas conocidas $q_i$, atendidos por una flota homogénea de vehículos con capacidad máxima $Q$ sobre una matriz de distancias simétricas $d_{ij}$.

El algoritmo parte de $n$ rutas directas $[0, i, 0]$ y calcula para cada par de clientes $(i, j)$ con $i < j$ el ahorro en distancia que produce atenderlos en una misma ruta:

$$S_{ij} = d_{0i} + d_{0j} - d_{ij}$$

Los pares se ordenan de mayor a menor ahorro y se fusionan iterativamente siempre que:
1. $i$ y $j$ pertenezcan a rutas distintas.
2. Ambos nodos estén conectados directamente al depósito `0` en los extremos de sus rutas actuales.
3. La demanda acumulada de ambas rutas no supere la capacidad $Q$.

---

## Organización del Código

- `src/red_logistica.py`: Clase `RedLogistica`. Valida que la matriz de distancias sea cuadrada, simétrica y sin valores negativos, y que ninguna demanda individual supere $Q$. Incluye lectura y escritura de escenarios en JSON.
- `src/clarke_wright.py`: Función `resolver_clarke_wright` y estructura `ResultadoClarkeWright` con los ahorros ordenados, las rutas finales, distancias y registro de fusiones.
- `src/visualizador.py`: Construcción del grafo de rutas con `pyvis`.
- `app.py`: Interfaz web en `streamlit` con parámetros en barra lateral (selección de escenario, edición de capacidad, demandas y distancias) y panel principal con el grafo y tablas de resultados.
- `main.py`: Ejecución directa del caso de estudio por consola.
- `data/`: Escenarios de prueba en formato JSON.
- `docs/explicacion_codigo.md`: Explicación detallada del funcionamiento del algoritmo y guía archivo por archivo del código.
- `tests/test_clarke_wright.py`: Pruebas unitarias con `pytest`.

---

## Instalación

```powershell
pip install -r requirements.txt
```

## Uso

**Ejecución en consola:**
```powershell
python main.py
```

**Interfaz web:**
```powershell
streamlit run app.py
```

**Pruebas unitarias:**
```powershell
pytest
```

---

## Caso de Estudio Base

Parámetros (`data/caso_estudio_informe.json`):
- **Capacidad ($Q$)**: `10.0`
- **Demandas**: $q_1 = 4$, $q_2 = 3$, $q_3 = 5$, $q_4 = 3$
- **Resultados**:
  - Rutas finales: `[0, 2, 3, 0]` (carga `8/10`, distancia `36.0`) y `[0, 1, 4, 0]` (carga `7/10`, distancia `30.0`)
  - Distancia inicial: `90.0`
  - Distancia total: `66.0`
  - Ahorro total: `24.0`
