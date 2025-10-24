# Importar bibliotecas necesarias
import pandas as pd
import re


# **02. Limpieza de Datos**
def limpieza_datos(df):
    # --- Validación de ID ---
    # Normaliza por si vienen espacios o minúsculas
    df["ID"] = df["ID"].astype("string").str.strip().str.upper()

    # True si cumple ^PAC\d{5}$, False si no (y False también para NaN)
    df["ID_valido"] = df["ID"].str.fullmatch(r"^PAC\d{5}$").fillna(False)

    # --- Numérico para las llaves o códigos ---

    for c in [
        "VIA INGRESO",
        "CAUSA EXT",
        "EDAD",
        "UNIDAD EDAD",
        "MUNICIPIO",
        "GRUPO EDAD",
        "AÑO",
    ]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce").astype("Int64")
    df.head()

    # --- Fechas ---
    # Fechas (formato dd/mm/yyyy)
    for c in ["Fecha_Ingreso", "Fecha_Egreso"]:
        df[c] = pd.to_datetime(df[c], errors="coerce", dayfirst=True)

    # Validación de orden y no futuro
    hoy = pd.Timestamp.today().normalize()
    df.loc[df["Fecha_Ingreso"] > hoy, "Fecha_Ingreso"] = pd.NaT
    df.loc[df["Fecha_Egreso"] > hoy, "Fecha_Egreso"] = pd.NaT
    df.loc[
        (df["Fecha_Ingreso"].notna())
        & (df["Fecha_Egreso"].notna())
        & (df["Fecha_Egreso"] < df["Fecha_Ingreso"]),
        "Fecha_Egreso",
    ] = pd.NaT

    # --- Validación CIE-10 ---
    cie_regex = re.compile(r"^[A-TV-Z][0-9][0-9A-Z](\.[0-9A-Z]{1,2})?$")
    cie_cols = [
        "Cod_Dx_Ppal_Egreso",
        "DIAG EGRESO REL 1",
        "DIAG EGRESO REL 2",
        "DIAG EGRESO REL 3",
        "DIAG COMPLICACION",
        "DIAG MUERTE",
    ]

    # Edad normalizada a años (derivada) — la FK será a dim_edad; aquí solo derivamos métrica
    MAP_UNIDAD_EDAD = {"1": "A", "2": "M", "3": "D"}
    df["UNIDAD_EDAD_TXT"] = df["UNIDAD EDAD"].astype("string").map(MAP_UNIDAD_EDAD)

    # Duración de estancia (derivada)
    df["Duracion_Dias"] = (df["Fecha_Egreso"] - df["Fecha_Ingreso"]).dt.days
    df.loc[df["Duracion_Dias"] < 0, "Duracion_Dias"] = pd.NA

    return df
