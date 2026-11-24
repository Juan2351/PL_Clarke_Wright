"""Interfaz web para el Algoritmo de Ahorros de Clarke & Wright (CVRP)."""

from pathlib import Path
from typing import Any, Dict, List
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

from src.clarke_wright import resolver_clarke_wright
from src.red_logistica import RedLogistica
from src.visualizador import calcular_colores_por_costo_ruta, generar_html_red

RUTA_DATA = Path(__file__).resolve().parent / "data"
OPCION_DESDE_CERO = "Crear red desde cero (Personalizada)"
ESCENARIOS_PREDEFINIDOS: Dict[str, Path] = {
    "Caso base del informe (4 clientes, Q=10)": RUTA_DATA / "caso_estudio_informe.json",
    "Distribución regional (6 clientes, Q=15)": RUTA_DATA / "red_distribucion_6_clientes.json",
}


def crear_red_vacia(num_clientes: int, capacidad: float) -> Dict[str, Any]:
    """Crea una estructura de red inicial desde cero para que el usuario ingrese sus propios datos."""
    total_nodos = num_clientes + 1
    matriz: List[List[float]] = []
    for i in range(total_nodos):
        fila = [0.0 if i == j else 10.0 for j in range(total_nodos)]
        matriz.append(fila)

    demandas = {str(i): 2.0 for i in range(1, num_clientes + 1)}
    return {
        "nombre": "Red Personalizada",
        "deposito": 0,
        "capacidad_vehiculo": float(capacidad),
        "demandas": demandas,
        "matriz_distancias": matriz,
    }


def inicializar_estado() -> None:
    """Inicializa el estado de la sesión con el caso base por defecto."""
    if "red_dict" not in st.session_state:
        nombre_defecto = "Caso base del informe (4 clientes, Q=10)"
        red = RedLogistica.cargar_desde_json(ESCENARIOS_PREDEFINIDOS[nombre_defecto])
        st.session_state["red_dict"] = red.a_diccionario()
        st.session_state["modo_actual"] = nombre_defecto
        st.session_state["version_editor"] = 0


def al_cambiar_modo() -> None:
    """Actualiza la red cuando el usuario cambia entre un caso predefinido o crear desde cero."""
    seleccion = st.session_state["selector_modo"]
    st.session_state["modo_actual"] = seleccion
    st.session_state["version_editor"] += 1

    if seleccion in ESCENARIOS_PREDEFINIDOS:
        red = RedLogistica.cargar_desde_json(ESCENARIOS_PREDEFINIDOS[seleccion])
        st.session_state["red_dict"] = red.a_diccionario()
    else:
        st.session_state["red_dict"] = crear_red_vacia(num_clientes=3, capacidad=10.0)


def redimensionar_red(nuevo_n: int, capacidad: float) -> None:
    """Ajusta la cantidad de clientes conservando los valores ya ingresados o reiniciando si se pide."""
    datos = st.session_state["red_dict"]
    matriz_ant: List[List[float]] = datos["matriz_distancias"]
    demandas_ant: Dict[str, float] = datos["demandas"]
    n_ant = len(matriz_ant) - 1

    if nuevo_n == n_ant:
        return

    nueva_matriz: List[List[float]] = []
    for i in range(nuevo_n + 1):
        fila: List[float] = []
        for j in range(nuevo_n + 1):
            if i == j:
                fila.append(0.0)
            elif i <= n_ant and j <= n_ant:
                fila.append(float(matriz_ant[i][j]))
            else:
                fila.append(10.0)
        nueva_matriz.append(fila)

    nuevas_demandas: Dict[str, float] = {}
    for i in range(1, nuevo_n + 1):
        if str(i) in demandas_ant:
            nuevas_demandas[str(i)] = min(float(demandas_ant[str(i)]), capacidad)
        else:
            nuevas_demandas[str(i)] = min(2.0, capacidad)

    datos["matriz_distancias"] = nueva_matriz
    datos["demandas"] = nuevas_demandas
    datos["capacidad_vehiculo"] = float(capacidad)
    st.session_state["version_editor"] += 1


