"""
Análisis de coocurrencias de diagnósticos CIE-10 en datos RIPS.

Este script realiza:
1. Lectura y limpieza de los archivos RIPS y CIE-10.
2. Consolidación de diagnósticos por usuario (4 y 3 dígitos).
3. Cálculo de frecuencias de diagnósticos.
4. Análisis de coocurrencias (Chi-cuadrado, OR, IC95).
5. Exportación de resultados significativos.

"""

import itertools
import logging
import time
from pathlib import Path
from typing import Any, Dict, List, Tuple

import numpy as np
import pandas as pd
from scipy.sparse import triu
from scipy.stats import chi2_contingency, norm
from sklearn.preprocessing import MultiLabelBinarizer
from statsmodels.stats.multitest import multipletests
from tqdm import tqdm

# ============================================================
# CONFIGURACIÓN
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

ruta_rips = Path(
    r"C:\Users\ZENBOOK\OneDrive - MUNICIPIO DE ENVIGADO"
    r"\Documentos\Personales\Analisis de datos avanzado\RIPS"
    r"\RIPS_20232024_HOSP.xlsx"
)
ruta_cie = Path(
    r"C:\Users\ZENBOOK\OneDrive - MUNICIPIO DE ENVIGADO"
    r"\Documentos\Personales\Analisis de datos avanzado\RIPS"
    r"\Tabla-CIE-10-2018_08022021 sin restricciones.xlsx"
)
ruta_salida = Path(
    r"C:\Users\ZENBOOK\OneDrive - MUNICIPIO DE ENVIGADO"
    r"\Documentos\Personales\Analisis de datos avanzado\RIPS"
)

dx_cols: List[str] = [
    "DIAGNOSTICO INGRESO", "Cod_Dx_Ppal_Egreso", "DIAG EGRESO REL 1",
    "DIAG EGRESO REL 2", "DIAG EGRESO REL 3", "DIAG COMPLICACION",
    "DIAG MUERTE"
]

# ============================================================
# FUNCIONES
# ============================================================

def leer_datos() -> Tuple[pd.DataFrame, Dict[str, str], Dict[str, str]]:
    """
    Lee los archivos RIPS y CIE-10 desde las rutas configuradas y construye diccionarios de descripciones.

    Returns:
        tuple:
            - DataFrame con los datos RIPS.
            - Diccionario de códigos CIE-10 a 3 caracteres y su descripción.
            - Diccionario de códigos CIE-10 a 4 caracteres y su descripción.
    """
    logging.info("Leyendo archivos...")
    rips = pd.read_excel(ruta_rips)
    cie = pd.read_excel(ruta_cie, sheet_name="Final")

    cie_dict_3 = (
        cie[["Código de la CIE-10 tres caracteres", "Descripcion  de codigos a tres caracteres"]]
        .dropna()
        .drop_duplicates(subset="Código de la CIE-10 tres caracteres")
        .set_index("Código de la CIE-10 tres caracteres")["Descripcion  de codigos a tres caracteres"]
        .to_dict()
    )

    cie_dict_4 = (
        cie[["Código de la CIE-10 cuatro caracteres", "Descripcion  de códigos a cuatro caracteres"]]
        .dropna()
        .drop_duplicates(subset="Código de la CIE-10 cuatro caracteres")
        .set_index("Código de la CIE-10 cuatro caracteres")["Descripcion  de códigos a cuatro caracteres"]
        .to_dict()
    )

    return rips, cie_dict_3, cie_dict_4


def consolidar_diagnosticos(rips: pd.DataFrame) -> pd.DataFrame:
    """
    Consolida todos los diagnósticos por usuario en una lista única a 4 dígitos.

    Args:
        rips: DataFrame con los datos RIPS.

    Returns:
        DataFrame con los diagnósticos consolidados por usuario (ID).
    """
    rips[dx_cols] = rips[dx_cols].apply(
        lambda col: col.map(lambda x: str(x).strip().upper().replace(".", "") if pd.notna(x) else None)
    )

    consolidado_4dig = rips.groupby("ID")[dx_cols].agg(lambda x: list(x.dropna()))
    consolidado_4dig["dx_list_4dig"] = consolidado_4dig.apply(
        lambda row: list(set(itertools.chain.from_iterable(row))), axis=1
    )

    return consolidado_4dig


