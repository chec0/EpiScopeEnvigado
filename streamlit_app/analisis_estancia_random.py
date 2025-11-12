# streamlit_app/analisis_estancia_rf.py
# =====================================================
# 🌲 Análisis de la duración de estancia hospitalaria con Random Forest
# =====================================================

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score

# 📦 Funciones personalizadas del proyecto
from episcopeenvigado.dataset import obtener_dataset_completo, unificar_dataset

# -----------------------------------------------------
# 🏷️ Título principal
# -----------------------------------------------------
st.title("🌲 Análisis de la Duración de la Estancia Hospitalaria con Random Forest")

st.markdown("""
Explora un modelo basado en **Random Forest** para estimar la duración de la estancia hospitalaria.  
El enfoque no asume linealidad ni normalidad, y puede capturar relaciones no lineales entre variables.
""")

# -----------------------------------------------------
# 1️⃣ Carga de datos
# -----------------------------------------------------
if st.checkbox("📥 Cargar y visualizar datos"):
    st.subheader("Carga y unificación de datos")
    data = obtener_dataset_completo()
    df_unificado = unificar_dataset(data)

    st.write("Primeras filas del dataset unificado:")
    st.dataframe(df_unificado.head())
    st.info(f"Registros totales: {df_unificado.shape[0]:,} | Columnas: {df_unificado.shape[1]}")

# -----------------------------------------------------
# 2️⃣ Selección y exploración de variables
# -----------------------------------------------------
if st.checkbox("🔍 Seleccionar y explorar variables"):
    st.subheader("Selección de variables relevantes")

    variables_usadas = [
        'Via_Ingreso_Desc',
        'Estado_Salida_Desc',
        'Causa_Externa_Desc',
        'EDAD_ANIOS',
        'SEXO',
        'Capitulo_CIE10',
        'Duracion_Dias'
    ]

    df_modelo = df_unificado[variables_usadas].dropna()
    st.dataframe(df_modelo.head())

    # Distribución
    fig_hist = px.histogram(df_modelo, x="Duracion_Dias", nbins=50, title="Distribución de la duración de la estancia")
    st.plotly_chart(fig_hist, use_container_width=True)

# -----------------------------------------------------
# 3️⃣ Preparación de datos para Random Forest
# -----------------------------------------------------
if st.checkbox("⚙️ Preparar datos para el modelo"):
    st.subheader("Codificación y separación de datos")

    variables_numericas = ['EDAD_ANIOS']
    variables_categoricas = [
        'SEXO',
        'Via_Ingreso_Desc',
        'Causa_Externa_Desc',
        'Estado_Salida_Desc',
        'Capitulo_CIE10'
    ]

    # Codificar variables categóricas
    df_cats = df_modelo[variables_categoricas].astype(str)
    X_cat = pd.get_dummies(df_cats, drop_first=True)
    X = pd.concat([df_modelo[variables_numericas], X_cat], axis=1)
    y = df_modelo['Duracion_Dias']

    st.write(f"Variables finales: {X.shape[1]} columnas")
    st.dataframe(X.head())

    # División de datos
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    st.success(f"✅ Datos divididos: {X_train.shape[0]} entrenamiento | {X_test.shape[0]} prueba")

# -----------------------------------------------------
# 4️⃣ Entrenamiento y evaluación del modelo Random Forest
# -----------------------------------------------------
if st.checkbox("🌳 Entrenar modelo Random Forest"):
    st.subheader("Entrenamiento y evaluación")

    n_estimators = st.slider("Número de árboles", 50, 500, 200, step=50)
    max_depth = st.slider("Profundidad máxima del árbol", 3, 30, 10, step=1)
    random_state = 42

    modelo_rf = RandomForestRegressor(
        n_estimators=n_estimators,
        max_depth=max_depth,
        random_state=random_state,
        n_jobs=-1
    )
    modelo_rf.fit(X_train, y_train)

    y_pred = modelo_rf.predict(X_test)

    # Métricas de desempeño
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    mae = mean_absolute_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)

    resultados = pd.DataFrame({
        "Métrica": ["R²", "RMSE", "MAE"],
        "Valor": [round(r2, 3), round(rmse, 3), round(mae, 3)]
    })
    st.table(resultados)

    st.markdown("""
    **Interpretación:**
    - **R²:** proporción de variabilidad explicada por el modelo (1 es perfecto).
    - **RMSE:** error cuadrático medio, penaliza errores grandes.
    - **MAE:** error absoluto medio, mide desviación promedio.
    """)

    # Importancia de variables
    importancias = pd.DataFrame({
        "Variable": X.columns,
        "Importancia": modelo_rf.feature_importances_
    }).sort_values(by="Importancia", ascending=False)

    fig_imp = px.bar(importancias.head(20), x="Importancia", y="Variable",
                     orientation='h', title="Top 20 variables más importantes",
                     color="Importancia", color_continuous_scale="Blues")
    st.plotly_chart(fig_imp, use_container_width=True)

# -----------------------------------------------------
# 5️⃣ Predicción interactiva
# -----------------------------------------------------
if st.checkbox("🧮 Predicción interactiva"):
    st.subheader("Predicción con Random Forest")

    edad = st.slider("Edad (años)", 0, 100, 40)
    sexo = st.selectbox("Sexo", sorted(df_modelo['SEXO'].unique()))
    via = st.selectbox("Vía de ingreso", sorted(df_modelo['Via_Ingreso_Desc'].unique()))
    causa = st.selectbox("Causa externa", sorted(df_modelo['Causa_Externa_Desc'].unique()))
    estado = st.selectbox("Estado de salida", sorted(df_modelo['Estado_Salida_Desc'].unique()))
    capitulo = st.selectbox("Capítulo CIE10", sorted(df_modelo['Capitulo_CIE10'].unique()))

    input_data = pd.DataFrame({
        'EDAD_ANIOS': [edad],
        'SEXO': [str(sexo)],
        'Via_Ingreso_Desc': [str(via)],
        'Causa_Externa_Desc': [str(causa)],
        'Estado_Salida_Desc': [str(estado)],
        'Capitulo_CIE10': [str(capitulo)]
    })

    # Codificar entrada
    input_cat = pd.get_dummies(input_data[variables_categoricas].astype(str), drop_first=True)
    input_X = pd.concat([input_data[variables_numericas], input_cat], axis=1)
    input_X = input_X.reindex(columns=X.columns, fill_value=0)

    pred = modelo_rf.predict(input_X)[0]
    st.success(f"🕐 Duración estimada de estancia: **{pred:.2f} días**")

# -----------------------------------------------------
# 📎 Nota final
# -----------------------------------------------------
st.caption("""
Este modelo usa **Random Forest**, un método de ensamble no lineal que captura interacciones complejas entre variables.  
No requiere supuestos de normalidad ni homocedasticidad, y puede mejorar la precisión predictiva respecto a modelos lineales.
""")