def main() -> None:
    st.set_page_config(
        page_title="CVRP - Clarke & Wright",
        layout="wide",
    )

    inicializar_estado()
    datos = st.session_state["red_dict"]
    matriz: List[List[float]] = datos["matriz_distancias"]
    demandas: Dict[str, float] = datos["demandas"]
    n_clientes = len(matriz) - 1
    ver = st.session_state["version_editor"]

    # -------------------------------------------------------------------------
    # BARRA LATERAL: Selección de modo y parámetros globales
    # -------------------------------------------------------------------------
    with st.sidebar:
        st.header("Configuración del Modelo")

        opciones_modo = list(ESCENARIOS_PREDEFINIDOS.keys()) + [OPCION_DESDE_CERO]
        st.selectbox(
            "Origen de los datos",
            options=opciones_modo,
            key="selector_modo",
            on_change=al_cambiar_modo,
        )

        capacidad_q = st.number_input(
            "Capacidad máxima por vehículo (Q)",
            min_value=1.0,
            value=float(datos["capacidad_vehiculo"]),
            step=1.0,
        )
        datos["capacidad_vehiculo"] = float(capacidad_q)

        nuevo_num_clientes = int(
            st.number_input(
                "Número de clientes (n)",
                min_value=2,
                max_value=12,
                value=n_clientes,
                step=1,
                help="Puedes aumentar o reducir el número de clientes tanto en una red desde cero como en una existente.",
            )
        )
        if nuevo_num_clientes != n_clientes:
            redimensionar_red(nuevo_num_clientes, capacidad_q)
            st.rerun()

        if st.session_state["modo_actual"] == OPCION_DESDE_CERO:
            if st.button("Reiniciar valores en blanco", use_container_width=True):
                st.session_state["red_dict"] = crear_red_vacia(
                    num_clientes=n_clientes, capacidad=capacidad_q
                )
                st.session_state["version_editor"] += 1
                st.rerun()

        st.divider()
        mostrar_inactivas = st.checkbox(
            "Mostrar arcos no utilizados en el grafo",
            value=False,
        )

        st.caption(
            "Código de colores del grafo:\n"
            "- Verde: Ruta de menor costo (distancia)\n"
            "- Rojo: Ruta de mayor costo (distancia)\n"
            "- Azul: Ruta de costo intermedio (si hay 3 o más rutas)"
        )

    # -------------------------------------------------------------------------
    # ÁREA PRINCIPAL: Edición clara de datos + Resultados
    # -------------------------------------------------------------------------
    st.title("Enrutamiento de Vehículos con Capacidad (CVRP)")
    st.caption("Algoritmo de Ahorros de Clarke & Wright")

    # SECCIÓN 1: EDICIÓN DIRECTA DE DEMANDAS Y DISTANCIAS
    with st.expander("Editar Demandas y Distancias de la Red", expanded=True):
        st.markdown(
            "Modifica cualquier celda directamente en las tablas inferiores. "
            "Al editar la distancia entre dos nodos, su valor simétrico ($d_{ij} = d_{ji}$) se actualiza automáticamente."
        )
        col_ed_dem, col_ed_dist = st.columns([1.0, 1.8], gap="large")

        with col_ed_dem:
            st.markdown("**1. Demandas por cliente ($q_i$)**")
            df_demandas = pd.DataFrame(
                [
                    {"ID": i, "Cliente": f"Cliente {i}", "Demanda": float(demandas[str(i)])}
                    for i in range(1, n_clientes + 1)
                ]
            )
            df_dem_edit = st.data_editor(
                df_demandas,
                column_config={
                    "ID": None,
                    "Cliente": st.column_config.TextColumn("Nodo", disabled=True),
                    "Demanda": st.column_config.NumberColumn(
                        f"Demanda (máx Q={capacidad_q:g})",
                        min_value=0.0,
                        step=1.0,
                        format="%.1f",
                    ),
                },
                hide_index=True,
                use_container_width=True,
                key=f"editor_demandas_{ver}",
            )
            datos["demandas"] = {
                str(int(row["ID"])): float(row["Demanda"])
                for _, row in df_dem_edit.iterrows()
            }

        with col_ed_dist:
            st.markdown("**2. Distancias entre pares de nodos ($d_{ij}$)**")
            etiquetas_nodos = {0: "0 (Depósito)"}
            for i in range(1, n_clientes + 1):
                etiquetas_nodos[i] = f"{i} (Cliente {i})"

            pares_filas = []
            for i in range(n_clientes + 1):
                for j in range(i + 1, n_clientes + 1):
                    pares_filas.append(
                        {
                            "i": i,
                            "j": j,
                            "Desde": etiquetas_nodos[i],
                            "Hasta": etiquetas_nodos[j],
                            "Distancia": float(matriz[i][j]),
                        }
                    )

            df_pares = pd.DataFrame(pares_filas)
            df_pares_edit = st.data_editor(
                df_pares,
                column_config={
                    "i": None,
                    "j": None,
                    "Desde": st.column_config.TextColumn("Nodo Origen (i)", disabled=True),
                    "Hasta": st.column_config.TextColumn("Nodo Destino (j)", disabled=True),
                    "Distancia": st.column_config.NumberColumn(
                        "Distancia d(i, j)",
                        min_value=0.0,
                        step=1.0,
                        format="%.1f",
                    ),
                },
                hide_index=True,
                use_container_width=True,
                height=240,
                key=f"editor_pares_{ver}",
            )

            for _, fila in df_pares_edit.iterrows():
                u = int(fila["i"])
                v = int(fila["j"])
                d_val = float(fila["Distancia"])
                matriz[u][v] = d_val
                matriz[v][u] = d_val

    # VALIDACIÓN Y EJECUCIÓN DEL ALGORITMO
    try:
        red = RedLogistica.desde_diccionario(datos)
        resultado = resolver_clarke_wright(red)
    except ValueError as err:
        st.error(f"Error de validación en los datos ingresados: {err}")
        st.stop()

    colores_ruta, etiquetas_costo = calcular_colores_por_costo_ruta(
        red, resultado.rutas_finales
    )

    # SECCIÓN 2: MÉTRICAS DE RESUMEN
    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    col_m1.metric("Distancia inicial (rutas individuales)", f"{resultado.distancia_inicial:.1f}")
    col_m2.metric("Distancia total final", f"{resultado.distancia_total:.1f}")
    col_m3.metric("Ahorro total obtenido", f"{resultado.ahorro_total:.1f}")
    col_m4.metric("Vehículos / Rutas", f"{len(resultado.rutas_finales)}")

    st.divider()

    # SECCIÓN 3: GRAFO Y TABLA DE RUTAS COLOREADAS POR COSTO
    col_grafo, col_rutas = st.columns([1.35, 1.0], gap="large")

    with col_grafo:
        st.subheader("Topología de Rutas")
        st.caption(
            "Verde: ruta de menor distancia | Rojo: ruta de mayor distancia"
        )
        html_grafo = generar_html_red(
            red=red,
            resultado=resultado,
            mostrar_aristas_inactivas=mostrar_inactivas,
            altura_px=430,
        )
        components.html(html_grafo, height=445, scrolling=False)

    with col_rutas:
        st.subheader("Comparación de Costo por Ruta")
        filas_rutas = []
        for idx, ruta in enumerate(resultado.rutas_finales, start=1):
            carga = red.demanda_ruta(ruta)
            dist = red.distancia_ruta(ruta)
            filas_rutas.append(
                {
                    "Ruta": f"Ruta {idx}",
                    "Secuencia": " -> ".join(str(n) for n in ruta),
                    "Carga": f"{carga:.1f} / {red.capacidad_vehiculo:.1f}",
                    "Distancia (Costo)": dist,
                    "Clasificación": etiquetas_costo.get(idx, ""),
                }
            )
        df_rutas = pd.DataFrame(filas_rutas)
        st.dataframe(
            df_rutas,
            column_config={
                "Distancia (Costo)": st.column_config.NumberColumn(
                    "Distancia (Costo)", format="%.1f"
                )
            },
            hide_index=True,
            use_container_width=True,
        )

        st.subheader("Matriz Simétrica Actual")
        etiquetas_mat = ["Dep. 0"] + [f"C{i}" for i in range(1, n_clientes + 1)]
        df_mat = pd.DataFrame(matriz, index=etiquetas_mat, columns=etiquetas_mat)
        st.dataframe(df_mat.style.format("{:.1f}"), use_container_width=True)

    st.divider()

    # SECCIÓN 4: TABLA DE AHORROS Y REGISTRO DE FUSIONES
    col_ahorros, col_traza = st.columns(2, gap="large")

    with col_ahorros:
        st.subheader("Tabla de Ahorros Ordenados (S_ij)")
        filas_ahorros = []
        for item in resultado.ahorros_ordenados:
            d_0i = red.distancia(0, item.nodo_i)
            d_0j = red.distancia(0, item.nodo_j)
            d_ij = red.distancia(item.nodo_i, item.nodo_j)
            filas_ahorros.append(
                {
                    "Par (i, j)": f"({item.nodo_i}, {item.nodo_j})",
                    "d(0, i)": d_0i,
                    "d(0, j)": d_0j,
                    "d(i, j)": d_ij,
                    "Ahorro S_ij": item.ahorro,
                }
            )
        st.dataframe(
            pd.DataFrame(filas_ahorros),
            hide_index=True,
            use_container_width=True,
        )

    with col_traza:
        st.subheader("Evaluación de Fusiones")
        df_traza = pd.DataFrame(
            [
                {"Paso": i, "Decisión": texto}
                for i, texto in enumerate(resultado.trazabilidad_fusiones, start=1)
            ]
        )
        st.dataframe(
            df_traza,
            hide_index=True,
            use_container_width=True,
        )


if __name__ == "__main__":
    main()