def preparar_3dig(rips: pd.DataFrame) -> pd.DataFrame:
    """
    Convierte los diagnósticos a tres caracteres y consolida por usuario.

    Args:
        rips: DataFrame con los datos RIPS originales.

    Returns:
        DataFrame con listas de diagnósticos a 3 caracteres por usuario.
    """
    rips_3dig = rips[dx_cols].applymap(lambda x: x[:3] if x else None)
    consolidado_3dig = rips_3dig.groupby(rips["ID"]).agg(lambda x: list(x.dropna()))
    consolidado_3dig["dx_list_3dig"] = consolidado_3dig.apply(
        lambda row: list(set(itertools.chain.from_iterable(row))), axis=1
    )
    consolidado_3dig["dx_list_3dig"] = consolidado_3dig["dx_list_3dig"].apply(
        lambda l: [dx for dx in l if dx and dx[0] not in ["Z", "R"]]
    )

    return consolidado_3dig


def crear_matriz(consolidado_3dig: pd.DataFrame, frecuencia_minima: int = 30) -> Tuple[Any, List[str]]:
    """
    Crea una matriz binaria de usuarios x diagnósticos (3 dígitos), filtrando por frecuencia mínima.

    Args:
        consolidado_3dig: DataFrame con la columna 'dx_list_3dig'.
        frecuencia_minima: Frecuencia mínima requerida para incluir un diagnóstico.

    Returns:
        tuple:
            - Matriz dispersa binaria (usuarios x diagnósticos).
            - Lista de diagnósticos incluidos tras el filtrado.
    """
    diagnosticos_unicos = sorted(
        set(itertools.chain.from_iterable(consolidado_3dig["dx_list_3dig"]))
    )
    mlb = MultiLabelBinarizer(classes=diagnosticos_unicos, sparse_output=True)
    matriz = mlb.fit_transform(
        tqdm(consolidado_3dig["dx_list_3dig"], desc="Creando matriz binaria")
    )

    frecuencias = matriz.sum(axis=0).A1
    indices_validos = np.where(frecuencias >= frecuencia_minima)[0]
    matriz_filtrada = matriz[:, indices_validos]
    diagnosticos_filtrados = [diagnosticos_unicos[i] for i in indices_validos]

    logging.info(
        f"Diagnósticos filtrados: {len(diagnosticos_filtrados)} "
        f"(umbral: ≥ {frecuencia_minima} usuarios)"
    )

    return matriz_filtrada, diagnosticos_filtrados


def analizar(matriz: Any, diagnosticos_unicos: List[str], cie_dict_3: Dict[str, str]) -> pd.DataFrame:
    """
    Realiza análisis de coocurrencias entre diagnósticos mediante chi-cuadrado y OR.

    Args:
        matriz: Matriz binaria dispersa (usuarios x diagnósticos).
        diagnosticos_unicos: Lista de diagnósticos (columnas de la matriz).
        cie_dict_3: Diccionario con descripciones CIE-10 a 3 dígitos.

    Returns:
        DataFrame con las asociaciones entre diagnósticos (Chi², OR, IC95, p-values).
    """
    n = matriz.shape[0]
    col_sums = np.array(matriz.sum(axis=0)).ravel()
    cooc = triu(matriz.T @ matriz, k=1).tocoo()
    resultados, p_values = [], []

    for i, j, a in tqdm(zip(cooc.row, cooc.col, cooc.data),
                        total=len(cooc.data),
                        desc="Analizando coocurrencias"):
        if a < 5:
            continue

        b = col_sums[i] - a
        c = col_sums[j] - a
        d = n - (a + b + c)
        tabla = np.array([[a, b], [c, d]], dtype=float) + 0.5
        chi2, p, _, _ = chi2_contingency(tabla, correction=False)
        p_values.append(p)

        or_value = (tabla[0, 0] * tabla[1, 1]) / (tabla[0, 1] * tabla[1, 0])
        se_log_or = np.sqrt(1 / tabla[0, 0] + 1 / tabla[0, 1] + 1 / tabla[1, 0] + 1 / tabla[1, 1])
        z = norm.ppf(0.975)
        log_or = np.log(or_value)
        ci_low, ci_high = np.exp([log_or - z * se_log_or, log_or + z * se_log_or])

        resultados.append({
            "Dx1": diagnosticos_unicos[i],
            "Desc1": cie_dict_3.get(diagnosticos_unicos[i], "No encontrado"),
            "Dx2": diagnosticos_unicos[j],
            "Desc2": cie_dict_3.get(diagnosticos_unicos[j], "No encontrado"),
            "Chi2": round(chi2, 3),
            "p_value": p,
            "OR": round(or_value, 3),
            "IC95_Lower": round(ci_low, 3),
            "IC95_Upper": round(ci_high, 3),
            "count_dx1": int(col_sums[i]),
            "count_dx2": int(col_sums[j]),
            "count_coocurrence": int(a),
            "P_conjunta": round(a / n, 5),
            "P_B_dado_A": round(a / col_sums[i], 5) if col_sums[i] > 0 else 0,
            "P_A_dado_B": round(a / col_sums[j], 5) if col_sums[j] > 0 else 0
        })

    if resultados:
        _, p_adj, _, _ = multipletests(p_values, method="fdr_bh")
        for res, p_corr in zip(resultados, p_adj):
            res["p_value_adj"] = round(p_corr, 5)

    return pd.DataFrame(resultados)

