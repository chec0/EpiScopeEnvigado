"""
diagnosticoOp.py
================
Analiza la coocurrencia de diagnósticos a partir de los datos almacenados
en las tablas `fact_atenciones` (RIPS) y `dim_cie10` (catálogo CIE-10).
Incluye consolidación por usuario, cálculo de frecuencias, creación de matriz binaria
y análisis estadístico avanzado (Chi² y Odds Ratio).
"""

# ======================================================
# 1. IMPORTACIONES
# ======================================================
import pandas as pd
import itertools
import numpy as np
import time
from loguru import logger
from scipy.sparse import triu
from scipy.stats import chi2_contingency, norm
from sklearn.preprocessing import MultiLabelBinarizer
from statsmodels.stats.multitest import multipletests
from tqdm import tqdm
from pathlib import Path
import episcopeenvigado.dataset as ds
from episcopeenvigado.config import PROCESSED_DATA_DIR


# ======================================================
# 2. FUNCIONES AUXILIARES
# ======================================================


def exportar_excel(df: pd.DataFrame, nombre: str):
    """
    Exporta un DataFrame a un archivo Excel dentro del directorio especificado.

    Parámetros
    ----------
    df : pd.DataFrame
        DataFrame que se desea exportar.
    nombre : str
        Nombre del archivo de salida (incluye extensión .xlsx).

    Retorna
    -------
    None
        Solo guarda el archivo y registra el evento en el log.
    """
    ruta_salida = PROCESSED_DATA_DIR / nombre
    df.to_excel(ruta_salida, index=False)
    logger.info(f"📁 Exportado: {ruta_salida}")


def limpiar_diagnosticos(df: pd.DataFrame) -> pd.DataFrame:
    """
    Limpia y normaliza los códigos de diagnóstico:
    convierte a mayúsculas, elimina espacios, valores nulos y cadenas vacías.

    Parámetros
    ----------
    df : pd.DataFrame
        DataFrame con columnas de diagnósticos.

    Retorna
    -------
    pd.DataFrame
        DataFrame con los valores normalizados.
    """
    df = df.copy()
    for col in df.columns:
        df[col] = (
            df[col].astype(str).str.strip().str.upper().replace({"NAN": None, "": None})
        )
        df[col] = df[col].where(df[col].notna())  # filtra None
    return df


def consolidar_4dig(df: pd.DataFrame, dx_cols: list) -> pd.DataFrame:
    """
    Consolida los diagnósticos de 4 dígitos por paciente (ID).

    Parámetros
    ----------
    df : pd.DataFrame
        Tabla de hechos con diagnósticos por atención.
    dx_cols : list
        Columnas que contienen los códigos CIE-10.

    Retorna
    -------
    pd.DataFrame
        DataFrame con una lista de diagnósticos por paciente (dx_list_4dig).
    """
    df_dx = limpiar_diagnosticos(df[dx_cols])
    consolidado = df_dx.groupby(df["ID"]).agg(lambda x: list(x.dropna()))
    consolidado["dx_list_4dig"] = consolidado.apply(
        lambda row: [
            dx
            for dx in set(itertools.chain.from_iterable(row))
            if dx not in [None, "NONE"]
        ],
        axis=1,
    )
    return consolidado


def consolidar_3dig(df: pd.DataFrame, dx_cols: list) -> pd.DataFrame:
    """
    Consolida los diagnósticos a 3 dígitos, excluyendo códigos 'Z' y 'R'.

    Parámetros
    ----------
    df : pd.DataFrame
        Tabla de hechos con diagnósticos por atención.
    dx_cols : list
        Columnas que contienen los códigos CIE-10.

    Retorna
    -------
    pd.DataFrame
        DataFrame con diagnósticos de 3 dígitos consolidados (dx_list_3dig).
    """

    df_dx = limpiar_diagnosticos(df[dx_cols]).applymap(lambda x: x[:3] if x else None)
    consolidado = df_dx.groupby(df["ID"]).agg(lambda x: list(x.dropna()))
    consolidado["dx_list_3dig"] = consolidado.apply(
        lambda row: [
            dx
            for dx in set(itertools.chain.from_iterable(row))
            if dx not in [None, "NONE"]
        ],
        axis=1,
    )
    # Excluir códigos Z y R
    consolidado["dx_list_3dig"] = consolidado["dx_list_3dig"].apply(
        lambda l: [dx for dx in l if dx[0] not in ["Z", "R"]]
    )
    return consolidado


