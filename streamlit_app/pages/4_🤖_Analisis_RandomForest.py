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
    st.title("🌲 Análisis de la Duración de la Estancia Hospitalaria con Random Forest")

    st.markdown("""
    Explora un modelo basado en **Random Forest** para estimar la duración de la estancia hospitalaria.  
    El enfoque no asume linealidad ni normalidad, y puede capturar relaciones no lineales entre variables.
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
            "Capitulo_CIE10",
            "Duracion_Dias",
        ]

        df_modelo = df_unificado[variables_usadas].dropna()
        st.session_state.df_modelo = df_modelo
        st.dataframe(df_modelo.head())

        # Crear columnas
        colH1, colH2, colH3 = st.columns([1, 4, 1])

        with colH2:
            # Distribución
            fig_hist = px.histogram(
                df_modelo,
                x="Duracion_Dias",
                nbins=50,
                title="Distribución de la duración de la estancia",
            )
            st.plotly_chart(fig_hist, use_container_width=True)

    # -----------------------------------------------------
    # 3️⃣ Preparación de datos para Random Forest
    # -----------------------------------------------------
    if st.button("⚙️ Preparar datos para el modelo"):
        if "df_modelo" not in st.session_state:
            st.warning("⚠️ Primero debes seleccionar las variables.")
            st.stop()

        df_modelo = st.session_state.df_modelo

        st.subheader("Codificación y separación de datos")

        st.session_state.variables_numericas = ["EDAD_ANIOS"]
        st.session_state.variables_categoricas = [
            "SEXO",
            "Via_Ingreso_Desc",
            "Causa_Externa_Desc",
            "Estado_Salida_Desc",
            "Capitulo_CIE10",
        ]

        # Codificar variables categóricas
        df_cats = df_modelo[st.session_state.variables_categoricas].astype(str)
        X_cat = pd.get_dummies(df_cats, drop_first=True)
        X = pd.concat([df_modelo[st.session_state.variables_numericas], X_cat], axis=1)
        y = df_modelo["Duracion_Dias"]
        st.session_state.X = X
        st.session_state.y = y

        st.write(f"Variables finales: {X.shape[1]} columnas")
        st.dataframe(X.head())

        # División de datos
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )

        st.session_state.X_train = X_train
        st.session_state.X_test = X_test
        st.session_state.y_train = y_train
        st.session_state.y_test = y_test

        st.success(
            f"✅ Datos divididos: {X_train.shape[0]} entrenamiento | {X_test.shape[0]} prueba"
        )

    # -----------------------------------------------------
    # 4️⃣ Entrenamiento y evaluación del modelo Random Forest
    # -----------------------------------------------------
    if st.checkbox("🌳 Entrenar modelo Random Forest"):
        if "X_train" not in st.session_state:
            st.warning("⚠️ Primero debes preparar los datos.")
            st.stop()

        st.subheader("Entrenamiento y evaluación")

        arb1, arb2, arb3 = st.columns([2, 3, 3])

        with arb1:
            n_estimators = st.slider("Número de árboles", 50, 500, 200, step=50)
            max_depth = st.slider("Profundidad máxima del árbol", 3, 30, 10, step=1)
            random_state = 42

        modelo_rf = RandomForestRegressor(
            n_estimators=n_estimators,
            max_depth=max_depth,
            random_state=random_state,
            n_jobs=-1,
        )
        modelo_rf.fit(st.session_state.X_train, st.session_state.y_train)

        st.session_state.modelo_rf = modelo_rf

        y_pred = modelo_rf.predict(st.session_state.X_test)

        # Métricas de desempeño
        rmse = np.sqrt(mean_squared_error(st.session_state.y_test, y_pred))
        mae = mean_absolute_error(st.session_state.y_test, y_pred)
        r2 = r2_score(st.session_state.y_test, y_pred)

        resultados = pd.DataFrame(
            {
                "Métrica": ["R²", "RMSE", "MAE"],
                "Valor": [round(r2, 3), round(rmse, 3), round(mae, 3)],
            }
        )
        st.table(resultados)

        st.markdown("""
        **Interpretación:**
        - **R²:** proporción de variabilidad explicada por el modelo (1 es perfecto).
        - **RMSE:** error cuadrático medio, penaliza errores grandes.
        - **MAE:** error absoluto medio, mide desviación promedio.
        """)

        # Importancia de variables
        importancias = pd.DataFrame(
            {
                "Variable": st.session_state.X.columns,
                "Importancia": modelo_rf.feature_importances_,
            }
        ).sort_values(by="Importancia", ascending=False)

        fig_imp = px.bar(
            importancias.head(20),
            x="Importancia",
            y="Variable",
            orientation="h",
            title="Top 20 variables más importantes",
            color="Importancia",
            color_continuous_scale="Blues",
        )
        st.plotly_chart(fig_imp, use_container_width=True)

    # -----------------------------------------------------
    # 5️⃣ Predicción interactiva
    # -----------------------------------------------------
    if st.checkbox("🧮 Predicción interactiva"):
        if "modelo_rf" not in st.session_state:
            st.warning("⚠️ Debes entrenar el modelo primero.")
            st.stop()

        modelo_rf = st.session_state.modelo_rf
        X = st.session_state.X
        df_modelo = st.session_state.df_modelo

        st.subheader("Predicción con Random Forest")

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
            capitulo = st.selectbox(
                "Capítulo CIE10",
                options=["- Seleccione -"]
                + sorted(df_modelo["Capitulo_CIE10"].unique()),
                index=0,
            )
        # Botón para calcular
        calcular = st.button("📊 Calcular duración estimada")

        if calcular:
            if (
                via == "- Seleccione -"
                or causa == "- Seleccione -"
                or estado == "- Seleccione -"
                or capitulo == "- Seleccione -"
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
                    "Capitulo_CIE10": [str(capitulo)],
                }
            )

            # Codificar entrada
            input_cat = pd.get_dummies(
                input_data[st.session_state.variables_categoricas].astype(str),
                drop_first=True,
            )
            input_X = pd.concat(
                [input_data[st.session_state.variables_numericas], input_cat], axis=1
            )
            input_X = input_X.reindex(columns=X.columns, fill_value=0)

            pred = modelo_rf.predict(input_X)[0]

            # Mostrar resultado en una “placa”
            st.markdown(
                f"""
                <div class="grafico-marco" style="text-align:center; width:60%; margin:auto;">
                    🕐 <strong>Duración estimada de estancia:</strong>  
                    <div style="font-size:28px; color:#5b10ad; font-weight:bold;">
                        {pred:.2f} días
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    # -----------------------------------------------------
    # 📎 Nota final
    # -----------------------------------------------------
    st.caption("""
    Este modelo usa **Random Forest**, un método de ensamble no lineal que captura interacciones complejas entre variables.  
    No requiere supuestos de normalidad ni homocedasticidad, y puede mejorar la precisión predictiva respecto a modelos lineales.
    """)


if __name__ == "__main__":
    main()
