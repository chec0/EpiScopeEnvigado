import streamlit as st
import os
from utils_sidebar import mostrar_sidebar

# ==============================
# CONFIGURACIÓN GENERAL
# ==============================
st.sidebar.empty()

# ==============================
# SIDEBAR GLOBAL
# ==============================
mostrar_sidebar()
st.title("🏥 EpiScope Envigado")
st.markdown(
    "### Analítica predictiva para la planeación hospitalaria y epidemiológica en Envigado"
)
st.markdown("---")
st.markdown(
    "Selecciona una página en el menú lateral para explorar los análisis, modelos y resultados del proyecto. 📊"
)
st.set_page_config(
    page_title="EpiScope Envigado",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
)
