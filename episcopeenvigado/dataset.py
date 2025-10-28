from pathlib import Path
from sqlalchemy import create_engine
from tqdm import tqdm
import typer

app = typer.Typer()

from etl_modules._config import (
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


@app.command()
def main(
    # ---- REMPLAZAR EL NOMBRE DEL ARCHIVO CORRECTO ----
    input_path: Path = RAW_DATA_DIR / "RIPS_20232024_HOSP.xlsx",
    output_path: Path = PROCESSED_DATA_DIR / "RIPS_20232024_HOSP.xlsx",
    # ----------------------------------------------
):
    # ---- REPLACE THIS WITH YOUR OWN CODE ----
    logger.info("Processing dataset...")
    for i in tqdm(range(10), total=10):
        if i == 5:
            logger.info("Something happened for iteration 5.")
    logger.success("Processing dataset complete.")
    # -----------------------------------------


if __name__ == "__main__":
    app()


# ======================================================
# Catálogo de causas externas (CAUSA EXT)
# ======================================================
CAT_CAUSA_EXT = {
    "01": "ACCIDENTE DE TRABAJO",
    "02": "ACCIDENTE DE TRÁNSITO",
    "03": "ACCIDENTE RÁBICO",
    "04": "ACCIDENTE OFÍDICO",
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
