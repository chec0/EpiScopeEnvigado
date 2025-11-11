import streamlit as st
import pandas as pd
import numpy as np
import statsmodels.api as sm
from pathlib import Path
from episcopeenvigado.dataset import cargar_datasets_locales
from episcopeenvigado.config import PROCESSED_DATA_DIR

# -----------------------------------------------------
# Título de la app
# -----------------------------------------------------
st.title("🔹 Regresión Logística: Dx1 → Dx2 con covariables")

# -----------------------------------------------------
# Cargar datasets procesados
# -----------------------------------------------------
if "datasets_locales" not in st.session_state:
    with st.spinner("Cargando archivos procesados..."):
        st.session_state["datasets_locales"] = cargar_datasets_locales(PROCESSED_DATA_DIR)

datasets = st.session_state["datasets_locales"]

# Normalizar claves para evitar problemas de mayúsculas o espacios
datasets_normalizados = {
    str(k).strip().lower(): v for k, v in datasets.items()
}

st.write("Archivos disponibles:", list(datasets_normalizados.keys()))

# Acceder al dataset de coocurrencias
df_cooc = datasets_normalizados.get("analisis_coocurrencias_significativas")

if df_cooc is None or df_cooc.empty:
    st.warning("⚠️ No se encontró el archivo 'analisis_coocurrencias_significativas.xlsx' o está vacío.")
    st.stop()
else:
    st.success(f"✅ Dataset cargado con {df_cooc.shape[0]} filas")
    st.dataframe(df_cooc.head())

# -----------------------------------------------------
# Selección de Dx1 y Dx2
# -----------------------------------------------------
st.subheader("🔍 Selección de diagnósticos")
dx1_selected = st.selectbox("Seleccione Dx1", sorted(df_cooc['Dx1'].unique()))
dx2_selected = st.selectbox("Seleccione Dx2", sorted(df_cooc['Dx2'].unique()))

# Filtrar dataset según selección
df_model = df_cooc[(df_cooc['Dx1'] == dx1_selected) & (df_cooc['Dx2'] == dx2_selected)].copy()
st.write(f"Filtrado: {len(df_model)} filas")

# -----------------------------------------------------
# Variable dependiente y covariables
# -----------------------------------------------------
# Crear variable binaria: Dx2 presente (1) o no (0)
df_model['Dx2_presente'] = np.where(df_model['count_coocurrence'] > 0, 1, 0)

# Covariables (solo se conservan las que existan)
covariables = ['EDAD_ANIOS', 'SEXO', 'Via_Ingreso_Desc', 'Estado_Salida_Desc']
covariables = [col for col in covariables if col in df_model.columns]

if not covariables:
    st.warning("⚠️ No se encontraron covariables disponibles en el dataset. Solo se usará constante.")
    X = pd.DataFrame({'const': 1}, index=df_model.index)
else:
    X = df_model[covariables]
    X = pd.get_dummies(X, drop_first=True)
    X = sm.add_constant(X)

y = df_model['Dx2_presente']

# -----------------------------------------------------
# Ajuste del modelo logístico
# -----------------------------------------------------
st.subheader("📈 Ajuste de modelo de regresión logística")
try:
    modelo = sm.Logit(y, X).fit(disp=False)
    st.write(modelo.summary())

    # Tabla de OR y CI95%
    OR = np.exp(modelo.params)
    CI_lower = np.exp(modelo.conf_int()[0])
    CI_upper = np.exp(modelo.conf_int()[1])
    p_values = modelo.pvalues

    df_or = pd.DataFrame({
        "Variable": OR.index,
        "OR": OR.values,
        "IC95_Lower": CI_lower.values,
        "IC95_Upper": CI_upper.values,
        "p-value": p_values.values
    }).sort_values(by="p-value")
    st.markdown("### 📝 Odds Ratios y IC95%")
    st.dataframe(df_or)

except Exception as e:
    st.error(f"Error al ajustar el modelo: {e}")

# -----------------------------------------------------
# Predicción interactiva
# -----------------------------------------------------
st.subheader("🧮 Predicción interactiva")

if not X.empty:
    input_dict = {}
    for col in covariables:
        if col in df_model.columns and df_model[col].dtype == object:
            input_dict[col] = [st.selectbox(col, sorted(df_model[col].dropna().unique()))]
        elif col in df_model.columns:
            input_dict[col] = [st.number_input(col, value=int(df_model[col].median()))]

    input_df = pd.DataFrame(input_dict)
    input_df = pd.get_dummies(input_df, drop_first=True)
    
    # Asegurar mismas columnas que X
    for col in X.columns:
        if col not in input_df.columns:
            input_df[col] = 0
    input_df = input_df[X.columns]

    pred_pr_
