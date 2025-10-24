# ==================================================
# Script inicial de la aplicación EpiScope Envigado
# ==================================================


# Importar bibliotecas necesarias
from pathlib import Path

from loguru import logger
from tqdm import tqdm
import typer

from episcopeenvigado.config import PROCESSED_DATA_DIR, RAW_DATA_DIR
import etl_modules.extractor_data as et
import etl_modules.transform_data as td
import etl_modules.load_data as ld

app = typer.Typer()


@app.command()
def main(
    # ---- REMPLAZAR EL NOMBRE DEL ARCHIVO CORRECTO ----
    input_path: Path = RAW_DATA_DIR / "RIPS_20232024_HOSP.xlsx",
    output_path: Path = PROCESSED_DATA_DIR / "RIPS_20232024_HOSP.xlsx",
    # ----------------------------------------------
):
    """
    Proceso principal del pipeline ETL:
    1. Carga de datos
    2. Limpieza
    3. (opcional) Carga a base de datos
    """
    logger.info("🚀 Comienza la ejecución del proceso ETL...")
    print("🚀 Comienza la ejecución del proceso ETL...")

    # 1️⃣ Extracción
    df = et.cargar_datos(input_path)
    logger.success("Dataset cargado correctamente")

    # 2️⃣ Transformación
    logger.info("🧹 Comienza la limpieza de datos...")
    print("🧹 Comienza la limpieza de datos...")
    df_limpio = td.limpieza_datos(df)
    logger.success("✅ Limpieza finalizada.")
    print("✅ Limpieza finalizada.")

    ld.crear_base_datos(df_limpio)

    # ---- REPLACE THIS WITH YOUR OWN CODE ----
    logger.info("Processing dataset...")
    for i in tqdm(range(10), total=10):
        if i == 5:
            logger.info("Something happened for iteration 5.")
    logger.success("Processing dataset complete.")
    # -----------------------------------------


if __name__ == "__main__":
    app()
