import streamlit as st
import os


# ==============================================
# CONFIGURACIÓN GENERAL
# ==============================================
def mostrar_sidebar():
    """Carga el logo y el pie de página común en todas las páginas."""

    # Logo
    logo_path = os.path.join("streamlit_app", "LogoEpiScope.jpg")

    # --- Bloque superior con logo y encabezado ---
    with st.sidebar:
        st.image(logo_path, width=120)
        st.markdown("### 🏥 EpiScope Envigado")
        st.markdown("Analítica Predictiva en Salud Pública")
        st.markdown("---")

    # --- Bloque inferior (se muestra después de los enlaces) ---
    st.sidebar.markdown("👩‍💻 *Proyecto desarrollado por:*")
    st.sidebar.markdown("**Equipo EpiScope Envigado**")
    st.sidebar.markdown("© 2025")
