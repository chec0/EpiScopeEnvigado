import streamlit as st
import plotly.express as px
from utils_sidebar import mostrar_sidebar
from episcopeenvigado.config import PROCESSED_DATA_DIR
from episcopeenvigado.dataset import cargar_datasets_locales
import networkx as nx
from pyvis.network import Network
import matplotlib.cm as cm
import matplotlib.colors as mcolors

# ======================================
# 🔧 FUNCIONES AUXILIARES
# ======================================
def crear_grafo(df, dx_central):
    """Crea un grafo coloreado según OR y tamaño de arista según coocurrencia."""
    G = nx.Graph()

    vmin, vmax = df["OR"].min(), df["OR"].max()
    if vmin == vmax:
        vmax = vmin + 1

    norm = mcolors.Normalize(vmin=vmin, vmax=vmax)
    cmap = cm.get_cmap("YlOrRd")

    for _, row in df.iterrows():
        for dx, desc in [
            (row["Dx1"], row.get("Desc1", "")),
            (row["Dx2"], row.get("Desc2", "")),
        ]:
            if dx not in G.nodes:
                G.add_node(
                    dx,
                    title=desc,
                    color="red" if dx == dx_central else "#87CEEB",
                    size=30 if dx == dx_central else 20,
                )

        rgba = cmap(norm(row["OR"]))
        hex_color = mcolors.to_hex(rgba)
        width = min(max(row.get("count_coocurrence", 5) / 5, 2), 8)

        G.add_edge(
            row["Dx1"],
            row["Dx2"],
            color=hex_color,
            width=width,
            title=f"Coocurrencias: {row.get('count_coocurrence', 'N/A')} | OR={row['OR']:.2f}",
        )

    return G


def visualizar_red(df, dx_sel):
    """Visualiza el grafo de coocurrencias en Streamlit."""
    G = crear_grafo(df, dx_sel)
    net = Network(height="700px", width="100%", bgcolor="#fff", font_color="black")
    net.from_nx(G)
    net.repulsion(node_distance=280, spring_length=180, damping=0.8)

    html_str = net.generate_html()
    st.components.v1.html(html_str, height=750, scrolling=True)


# ======================================
# 🧠 PÁGINA PRINCIPAL
# ======================================
def main():
    st.set_page_config(
        page_title="Análisis Coocurrencias Diagnósticas",
        page_icon="🌐",
        layout="wide",
    )

    mostrar_sidebar()
    st.title("🌐 Análisis Coocurrencias Diagnósticas")
    st.markdown("### Análisis de Coocurrencias Significativas entre Diagnósticos")

    # Cargar datasets locales
    datasets = cargar_datasets_locales(PROCESSED_DATA_DIR)
    if "analisis_coocurrencias_significativas" not in datasets:
        st.warning("⚠️ No se encontró el archivo 'analisis_coocurrencias_significativas.xlsx'.")
        st.stop()

    df_cooc = datasets["analisis_coocurrencias_significativas"]

    # Crear mapa de descripciones
    desc_map = {
        **dict(zip(df_cooc["Dx1"], df_cooc["Desc1"])),
        **dict(zip(df_cooc["Dx2"], df_cooc["Desc2"])),
    }

    # ======================================
    # 1️⃣ Selección de diagnóstico
    # ======================================
    opciones = [
        f"{dx} — {desc_map.get(dx, 'Sin descripción')}"
        for dx in sorted(set(df_cooc["Dx1"]) | set(df_cooc["Dx2"]))
    ]
    seleccion = st.selectbox("Selecciona diagnóstico:", options=opciones)
    dx_sel = seleccion.split(" — ")[0]

    # Filtrar el DataFrame
    df_filtrado = df_cooc[
        (df_cooc["Dx1"] == dx_sel) | (df_cooc["Dx2"] == dx_sel)
    ].sort_values("OR", ascending=False)

    if df_filtrado.empty:
        st.info("No hay coocurrencias significativas para este diagnóstico.")
        st.stop()

    st.markdown(
        f"### {len(df_filtrado)} asociaciones con **{dx_sel} — {desc_map.get(dx_sel, 'Sin descripción')}**"
    )
    st.dataframe(df_filtrado)

    # ======================================
    # 2️⃣ Gráfico descriptivo
    # ======================================
    fig = px.scatter(
        df_filtrado,
        x="p_value_adj",
        y="OR",
        color="OR",
        size="count_coocurrence",
        hover_data=["Dx1", "Dx2", "Desc1", "Desc2"],
        title=f"Relación entre {dx_sel} y otros diagnósticos",
        color_continuous_scale="YlOrRd",
        template="plotly_white",
    )
    st.plotly_chart(fig, use_container_width=True)

    # ======================================
    # 3️⃣ Red interactiva
    # ======================================
    st.markdown("#### 🌐 Visualización de red")
    min_cooc = st.slider(
        "Umbral mínimo de coocurrencias para incluir en la red",
        min_value=1,
        max_value=20,
        value=5,
    )

    df_top = df_filtrado[df_filtrado["count_coocurrence"] >= min_cooc]
    if df_top.empty:
        df_top = df_filtrado.head(20)

    if st.button("Generar red interactiva"):
        visualizar_red(df_top, dx_sel)


if __name__ == "__main__":
    main()
