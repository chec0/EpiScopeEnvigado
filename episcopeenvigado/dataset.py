from pathlib import Path
from sqlalchemy import create_engine
import pandas as pd
import typer
from typing import Optional

app = typer.Typer()

# ✅ Importación corregida (usa el paquete completo)
from episcopeenvigado.etl_modules._config import (
    MYSQL_USER,
    MYSQL_HOST,
    MYSQL_PORT,
    MYSQL_DB,
    MYSQL_PASSWORD_URL,
)

from episcopeenvigado.config import PROCESSED_DATA_DIR, RAW_DATA_DIR
from loguru import logger


# ======================================================
# Función: crear_conexion
# ======================================================
def crear_conexion(bd: bool = False):
    """
    Crea y devuelve un motor de conexión a la base de datos MySQL usando SQLAlchemy.

    Parámetros
    ----------
    bd : bool, opcional
        Indica si la conexión debe incluir el nombre de la base de datos.
        - True: conecta directamente a la base de datos indicada en MYSQL_DB.
        - False: conecta solo al servidor (sin seleccionar base de datos).
        Por defecto es False.

    Variables requeridas (definidas en _config.py)
    ----------------------------------------------
    MYSQL_USER : str
        Usuario de la base de datos.
    MYSQL_PASSWORD_URL : str
        Contraseña o token de acceso del usuario.
    MYSQL_HOST : str
        Dirección o IP del servidor MySQL (por ejemplo, "localhost").
    MYSQL_PORT : str
        Puerto de conexión (por ejemplo, "3306").
    MYSQL_DB : str
        Nombre de la base de datos.

    Retorna
    -------
    sqlalchemy.Engine
        Motor de conexión a la base de datos.

    Ejemplo
    -------
    >>> engine = crear_conexion(bd=True)
    >>> print(engine)
    Engine(mysql+pymysql://user:***@localhost:3306/mydb)
    """
    # Si se solicita conexión a la BD específica
    if bd:
        engine_db = create_engine(
            f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD_URL}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}?charset=utf8mb4",
            pool_pre_ping=True,
        )
    else:
        engine_db = create_engine(
            f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD_URL}@{MYSQL_HOST}:{MYSQL_PORT}",
            pool_pre_ping=True,
        )

    return engine_db


# ======================================================
# Función: obtener_dataset_completo
# ======================================================
def obtener_dataset_completo() -> dict[str, pd.DataFrame]:
    """
    Recupera todas las tablas disponibles en la base de datos MySQL definida en la configuración
    y las devuelve como un diccionario de DataFrames de pandas.

    Parámetros
    ----------
    Ninguno.

    Retorna
    -------
    dict[str, pandas.DataFrame]
        Un diccionario donde:
          - La clave es el nombre de la tabla.
          - El valor es un DataFrame con el contenido completo de esa tabla.

    Ejemplo
    -------
    >>> dataset = obtener_dataset_completo()
    >>> dataset.keys()
    dict_keys(['dim_departamento', 'dim_municipio', 'hecho_ventas', ...])
    >>> dataset['hecho_ventas'].head()
    """

    # Crear conexión a la base de datos
    engine_db = crear_conexion(bd=True)

    try:
        with engine_db.begin() as conn:
            # 1️⃣ Obtener la lista de tablas
            tablas = pd.read_sql("SHOW TABLES;", con=conn).iloc[:, 0].tolist()
            logger.info(f"📋 Se encontraron {len(tablas)} tablas en la base de datos.")

            dataset = {}

            # 2️⃣ Cargar cada tabla en un DataFrame
            for tabla in tablas:
                try:
                    df = pd.read_sql(f"SELECT * FROM {tabla};", con=conn)
                    dataset[tabla] = df
                    logger.success(
                        f"✅ Tabla '{tabla}' cargada correctamente ({len(df)} filas)."
                    )
                except Exception as e:
                    logger.error(f"⚠️ Error al cargar la tabla '{tabla}': {e}")

            logger.info(
                f"✅ Dataset completo cargado ({len(dataset)} tablas exitosas)."
            )
            return dataset

    except Exception as e:
        logger.error(f"❌ Error al obtener el dataset completo: {e}")
        return {}


