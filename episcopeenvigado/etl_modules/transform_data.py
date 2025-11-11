# Importar bibliotecas necesarias
import pandas as pd
import re
from loguru import logger


# **02. Limpieza de Datos**


# ======================================================
# Función: limpieza_datos
# ======================================================
def limpieza_datos(df: pd.DataFrame):
    # --- Validación de ID ---
    # Normaliza por si vienen espacios o minúsculas
    df["ID"] = df["ID"].astype("string").str.strip().str.upper()

    # True si cumple ^PAC\d{5}$, False si no (y False también para NaN)
    df["ID_valido"] = df["ID"].str.fullmatch(r"^PAC\d{5}$").fillna(False)

    df["MUNICIPIO"] = df["MUNICIPIO"].apply(
        lambda x: str(int(x)).zfill(3) if pd.notnull(x) else None
    )
    df["DEPARTAMENTO"] = df["DEPARTAMENTO"].apply(
        lambda x: str(int(x)).zfill(2) if pd.notnull(x) else None
    )

    # --- Via Ingreso valida ---
    df = df[df["VIA INGRESO"].astype(str).isin(["1", "2", "3", "4"])]

    # --- Numérico para las llaves o códigos ---
    for c in [
        "VIA INGRESO",
        "CAUSA EXT",
        "EDAD",
        "UNIDAD EDAD",
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
    df["Duracion_Dias"] = (df["Fecha_Egreso"] - df["Fecha_Ingreso"]).dt.days + 1
    df.loc[df["Duracion_Dias"] < 0, "Duracion_Dias"] = pd.NA

    return df


# ======================================================
# Función: limpieza_departamentos
# ======================================================
def limpieza_departamentos(df: pd.DataFrame) -> pd.DataFrame:
    """
    Limpia y transforma los datos del catálogo de departamentos.

    Operaciones aplicadas:
    ----------------------
    1. Selecciona las columnas `Codigo` y `Nombre` del DataFrame original.
    2. Elimina los registros con valores nulos en dichas columnas.
    3. Elimina los duplicados basados en el campo `Codigo`.
    4. Renombra las columnas para que coincidan con los nombres de la tabla SQL:
           - `Codigo` → `departamento_cod`
           - `Nombre` → `departamento_desc`
    5. Ordena los registros por el código del departamento y reinicia el índice.

    Parámetros
    ----------
    df : pandas.DataFrame
        DataFrame original con los datos crudos de departamentos.

    Retorna
    -------
    pandas.DataFrame
        DataFrame limpio, transformado y con los nombres de columnas estandarizados.
    """

    logger.info("🧹 Iniciando transformación de datos de departamentos")

    # Limpiar y preparar
    dim_depto = (
        df[["Codigo", "Nombre"]]
        .dropna(subset=["Codigo", "Nombre"])
        .drop_duplicates(subset=["Codigo"])
        .rename(
            columns={
                "Codigo": "departamento_cod",
                "Nombre": "departamento_desc",
            }
        )
        .sort_values(by="departamento_cod")
        .reset_index(drop=True)
    )

    logger.success(f"✅ Transformación completada: {len(dim_depto)} registros válidos")

    return dim_depto


# ======================================================
# Función: limpieza_municipios
# ======================================================
def limpieza_municipios(df: pd.DataFrame) -> pd.DataFrame:
    """
    Limpia y transforma los datos de municipios.

    Operaciones aplicadas:
    ----------------------
    1. Selecciona las columnas `Codigo`, `Nombre` y `Extra_I:Departamento`.
    2. Elimina registros con valores nulos en dichas columnas.
    3. Elimina duplicados basados en el código del municipio.
    4. Renombra las columnas para coincidir con los nombres de la tabla SQL:
           - `Codigo` → `municipio_dane`
           - `Nombre` → `municipio_desc`
           - `Extra_I:Departamento` → `departamento_cod`
    5. Ordena los registros por el código del departamento.

    Parámetros
    ----------
    df : pandas.DataFrame
        DataFrame original con los datos crudos de municipios.

    Retorna
    -------
    pandas.DataFrame
        DataFrame limpio y transformado con las columnas estandarizadas.
    """
    logger.info("🧹 Iniciando transformación de datos de departamentos")

    # Limpiar y preparar
    dim_muni = (
        df[["Codigo", "Nombre", "Extra_I:Departamento"]]
        .dropna(subset=["Codigo", "Nombre", "Extra_I:Departamento"])
        .drop_duplicates(subset=["Codigo"])
        .rename(
            columns={
                "Codigo": "municipio_dane",
                "Nombre": "municipio_desc",
                "Extra_I:Departamento": "departamento_cod",
            }
        )
        .sort_values(by="departamento_cod")
        .reset_index(drop=True)
    )

    logger.success(f"✅ Transformación completada: {len(dim_muni)} registros válidos")

    return dim_muni


# ======================================================
# Función: limpieza_cie10
# ======================================================
def limpieza_cie10(df: pd.DataFrame) -> pd.DataFrame:
    """
    Limpia y transforma los datos de la tabla de referencia CIE-10
    para que coincidan con la estructura real de la tabla `dim_cie10`.
    """

    logger.info("🧹 Iniciando transformación de datos de la tabla CIE-10")

    dim_cie10 = (
        df[
            [
                "CAPITULO",
                "NOMBRE_CAP",
                "CIE_3CAT",
                "DESC_3CAT",
                "CIE_4CAT",
                "DESC_4CAT",
                "Extra_I:AplicaASexo",
                "Extra_II:EdadMinima",
                "Extra_III:EdadMaxima",
                "Extra_VIII:SubGrupo",
                "Extra_X:Sexo",
            ]
        ]
        .dropna(subset=["CIE_4CAT"])
        .drop_duplicates(subset=["CIE_4CAT"])
        .rename(
            columns={
                "CAPITULO": "capitulo",
                "NOMBRE_CAP": "nombre_cap",
                "CIE_3CAT": "cie_3cat",
                "DESC_3CAT": "desc_3cat",
                "CIE_4CAT": "cie_4cat",
                "DESC_4CAT": "desc_4cat",
                "Extra_I:AplicaASexo": "extra_i_aplicaASexo",
                "Extra_II:EdadMinima": "extra_ii_edadMinima",
                "Extra_III:EdadMaxima": "extra_iii_edadMaxima",
                "Extra_VIII:SubGrupo": "extra_viii_subGrupo",
                "Extra_X:Sexo": "extra_x_sexo",
            }
        )
        .assign(
            extra_ii_edadMinima=lambda d: pd.to_numeric(
                d["extra_ii_edadMinima"], errors="coerce"
            ).astype("Int64"),
            extra_iii_edadMaxima=lambda d: pd.to_numeric(
                d["extra_iii_edadMaxima"], errors="coerce"
            ).astype("Int64"),
        )
        .sort_values(by="cie_4cat")
        .reset_index(drop=True)
    )

    logger.success(f"✅ Transformación completada: {len(dim_cie10)} registros válidos")

    return dim_cie10