# ============================================================
# EJECUCIÓN PRINCIPAL
# ============================================================

if __name__ == "__main__":
    start_time = time.time()

    rips, cie_dict_3, cie_dict_4 = leer_datos()

    # --- Consolidado 4 dígitos ---
    consolidado_4dig = consolidar_diagnosticos(rips)
    consolidado_export = pd.DataFrame({
        "ID": consolidado_4dig.index,
        "diagnosticos_4dig": consolidado_4dig["dx_list_4dig"]
    })
    ruta_consolidado_4dig = ruta_salida / "consolidado_por_usuario_4dig.xlsx"
    consolidado_export.to_excel(ruta_consolidado_4dig, index=False)
    logging.info(f"Consolidado 4 dígitos exportado en: {ruta_consolidado_4dig}")

    # --- Frecuencias CIE-4 ---
    logging.info("Calculando frecuencias de diagnósticos CIE-4...")
    dx_expandidos = consolidado_4dig["dx_list_4dig"].explode().dropna()
    freq_total = (
        dx_expandidos.value_counts()
        .rename_axis("Diagnostico")
        .reset_index(name="Frecuencia")
    )
    pacientes_por_dx = (
        consolidado_4dig
        .explode("dx_list_4dig")
        .dropna(subset=["dx_list_4dig"])
        .reset_index()
        .groupby("dx_list_4dig")["ID"]
        .nunique()
        .rename("Pacientes")
        .reset_index()
        .rename(columns={"dx_list_4dig": "Diagnostico"})
    )
    resumen_dx4 = pd.merge(freq_total, pacientes_por_dx, on="Diagnostico", how="left")
    resumen_dx4["Descripcion_4dig"] = resumen_dx4["Diagnostico"].map(cie_dict_4)
    resumen_dx4["Descripcion_3dig"] = resumen_dx4["Diagnostico"].str[:3].map(cie_dict_3)
    resumen_dx4 = resumen_dx4.sort_values(by="Frecuencia", ascending=False)
    ruta_resumen_dx4 = ruta_salida / "frecuencia_diagnosticos_CIE4.xlsx"
    resumen_dx4.to_excel(ruta_resumen_dx4, index=False)
    logging.info(f"Frecuencias de diagnósticos CIE-4 exportadas en: {ruta_resumen_dx4}")

    # --- Análisis de coocurrencias ---
    logging.info("Iniciando análisis de coocurrencias...")
    consolidado_3dig = preparar_3dig(rips)
    matriz, diagnosticos_unicos = crear_matriz(consolidado_3dig)
    resultados_df = analizar(matriz, diagnosticos_unicos, cie_dict_3)

    # Filtrar solo asociaciones significativas
    resultados_signif = resultados_df[resultados_df["p_value_adj"] < 0.05]
    ruta_resultados = ruta_salida / "analisis_coocurrencias_significativas.xlsx"
    resultados_signif.to_excel(ruta_resultados, index=False)
    logging.info(f"Análisis de coocurrencias exportado en: {ruta_resultados}")

    total_time = time.time() - start_time
    logging.info(f"Proceso completado en {total_time / 60:.2f} minutos.")