def cargar_datasets_locales(
    processed_dir: Optional[Path] = None,
) -> dict[str, pd.DataFrame]:
    """
    Carga todos los archivos Excel (.xlsx) disponibles en la carpeta 'processed'
    y los guarda como un diccionario de DataFrames en la variable de sesión.

    Parámetros
    ----------
    processed_dir : Path
        Ruta del directorio 'processed' donde se almacenan los archivos procesados.

    Retorna
    -------
    dict[str, pd.DataFrame]
        Diccionario con los DataFrames cargados.
        La clave es el nombre base del archivo (sin extensión).

    Ejemplo
    -------
    >>> from episcopeenvigado.config import PROCESSED_DATA_DIR
    >>> datasets = cargar_datasets_locales(PROCESSED_DATA_DIR)
    >>> list(datasets.keys())
    ['analisis_coocurrencias_significativas', 'frecuencia_diagnosticos_CIE4', ...]

    Notas
    -----
    - Los archivos deben tener extensión .xlsx.
    - Los DataFrames se almacenan en `st.session_state['datasets_locales']`
      para reutilizarlos en otros notebooks o apps.
    """
    if processed_dir is None:
        processed_dir = PROCESSED_DATA_DIR  # Valor por defecto real

    processed_dir = Path(processed_dir)
    if not processed_dir.exists():
        logger.error(f"❌ No se encontró el directorio: {processed_dir}")
        return {}

    archivos = list(processed_dir.glob("*.xlsx"))
    if not archivos:
        logger.warning(f"⚠️ No se encontraron archivos Excel en {processed_dir}")
        return {}

    datasets = {}
    for archivo in archivos:
        try:
            df = pd.read_excel(archivo)
            nombre_base = archivo.stem  # nombre sin extensión
            datasets[nombre_base] = df
            logger.success(
                f"✅ Archivo '{nombre_base}' cargado con {df.shape[0]} filas."
            )
        except Exception as e:
            logger.error(f"⚠️ Error al leer '{archivo.name}': {e}")

    return datasets


@app.command()
def main():
    df = obtener_dataset_completo()
    datasets = cargar_datasets_locales()
    list(df.keys())
    print(datasets.keys())


if __name__ == "__main__":
    app()


# ======================================================
# Catálogo de vías de ingreso (VIA INGRESO)
# ======================================================
CAT_CAUSA_EXT = {
    "01": "ACCIDENTE DE TRABAJO",
    "02": "ACCIDENTE DE TRÁNSITO",
    "03": "ACCIDENTE RÁBICO",
    "05": "OTRO TIPO DE ACCIDENTE",
    "06": "EVENTO CATASTRÓFICO",
    "07": "LESIÓN POR AGRESIÓN",
    "08": "LESIÓN AUTO INFLIGIDA",
    "09": "SOSPECHA DE MALTRATO FÍSICO",
    "10": "SOSPECHA DE ABUSO SEXUAL",
    "11": "SOSPECHA DE VIOLENCIA SEXUAL",
    "12": "SOSPECHA DE MALTRATO EMOCIONAL",
    "13": "ENFERMEDAD GENERAL",
    "14": "ENFERMEDAD PROFESIONAL",
    "15": "OTRA",
}


# ======================================================
# Función auxiliar para traducir código a descripción
# ======================================================
def obtener_causa_ext(codigo: str) -> str:
    """
    Retorna la descripción textual de la causa externa según su código.

    Parámetros
    ----------
    codigo : str o int
        Código de causa externa (por ejemplo '07' o 7).

    Retorna
    -------
    str : Descripción correspondiente o 'NO DEFINIDA' si no existe.

    Ejemplo de uso
    -------
    obtener_causa_ext(2)
    'ACCIDENTE DE TRÁNSITO'

    # Supón que tu DataFrame tiene una columna 'CAUSA_EXT'
    df["CAUSA_EXT_DESC"] = df["CAUSA_EXT"].apply(obtener_causa_ext)
    """

    # Convertir a string y asegurar formato con dos dígitos
    codigo_str = str(codigo).zfill(2)
    return CAT_CAUSA_EXT.get(codigo_str, "NO DEFINIDA")


