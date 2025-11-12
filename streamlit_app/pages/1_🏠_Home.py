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


if __name__ == "__main__":
    main()
