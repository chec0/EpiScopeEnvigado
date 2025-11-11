# streamlit_app/analisis_estancia.py
# =====================================================
# 🧠 Análisis de la duración de estancia hospitalaria
# =====================================================

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import statsmodels.api as sm
from statsmodels.stats.outliers_influence import variance_inflation_factor

# 📦 Funciones personalizadas del proyecto
from episcopeenvigado.dataset import obtener_dataset_completo, unificar_dataset

# -----------------------------------------------------
# 🏷️ Título principal
# -----------------------------------------------------
st.title("📊 Análisis de la Duración de la Estancia Hospitalaria")

st.markdown("""
Explora paso a paso el proceso de análisis y modelado de la duración de la estancia hospitalaria.  
Cada sección puede expandirse con un *checkbox* para facilitar la exploración.  
Se incluyen explicaciones para interpretar los resultados estadísticos y gráficos.
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

    st.markdown("""
    **Interpretación:**
    - Aquí puedes verificar que los datos se hayan cargado correctamente.
    - Observa los tipos de variables y posibles valores nulos.
    - Esta revisión preliminar permite detectar errores de carga antes de análisis más profundos.
    """)

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
        'Duracion_Dias'
    ]

    df_modelo = df_unificado[variables_usadas].dropna()
    st.write("Dataset para el modelo:")
    st.dataframe(df_modelo.head())

    # Histograma interactivo
    fig_hist = px.histogram(
        df_modelo,
        x="Duracion_Dias",
        nbins=50,
        title="Distribución de la duración de la estancia",
        color_discrete_sequence=['#6ab7ff']
    )
    st.plotly_chart(fig_hist, use_container_width=True)

    st.markdown("""
    **Interpretación del histograma:**
    - Permite visualizar cómo se distribuyen los días de estancia.
    - Busca sesgos, colas largas o valores atípicos.
    - Una distribución muy sesgada puede afectar la regresión lineal.
    """)

    # Boxplot por sexo
    fig_box = px.box(
        df_modelo,
        x="SEXO",
        y="Duracion_Dias",
        title="Duración de la estancia por sexo",
        color="SEXO",
        color_discrete_sequence=['#9ad0f5', '#f5a3a3']
    )
    st.plotly_chart(fig_box, use_container_width=True)

    st.markdown("""
    **Interpretación del boxplot:**
    - Compara la duración de estancia entre hombres y mujeres.
    - Los “bigotes” muestran la variabilidad y posibles valores extremos.
    - Útil para detectar diferencias de comportamiento según sexo.
    """)

# -----------------------------------------------------
# 3️⃣ Preparación del modelo
# -----------------------------------------------------
if st.checkbox("⚙️ Preparar datos para el modelo"):
    st.subheader("Preparación de variables")

    variables_numericas = ['EDAD_ANIOS']
    variables_categoricas = [
        'SEXO',
        'Via_Ingreso_Desc',
        'Causa_Externa_Desc',
        'Estado_Salida_Desc'
    ]

    df_cats = df_modelo[variables_categoricas].astype(str)
    X_cat = pd.get_dummies(df_cats, drop_first=True)
    X = pd.concat([df_modelo[variables_numericas], X_cat], axis=1)
    X = sm.add_constant(X)
    y = df_modelo['Duracion_Dias']

    # Filtrar datos válidos
    mask = X.notnull().all(axis=1) & y.notnull()
    X = X.loc[mask].astype(float)
    y = y.loc[mask].astype(float)

    st.write("Variables finales para el modelo:")
    st.write(f"**X:** {X.shape[1]} columnas | **y:** {y.shape[0]} registros")
    st.dataframe(X.head())

    st.markdown("""
    **Interpretación:**
    - Se crean **variables dummy** para variables categóricas, necesarias para regresión lineal.
    - `drop_first=True` evita la multicolinealidad perfecta.
    - Se revisa que no haya valores nulos ni inconsistencias en X o y.
    """)

# -----------------------------------------------------
# 4️⃣ Ajuste del modelo OLS y análisis estadístico
# -----------------------------------------------------
if st.checkbox("📈 Ajustar modelo de regresión OLS"):
    st.subheader("Modelo de Regresión Lineal (OLS)")

    modelo = sm.OLS(y, X).fit()

    # Resumen estructurado
    st.markdown("### 🧾 Resumen del modelo")
    resumen = pd.DataFrame({
        "Métrica": [
            "R²",
            "R² ajustado",
            "F-Statistic",
            "Prob (F-stat)",
            "Observaciones",
            "Condición numérica"
        ],
        "Valor": [
            round(modelo.rsquared, 3),
            round(modelo.rsquared_adj, 3),
            round(modelo.fvalue, 3),
            round(modelo.f_pvalue, 6),
            int(modelo.nobs),
            round(modelo.condition_number, 2)
        ]
    })
    st.table(resumen)

    st.markdown("""
    **Interpretación estadística del resumen:**
    - **R²:** porcentaje de la variabilidad explicada por el modelo.
    - **R² ajustado:** ajusta R² por número de variables; útil para comparar modelos con diferente cantidad de predictores.
    - **F-Statistic y Prob (F-stat):** evalúa si el modelo completo es significativo.
    - **Condición numérica:** alerta sobre posibles problemas de multicolinealidad alta.
    """)

    # Tabla de coeficientes
    coef_df = pd.DataFrame({
        'Variable': modelo.params.index,
        'Coeficiente': modelo.params.values,
        'Error Std': modelo.bse.values,
        't-Valor': modelo.tvalues.values,
        'p-Valor': modelo.pvalues.values
    }).sort_values(by="p-Valor")
    st.markdown("### 📊 Coeficientes del modelo")
    st.dataframe(coef_df, use_container_width=True)

    st.markdown("""
    **Interpretación de coeficientes:**
    - Un coeficiente positivo indica que al aumentar la variable, la duración de estancia tiende a aumentar.
    - Un p-valor < 0.05 indica significancia estadística.
    - El error estándar indica precisión de la estimación.
    """)

    # -------------------------------
    # Multicolinealidad (VIF)
    # -------------------------------
    st.markdown("### ⚖️ Multicolinealidad (VIF)")
    vif_data = pd.DataFrame()
    vif_data["Variable"] = X.columns
    vif_data["VIF"] = [variance_inflation_factor(X.values, i) for i in range(X.shape[1])]
    st.dataframe(vif_data.sort_values(by="VIF", ascending=False))

    st.markdown("""
    **Interpretación de VIF:**
    - VIF > 5-10 indica posible multicolinealidad alta.
    - Variables muy correlacionadas pueden inflar errores estándar y afectar interpretación de coeficientes.
    """)

    # -------------------------------
    # Residuos del modelo
    # -------------------------------
    st.markdown("### 📉 Análisis de residuos")
    resid = modelo.resid
    fig_resid = px.histogram(resid, nbins=50, title="Distribución de residuos", color_discrete_sequence=['#ff7f0e'])
    st.plotly_chart(fig_resid, use_container_width=True)

    fig_resid_scatter = px.scatter(x=modelo.fittedvalues, y=resid,
                                  labels={'x':'Valores ajustados','y':'Residuos'},
                                  title="Residuos vs Valores ajustados")
    st.plotly_chart(fig_resid_scatter, use_container_width=True)

    st.markdown("""
    **Interpretación de residuos:**
    - Los residuos deberían seguir distribución aproximadamente normal (histograma simétrico).
    - Residuos vs valores ajustados permite verificar **homocedasticidad** (varianza constante).
    - Patrones claros o funil en el scatter sugieren problemas en el modelo.
    """)

# -----------------------------------------------------
# 5️⃣ Predicción interactiva con intervalo de confianza
# -----------------------------------------------------
if st.checkbox("🧮 Predicción interactiva"):
    st.subheader("Estimación de duración de estancia")

    edad = st.slider("Edad (años)", 0, 100, 40)
    sexo = st.selectbox("Sexo", sorted(df_modelo['SEXO'].unique()))
    via = st.selectbox("Vía de ingreso", sorted(df_modelo['Via_Ingreso_Desc'].unique()))
    causa = st.selectbox("Causa externa", sorted(df_modelo['Causa_Externa_Desc'].unique()))
    estado = st.selectbox("Estado a la salida", sorted(df_modelo['Estado_Salida_Desc'].unique()))

    input_data = pd.DataFrame({
        'EDAD_ANIOS': [edad],
        'SEXO': [str(sexo)],
        'Via_Ingreso_Desc': [str(via)],
        'Causa_Externa_Desc': [str(causa)],
        'Estado_Salida_Desc': [str(estado)]
    })

    input_cat = pd.get_dummies(input_data[variables_categoricas].astype(str), drop_first=True)
    input_X = pd.concat([input_data[variables_numericas], input_cat], axis=1)
    input_X = sm.add_constant(input_X.reindex(columns=X.columns, fill_value=0))

    # Predicción con intervalo de confianza
    prediccion = modelo.get_prediction(input_X)
    pred_summary = prediccion.summary_frame(alpha=0.05)  # 95% CI

    st.success(f"🕐 Duración estimada de estancia: **{pred_summary['mean'][0]:.2f} días**")
    st.info(f"Intervalo de confianza 95%: {pred_summary['obs_ci_lower'][0]:.2f} - {pred_summary['obs_ci_upper'][0]:.2f} días")

    st.markdown("""
    **Interpretación de predicciones:**
    - El valor central es la duración estimada para un paciente con estas características.
    - El **intervalo de confianza 95%** indica el rango donde se espera que caiga la duración real del paciente el 95% de las veces.
    """)

# -----------------------------------------------------
# 📎 Nota final
# -----------------------------------------------------
st.caption("""
Este modelo usa regresión lineal (OLS) para estimar la duración de estancia hospitalaria según variables clínicas y demográficas.  
Incluye análisis de residuos, multicolinealidad y predicciones con intervalo de confianza para facilitar interpretación estadística.
""")