def calcular_frecuencias(
    consolidado_4dig: pd.DataFrame, cie: pd.DataFrame
) -> pd.DataFrame:
    """
    Calcula las frecuencias de diagnóstico y número de pacientes únicos por código.

    Parámetros
    ----------
    consolidado_4dig : pd.DataFrame
        Diagnósticos por paciente a 4 dígitos.
    cie : pd.DataFrame
        Catálogo CIE-10 con descripciones.

    Retorna
    -------
    pd.DataFrame
        Tabla resumen con frecuencia total, número de pacientes y descripciones.
    """

    cie_dict_3 = cie.set_index("cie_3cat")["desc_3cat"].to_dict()
    cie_dict_4 = cie.set_index("cie_4cat")["desc_4cat"].to_dict()

    dx_exp = consolidado_4dig["dx_list_4dig"].explode().dropna()
    freq_total = (
        dx_exp.value_counts().rename_axis("Diagnostico").reset_index(name="Frecuencia")
    )

    pacientes_por_dx = (
        consolidado_4dig.explode("dx_list_4dig")
        .dropna(subset=["dx_list_4dig"])
        .reset_index()
        .groupby("dx_list_4dig")["ID"]
        .nunique()
        .rename("Pacientes")
        .reset_index()
        .rename(columns={"dx_list_4dig": "Diagnostico"})
    )

    resumen = pd.merge(freq_total, pacientes_por_dx, on="Diagnostico", how="left")
    resumen["Descripcion_4dig"] = resumen["Diagnostico"].map(cie_dict_4)
    resumen["Descripcion_3dig"] = resumen["Diagnostico"].str[:3].map(cie_dict_3)
    resumen = resumen.sort_values(by="Frecuencia", ascending=False)
    return resumen


