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
from utils_sidebar import mostrar_sidebar

# 📦 Funciones personalizadas del proyecto
from episcopeenvigado.dataset import obtener_dataset_completo, unificar_dataset

# =========================================================
#  ESTILOS PARA MOSTRAR DATOS
# =========================================================
st.markdown(
    """
    <style>
    .grafico-marco {
        color: #1e1e1e;
        background: linear-gradient(180deg, #ffffff 0%, #f7f8fa 100%);
        border: 1px solid rgba(0, 0, 0, 0.08);
        border-left: 6px solid #5b10ad; /* acento corporativo */
        border-radius: 10px;
        box-shadow: 0 6px 14px rgba(0, 0, 0, 0.08);
        padding: 0.5em 1.8em;
        margin-bottom: 1.8em;
        width: 40%;
        transition: all 0.25s ease-in-out;
        font-weight: bolder;
        font-size: larger;            
    }

    .grafico-marco:hover {
        transform: translateY(-3px);
        box-shadow: 0 10px 20px rgba(0, 0, 0, 0.15);
        border-left-color: #00c0e2; /* efecto hover con color secundario */
    }
    .stButton > button {
        background-color: #a7c957;
        color: white;
        border: none;
        padding: 0.6em 1.2em;
        border-radius: 8px;
        font-size: 16px;
        font-weight: 400;
        transition: all 0.2s ease-in-out;
    }
    .stButton > button:hover {
        background-color: #0077b6;
        transform: scale(1.03);
    }
    .titulo-h3 {
        font-size: 20px;
        font-weight: 600;
        margin-top: -0.2em;
        margin-bottom: 1em;
    }        
    </style>
    """,
    unsafe_allow_html=True,
)


