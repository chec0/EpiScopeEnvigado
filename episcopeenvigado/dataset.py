from pathlib import Path

from loguru import logger
from tqdm import tqdm
import typer

from episcopeenvigado.config import PROCESSED_DATA_DIR, RAW_DATA_DIR

app = typer.Typer()


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
