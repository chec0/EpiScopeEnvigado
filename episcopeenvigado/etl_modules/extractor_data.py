# Importar bibliotecas necesarias
import pandas as pd
from loguru import logger


# **01. Carga de Datos**
def cargar_datos(input_path):
    try:
        data = pd.read_excel(input_path)
        logger.success("Datos cargados correctamente de archivo local!")
    except FileNotFoundError:
        logger.error(
            f"Error: El archivo no ha sido encontrado en la ruta: {input_path}"
        )
    except Exception as e:
        logger.error(f"Ocurrió otro error: {e}")

    return data


# ======================================================
# Función: extraer_departamentos
# ======================================================
def extraer_departamentos(ruta_archivo, hoja: str = None) -> pd.DataFrame:
    """
    Extrae la información de departamentos desde un archivo Excel.

    Parámetros
    ----------
    nombre_archivo : str
        Nombre del archivo Excel que contiene el catálogo de departamentos.
    hoja : str, opcional
        Nombre de la hoja a leer. Si no se especifica, se leerá la primera hoja.

    Retorna
    -------
    pandas.DataFrame
        DataFrame con las columnas originales del archivo.

    Excepciones
    -----------
    FileNotFoundError
        Si el archivo Excel no se encuentra en el directorio configurado.
    """

    if not ruta_archivo or not ruta_archivo.exists():
        logger.error(f"No se encontró el archivo en {ruta_archivo}")

    logger.info(f"📂 Leyendo archivo Excel: {ruta_archivo}")
    df = pd.read_excel(
        ruta_archivo,
        dtype={
            "Codigo": "str",
            "Nombre": "str",
        },
    )
    logger.success(
        f"✅ Archivo leído correctamente: {df.shape[0]} filas, {df.shape[1]} columnas"
    )

    return df


# ======================================================
# Función: extraer_municipios
# ======================================================
def extraer_municipios(ruta_archivo, hoja: str = None) -> pd.DataFrame:
    """
    Extrae la información de departamentos desde un archivo Excel.

    Parámetros
    ----------
    nombre_archivo : str
        Nombre del archivo Excel que contiene el catálogo de departamentos.
    hoja : str, opcional
        Nombre de la hoja a leer. Si no se especifica, se leerá la primera hoja.

    Retorna
    -------
    pandas.DataFrame
        DataFrame con las columnas originales del archivo.

    Excepciones
    -----------
    FileNotFoundError
        Si el archivo Excel no se encuentra en el directorio configurado.
    """

    if not ruta_archivo or not ruta_archivo.exists():
        logger.error(f"No se encontró el archivo en {ruta_archivo}")

    logger.info(f"📂 Leyendo archivo Excel: {ruta_archivo}")
    df = pd.read_excel(
        ruta_archivo,
        dtype={
            "Codigo": "str",
            "Nombre": "str",
            "Extra_I:Departamento": "str",
        },
    )
    logger.success(
        f"✅ Archivo leído correctamente: {df.shape[0]} filas, {df.shape[1]} columnas"
    )

    return df


# ======================================================
# Función: extraer_cie10
# ======================================================
def extraer_cie10(ruta_archivo, hoja: str = "Final") -> pd.DataFrame:
    """
    Extrae la información de la tabla de referencia CIE-10 desde un archivo Excel.

    Parámetros
    ----------
    ruta_archivo : str
        Ruta del archivo Excel que contiene la tabla de referencia CIE-10.
    hoja : str, opcional
        Nombre de la hoja a leer. Si no se especifica, se leerá la primera hoja.

    Retorna
    -------
    pandas.DataFrame
        DataFrame con las columnas originales del archivo.

    Excepciones
    -----------
    FileNotFoundError
        Si el archivo Excel no se encuentra en el directorio configurado.
    """

    if not ruta_archivo or not ruta_archivo.exists():
        logger.error(f"No se encontró el archivo en {ruta_archivo}")

    logger.info(f"📂 Leyendo archivo Excel: {ruta_archivo}")
    df = pd.read_excel(
        ruta_archivo,
        sheet_name=hoja,
        dtype={
            "CAPITULO": "str",
            "NOMBRE_CAP": "str",
            "CIE_3CAT": "str",
            "DESC_3CAT": "str",
            "CIE_4CAT": "str",
            "DESC_4CAT": "str",
            "Extra_I:AplicaASexo": "str",
            "Extra_II:EdadMinima": "Int64",
            "Extra_III:EdadMaxima": "Int64",
            "Extra_VIII:SubGrupo": "str",
            "Extra_X:Sexo": "str",
        },
    )
    logger.success(
        f"✅ Archivo CIE-10 leído correctamente: {df.shape[0]} filas, {df.shape[1]} columnas"
    )

    return df
