import streamlit as st
import os

# Configuración general
st.set_page_config(
    page_title="EpiScope Envigado",
    page_icon="🏥",
    layout="wide",
)
# Ruta relativa (suponiendo que el script streamlit_app.py está en la raíz del proyecto)
logo_path = os.path.join("streamlit_app", "LogoEpiScope.jpg")


# --- Sidebar de navegación ---
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

# --- Contenido del Home ---
if page == "🏠 Home":
    st.title("🏥 EpiScope Envigado")
    st.markdown("### Analítica predictiva para la planeación hospitalaria y epidemiológica en Envigado")

    st.markdown("---")

    # Introducción
    st.markdown("""
    Hoy, el sistema de salud de **Envigado** enfrenta un reto silencioso pero crítico: la dificultad para anticipar la demanda hospitalaria.  
    Los picos de atención llegan sin aviso, los diagnósticos se dispersan en bases de datos extensas y las decisiones se toman mirando hacia atrás, no hacia adelante.

    **EpiScope Envigado** nace para cambiar eso.  
    Es un proyecto de analítica predictiva que aprovecha los registros **RIPS 2023–2024** para detectar patrones en los diagnósticos **CIE-10** y anticipar tendencias.  
    Con este modelo, los hospitales podrán prever picos de atención, optimizar su capacidad instalada y asignar recursos de manera más eficiente.
    """)

    st.markdown("---")

    # Contexto
    st.subheader("🏙️ 1. Contexto territorial y epidemiológico")
    st.markdown("""
    El municipio de **Envigado** cuenta con una extensión de **51 km²** y una densidad poblacional estimada de **4.868,7 habitantes por km²** para el año **2024**.  
    La población total proyectada asciende a **248.304 habitantes**, con una distribución de **54,1 % mujeres** y **45,9 % hombres**.  
    De ellos, el **96,9 %** reside en zona urbana y el **3,1 %** en zona rural, según el **DANE** (Censo 2018, proyecciones 2024).  

    En 2023, el municipio contaba con **652 camas hospitalarias**, **133 salas** (30 quirófanos) y **90 camillas**, reflejando una red hospitalaria sólida pero exigida por la alta demanda.  

    El análisis de morbilidad muestra que las **enfermedades no transmisibles (ENT)** —cardiovasculares, neuropsiquiátricas, respiratorias y neoplasias malignas— representan la mayor proporción de consultas en todos los grupos etarios.  
    Las **condiciones transmisibles**, **nutricionales** y las **lesiones por causas externas** también tienen una participación importante, especialmente en la infancia y juventud.  

    Estos datos evidencian la necesidad de fortalecer la **planeación sanitaria preventiva y predictiva**, dada la creciente carga de enfermedades crónicas y de alto costo que presionan la red asistencial.  

    📖 *Fuente: Análisis de Situación de Salud Participativo (ASIS) – Municipio de Envigado, 2024.*
    """)

    st.markdown("---")

    # Problema
    st.subheader("⚠️ 2. Problema")
    st.markdown("""
    El sistema de salud de Envigado enfrenta un desafío creciente:  

    - La **alta demanda hospitalaria** y la **capacidad instalada limitada** generan picos de atención imprevisibles.  
    - Las decisiones se basan principalmente en **datos históricos**, dificultando anticipar brotes o variaciones en la demanda.  
    - No existen **herramientas locales de analítica predictiva** que integren los RIPS 2023–2024 para generar alertas tempranas o estimaciones de morbilidad.  

    Como resultado, la planeación en salud pública se ve afectada por la falta de información proyectiva que permita una gestión proactiva de los recursos hospitalarios.
    """)

    st.markdown("---")

    # Solución
    st.subheader("💡 3. Solución: *EpiScope Envigado*")
    st.markdown("""
    **EpiScope Envigado** es un proyecto de analítica avanzada que utiliza los **RIPS de hospitalización 2023–2024** para **identificar patrones diagnósticos (CIE-10)** y **anticipar tendencias de morbilidad**.  

    El modelo predictivo busca:  
    - Detectar cambios en los patrones de enfermedad.  
    - Estimar la demanda futura por diagnóstico y especialidad médica.  
    - Fortalecer la toma de decisiones en salud pública con base en datos reales.  

    En esencia, *EpiScope* transforma los RIPS en una **herramienta de inteligencia sanitaria**, pasando de un enfoque reactivo a uno **anticipativo y basado en evidencia**.
    """)

    st.markdown("---")

    # Objetivos
    st.subheader("🎯 4. Objetivos del proyecto")
    st.markdown("""
    **Objetivo general**  
    Desarrollar un modelo predictivo basado en analítica avanzada de los RIPS de hospitalización (2023–2024) del municipio de Envigado, para identificar patrones diagnósticos (CIE-10) y anticipar tendencias de morbilidad que fortalezcan la planeación epidemiológica y la gestión eficiente de recursos hospitalarios.  

    **Objetivos específicos**  
    1. Diseñar e implementar la infraestructura de datos del proyecto mediante un proceso **ETL (Extracción, Transformación y Carga)** que integre y gestione las fuentes de información.  
    2. Realizar un **análisis exploratorio** de los RIPS 2023–2024 para caracterizar la población hospitalizada y detectar patrones de morbilidad.  
    3. Construir y validar un **modelo predictivo** basado en diagnósticos CIE-10 que permita anticipar eventos de salud y apoyar la toma de decisiones en salud pública.
    """)

    st.markdown("---")

    # Impacto
    st.subheader("📈 5. Valor e impacto esperado")
    st.markdown("""
    El proyecto permitirá:  
    - Incrementar la **eficiencia operativa** mediante una mejor planeación de camas y servicios.  
    - **Reducir hasta en 20 %** la congestión hospitalaria mediante asignación preventiva de recursos.  
    - **Optimizar la inversión pública**, proyectando un ahorro del 15–20 % en costos de atención.  
    - Fortalecer la **capacidad institucional** de análisis de datos en salud pública local.
    """)

    st.markdown("---")

    # Equipo
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

# --- Páginas en construcción ---
elif page == "🔍 Análisis Exploratorio":
    st.title("🔍 Análisis Exploratorio")
    st.info("Esta sección mostrará el análisis descriptivo de los RIPS: distribución de diagnósticos, edades, sexo, EPS, y más. 🧮")

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

