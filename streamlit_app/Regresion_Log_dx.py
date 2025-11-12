import streamlit as st  
import pandas as pd
import numpy as np
import statsmodels.api as sm
import plotly.express as px
from pathlib import Path
from episcopeenvigado.config import PROCESSED_DATA_DIR
from episcopeenvigado.dataset import obtener_dataset_completo
import ast
from collections import Counter

# -----------------------------------------------------
# Configuración de página
# -----------------------------------------------------
st.set_page_config(page_title="🔹 Regresión Logística Diagnósticos", layout="wide")
st.title("🔹 Regresión Logística: Probabilidad de Dx2 dado Dx1")
st.markdown("""
Este módulo permite explorar la **probabilidad de que un paciente con un diagnóstico (Dx1)** 
también presente otro diagnóstico (Dx2)**, considerando la edad y el sexo mediante **regresión logística**.
""")

# -----------------------------------------------------
# Cargar dataset base
# -----------------------------------------------------
dataset_path = PROCESSED_DATA_DIR / "consolidado_por_usuario_3dig_enriquecido.xlsx"
if not dataset_path.exists():
    st.error(f"❌ No se encontró el archivo {dataset_path}")
    st.stop()

df = pd.read_excel(dataset_path)
st.success(f"✅ Dataset cargado con {df.shape[0]} pacientes")

# -----------------------------------------------------
# Procesar diagnósticos
# -----------------------------------------------------
df['diagnosticos_3dig'] = df['diagnosticos_3dig'].apply(
    lambda x: ast.literal_eval(x) if pd.notna(x) and x != '[]' else []
)

# -----------------------------------------------------
# Cargar tabla dim_cie10
# -----------------------------------------------------
@st.cache_data
def cargar_cie10():
    episcope_data = obtener_dataset_completo()
    if "dim_cie10" not in episcope_data:
        st.warning("⚠️ No se encontró la tabla 'dim_cie10' en la base de datos.")
        return {}
    cie = episcope_data["dim_cie10"][["cie_3cat", "desc_3cat"]].drop_duplicates()
    return dict(zip(cie["cie_3cat"], cie["desc_3cat"]))

cie_dict = cargar_cie10()

# -----------------------------------------------------
# Selección de diagnósticos
# -----------------------------------------------------
dx_counter = Counter([dx for sublist in df['diagnosticos_3dig'] for dx in sublist if dx])
dx_all = sorted([dx for dx, count in dx_counter.items() if count >= 30])

st.subheader("🔍 Selección de diagnósticos")
dx1_options = [f"{dx} - {cie_dict.get(dx, 'Sin descripción disponible')}" for dx in dx_all]
dx1_display = st.selectbox("Seleccione Dx1", dx1_options)
dx1_selected = dx1_display.split(" - ", 1)[0]

st.info(f"**Dx1 seleccionado:** {dx1_selected} - {cie_dict.get(dx1_selected, 'Sin descripción disponible')}")

# Filtrar pacientes
df_dx1 = df[df['diagnosticos_3dig'].apply(lambda x: dx1_selected in x)].copy()
st.write(f"Pacientes con {dx1_selected}: {len(df_dx1)}")

# -----------------------------------------------------
# Obtener Dx2 válidos
# -----------------------------------------------------
def obtener_dx2_validos(df_dx1, min_count=5):
    dx2_counts = Counter([dx2 for sublist in df_dx1['diagnosticos_3dig'] for dx2 in sublist if dx2 != dx1_selected])
    candidatos = [dx for dx, c in dx2_counts.items() if c >= min_count]
    dx2_validos = [dx for dx in candidatos if len(df_dx1['diagnosticos_3dig'].apply(lambda x: dx in x).unique()) > 1]
    return sorted(dx2_validos), dx2_counts

dx2_options, dx2_counts = obtener_dx2_validos(df_dx1)
dx2_options_display = [
    f"{dx} - {cie_dict.get(dx, 'Sin descripción disponible')} ({dx2_counts.get(dx,0)} casos)"
    for dx in dx2_options
]

