import streamlit as st
import plotly.express as px
import numpy as np
import pandas as pd
from utils_sidebar import mostrar_sidebar
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
        width: 200px;
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
    st.title("🔍 Análisis Exploratorio de los RIPS")
    st.markdown(
        '<div class="titulo-h3">📊 Caracterización general de la base de datos</div>',
        unsafe_allow_html=True,
    )

    with st.spinner("Cargando dataset..."):
        datasets = obtener_dataset_completo()

    if not datasets:
        st.error("❌ No se pudieron cargar las tablas desde la base de datos.")
        st.stop()

    try:
        df_unificado = unificar_dataset(datasets)
    except KeyError as e:
        st.error(f"❌ Falta la tabla '{e.args[0]}'")
        st.stop()
    st.write(
        f"<div class='grafico-marco'>Registros totales: <b>{len(df_unificado):,}</b></div>",
        unsafe_allow_html=True,
    )

    # =========================================================
    # TABS PRINCIPALES
    # =========================================================
    tab1, tab2, tab3 = st.tabs(
        [
            "📋 Descripción del dataset",
            "📊 Distribuciones básicas",
            "🧠 Diagnósticos y causas externas",
        ]
    )

    # =========================================================
    # TAB 1: DESCRIPCIÓN DEL DATASET
    # =========================================================
    with tab1:
        st.subheader("🧾 Panel de inspección del dataset")

        if st.button("📋 Descripción de columnas"):
            col_desc = pd.DataFrame(
                {
                    "Columna": df_unificado.columns,
                    "Tipo": [df_unificado[col].dtype for col in df_unificado.columns],
                    "Count": [
                        df_unificado[col].count() for col in df_unificado.columns
                    ],
                    "Nulos": [
                        df_unificado[col].isna().sum() for col in df_unificado.columns
                    ],
                }
            )
            st.dataframe(col_desc)

        if st.button("📈  Estadísticas descriptivas"):
            st.dataframe(df_unificado.describe(include="all").T)

        if st.button("👀 Mostrar Primeras filas"):
            st.dataframe(df_unificado.head(10))

    # =========================================================
    # TAB 2: DISTRIBUCIONES BÁSICAS
    # =========================================================
    with tab2:
        st.subheader("🚪 Distribuciones principales")
        col1, col2 = st.columns(2)

        # --- Distribución de vía de ingreso ---
        with col1:
            st.markdown(
                '<div class="titulo-panel">Distribución de la vía de ingreso</div>',
                unsafe_allow_html=True,
            )

            if "Via_Ingreso_Desc" in df_unificado.columns:
                frecuencia_via = (
                    df_unificado["Via_Ingreso_Desc"]
                    .value_counts()
                    .rename_axis("Via_Ingreso_Desc")
                    .reset_index(name="Frecuencia")
                )
                fig_via = px.pie(
                    frecuencia_via,
                    names="Via_Ingreso_Desc",
                    values="Frecuencia",
                    color_discrete_sequence=px.colors.qualitative.Set1,
                )
                fig_via.update_traces(
                    textfont_size=13,
                    pull=[0.02] * len(frecuencia_via),
                    hoverinfo="label+percent+value",
                )
                fig_via.update_layout(
                    font=dict(size=12, color="#333"),
                    margin=dict(l=40, r=40, t=60, b=40),
                    showlegend=True,
                )

                with st.container():
                    # st.markdown('<div class="grafico-marco">', unsafe_allow_html=True)
                    st.plotly_chart(fig_via, use_container_width=True)
                    # st.markdown("</div>", unsafe_allow_html=True)
            else:
                st.warning("⚠️ No existe la columna 'Via_Ingreso_Desc'.")

        # --- Distribución por estado de salida ---
        with col2:
            st.markdown(
                '<div class="titulo-panel">🚑 Estado de salida</div>',
                unsafe_allow_html=True,
            )

            if "Estado_Salida_Desc" in df_unificado.columns:
                estado_counts = (
                    df_unificado["Estado_Salida_Desc"]
                    .value_counts()
                    .rename_axis("Estado_Salida")
                    .reset_index(name="Frecuencia")
                )
                fig_estado = px.pie(
                    estado_counts,
                    names="Estado_Salida",
                    values="Frecuencia",
                    color_discrete_sequence=px.colors.qualitative.Set3,
                )
                fig_estado.update_traces(
                    textfont_size=13,
                    pull=[0.02] * len(frecuencia_via),
                    hoverinfo="label+percent+value",
                )
                fig_estado.update_layout(
                    font=dict(size=12, color="#333"),
                    margin=dict(l=40, r=40, t=60, b=40),
                    showlegend=True,
                )

                with st.container():
                    # st.markdown('<div class="grafico-marco">', unsafe_allow_html=True)
                    st.plotly_chart(fig_estado, use_container_width=True)
                    # st.markdown("</div>", unsafe_allow_html=True)

        # --- Separador ---
        st.markdown('<hr class="separador">', unsafe_allow_html=True)

        # --- Fila 2: Sexo y Edad ---
        col3, col4 = st.columns(2)

        with col3:
            st.markdown(
                '<div class="titulo-panel">🧍 Distribución por sexo</div>',
                unsafe_allow_html=True,
            )

            if "SEXO" in df_unificado.columns:
                df_sexo = df_unificado["SEXO"].replace(
                    {"M": "Masculino", "F": "Femenino"}
                )
                sexo_counts = (
                    df_sexo.value_counts()
                    .rename_axis("Sexo")
                    .reset_index(name="Frecuencia")
                )
                fig_sexo_pie = px.pie(
                    sexo_counts,
                    names="Sexo",
                    values="Frecuencia",
                    color="Sexo",
                )
                fig_sexo_pie.update_traces(
                    textfont_size=13,
                    pull=[0.02] * len(frecuencia_via),
                    hoverinfo="label+percent+value",
                )
                fig_sexo_pie.update_layout(
                    font=dict(size=12, color="#333"),
                    margin=dict(l=40, r=40, t=60, b=40),
                    showlegend=True,
                )

                # st.markdown('<div class="grafico-marco">', unsafe_allow_html=True)
                st.plotly_chart(fig_sexo_pie, use_container_width=True)
                # st.markdown("</div>", unsafe_allow_html=True)

        with col4:
            st.markdown(
                '<div class="titulo-panel">📊 Histograma de edades</div>',
                unsafe_allow_html=True,
            )

            if "EDAD_ANIOS" in df_unificado.columns:
                edades = df_unificado["EDAD_ANIOS"]
                edades = edades[(edades >= 0) & (edades <= 120)].dropna()
                if len(edades) > 0:
                    num_clases = int(1 + 3.3 * np.log10(len(edades)))
                    fig_hist = px.histogram(
                        edades,
                        x=edades,
                        nbins=num_clases,
                        color_discrete_sequence=["#005f73"],
                        marginal="box",
                        text_auto=True,
                    )
                    fig_hist.update_layout(
                        title=dict(
                            text="Distribución de edades de los pacientes", x=0.5
                        ),
                        xaxis_title="Edad (años)",
                        yaxis_title="Frecuencia",
                        bargap=0.05,
                        font=dict(size=12),
                        margin=dict(l=60, r=40, t=80, b=60),
                        shapes=[
                            dict(
                                type="rect",
                                xref="paper",
                                yref="paper",
                                x0=0,
                                y0=0,
                                x1=1,
                                y1=1,
                                line=dict(color="rgba(90,90,90,0.5)", width=1.5),
                            )
                        ],
                    )

                    # st.markdown('<div class="grafico-marco">', unsafe_allow_html=True)
                    st.plotly_chart(fig_hist, use_container_width=True)
                    # st.markdown("</div>", unsafe_allow_html=True)

        # --- Separador ---
        st.markdown('<hr class="separador">', unsafe_allow_html=True)

        # --- Fila 3: Duración de hospitalización ---
        col5, _ = st.columns(2)
        with col5:
            st.markdown(
                '<div class="titulo-panel">⏱️ Duración de hospitalización (≤ 60 días)</div>',
                unsafe_allow_html=True,
            )

            if "Duracion_Dias" in df_unificado.columns:
                duracion = df_unificado["Duracion_Dias"].dropna()
                if len(duracion) > 0:
                    duracion_filtrada = duracion[duracion <= 60]
                    rango = duracion_filtrada.max() - duracion_filtrada.min()
                    num_clases = int(1 + 3.3 * np.log10(len(duracion_filtrada)))
                    ancho_clases = rango / num_clases
                    fig_duracion = px.histogram(
                        duracion_filtrada,
                        x=duracion_filtrada,
                        nbins=num_clases,
                        color_discrete_sequence=["#A8E6A3"],
                        marginal="box",
                        text_auto=True,
                    )
                    fig_duracion.update_layout(
                        bargap=0.05,
                        template="plotly_white",
                        xaxis_title="Duración (días)",
                        yaxis_title="Frecuencia",
                    )
                    # st.markdown('<div class="grafico-marco">', unsafe_allow_html=True)
                    st.plotly_chart(fig_duracion, use_container_width=True)
                    # st.markdown("</div>", unsafe_allow_html=True)

    # =========================================================
    # TAB 3: DIAGNÓSTICOS Y CAUSAS EXTERNAS
    # =========================================================
    with tab3:
        st.subheader("🧠 Top 10 diagnósticos principales")
        if "Diagnostico_Principal_Desc" in df_unificado.columns:
            top_diagnosticos = (
                df_unificado["Diagnostico_Principal_Desc"]
                .value_counts()
                .head(10)
                .rename_axis("Diagnóstico")
                .reset_index(name="Frecuencia")
            )
            fig_dx_heat = px.imshow(
                top_diagnosticos[["Frecuencia"]],
                labels=dict(x="Frecuencia", y="Diagnóstico", color="Frecuencia"),
                y=top_diagnosticos["Diagnóstico"],
                x=["Frecuencia"],
                text_auto=True,
                color_continuous_scale="Oranges",
                title="Top 10 diagnósticos principales",
            )
            fig_dx_heat.update_xaxes(showticklabels=False)
            # st.markdown('<div class="grafico-marco">', unsafe_allow_html=True)
            st.plotly_chart(fig_dx_heat, use_container_width=True)
            # st.markdown("</div>", unsafe_allow_html=True)

            st.subheader("⚠️ Distribución por causa externa")
            if "Causa_Externa_Desc" in df_unificado.columns:
                causa_counts = (
                    df_unificado["Causa_Externa_Desc"]
                    .value_counts()
                    .rename_axis("Causa_Externa_Desc")
                    .reset_index(name="Frecuencia")
                    .sort_values("Frecuencia", ascending=True)
                )
                fig_causa = px.bar(
                    causa_counts,
                    x="Frecuencia",
                    y="Causa_Externa_Desc",
                    orientation="h",
                    text="Frecuencia",
                    title="Distribución de causas externas",
                    color="Causa_Externa_Desc",
                    color_discrete_sequence=px.colors.qualitative.Pastel,
                )
                fig_causa.update_layout(
                    yaxis_title="Causa Externa",
                    yaxis=dict(autorange="reversed"),
                    showlegend=False,
                )
                # st.markdown('<div class="grafico-marco">', unsafe_allow_html=True)
                st.plotly_chart(fig_causa, use_container_width=True)
                # st.markdown("</div>", unsafe_allow_html=True)


if __name__ == "__main__":
    main()
