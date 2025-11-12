import streamlit as st
import plotly.express as px
from utils_sidebar import mostrar_sidebar
from episcopeenvigado.config import PROCESSED_DATA_DIR
from episcopeenvigado.dataset import cargar_datasets_locales
import networkx as nx
from pyvis.network import Network
import matplotlib.cm as cm
import matplotlib.colors as mcolors


def crear_grafo(df, dx_central):
    G = nx.Graph()
    norm = mcolors.Normalize(vmin=df["OR"].min(), vmax=df["OR"].max())
    cmap = cm.get_cmap("YlOrRd")

    for _, row in df.iterrows():
        for dx in [row["Dx1"], row["Dx2"]]:
            if dx not in G.nodes:
                G.add_node(dx, color="#87CEEB", size=20)
        G.add_edge(
            row["Dx1"], row["Dx2"], color=mcolors.to_hex(cmap(norm(row["OR"]))), width=3
        )
    return G


def visualizar_red(df, dx_sel):
    G = crear_grafo(df, dx_sel)
    net = Network(height="700px", width="100%", bgcolor="#fff", font_color="black")
    net.from_nx(G)
    net.repulsion(node_distance=250, spring_length=180)
    st.components.v1.html(net.generate_html(), height=750)


def main():
    mostrar_sidebar()
    st.title("🤖 Modelo Predictivo — Coocurrencias Diagnósticas")

    datasets = cargar_datasets_locales(PROCESSED_DATA_DIR)
    if "analisis_coocurrencias_significativas" not in datasets:
        st.warning(
            "⚠️ No se encontró el archivo 'analisis_coocurrencias_significativas.xlsx'."
        )
        st.stop()

    df_cooc = datasets["analisis_coocurrencias_significativas"]
    desc_map = {
        **dict(zip(df_cooc["Dx1"], df_cooc["Desc1"])),
        **dict(zip(df_cooc["Dx2"], df_cooc["Desc2"])),
    }

    seleccion = st.selectbox("Selecciona diagnóstico:", options=sorted(desc_map.keys()))
    df_filtrado = df_cooc[(df_cooc["Dx1"] == seleccion) | (df_cooc["Dx2"] == seleccion)]
    st.dataframe(df_filtrado)
    if st.button("🌐 Visualizar red"):
        visualizar_red(df_filtrado, seleccion)


if __name__ == "__main__":
    main()