dx2_display_selected = st.multiselect("Seleccione uno o más Dx2", dx2_options_display)
dx2_selected = [dx.split(" - ", 1)[0] for dx in dx2_display_selected]

if not dx2_selected:
    st.stop()

st.markdown("**Dx2 seleccionados:**")
for dx2 in dx2_selected:
    st.write(f"- {dx2} - {cie_dict.get(dx2, 'Sin descripción disponible')}")

st.divider()

# -----------------------------------------------------
# Distribuciones (Plotly)
# -----------------------------------------------------
st.subheader(f"📊 Distribución de edad y sexo para pacientes con {dx1_selected}")

# Distribución por sexo
sexo_counts = df_dx1['SEXO'].value_counts().reset_index()
sexo_counts.columns = ['SEXO', 'count']

fig_sexo = px.bar(
    sexo_counts,
    x='SEXO',
    y='count',
    title='Distribución por sexo',
    text='count',
    color='SEXO',
    color_discrete_sequence=px.colors.qualitative.Set2
)
fig_sexo.update_traces(textposition='outside')
fig_sexo.update_layout(showlegend=False, template='simple_white')
st.plotly_chart(fig_sexo, use_container_width=True)

# Histograma de edad
fig_edad = px.histogram(
    df_dx1,
    x='EDAD_ANIOS',
    nbins=30,
    title='Distribución de edad',
    color_discrete_sequence=['#4C78A8']
)
fig_edad.update_layout(
    xaxis_title='Edad',
    yaxis_title='Frecuencia',
    bargap=0.05,
    template='simple_white'
)
st.plotly_chart(fig_edad, use_container_width=True)

# -----------------------------------------------------
# Modelado
# -----------------------------------------------------
st.subheader("📈 Regresión logística: Probabilidad de Dx2 dado Dx1")
st.markdown("""
La regresión logística estima cómo cambia la **probabilidad de presentar Dx2** 
según la **edad** y el **sexo**, entre pacientes que ya tienen Dx1.
""")

