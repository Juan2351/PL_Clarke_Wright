# Documentación Técnica y Guía del Código

Este documento explica el funcionamiento interno del proyecto, desde el modelo matemático del Algoritmo de Clarke & Wright hasta la ubicación exacta de cada responsabilidad dentro del código fuente.

---

## 1. Flujo General de Funcionamiento

El sistema resuelve el **Problema de Enrutamiento de Vehículos con Capacidad (CVRP)** en cuatro etapas secuenciales:

1. **Modelado y Validación (`src/red_logistica.py`)**: Se reciben los datos del depósito (`0`), los clientes (`1..n`), sus demandas $q_i$, la capacidad máxima $Q$ de cada vehículo y la matriz de distancias $d_{ij}$. Antes de ejecutar cualquier cálculo, se verifica que la instancia sea matemáticamente válida.
2. **Optimización por Ahorros (`src/clarke_wright.py`)**: Se calculan los ahorros $S_{ij} = d_{0i} + d_{0j} - d_{ij}$ para cada par de clientes, se ordenan de mayor a menor y se fusionan las rutas de forma iterativa respetando las restricciones de capacidad y de conexión extremo a extremo.
3. **Construcción Visual del Grafo (`src/visualizador.py`)**: A partir de las rutas finales, se identifican los arcos activos, se calcula cuál ruta tiene el menor costo (pintándola de **verde**) y cuál tiene el mayor costo (pintándola de **rojo**), y se genera el grafo interactivo con PyVis.
4. **Presentación y Edición (`app.py` y `main.py`)**: Se expone el modelo tanto por consola como mediante una interfaz web en Streamlit donde se pueden editar nodos, demandas y distancias o crear redes desde cero.

---

## 2. Mapa del Código: Qué Hace Cada Archivo y Función

### 2.1. `src/red_logistica.py` — Modelo de Datos y Validaciones

La clase `RedLogistica` encapsula toda la información de la red y garantiza que no entren datos inconsistentes al algoritmo.

- **`__init__(demandas, capacidad_vehiculo, matriz_distancias, nombre)`**:
  - Verifica que la capacidad del vehículo sea estrictamente positiva ($Q > 0$).
  - Llama a los métodos privados de validación y almacena `self.deposito = 0`, `self.clientes`, `self.demandas` y `self.matriz_distancias`.
- **`_validar_matriz_distancias(num_nodos)`**:
  - Comprueba que la matriz sea **cuadrada** de tamaño $(n+1) \times (n+1)$.
  - Comprueba que **no existan distancias negativas** ($d_{ij} \ge 0$) y que la diagonal principal sea cero ($d_{ii} = 0$).
  - Comprueba que la matriz sea **simétrica** ($d_{ij} = d_{ji}$). Si alguna condición falla, lanza un `ValueError`.
- **`_procesar_y_validar_demandas(demandas, num_clientes)`**:
  - Normaliza las demandas de los clientes `1..n`.
  - Verifica que ninguna demanda sea negativa y que **ningún cliente tenga una demanda individual mayor a la capacidad del vehículo** ($q_i \le Q$). Si $q_i > Q$, el problema sería infactible y lanza `ValueError`.
- **`distancia(nodo_origen, nodo_destino)`**:
  - Devuelve el costo $d_{ij}$ entre dos nodos.
- **`demanda_ruta(ruta)` y `distancia_ruta(ruta)`**:
  - Dada una secuencia de nodos como `[0, 2, 3, 0]`, suman respectivamente la carga total de los clientes visitados y la distancia total recorrida tramo a tramo.
- **`cargar_desde_json(ruta_archivo)`, `desde_diccionario(datos)`, `a_diccionario()`**:
  - Permiten leer los escenarios guardados en la carpeta `data/` o reconstruir la red en vivo cuando el usuario modifica tablas en la interfaz web.

---

### 2.2. `src/clarke_wright.py` — Motor del Algoritmo de Clarke & Wright

Contiene la lógica central de Investigación de Operaciones.

- **`AhorroPar` (`@dataclass`)**:
  - Estructura inmutable que guarda un par de clientes `(nodo_i, nodo_j)` con $i < j$ y su ahorro `ahorro` ($S_{ij}$).
- **`ResultadoClarkeWright` (`@dataclass`)**:
  - Empaqueta toda la salida del algoritmo:
    - `ahorros_ordenados`: Lista de todos los pares evaluados de mayor a menor ahorro.
    - `rutas_finales`: Lista de rutas óptimas, por ejemplo `[[0, 2, 3, 0], [0, 1, 4, 0]]`.
    - `distancia_inicial`: Costo de atender a cada cliente en un viaje individual de ida y vuelta ($\sum 2 \cdot d_{0i}$).
    - `distancia_total`: Suma de las distancias de las `rutas_finales`.
    - `ahorro_total`: Diferencia exacta `distancia_inicial - distancia_total`.
    - `trazabilidad_fusiones`: Lista de textos explicando qué ocurrió en cada paso (si un par se fusionó o por qué razón fue rechazado).
- **`calcular_ahorros(red)`**:
  - Recorre todos los pares de clientes $(i, j)$ con $i < j$.
  - Aplica la ecuación de Clarke & Wright:
    $$S_{ij} = d_{0i} + d_{0j} - d_{ij}$$
  - Ordena la lista en orden **estrictamente descendente** por el valor de $S_{ij}$.
- **`_es_extremo(seq_clientes, nodo)`**:
  - Determina si un cliente está al inicio (`seq_clientes[0]`) o al final (`seq_clientes[-1]`) de su ruta actual, lo que significa que sigue conectado directamente al depósito `0` y no ha quedado atrapado como nodo interior.