def crear_matriz_binaria(consolidado_3dig: pd.DataFrame, frecuencia_minima: int = 30):
    """
    Crea una matriz binaria (paciente x diagnóstico) y filtra por frecuencia mínima.

    Parámetros
    ----------
    consolidado_3dig : pd.DataFrame
        Diagnósticos por paciente (3 dígitos).
    frecuencia_minima : int, opcional
        Umbral mínimo de pacientes por diagnóstico. Default = 30.

    Retorna
    -------
    matriz_filtrada : scipy.sparse.csr_matrix
        Matriz binaria paciente-diagnóstico.
    diagnosticos_filtrados : list
        Lista de diagnósticos que cumplen el umbral.
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

    logger.info(
        f"✅ Diagnósticos filtrados: {len(diagnosticos_filtrados)} (≥ {frecuencia_minima} pacientes)"
    )
    return matriz_filtrada, diagnosticos_filtrados


def analizar_coocurrencias_estadistico(matriz, diagnosticos, cie_dict_3):
    """
    Calcula la coocurrencia estadística entre diagnósticos mediante Chi² y Odds Ratio (OR).

    Parámetros
    ----------
    matriz : scipy.sparse.csr_matrix
        Matriz binaria paciente-diagnóstico.
    diagnosticos : list
        Lista de diagnósticos en el mismo orden que las columnas de la matriz.
    cie_dict_3 : dict
        Diccionario {cie_3cat: descripción} del catálogo CIE-10.

    Retorna
    -------
    pd.DataFrame
        Tabla con resultados estadísticos (Chi², OR, IC95%, p-value y p-value ajustado).
    """

    n = matriz.shape[0]
    col_sums = np.array(matriz.sum(axis=0)).ravel()
    cooc = triu(matriz.T @ matriz, k=1).tocoo()

    resultados, p_values = [], []

    for i, j, a in tqdm(
        zip(cooc.row, cooc.col, cooc.data),
        total=len(cooc.data),
        desc="Analizando coocurrencias",
    ):
        if a < 5:
            continue

        b = col_sums[i] - a
        c = col_sums[j] - a
        d = n - (a + b + c)
        tabla = np.array([[a, b], [c, d]], dtype=float) + 0.5
        chi2, p, _, _ = chi2_contingency(tabla, correction=False)
        p_values.append(p)

        or_value = (tabla[0, 0] * tabla[1, 1]) / (tabla[0, 1] * tabla[1, 0])
        se_log_or = np.sqrt(
            1 / tabla[0, 0] + 1 / tabla[0, 1] + 1 / tabla[1, 0] + 1 / tabla[1, 1]
        )
        z = norm.ppf(0.975)
        log_or = np.log(or_value)
        ci_low, ci_high = np.exp([log_or - z * se_log_or, log_or + z * se_log_or])

        resultados.append(
            {
                "Dx1": diagnosticos[i],
                "Desc1": cie_dict_3.get(diagnosticos[i], "No encontrado"),
                "Dx2": diagnosticos[j],
                "Desc2": cie_dict_3.get(diagnosticos[j], "No encontrado"),
                "Chi2": round(chi2, 3),
                "p_value": p,
                "OR": round(or_value, 3),
                "IC95_Lower": round(ci_low, 3),
                "IC95_Upper": round(ci_high, 3),
                "count_dx1": int(col_sums[i]),
                "count_dx2": int(col_sums[j]),
                "count_coocurrence": int(a),
                "P_conjunta": round(a / n, 5),
                "P_B_dado_A": round(a / col_sums[i], 5),
                "P_A_dado_B": round(a / col_sums[j], 5),
            }
        )

    if resultados:
        _, p_adj, _, _ = multipletests(p_values, method="fdr_bh")
        for res, p_corr in zip(resultados, p_adj):
            res["p_value_adj"] = round(p_corr, 5)

    return pd.DataFrame(resultados)


# ======================================================
# 3. BLOQUE PRINCIPAL
# ======================================================

if __name__ == "__main__":
    start_time = time.time()
    logger.info("🚀 Iniciando análisis de coocurrencia de diagnósticos...")

    try:
        # 1. CARGA DE DATOS DESDE EL MÓDULO DE DATASET
        t0 = time.time()
        episcope_data = ds.obtener_dataset_completo()
        dim_fact = episcope_data["fact_atenciones"]
        dim_cie10 = episcope_data["dim_cie10"]

        logger.info(
            f"📊 Datos cargados: {len(dim_fact):,} atenciones y {len(dim_cie10):,} diagnósticos CIE-10."
        )
        logger.debug(f"⏱ Tiempo carga datos: {(time.time() - t0):.2f}s")

        # 2. DEFINICIÓN DE COLUMNAS DE DIAGNÓSTICOS
        dx_cols = [
            "DIAGNOSTICO INGRESO",
            "Cod_Dx_Ppal_Egreso",
            "DIAG EGRESO REL 1",
            "DIAG EGRESO REL 2",
            "DIAG EGRESO REL 3",
            "DIAG COMPLICACION",
            "DIAG MUERTE",
        ]
        dx_cols = [col for col in dx_cols if col in dim_fact.columns]

        # 3. CONSOLIDADO 4 DÍGITOS
        t1 = time.time()
        consolidado_4dig = consolidar_4dig(dim_fact, dx_cols)
        consolidado_export = consolidado_4dig[["dx_list_4dig"]].reset_index()
        consolidado_export.rename(
            columns={"dx_list_4dig": "diagnosticos_4dig"}, inplace=True
        )
        exportar_excel(consolidado_export, "consolidado_por_usuario_4dig.xlsx")
        logger.debug(f"⏱ Tiempo consolidado 4 dígitos: {(time.time() - t1):.2f}s")

        # 4. FRECUENCIAS CIE-4
        t2 = time.time()
        resumen_dx4 = calcular_frecuencias(consolidado_4dig, dim_cie10)
        exportar_excel(resumen_dx4, "frecuencia_diagnosticos_CIE4.xlsx")
        logger.debug(f"⏱ Tiempo frecuencias: {(time.time() - t2):.2f}s")

        # 5. CONSOLIDADO Y MATRIZ 3 DÍGITOS
        t3 = time.time()
        consolidado_3dig = consolidar_3dig(dim_fact, dx_cols)
        matriz, diagnosticos_unicos = crear_matriz_binaria(consolidado_3dig)
        logger.debug(f"⏱ Tiempo consolidado 3 dígitos: {(time.time() - t3):.2f}s")

        # 6. ANÁLISIS ESTADÍSTICO DE COOCURRENCIAS
        t4 = time.time()
        cie_dict_3 = dim_cie10.set_index("cie_3cat")["desc_3cat"].to_dict()
        resultados_cooc = analizar_coocurrencias_estadistico(
            matriz, diagnosticos_unicos, cie_dict_3
        )
        logger.debug(f"⏱ Tiempo análisis coocurrencias: {(time.time() - t4):.2f}s")

        # 7. FILTRAR ASOCIACIONES SIGNIFICATIVAS
        t5 = time.time()
        resultados_signif = resultados_cooc[resultados_cooc["p_value_adj"] < 0.05]
        exportar_excel(resultados_signif, "analisis_coocurrencias_significativas.xlsx")

        logger.success(
            f"🏁 Análisis completado en {(time.time() - start_time) / 60:.2f} minutos."
        )

    except Exception as e:
        logger.error(f"❌ Error durante la ejecución: {e}")