# ======================================================
# Catálogo de vías de ingreso (VIA INGRESO)
# ======================================================
CAT_VIA_INGRESO = {
    "01": "URGENCIAS",
    "02": "CONSULTA EXTERNA",
    "03": "REMITIDO",
    "04": "NACIDO EN LA INSTITUCIÓN",
}


# ======================================================
# Función auxiliar para traducir código a descripción
# ======================================================
def obtener_via_ingreso(codigo: str) -> str:
    """
    Retorna la descripción textual de la vía de ingreso según su código.

    Parámetros
    ----------
    codigo : str o int
        Código de vía de ingreso (por ejemplo '01' o 1).

    Retorna
    -------
    str : Descripción correspondiente o 'NO DEFINIDA' si no existe.

    Ejemplo de uso
    -------
    obtener_via_ingreso(1)
    'URGENCIAS'

    # Supón que tu DataFrame tiene una columna 'VIA_INGRESO'
    df["VIA_INGRESO_DESC"] = df["VIA_INGRESO"].apply(obtener_via_ingreso)
    """
    # Convertir a string y asegurar formato con dos dígitos
    codigo_str = str(codigo).zfill(2)
    return CAT_VIA_INGRESO.get(codigo_str, "NO DEFINIDA")


# ------------------------------------------------
# Función: unificar_dataset
# Une fact_atenciones con las tablas de dimensiones
# sin eliminar ninguna columna del fact
# ------------------------------------------------
def unificar_dataset(episcope_data: dict) -> pd.DataFrame:
    """
    Unifica las tablas fact y dimensiones del modelo Episcope.

    Parámetros
    ----------
    episcope_data : dict
        Diccionario con las tablas cargadas, donde las claves son los nombres
        de cada tabla (por ejemplo 'fact_atenciones', 'dim_via_ingreso', etc.)

    Retorna
    -------
    pd.DataFrame
        DataFrame unificado con todas las dimensiones asociadas.
    """

    # Extraer tablas individuales del diccionario
    fact = episcope_data["fact_atenciones"]
    dim_causa = episcope_data["dim_causa_ext"]
    dim_cie10 = episcope_data["dim_cie10"]
    dim_depto = episcope_data["dim_departamento"]
    dim_estado = episcope_data["dim_estado_salida"]
    dim_mpio = episcope_data["dim_municipio"]
    dim_via = episcope_data["dim_via_ingreso"]

    # Copiar fact para no modificar el original
    df = fact.copy()

    # --- Unir dimensiones al fact ---
    df = df.merge(dim_causa, on="causa_ext_id", how="left")
    df = df.merge(dim_depto, on="departamento_id", how="left")
    df = df.merge(dim_mpio, on="municipio_id", how="left")
    df = df.merge(dim_estado, on="estado_salida_id", how="left")
    df = df.merge(dim_via, on="via_ingreso_id", how="left")

    # --- Diagnóstico principal (CIE10) ---
    df = df.merge(
        dim_cie10[["cie_4cat", "desc_4cat", "nombre_cap"]],
        left_on="Cod_Dx_Ppal_Egreso",
        right_on="cie_4cat",
        how="left",
    )

    # --- Renombrar columnas descriptivas ---
    df = df.rename(
        columns={
            "desc_4cat": "Diagnostico_Principal_Desc",
            "nombre_cap": "Capitulo_CIE10",
            "causa_ext_desc": "Causa_Externa_Desc",
            "departamento_desc": "Departamento_Desc",
            "municipio_desc": "Municipio_Desc",
            "estado_salida_desc": "Estado_Salida_Desc",
            "via_ingreso_desc": "Via_Ingreso_Desc",
        }
    )

    return df
