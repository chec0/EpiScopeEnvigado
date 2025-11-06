import streamlit as st
import os
import pandas as pd
import numpy as np
import plotly.express as px
from episcopeenvigado.dataset import obtener_dataset_completo
from episcopeenvigado.etl_modules.unificar_tablas import unificar_dataset

# ==============================================
# CONFIGURACIÓN GENERAL
# ==============================================
st.set_page_config(
    page_title="EpiScope Envigado",
    page_icon="🏥",
    layout="wide",
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
        "📈 Dashboard",
        "ℹ️ Acerca del Proyecto",
    ],
)
st.sidebar.markdown("---")
st.sidebar.markdown("👩‍💻 *Proyecto desarrollado por:*")
st.sidebar.markdown("**Equipo EpiScope Envigado**")
st.sidebar.markdown("© 2025")

# ==============================================
# PÁGINA HOME
# ==============================================
if page == "🏠 Home":
    st.title("🏥 EpiScope Envigado")
    st.markdown("### Analítica predictiva para la planeación hospitalaria y epidemiológica en Envigado")
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
    st.markdown("© 2025 - Proyecto EpiScope Envigado | Analítica Predictiva para la Salud Pública 🩺")


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
        st.warning("⚠️ El dataset unificado está vacío o no se pudo generar correctamente.")
        st.stop()

    # ===========================================
    # Panel de inspección interactivo
    # ===========================================
    st.subheader("🧾 Panel de inspección del dataset")
    st.write(f"Registros totales: **{len(df_unificado):,}**")

    if st.checkbox("Mostrar descripción de columnas"):
        col_desc = pd.DataFrame({
            "Columna": df_unificado.columns,
            "Tipo": [df_unificado[col].dtype for col in df_unificado.columns],
            "Count": [df_unificado[col].count() for col in df_unificado.columns],
            "Nulos": [df_unificado[col].isna().sum() for col in df_unificado.columns]
        })
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
            names='Via_Ingreso_Desc',
            values='Frecuencia',
            title='Distribución de las vías de ingreso',
            color_discrete_sequence=px.colors.qualitative.Set2
        )
        fig_via.update_traces(textinfo='label+percent+value')
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
            color_discrete_sequence=px.colors.qualitative.Set3
        )
        fig_estado.update_traces(textinfo="label+percent+value")  # Mostrar etiqueta, %, y valor
        st.plotly_chart(fig_estado, use_container_width=True)

    else:
        st.warning("⚠️ La columna 'Estado_Salida_Desc' no existe en el dataset.")

    # ===========================================
    # Distribución por sexo
    # ===========================================
    st.subheader("🧍 Distribución por sexo")
    if "Sexo" in df_unificado.columns:
        sexo_counts = (
            df_unificado["Sexo"]
            .value_counts()
            .rename_axis("Sexo")
            .reset_index(name="Frecuencia")
        )
        fig_sexo = px.bar(
            sexo_counts,
            x="Sexo",
            y="Frecuencia",
            text="Frecuencia",
            title="Distribución por sexo de los pacientes",
            color="Sexo",
            color_discrete_sequence=px.colors.qualitative.Set3
        )
        st.plotly_chart(fig_sexo, use_container_width=True)

    # ===========================================
    # Histograma de edades
    # ===========================================
    st.subheader("📊 Histograma de edades")
    if "EDAD_ANIOS" in df_unificado.columns:
        edades = df_unificado["EDAD_ANIOS"].dropna()
        num_clases = int(1 + 3.3 * np.log10(len(edades)))

        fig_hist = px.histogram(
            edades,
            x=edades,
            nbins=num_clases,
            title="Histograma de edades de los pacientes",
            color_discrete_sequence=['#636EFA'],
            marginal="box",
            labels={"x": "Edad (años)", "y": "Frecuencia"},
            text_auto=True   # <- esto agrega automáticamente los valores sobre las barras
        )
        fig_hist.update_layout(bargap=0.05)
        st.plotly_chart(fig_hist, use_container_width=True)
    else:
        st.warning("⚠️ La columna 'EDAD_ANIOS' no existe en el dataset.")
        
    import calendar

    # ===========================================
    # Frecuencia de atenciones por mes (2023 vs 2024)
    # ===========================================
    st.subheader("📅 Frecuencia de atenciones por mes (2023 vs 2024)")

    if "Fecha_Ingreso" in df_unificado.columns:
        df_fecha = df_unificado.copy()
        
        # Asegurarnos de que sea datetime
        df_fecha["Fecha_Ingreso"] = pd.to_datetime(df_fecha["Fecha_Ingreso"], errors='coerce')
        
        # Extraer año y mes
        df_fecha["Año"] = df_fecha["Fecha_Ingreso"].dt.year
        df_fecha["Mes_Num"] = df_fecha["Fecha_Ingreso"].dt.month
        
        # Mapear números de mes a nombres
        df_fecha["Mes"] = df_fecha["Mes_Num"].apply(lambda x: calendar.month_abbr[x])
        
        # Filtrar solo años 2023 y 2024
        df_filtrado = df_fecha[df_fecha["Año"].isin([2023, 2024])]
        
        # Agrupar por año y mes
        atenciones_mes = (
            df_filtrado.groupby(["Año", "Mes_Num", "Mes"])
            .size()
            .reset_index(name="Frecuencia")
        )
        
        # Ordenar por mes
        atenciones_mes = atenciones_mes.sort_values(["Año", "Mes_Num"])
        
        # Crear gráfico de líneas
        fig_line = px.line(
            atenciones_mes,
            x="Mes",
            y="Frecuencia",
            color="Año",
            markers=True,
            title="Frecuencia mensual de atenciones (2023 vs 2024)",
            labels={"Mes": "Mes", "Frecuencia": "Número de atenciones", "Año": "Año"}
        )
        
        st.plotly_chart(fig_line, use_container_width=True)
    else:
        st.warning("⚠️ La columna 'Fecha_Ingreso' no existe en el dataset.")
   
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
            x=["Frecuencia"],                    # Solo una columna
            text_auto=True,
            color_continuous_scale="Oranges",
            title="Top 10 diagnósticos principales (Dx Principal egreso)"
        )

        fig_dx_heat.update_xaxes(showticklabels=False)  # Ocultamos etiquetas de la columna única
        st.plotly_chart(fig_dx_heat, use_container_width=True)

    else:
        st.warning("⚠️ La columna 'Diagnostico_Principal_Desc' no existe en el dataset.")


# ==============================================
# PÁGINAS PLACEHOLDER
# ==============================================
elif page == "🤖 Modelo Predictivo":
    st.title("🤖 Modelo Predictivo")
    st.info("Aquí se integrará el modelo de predicción basado en diagnósticos CIE-10 para estimar demanda hospitalaria. 📊")

elif page == "📈 Dashboard":
    st.title("📈 Dashboard")
    st.info("Visualización interactiva de los resultados y métricas clave. Gráficos dinámicos y filtros personalizables. 📉")

elif page == "ℹ️ Acerca del Proyecto":
    st.title("ℹ️ Acerca del Proyecto")
    st.markdown("""
    **EpiScope Envigado** es un desarrollo académico y técnico orientado a fortalecer la planeación sanitaria en el municipio mediante el uso de **inteligencia artificial y analítica de datos**.  
    Proyecto sin fines de lucro, desarrollado con propósito educativo e institucional.
    """)
