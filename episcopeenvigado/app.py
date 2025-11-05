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
    archivo_RIPS: Path = RAW_DATA_DIR / "RIPS_20232024_HOSP.xlsx",
    archivo_DEPTO: Path = RAW_DATA_DIR / "TablaReferencia_Departamento.xlsx",
    archivo_MUNI: Path = RAW_DATA_DIR / "TablaReferencia_Municipio.xlsx",
    archivo_CIE10: Path = RAW_DATA_DIR / "TablaReferencia_CIE10.xlsx",
    # ----------------------------------------------
):
    """
    Proceso principal del pipeline ETL:
    0. Verificar BD
    1. Carga de datos [RIPS, Departamentos, Municipios]
    2. Limpieza
    3. (opcional) Carga a base de datos
    """

    # Validación
    if ld.validar_base_datos():
        logger.info("La base de datos ya existe")
        df_cie10 = ld.cargar_cie10(archivo_CIE10)

    else:
        logger.info("Comienza la creación de la Base de Datos...")
        ld.crear_base_datos()

        # 1️⃣ Extracción
        logger.info("🚀 Comienza la ejecución del proceso ETL...")
        df = et.cargar_datos(archivo_RIPS)

        logger.success("Dataset cargado correctamente")

        # 2️⃣ Transformación
        logger.info("🧹 Comienza la limpieza de datos...")
        df_limpio = td.limpieza_datos(df)
        logger.success("✅ Limpieza finalizada.")

        # 3 Guardar datos
        df_depto = ld.cargar_departamentos(archivo_DEPTO)
        df_muni = ld.cargar_municipios(archivo_MUNI)
        df_cie10 = ld.cargar_cie10(archivo_CIE10)

        if ld.preparacion_dataset(df_limpio):
            logger.success("Datos cargados correctamente.")
        else:
            logger.error("Datos no cargados")


if __name__ == "__main__":
    app()