- **`_fusionar_secuencias(seq_a, nodo_a, seq_b, nodo_b)`**:
  - Une dos sub-rutas conectando directamente `nodo_a` con `nodo_b`.
  - Si `nodo_a` está al inicio de la primera ruta en vez de al final, o `nodo_b` está al final de la segunda ruta en vez de al inicio, **invierte la sub-ruta correspondiente** (lo cual es válido porque la matriz de distancias es simétrica) para que ambos nodos queden adyacentes en el punto de unión.
- **`resolver_clarke_wright(red)`**:
  - Inicializa $n$ rutas individuales internas `{1: [1], 2: [2], ..., n: [n]}`.
  - Recorre `ahorros_ordenados` y verifica las **3 condiciones de factibilidad**:
    1. **Condición (a)**: `id_ruta_i != id_ruta_j` (los clientes están en rutas separadas).
    2. **Condición (b)**: `_es_extremo(seq_i, i) and _es_extremo(seq_j, j)` (ambos clientes son extremos conectados al depósito).
    3. **Condición (c)**: `demanda_por_ruta[id_ruta_i] + demanda_por_ruta[id_ruta_j] <= red.capacidad_vehiculo` (la carga combinada no excede $Q$).
  - Si cumple las tres condiciones, fusiona las dos rutas, actualiza las cargas y registra el evento en `trazabilidad_fusiones`.
  - Al terminar, agrega el depósito `0` al inicio y al final de cada secuencia activa (`[0, ..., 0]`) y calcula los costos finales.

---

### 2.3. `src/visualizador.py` — Grafo Interactivo y Coloreado por Costo

Traduce el resultado matemático a una representación visual interactiva con `pyvis`.

- **`obtener_aristas_rutas_optimas(rutas_finales)`**:
  - Descompone cada ruta `[0, ..., 0]` en sus tramos individuales `(u, v)` y los asocia con el número de ruta/vehículo correspondiente.
- **`calcular_colores_por_costo_ruta(red, rutas_finales)`**:
  - Calcula la distancia de cada una de las rutas finales y las compara entre sí:
    - A la ruta con **menor distancia (menor costo)** le asigna el color **verde** (`#16A34A`).
    - A la ruta con **mayor distancia (mayor costo)** le asigna el color **rojo** (`#DC2626`).
    - Si existen 3 o más rutas, a las intermedias les asigna tonos diferenciados (azul, ámbar, etc.).
- **`construir_red_pyvis(red, resultado, mostrar_aristas_inactivas, altura_px)`**:
  - Crea el nodo **`Depósito (0)`** con forma de caja rectangular, fondo ámbar claro (`#FEF3C7`) y texto oscuro para que sea legible de inmediato.
  - Crea los nodos de los clientes mostrando su demanda (`Cliente i (q=...)`) y borde del color de su ruta.
  - Dibuja las aristas activas con trazo continuo grueso del color de la ruta (verde o rojo según costo) y etiqueta con la distancia $d_{ij}$. Si el usuario activa la casilla de arcos no utilizados, los dibuja en gris punteado.

---

### 2.4. `app.py` — Interfaz Web en Streamlit

Organiza la aplicación interactiva sin depender de código externo:

- **Funciones de estado (`inicializar_estado`, `al_cambiar_modo`, `crear_red_vacia`, `redimensionar_red`)**:
  - Mantienen la red activa en `st.session_state["red_dict"]`.
  - Permiten alternar entre los escenarios JSON de la carpeta `data/` o seleccionar **"Crear red desde cero (Personalizada)"**, así como cambiar dinámicamente el número de clientes $n$.
- **Barra Lateral (`with st.sidebar`)**:
  - Selector de origen de datos (casos predefinidos o red desde cero).
  - Control de capacidad máxima $Q$ y cantidad de clientes $n$.
  - Casilla para mostrar u ocultar arcos no utilizados.
- **Bloque Superior Editable (`Editar Demandas y Distancias de la Red`)**:
  - Presenta dos tablas `st.data_editor`: una para modificar las demandas $q_i$ y otra con todos los pares $(i, j)$ para editar las distancias $d_{ij}$. Cada cambio actualiza automáticamente su par simétrico $d_{ji}$ y vuelve a ejecutar Clarke & Wright en vivo.
- **Panel de Resultados**:
  - Muestra las 4 métricas principales (distancia inicial, distancia final, ahorro total y número de rutas).
  - Renderiza el grafo PyVis junto a la tabla comparativa de costos por ruta y la matriz simétrica actual.
  - En la parte inferior presenta la tabla de ahorros ordenados $S_{ij}$ y el registro paso a paso de las fusiones.

---

### 2.5. `main.py` y `tests/test_clarke_wright.py`

- **`main.py`**:
  - Carga el caso de estudio base (`data/caso_estudio_informe.json`), ejecuta `resolver_clarke_wright` e imprime en consola la tabla de ahorros, la trazabilidad de fusiones y las rutas óptimas.
  - Si se ejecuta con `python main.py --ui`, lanza automáticamente el servidor de Streamlit con `app.py`.
- **`tests/test_clarke_wright.py`**:
  - Contiene 6 pruebas unitarias con `pytest` que verifican la convergencia exacta del caso manual (distancia `66.0`, ahorro `24.0`, rutas `[[0, 2, 3, 0], [0, 1, 4, 0]]`), el rechazo por `ValueError` cuando $q_i > Q$, el rechazo ante distancias negativas o matrices asimétricas, la lectura desde JSON y el coloreado verde/rojo de las rutas en el visualizador.