def main():
    mostrar_sidebar()
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
    if "df_unificado" not in st.session_state:
        with st.spinner("Cargando dataset..."):
            data = obtener_dataset_completo()
            st.session_state.df_unificado = unificar_dataset(data)
        st.success("✅ Datos cargados y almacenados en sesión.")

    df_unificado = st.session_state.df_unificado

    if st.button("📥 Cargar y visualizar datos"):
        st.write("Primeras filas del dataset unificado:")
        st.dataframe(df_unificado.head())
        st.write(
            f"<div class='grafico-marco'>Registros totales: {df_unificado.shape[0]:,} | Columnas: {df_unificado.shape[1]}</div>",
            unsafe_allow_html=True,
        )

    # -----------------------------------------------------
    # 2️⃣ Selección y exploración de variables
    # -----------------------------------------------------
    if st.button("🔍 Seleccionar y explorar variables"):
        st.subheader("Selección de variables relevantes")

        variables_usadas = [
            "Via_Ingreso_Desc",
            "Estado_Salida_Desc",
            "Causa_Externa_Desc",
            "EDAD_ANIOS",
            "SEXO",
            "Duracion_Dias",
            "Capitulo_CIE10",
        ]
        df_modelo = df_unificado[variables_usadas].dropna()
        st.session_state.df_modelo = df_modelo
        st.dataframe(df_modelo.head())

        # Crear columnas
        colH1, colH2, colH3 = st.columns([1, 4, 1])

        with colH2:
            # Histograma interactivo
            fig_hist = px.histogram(
                df_modelo,
                x="Duracion_Dias",
                nbins=50,
                title="Distribución de la duración de la estancia",
                color_discrete_sequence=["#6ab7ff"],
                labels={
                    "Duracion_Dias": "Duración de la estancia (días)",
                    "count": "Frecuencia de pacientes",
                },
            )
            fig_hist.update_layout(
                xaxis_title="Duración de la estancia (días)",
                yaxis_title="Frecuencia de pacientes",
            )
            st.plotly_chart(fig_hist, use_container_width=True)

        st.markdown("""
        **Interpretación del histograma:**
        - Permite visualizar cómo se distribuyen los días de estancia.
        - Busca sesgos, colas largas o valores atípicos.
        - Una distribución muy sesgada puede afectar la regresión lineal.
        """)

        # Crear columnas
        colH1, colH2, colH3 = st.columns([1, 4, 1])

        with colH2:
            # Boxplot por sexo
            fig_box = px.box(
                df_modelo,
                x="SEXO",
                y="Duracion_Dias",
                title="Duración de la estancia por sexo",
                color="SEXO",
                color_discrete_sequence=["#9ad0f5", "#f5a3a3"],
                labels={
                    "SEXO": "Sexo del paciente",
                    "Duracion_Dias": "Duración de la estancia (días)",
                },
            )

            fig_box.update_layout(
                xaxis_title="Sexo del paciente",
                yaxis_title="Duración de la estancia (días)",
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
    if st.button("⚙️ Preparar datos para el modelo"):
        if "df_modelo" not in st.session_state:
            st.warning("⚠️ Primero debes seleccionar las variables.")
            st.stop()

        df_modelo = st.session_state.df_modelo

        st.subheader("Preparación de variables")

        st.session_state.variables_numericas = ["EDAD_ANIOS"]
        st.session_state.variables_categoricas = [
            "SEXO",
            "Via_Ingreso_Desc",
            "Causa_Externa_Desc",
            "Estado_Salida_Desc",
        ]

        df_cats = df_modelo[st.session_state.variables_categoricas].astype(str)
        X_cat = pd.get_dummies(df_cats, drop_first=True)
        X = pd.concat([df_modelo[st.session_state.variables_numericas], X_cat], axis=1)
        X = sm.add_constant(X)
        y = df_modelo["Duracion_Dias"]

        # Filtrar datos válidos
        mask = X.notnull().all(axis=1) & y.notnull()
        X = X.loc[mask].astype(float)
        y = y.loc[mask].astype(float)
        st.session_state.X = X
        st.session_state.y = y

        st.write("Variables finales para el modelo:")
        st.write(
            f"**X:** {st.session_state.X.shape[1]} columnas | **y:** {st.session_state.y.shape[0]} registros"
        )
        st.dataframe(st.session_state.X.head())

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

        modelo = sm.OLS(st.session_state.y, st.session_state.X).fit()
        st.session_state.modelo = modelo

        # Resumen estructurado
        st.markdown("### 🧾 Resumen del modelo")
        resumen = pd.DataFrame(
            {
                "Métrica": [
                    "R²",
                    "R² ajustado",
                    "F-Statistic",
                    "Prob (F-stat)",
                    "Observaciones",
                    "Condición numérica",
                ],
                "Valor": [
                    round(st.session_state.modelo.rsquared, 3),
                    round(st.session_state.modelo.rsquared_adj, 3),
                    round(st.session_state.modelo.fvalue, 3),
                    round(st.session_state.modelo.f_pvalue, 6),
                    int(st.session_state.modelo.nobs),
                    round(st.session_state.modelo.condition_number, 2),
                ],
            }
        )
        st.table(resumen)

        st.markdown("""
        **Interpretación estadística del resumen:**
        - **R²:** porcentaje de la variabilidad explicada por el modelo.
        - **R² ajustado:** ajusta R² por número de variables; útil para comparar modelos con diferente cantidad de predictores.
        - **F-Statistic y Prob (F-stat):** evalúa si el modelo completo es significativo.
        - **Condición numérica:** alerta sobre posibles problemas de multicolinealidad alta.
        """)

        # Tabla de coeficientes
        coef_df = pd.DataFrame(
            {
                "Variable": st.session_state.modelo.params.index,
                "Coeficiente": st.session_state.modelo.params.values,
                "Error Std": st.session_state.modelo.bse.values,
                "t-Valor": st.session_state.modelo.tvalues.values,
                "p-Valor": st.session_state.modelo.pvalues.values,
            }
        ).sort_values(by="p-Valor")
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
        vif_data["Variable"] = st.session_state.X.columns
        vif_data["VIF"] = [
            variance_inflation_factor(st.session_state.X.values, i)
            for i in range(st.session_state.X.shape[1])
        ]
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
        resid = st.session_state.modelo.resid
        # Crear columnas
        colH1, colH2, colH3 = st.columns([6, 1, 6])

        with colH1:
            fig_resid = px.histogram(
                resid,
                nbins=50,
                title="Distribución de residuos",
                color_discrete_sequence=["#ff7f0e"],
            )
            st.plotly_chart(fig_resid, use_container_width=True)

        with colH3:
            fig_resid_scatter = px.scatter(
                x=st.session_state.modelo.fittedvalues,
                y=resid,
                labels={"x": "Valores ajustados", "y": "Residuos"},
                title="Residuos vs Valores ajustados",
            )
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
        if "df_modelo" not in st.session_state:
            st.warning("⚠️ Debes entrenar el modelo primero.")
            st.stop()

        df_modelo = st.session_state.df_modelo

        st.markdown(
            "Ingresa los valores o selecciones los parámetros clínicos para estimar la duración de la estancia hospitalaria."
        )

        # Crear columnas
        col1, col2, col3, col4 = st.columns([3, 1, 2, 2])

        with col1:
            edad = st.slider("Edad (años)", 0, 100, 40)
        with col2:
            sexo = st.radio(
                "Sexo", options=sorted(df_modelo["SEXO"].unique()), horizontal=True
            )
        with col3:
            via = st.selectbox(
                "Vía de ingreso",
                options=["- Seleccione -"]
                + sorted(df_modelo["Via_Ingreso_Desc"].unique()),
                index=0,
            )
        with col4:
            estado = st.selectbox(
                "Estado de salida",
                options=["- Seleccione -"]
                + sorted(df_modelo["Estado_Salida_Desc"].unique()),
                index=0,
            )

        fil1, fil2 = st.columns([2, 2])

        with fil1:
            causa = st.selectbox(
                "Causa externa",
                options=["- Seleccione -"]
                + sorted(df_modelo["Causa_Externa_Desc"].unique()),
                index=0,
            )
        # Botón para calcular
        calcular = st.button("📊 Calcular duración estimada")

        if calcular:
            if (
                via == "- Seleccione -"
                or causa == "- Seleccione -"
                or estado == "- Seleccione -"
            ):
                st.warning(
                    "⚠️ Debes seleccionar todas las opciones antes de calcular la predicción."
                )
                st.stop()

            # Preparar datos de entrada
            input_data = pd.DataFrame(
                {
                    "EDAD_ANIOS": [edad],
                    "SEXO": [str(sexo)],
                    "Via_Ingreso_Desc": [str(via)],
                    "Causa_Externa_Desc": [str(causa)],
                    "Estado_Salida_Desc": [str(estado)],
                }
            )

            input_cat = pd.get_dummies(
                input_data[st.session_state.variables_categoricas].astype(str),
                drop_first=True,
            )
            input_X = pd.concat(
                [input_data[st.session_state.variables_numericas], input_cat], axis=1
            )
            input_X = sm.add_constant(
                input_X.reindex(columns=st.session_state.X.columns, fill_value=0)
            )

            # Predicción con intervalo de confianza
            prediccion = modelo.get_prediction(input_X)
            pred_summary = prediccion.summary_frame(alpha=0.05)  # 95% CI

            # Mostrar resultado en una “placa”
            st.info(
                f"Intervalo de confianza 95%: {pred_summary['obs_ci_lower'][0]:.2f} - {pred_summary['obs_ci_upper'][0]:.2f} días"
            )
            st.markdown(
                f"""
                <div class="grafico-marco" style="text-align:center; width:60%; margin:auto;">
                    🕐 <strong>Duración estimada de estancia:</strong>  
                    <div style="font-size:28px; color:#5b10ad; font-weight:bold;">
                        {pred_summary["mean"][0]:.2f} días
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

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


if __name__ == "__main__":
    main()
