from pathlib import Path
import streamlit as st

import os
import pandas as pd
import numpy as np
import plotly.express as px


from episcopeenvigado.dataset import (
    obtener_dataset_completo,
    cargar_datasets_locales,
    unificar_dataset,
)
from episcopeenvigado.config import PROCESSED_DATA_DIR
import networkx as nx
from pyvis.network import Network
import matplotlib.cm as cm
import matplotlib.colors as mcolors
from io import StringIO


# ==============================================
# CONFIGURACIÓN GENERAL
# ==============================================
st.set_page_config(
    page_title="EpiScope Envigado",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Logo
logo_path = os.path.join("streamlit_app", "LogoEpiScope.jpg")

# ==============================================
# SIDEBAR DE NAVEGACIÓN
# ==============================================
st.sidebar.image(logo_path, width=100)
page = st.sidebar.radio(
    "Ir a:",
    [
        "🏠 Home",
        "🔍 Análisis Exploratorio",
        "🤖 Modelo Predictivo",
        "📈 Modelo Predictivo RandomForest",
        "ℹ️ Acerca del Proyecto",
    ],
)

##
##Con las siguiente líneas se puede vincular páginas puntuales, al darle click cargarían a la derecha todo el archivo entero
## Eso evita que se tengan que recargar en este sólo archivo todo


st.sidebar.markdown("---")
st.sidebar.markdown("👩‍💻 *Proyecto desarrollado por:*")
st.sidebar.markdown("**Equipo EpiScope Envigado**")
st.sidebar.markdown("© 2025")

# ==============================================
# PÁGINA HOME
# ==============================================
if page == "🏠 Home":
    st.title("🏥 EpiScope Envigado")
    st.markdown(
        "### Analítica predictiva para la planeación hospitalaria y epidemiológica en Envigado"
    )
    st.markdown("---")

    st.markdown("""
    Hoy, el sistema de salud de **Envigado** enfrenta un reto silencioso pero crítico: la dificultad para anticipar la demanda hospitalaria.  
    Los picos de atención llegan sin aviso, los diagnósticos se dispersan en bases de datos extensas y las decisiones se toman mirando hacia atrás, no hacia adelante.

    **EpiScope Envigado** nace para cambiar eso.  
    Es un proyecto de analítica predictiva que aprovecha los registros **RIPS 2023–2024** para detectar patrones en los diagnósticos **CIE-10** y anticipar tendencias.  
    Con este modelo, los hospitales podrán prever picos de atención, optimizar su capacidad instalada y asignar recursos de manera más eficiente.
    """)

    st.markdown("---")
    st.subheader("🏙️ 1. Contexto territorial y epidemiológico")
    st.markdown("""
    El municipio de **Envigado** cuenta con una extensión de **51 km²** y una densidad poblacional estimada de **4.868,7 habitantes por km²** para el año **2024**.  
    La población total proyectada asciende a **248.304 habitantes**, con una distribución de **54,1 % mujeres** y **45,9 % hombres**.  
    De ellos, el **96,9 %** reside en zona urbana y el **3,1 %** en zona rural, según el **DANE** (Censo 2018, proyecciones 2024).  

    En 2023, el municipio contaba con **652 camas hospitalarias**, **133 salas** (30 quirófanos) y **90 camillas**, reflejando una red hospitalaria sólida pero exigida por la alta demanda.  

    El análisis de morbilidad muestra que las **enfermedades no transmisibles (ENT)** representan la mayor proporción de consultas en todos los grupos etarios.  
    Las **condiciones transmisibles**, **nutricionales** y las **lesiones por causas externas** también tienen una participación importante, especialmente en la infancia y juventud.  

    📖 *Fuente: Análisis de Situación de Salud Participativo (ASIS) – Municipio de Envigado, 2024.*
    """)

    st.markdown("---")
    st.subheader("⚠️ 2. Problema")
    st.markdown("""
    El sistema de salud de Envigado enfrenta un desafío creciente:  

    - La **alta demanda hospitalaria** y la **capacidad instalada limitada** generan picos de atención imprevisibles.  
    - Las decisiones se basan principalmente en **datos históricos**, dificultando anticipar brotes o variaciones en la demanda.  
    - No existen **herramientas locales de analítica predictiva** que integren los RIPS 2023–2024 para generar alertas tempranas o estimaciones de morbilidad.  
    """)

    st.markdown("---")
    st.subheader("💡 3. Solución: *EpiScope Envigado*")
    st.markdown("""
    **EpiScope Envigado** es un proyecto de analítica avanzada que utiliza los **RIPS de hospitalización 2023–2024** para **identificar patrones diagnósticos (CIE-10)** y **anticipar tendencias de morbilidad**.  

    El modelo predictivo busca:  
    - Detectar cambios en los patrones de enfermedad.  
    - Estimar la demanda futura por diagnóstico y especialidad médica.  
    - Fortalecer la toma de decisiones en salud pública con base en datos reales.
    """)

    st.markdown("---")
    st.subheader("🎯 4. Objetivos del proyecto")
    st.markdown("""
    **Objetivo general**  
    Desarrollar un modelo predictivo basado en analítica avanzada de los RIPS de hospitalización (2023–2024) del municipio de Envigado, para identificar patrones diagnósticos (CIE-10) y anticipar tendencias de morbilidad que fortalezcan la planeación epidemiológica y la gestión eficiente de recursos hospitalarios.  

    **Objetivos específicos**  
    1. Diseñar e implementar la infraestructura de datos mediante un proceso **ETL**.  
    2. Realizar un **análisis exploratorio** de los RIPS 2023–2024.  
    3. Construir y validar un **modelo predictivo** basado en diagnósticos CIE-10.
    """)

    st.markdown("---")
    st.subheader("📈 5. Valor e impacto esperado")
    st.markdown("""
    El proyecto permitirá:  
    - Incrementar la **eficiencia operativa** mediante una mejor planeación de camas y servicios.  
    - **Reducir hasta en 20 %** la congestión hospitalaria.  
    - **Optimizar la inversión pública**, proyectando un ahorro del 15–20 % en costos de atención.  
    - Fortalecer la **capacidad institucional** de análisis de datos en salud pública local.
    """)

    st.markdown("---")
    st.subheader("👥 6. Equipo de trabajo")
    st.markdown("""
    **Equipo interdisciplinario de analítica y salud pública:**  
    - Laura María Jaramillo Sánchez  
    - Joshua Mateo Quiroz Márquez  
    - Daniel Gil Arbeláez  
    - Diego Eusse  
    - Juan David Galego Ramírez
    """)

    st.markdown("---")
    st.markdown(
        "© 2025 - Proyecto EpiScope Envigado | Analítica Predictiva para la Salud Pública 🩺"
    )


# ==============================================
# PÁGINA ANÁLISIS EXPLORATORIO
# ==============================================
elif page == "🔍 Análisis Exploratorio":
    st.title("🔍 Análisis Exploratorio de los RIPS de Hospitalización")
    st.markdown("### 📊 Caracterización general de la base de datos procesada")

    # ===========================
    # Cargar y unificar datos
    # ===========================
    with st.spinner("Cargando dataset completo desde la base de datos..."):
        datasets = obtener_dataset_completo()

    if not datasets:
        st.error("❌ No se pudieron cargar las tablas desde la base de datos.")
        st.stop()

    try:
        df_unificado = unificar_dataset(datasets)
    except KeyError as e:
        st.error(f"❌ Error al unificar dataset: falta la tabla '{e.args[0]}'")
        st.stop()

    if df_unificado is None or df_unificado.empty:
        st.warning(
            "⚠️ El dataset unificado está vacío o no se pudo generar correctamente."
        )
        st.stop()

    # ===========================================
    # Panel de inspección interactivo
    # ===========================================
    st.subheader("🧾 Panel de inspección del dataset")
    st.write(f"Registros totales: **{len(df_unificado):,}**")

    if st.checkbox("Mostrar descripción de columnas"):
        col_desc = pd.DataFrame(
            {
                "Columna": df_unificado.columns,
                "Tipo": [df_unificado[col].dtype for col in df_unificado.columns],
                "Count": [df_unificado[col].count() for col in df_unificado.columns],
                "Nulos": [
                    df_unificado[col].isna().sum() for col in df_unificado.columns
                ],
            }
        )
        st.dataframe(col_desc)

    if st.checkbox("Mostrar estadísticas descriptivas"):
        st.dataframe(df_unificado.describe(include="all").T)

    if st.checkbox("Mostrar primeras filas del dataset"):
        st.dataframe(df_unificado.head(10))

    # ===========================================
    # Distribución de la vía de ingreso
    # ===========================================
    st.subheader("🚪 Distribución de la vía de ingreso")
    if "Via_Ingreso_Desc" in df_unificado.columns:
        frecuencia_via = (
            df_unificado["Via_Ingreso_Desc"]
            .value_counts()
            .rename_axis("Via_Ingreso_Desc")
            .reset_index(name="Frecuencia")
        )
        fig_via = px.pie(
            frecuencia_via,
            names="Via_Ingreso_Desc",
            values="Frecuencia",
            title="Distribución de las vías de ingreso",
            color_discrete_sequence=px.colors.qualitative.Set2,
        )
        fig_via.update_traces(textinfo="label+percent+value")
        st.plotly_chart(fig_via, use_container_width=True)
    # ===========================================
    # Distribución por Estado de Salida
    # ===========================================
    st.subheader("🚑 Distribución por Estado de Salida")

    if "Estado_Salida_Desc" in df_unificado.columns:
        estado_counts = (
            df_unificado["Estado_Salida_Desc"]
            .value_counts()
            .rename_axis("Estado_Salida")
            .reset_index(name="Frecuencia")
        )

        fig_estado = px.pie(
            estado_counts,
            names="Estado_Salida",
            values="Frecuencia",
            title="Distribución de pacientes según Estado de Salida",
            color_discrete_sequence=px.colors.qualitative.Set3,
        )
        fig_estado.update_traces(
            textinfo="label+percent+value"
        )  # Mostrar etiqueta, %, y valor
        st.plotly_chart(fig_estado, use_container_width=True)

    else:
        st.warning("⚠️ La columna 'Estado_Salida_Desc' no existe en el dataset.")

    # ===========================================
    # Distribución por sexo (gráfico de torta)
    # ===========================================
    st.subheader("🧍 Distribución por sexo")

    if "SEXO" in df_unificado.columns:
        # Reemplazar etiquetas
        df_sexo = df_unificado["SEXO"].replace({"M": "Masculino", "F": "Femenino"})

        # Contar frecuencia
        sexo_counts = (
            df_sexo.value_counts().rename_axis("Sexo").reset_index(name="Frecuencia")
        )

        # Definir colores
        colores = {"Masculino": "#aec6cf", "Femenino": "#ffb6c1"}  # azul y rosado

        # Crear gráfico de torta
        fig_sexo_pie = px.pie(
            sexo_counts,
            names="Sexo",
            values="Frecuencia",
            title="Distribución por sexo de los pacientes",
            color="Sexo",
            color_discrete_map=colores,
        )

        fig_sexo_pie.update_traces(
            textinfo="label+percent+value"
        )  # Mostrar etiqueta, %, y valor
        st.plotly_chart(fig_sexo_pie, use_container_width=True)

    else:
        st.warning("⚠️ La columna 'SEXO' no existe en el dataset.")

    # ===========================================
    # Histograma de edades (sin negativos)
    # ===========================================
    st.subheader("📊 Histograma de edades")
    if "EDAD_ANIOS" in df_unificado.columns:
        edades = df_unificado["EDAD_ANIOS"]
        edades = edades[(edades >= 0) & (edades <= 120)].dropna()

        if len(edades) > 0:
            num_clases = int(1 + 3.3 * np.log10(len(edades)))

            fig_hist = px.histogram(
                edades,
                x=edades,
                nbins=num_clases,
                title="Histograma de edades de los pacientes",
                color_discrete_sequence=["#636EFA"],
                marginal="box",
                labels={"x": "Edad (años)", "y": "Frecuencia"},
                text_auto=True,
            )

            fig_hist.update_layout(
                bargap=0.05,
                xaxis=dict(range=[0, edades.max() + 5]),  # evita valores negativos
            )

            st.plotly_chart(fig_hist, use_container_width=True)
        else:
            st.info("ℹ️ No hay datos válidos de edad en el dataset.")
    else:
        st.warning("⚠️ La columna 'EDAD_ANIOS' no existe en el dataset.")

    # ===========================================
    # Histograma de duración de hospitalización (Plotly mejorado)
    # ===========================================
    st.subheader("⏱️ Histograma de duración de hospitalización (en días)")

    import numpy as np
    import plotly.express as px

    if "Duracion_Dias" in df_unificado.columns:
        duracion = df_unificado["Duracion_Dias"].dropna()

        if len(duracion) > 0:
            # Filtrar valores extremos para mejor visualización
            duracion_filtrada = duracion[duracion <= 60]

            # Cálculo de parámetros de clase (Sturges)
            rango = duracion_filtrada.max() - duracion_filtrada.min()
            num_clases = int(1 + 3.3 * np.log10(len(duracion_filtrada)))
            ancho_clases = rango / num_clases

            # Crear histograma con Plotly
            fig_duracion = px.histogram(
                duracion_filtrada,
                x=duracion_filtrada,
                nbins=num_clases,
                color_discrete_sequence=["#A8E6A3"],  # verde pastel
                marginal="box",
                title="Histograma de duración de hospitalización (≤ 60 días)",
                labels={"x": "Duración (días)", "y": "Frecuencia"},
                text_auto=True,  # mostrar frecuencia sobre las barras
            )

            # Ajustes de layout
            fig_duracion.update_traces(marker_line_width=0.5, opacity=0.85)
            fig_duracion.update_layout(
                bargap=0.05,
                yaxis_title="Frecuencia",
                title_font=dict(size=15),
                template="plotly_white",
            )

            # Mostrar límites de clase reales en el eje X
            fig_duracion.update_xaxes(
                tickmode="linear",
                dtick=ancho_clases,
                tick0=duracion_filtrada.min(),
                tickfont=dict(size=10),
            )

            # Mostrar gráfico
            st.plotly_chart(fig_duracion, use_container_width=True)

            # Mostrar información de clases calculadas
            st.caption(
                f"📏 Rango: {rango:.1f} días | Clases: {num_clases} | Ancho de clase: {ancho_clases:.2f} días"
            )

        else:
            st.info("ℹ️ No hay datos disponibles en la columna 'Duracion_Dias'.")
    else:
        st.warning("⚠️ La columna 'Duracion_Dias' no existe en el dataset.")

    # ===========================================
    # Top 10 diagnósticos principales como mapa de calor vertical
    # ===========================================
    st.subheader("🧠 Top 10 diagnósticos principales (Dx Principal de egreso)")

    if "Diagnostico_Principal_Desc" in df_unificado.columns:
        top_diagnosticos = (
            df_unificado["Diagnostico_Principal_Desc"]
            .value_counts()
            .head(10)
            .rename_axis("Diagnóstico")
            .reset_index(name="Frecuencia")
        )

        # Crear heatmap vertical con px.imshow
        fig_dx_heat = px.imshow(
            top_diagnosticos[["Frecuencia"]],  # Mantener como columna única
            labels=dict(x="Frecuencia", y="Diagnóstico", color="Frecuencia"),
            y=top_diagnosticos["Diagnóstico"],  # Diagnósticos en filas
            x=["Frecuencia"],  # Solo una columna
            text_auto=True,
            color_continuous_scale="Oranges",
            title="Top 10 diagnósticos principales (Dx Principal egreso)",
        )

        fig_dx_heat.update_xaxes(
            showticklabels=False
        )  # Ocultamos etiquetas de la columna única
        st.plotly_chart(fig_dx_heat, use_container_width=True)

    else:
        st.warning("⚠️ La columna 'Diagnostico_Principal_Desc' no existe en el dataset.")

    # ===========================================
    # Distribución por causa externa
    # ===========================================
    st.subheader("⚠️ Distribución por causa externa")

    if "Causa_Externa_Desc" in df_unificado.columns:
        # Contar frecuencia
        causa_counts = (
            df_unificado["Causa_Externa_Desc"]
            .value_counts()
            .rename_axis("Causa_Externa_Desc")
            .reset_index(name="Frecuencia")
        )

        # Ordenar de mayor a menor
        causa_counts = causa_counts.sort_values("Frecuencia", ascending=True)

        # Crear gráfico de barras horizontales con colores pastel
        colores = px.colors.qualitative.Pastel  # paleta pastel

        fig_causa = px.bar(
            causa_counts,
            x="Frecuencia",
            y="Causa_Externa_Desc",
            orientation="h",
            text="Frecuencia",
            title="Distribución de causas externas",
            color="Causa_Externa_Desc",
            color_discrete_sequence=colores,
        )

        # Actualizar layout: eje y con nombre personalizado y quitar leyenda
        fig_causa.update_layout(
            yaxis_title="Causa Externa",
            yaxis=dict(autorange="reversed"),
            showlegend=False,
        )

        st.plotly_chart(fig_causa, use_container_width=True)

    else:
        st.warning("⚠️ La columna 'Causa_Externa_Desc' no existe en el dataset.")


# ==============================================
# PÁGINAS PLACEHOLDER
# ==============================================
# ======================================================
# SECCIÓN: 🤖 MODELO PREDICTIVO
# ======================================================


# --- Funciones auxiliares (van fuera de la condición de página) ---
def crear_grafo(df: pd.DataFrame, dx_central: str) -> nx.Graph:
    """Crea un grafo con colores según OR y grosor según coocurrencia."""
    G = nx.Graph()

    norm = mcolors.Normalize(vmin=df["OR"].min(), vmax=df["OR"].max())
    cmap = cm.get_cmap("YlOrRd")

    for _, row in df.iterrows():
        for dx, desc in [
            (row["Dx1"], row.get("Desc1", "")),
            (row["Dx2"], row.get("Desc2", "")),
        ]:
            if dx not in G.nodes:
                G.add_node(
                    dx,
                    title=desc,
                    color="red" if dx == dx_central else "#87CEEB",
                    size=30 if dx == dx_central else 20,
                )

        rgba = cmap(norm(row["OR"]))
        hex_color = mcolors.to_hex(rgba)
        width = min(max(row["count_coocurrence"] / 5, 2), 8)

        G.add_edge(
            row["Dx1"],
            row["Dx2"],
            color=hex_color,
            width=width,
            title=f"Coocurrencias: {row['count_coocurrence']} | OR={row['OR']:.2f}",
        )

    return G


def visualizar_red(df: pd.DataFrame, dx_sel: str):
    """Muestra la red interactiva en Streamlit."""
    G = crear_grafo(df, dx_sel)
    net = Network(height="700px", width="100%", bgcolor="#ffffff", font_color="black")
    net.from_nx(G)
    net.repulsion(node_distance=280, spring_length=180, damping=0.8)
    html_str = net.generate_html()
    st.components.v1.html(html_str, height=750, scrolling=True)


# --- Aquí sí comienza el bloque principal de la página ---
if page == "🤖 Modelo Predictivo":
    st.title("🤖 Modelo Predictivo")
    st.markdown("### Análisis de Coocurrencias Significativas entre Diagnósticos")

    # Cargar datasets procesados
    if "datasets_locales" not in st.session_state:
        with st.spinner("Cargando archivos procesados..."):
            st.session_state["datasets_locales"] = cargar_datasets_locales(
                PROCESSED_DATA_DIR
            )

    datasets = st.session_state["datasets_locales"]

    if "analisis_coocurrencias_significativas" not in datasets:
        st.warning(
            "⚠️ No se encontró el archivo 'analisis_coocurrencias_significativas.xlsx'."
        )
    else:
        df_cooc = datasets["analisis_coocurrencias_significativas"]

        # ======================================================
        # 1️⃣ Checkbox – Análisis general
        # ======================================================
        if st.checkbox("📊 Análisis de concurrencias significativas"):
            st.markdown(
                f"**{len(df_cooc):,} asociaciones significativas encontradas.**"
            )
            st.dataframe(df_cooc)

        # ======================================================
        # 2️⃣ Checkbox – Filtro por diagnóstico
        # ======================================================
        if st.checkbox("🔗 Asociaciones fuertes con filtro por diagnóstico"):
            desc_map = {
                **dict(zip(df_cooc["Dx1"], df_cooc["Desc1"])),
                **dict(zip(df_cooc["Dx2"], df_cooc["Desc2"])),
            }

            opciones = [
                f"{dx} — {desc_map.get(dx, 'Sin descripción')}"
                for dx in sorted(set(df_cooc["Dx1"]) | set(df_cooc["Dx2"]))
            ]
            seleccion = st.selectbox("Selecciona diagnóstico:", options=opciones)
            dx_sel = seleccion.split(" — ")[0]

            df_filtrado = df_cooc[
                (df_cooc["Dx1"] == dx_sel) | (df_cooc["Dx2"] == dx_sel)
            ].sort_values("OR", ascending=False)

            st.markdown(
                f"### {len(df_filtrado)} asociaciones con **{dx_sel} — {desc_map.get(dx_sel, 'Sin descripción')}**"
            )
            st.dataframe(df_filtrado)

            # Gráfico descriptivo
            fig = px.scatter(
                df_filtrado,
                x="p_value_adj",
                y="OR",
                color="OR",
                size="count_coocurrence",
                hover_data=["Dx1", "Dx2", "Desc1", "Desc2"],
                title=f"Relación entre {dx_sel} y otros diagnósticos",
            )
            st.plotly_chart(fig, use_container_width=True)

            # Red interactiva
            if st.button("🌐 Visualizar red de coocurrencias"):
                df_top = df_filtrado[df_filtrado["count_coocurrence"] >= 5]
                visualizar_red(df_top, dx_sel)


elif page == "📈 Dashboard":
    st.title("📈 Dashboard")
    st.info(
        "Visualización interactiva de los resultados y métricas clave. Gráficos dinámicos y filtros personalizables. 📉"
    )

elif page == "ℹ️ Acerca del Proyecto":
    st.title("ℹ️ Acerca del Proyecto")
    st.markdown("""
    **EpiScope Envigado** es un desarrollo académico y técnico orientado a fortalecer la planeación sanitaria en el municipio mediante el uso de **inteligencia artificial y analítica de datos**.  
    Proyecto sin fines de lucro, desarrollado con propósito educativo e institucional.
    """)
