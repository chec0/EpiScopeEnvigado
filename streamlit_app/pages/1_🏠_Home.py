import streamlit as st
from utils_sidebar import mostrar_sidebar


# ==============================================
# PÁGINA HOME
# ==============================================
def main():
    mostrar_sidebar()
    st.title("🏠 Home")
    st.markdown(
        "### EpiScope Envigado — Analítica predictiva para la planeación hospitalaria y epidemiológica en Envigado"
    )
    st.markdown("---")

    st.markdown("""
    Hoy, el sistema de salud de **Envigado** enfrenta un reto silencioso pero crítico: la dificultad para anticipar la demanda hospitalaria.
    Los picos de atención llegan sin aviso, los diagnósticos se dispersan en bases de datos extensas y las decisiones se toman mirando hacia atrás, no hacia adelante.
    """)

    st.markdown("""
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
    Evaluar un modelo predictivo basado en analítica avanzada de los RIPS de hospitalización (2023–2024) del municipio de Envigado, para identificar patrones diagnósticos (CIE-10) y anticipar tendencias de morbilidad que fortalezcan la planeación epidemiológica y la gestión eficiente de recursos hospitalarios.

    **Objetivos específicos**  
    1.Diseñar e implementar la infraestructura de datos del proyecto mediante un proceso ETL (Extracción, Transformación y Carga) que permita la creación y gestión eficiente de la base de datos, asegurando la integración adecuada de las fuentes de información.
    
    2.Realizar un Análisis Exploratorio de Datos (EDA) para caracterizar la población hospitalizada en Envigado durante el periodo 2023–2024, identificando tendencias de morbilidad, frecuencias de diagnóstico y variables relevantes para el modelado predictivo.
    
    3.Construir y validar un modelo predictivo basado en los códigos CIE-10, empleando técnicas de machine learning y algoritmos supervisados de clasificación, que permitan inferir relaciones entre diagnósticos y anticipar eventos de salud, contribuyendo a la toma de decisiones estratégicas en salud pública.

    """)

    st.markdown("---")
    st.subheader("📈 5. Valor e impacto esperado")
    st.markdown("""
    El proyecto permitirá:  
    - Incrementar la **eficiencia operativa** mediante una mejor planeación de camas y servicios.  
    - **Reducir** la congestión hospitalaria.  
    - **Optimizar la inversión pública**, proyectando un ahorro en costos de atención.  
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


if __name__ == "__main__":
    main()
