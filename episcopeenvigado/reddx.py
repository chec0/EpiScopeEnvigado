import pandas as pd
import networkx as nx
from pyvis.network import Network
import logging
from pathlib import Path
import matplotlib.cm as cm
import matplotlib.colors as mcolors

# ============================================================
# CONFIGURACIÓN GENERAL
# ============================================================
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

ruta_datos = Path(
    r"C:\Users\ZENBOOK\OneDrive - MUNICIPIO DE ENVIGADO"
    r"\Documentos\Personales\Analisis de datos avanzado\RIPS"
    r"\analisis_coocurrencias_significativas.xlsx"
)
ruta_salida = ruta_datos.parent

# ============================================================
# FUNCIONES
# ============================================================

def cargar_datos(ruta_excel: str) -> pd.DataFrame:
    df = pd.read_excel(ruta_excel)
    logging.info(f"Archivo cargado con {len(df)} filas.")
    return df

def filtrar_top_or(df: pd.DataFrame, dx: str, top_n: int = 20, cooc_min: int = 10) -> pd.DataFrame:
    """Filtra asociaciones de un diagnóstico específico y devuelve el Top N por OR,
       asegurando un mínimo de coocurrencias."""
    df_filtrado = df[(df["Dx1"] == dx) | (df["Dx2"] == dx)]
    df_filtrado = df_filtrado[df_filtrado["count_coocurrence"] >= cooc_min]
    df_filtrado = df_filtrado.sort_values(by="OR", ascending=False).head(top_n)
    logging.info(f"Top {top_n} asociaciones para {dx} seleccionadas por OR (cooc≥{cooc_min}).")
    return df_filtrado

def crear_grafo(df: pd.DataFrame, dx_central: str) -> nx.Graph:
    """Crea el grafo con color según OR y grosor según coocurrencia."""
    G = nx.Graph()

    # Normalizar OR para mapear a un gradiente de color
    norm = mcolors.Normalize(vmin=df["OR"].min(), vmax=df["OR"].max())
    cmap = cm.get_cmap("YlOrRd")

    for _, row in df.iterrows():
        # Nodos
        if row["Dx1"] == dx_central:
            G.add_node(row["Dx1"], title=row.get("Desc1", ""),
                       color="red", size=40, shape="circle")
        else:
            G.add_node(row["Dx1"], title=row.get("Desc1", ""))

        if row["Dx2"] == dx_central:
            G.add_node(row["Dx2"], title=row.get("Desc2", ""),
                       color="red", size=40, shape="circle")
        else:
            G.add_node(row["Dx2"], title=row.get("Desc2", ""))

        # Color según OR
        rgba = cmap(norm(row["OR"]))
        hex_color = mcolors.to_hex(rgba)

        # Grosor según frecuencia de coocurrencia
        edge_width = min(max(row["count_coocurrence"] / 5, 4), 8)

        # Arista
        G.add_edge(
            row["Dx1"], row["Dx2"],
            color=hex_color,
            width=edge_width,
            title=f"Coocurrencias: {row['count_coocurrence']}, OR={row['OR']:.2f}"
        )

    logging.info(f"Grafo creado con {G.number_of_nodes()} nodos y {G.number_of_edges()} enlaces.")
    return G

def visualizar_red(G: nx.Graph, nombre_salida: str):
    net = Network(height="800px", width="100%", bgcolor="#ffffff", font_color="black", notebook=False)
    net.from_nx(G)
    net.repulsion(node_distance=300, central_gravity=0.05,
                  spring_length=250, spring_strength=0.02, damping=0.08)
    ruta_html = ruta_salida / nombre_salida
    net.save_graph(str(ruta_html))
    logging.info(f"Red exportada en: {ruta_html}")

# ============================================================
# EJECUCIÓN PRINCIPAL
# ============================================================

def main():
    df = cargar_datos(str(ruta_datos))

    # --- Filtrar solo Top 20 asociaciones con I10 por OR ---
    df_i10 = filtrar_top_or(df, "N18", top_n=20, cooc_min=10)

    if df_i10.empty:
        logging.warning("No se encontraron asociaciones fuertes para I10.")
        return

    # --- Crear y visualizar red ---
    G_i10 = crear_grafo(df_i10, "N18")
    visualizar_red(G_i10, "red_N18_top20_OR.html")

    logging.info("✅ Red de N18 (Top 20 por OR) generada con éxito.")

if __name__ == "__main__":
    main()