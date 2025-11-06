# ==============================================
#  UNIFICAR TABLAS DEL MODELO EPISCOPE
# ==============================================

import pandas as pd
import episcopeenvigado.dataset as ds


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
        how="left"
    )

    # --- Renombrar columnas descriptivas ---
    df = df.rename(columns={
        "desc_4cat": "Diagnostico_Principal_Desc",
        "nombre_cap": "Capitulo_CIE10",
        "causa_ext_desc": "Causa_Externa_Desc",
        "departamento_desc": "Departamento_Desc",
        "municipio_desc": "Municipio_Desc",
        "estado_salida_desc": "Estado_Salida_Desc",
        "via_ingreso_desc": "Via_Ingreso_Desc",
    })

    return df


# ==============================================
#  USO DE LA FUNCIÓN (opcional para pruebas locales)
# ==============================================
if __name__ == "__main__":
    episcope_data = ds.obtener_dataset_completo()
    df_unificado = unificar_dataset(episcope_data)
    print(f"✅ Dataset unificado: {df_unificado.shape[0]} filas, {df_unificado.shape[1]} columnas")
    print(df_unificado.head())