for dx2 in dx2_selected:
    st.divider()
    st.markdown(f"### 📌 Modelo para **{dx2} - {cie_dict.get(dx2, 'Sin descripción disponible')}**")

    df_dx1['Dx2_presente'] = df_dx1['diagnosticos_3dig'].apply(lambda x: 1 if dx2 in x else 0)
    df_model = df_dx1.dropna(subset=['EDAD_ANIOS', 'Dx2_presente']).copy()

    X = pd.concat([
        df_model[['EDAD_ANIOS']].astype(float),
        pd.get_dummies(df_model['SEXO'], drop_first=True).astype(float)
    ], axis=1)

    X = sm.add_constant(X, has_constant='add').astype(float)
    y = df_model['Dx2_presente'].astype(float)

    if X.isnull().any().any() or y.isnull().any():
        st.warning(f"⚠️ {dx2}: Se encontraron valores nulos en las variables. Filtrando filas incompletas...")
        valid_idx = (~X.isnull().any(axis=1)) & (~y.isnull())
        X, y = X[valid_idx], y[valid_idx]

    if X.select_dtypes(exclude=[np.number]).shape[1] > 0:
        st.error(f"⚠️ {dx2}: Existen columnas no numéricas en X. Revise los datos.")
        continue

    try:
        model = sm.Logit(y, X).fit(disp=False)

        with st.expander("📄 Ver resumen estadístico completo"):
            st.text(model.summary())

        OR = np.exp(model.params).round(3)
        CI = np.exp(model.conf_int()).round(3)
        p_values = model.pvalues.round(3)

        df_or = pd.DataFrame({
            "Variable": OR.index,
            "OR": OR.values,
            "IC95_Lower": CI[0].values,
            "IC95_Upper": CI[1].values,
            "p-value": p_values.values
        })

        st.markdown("#### 🧩 Interpretación general")
        st.markdown("""
        - **OR > 1:** la variable aumenta la probabilidad de Dx2.  
        - **OR < 1:** la variable disminuye la probabilidad.  
        - **p < 0.05:** asociación estadísticamente significativa.
        """)

        st.dataframe(
            df_or.style.applymap(lambda v: "background-color: #b3ffb3" if v < 0.05 else "", subset=["p-value"])
        )

        # -----------------------------------------------------
        # 🔹 Predicción interactiva
        # -----------------------------------------------------
        st.markdown(f"#### 🧮 Predicción interactiva para {dx2}")

        min_age = int(max(0, df_model['EDAD_ANIOS'].min()))
        max_age = int(min(120, df_model['EDAD_ANIOS'].max()))
        edad_input = st.slider(
            "Edad del paciente",
            min_value=min_age,
            max_value=max_age,
            value=int(df_model['EDAD_ANIOS'].median()),
            step=1,
            key=f"edad_{dx2}"
        )


        sexo_values = sorted(df_model['SEXO'].dropna().unique().astype(str))
        sexo_input = st.selectbox("Sexo del paciente", sexo_values, key=f"sexo_{dx2}")

        input_df = pd.DataFrame({"EDAD_ANIOS": [edad_input], "SEXO": [sexo_input]})
        input_df_sexo = pd.get_dummies(input_df['SEXO'], drop_first=True).astype(float)
        input_df = pd.concat([input_df[['EDAD_ANIOS']].astype(float), input_df_sexo], axis=1)

        for col in X.columns:
            if col not in input_df.columns:
                input_df[col] = 0
        input_df = input_df[X.columns]

        pred_prob = model.predict(input_df)[0]

        params = model.params.values
        cov_matrix = model.cov_params().values
        x_vector = input_df.values[0]
        var_lp = np.dot(x_vector.T, np.dot(cov_matrix, x_vector))
        se_lp = np.sqrt(var_lp)
        lp = np.dot(x_vector, params)
        ci_low = 1 / (1 + np.exp(-(lp - 1.96 * se_lp)))
        ci_high = 1 / (1 + np.exp(-(lp + 1.96 * se_lp)))

        st.markdown(f"""
        **👉 Probabilidad estimada de tener `{dx2}` dado `{dx1_selected}`**  
        Edad: **{edad_input} años** · Sexo: **{sexo_input}**

        🔹 Probabilidad: **{pred_prob:.3f} ({pred_prob*100:.1f}%)**  
        🔹 Intervalo de confianza 95%: **{ci_low*100:.1f}% – {ci_high*100:.1f}%**
        """)

        interpretacion = (
            "muy baja" if pred_prob < 0.05 else
            "baja" if pred_prob < 0.15 else
            "moderada" if pred_prob < 0.35 else
            "alta" if pred_prob < 0.65 else
            "muy alta"
        )

        st.info(
            f"🩺 Interpretación: Según el modelo, la probabilidad de presentar "
            f"{cie_dict.get(dx2, dx2)} dado que el paciente tiene "
            f"{cie_dict.get(dx1_selected, dx1_selected)} es **{interpretacion}**."
        )

        # -----------------------------------------------------
        # Distribución de probabilidades (Plotly)
        # -----------------------------------------------------
        df_model['prob'] = model.predict(X)

        fig_prob = px.histogram(
            df_model,
            x='prob',
            nbins=20,
            title=f"Distribución de probabilidad para {dx2}",
            color_discrete_sequence=['teal'],
            opacity=0.7
        )
        fig_prob.add_vline(
            x=pred_prob,
            line_dash="dash",
            line_color="red",
            annotation_text=f"Tu caso ({pred_prob*100:.1f}%)",
            annotation_position="top right"
        )
        fig_prob.update_layout(
            xaxis_title="Probabilidad estimada",
            yaxis_title="Cantidad de pacientes",
            template="simple_white"
        )
        st.plotly_chart(fig_prob, use_container_width=True)

    except Exception as e:
        st.error(f"Error al ajustar modelo para {dx2}: {e}")
