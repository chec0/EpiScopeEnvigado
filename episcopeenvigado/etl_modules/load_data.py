# Importar bibliotecas necesarias
from pathlib import Path
import pandas as pd
import numpy as np
import pymysql
import re
from io import StringIO
from sqlalchemy import Engine, create_engine, text
from urllib.parse import quote_plus
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


# ======================================================
# Función: probar_conexion
# ======================================================
def probar_conexion(engine_db: Engine, bd_name: str = None) -> bool:
    """
    Verifica la conexión al servidor MySQL y opcionalmente la existencia de una BD.

    Parámetros
    ----------
    engine_db : sqlalchemy.Engine
        Motor de conexión al servidor MySQL (con o sin BD seleccionada).
    bd_name : str, opcional
        Nombre de la base de datos a validar en INFORMATION_SCHEMA.

    Comportamiento
    --------------
    - Si bd_name está definido: consulta INFORMATION_SCHEMA y retorna True/False si existe.
    - Si bd_name no está definido: ejecuta `SELECT NOW()` y retorna el timestamp del servidor como str.

    Retorna
    -------
    bool | str | None
        - bool: existencia de la BD cuando se proporciona bd_name.
        - str: fecha/hora del servidor cuando NO se proporciona bd_name.
        - None: si ocurre un error (también imprime el error).

    Ejemplos
    --------
    >>> probar_conexion(engine_db)            # -> 'True/False'
    >>> probar_conexion(engine_db, 'episcope')# -> True/False
    """
    try:
        with engine_db.connect() as conn:
            if bd_name:
                # Opción principal: INFORMATION_SCHEMA
                q = text("""
                    SELECT 1
                    FROM INFORMATION_SCHEMA.SCHEMATA
                    WHERE SCHEMA_NAME = :db
                    LIMIT 1
                """)
                exists = conn.execute(q, {"db": bd_name}).first() is not None
                return exists
            else:
                # Ping ligero al servidor
                server_now = conn.execute(text("SELECT NOW();")).scalar()
                if server_now is not None:
                    server_now = str(server_now)
                    logger.success(server_now)
                return True
    except Exception as e:
        logger.error(f"[ERROR] No se pudo establecer/verificar la conexión: {e}")
        return False


# ======================================================
# Función: obtener_dimensiones_existentes
# ======================================================
def obtener_dimensiones_existentes(tabla: str) -> pd.DataFrame:
    """
    Recupera las dimensiones ya cargadas en la base de datos MySQL.

    Parámetros
    ----------
    tabla : str
        Nombre de la tabla de dimensión a consultar (por ejemplo: 'dim_departamento' o 'dim_municipio').
    engine : sqlalchemy.Engine
        Motor de conexión SQLAlchemy a la base de datos.

    Retorna
    -------
    pandas.DataFrame
        DataFrame con las columnas de código y clave primaria (ID) de la dimensión solicitada.
    """

    query = ""
    if tabla == "dim_departamento":
        query = "SELECT departamento_id, departamento_cod FROM dim_departamento;"
    elif tabla == "dim_municipio":
        query = (
            "SELECT municipio_id, municipio_dane, departamento_cod FROM dim_municipio;"
        )
    else:
        logger.error(f"Tabla {tabla} no reconocida en el contexto de dimensiones.")

    engine_db = crear_conexion(bd=True)
    try:
        with engine_db.begin() as conn:
            df = pd.read_sql(query, con=conn)
        logger.info(
            f"✅ Dimensión {tabla} cargada correctamente ({len(df)} registros)."
        )
        return df
    except Exception as e:
        logger.error(f"❌ Error al obtener datos de {tabla}: {e}")
        return pd.DataFrame()  # Evita romper el flujo


# ======================================================
# Función: cargar_departamentos
# ======================================================
def cargar_departamentos(nombre_archivo: str, hoja: str = None):
    """
    Carga la información de departamentos desde un archivo Excel y la inserta
    en la tabla `dim_departamento` de la base de datos MySQL.

    Esta función forma parte del proceso ETL para poblar las tablas de
    dimensiones a partir de archivos fuente almacenados en el directorio
    definido por la variable de entorno `RAW_DATA_DIR`.

    Parámetros
    ----------
    nombre_archivo : str
        Nombre del archivo Excel que contiene el catálogo de departamentos.
        Ejemplo: `'TablaReferencia_Departamento.xlsx'`
    hoja : str, opcional
        Nombre de la hoja dentro del archivo Excel que se desea leer.
        Si no se especifica, se cargará la primera hoja del libro.

    Requisitos
    ----------
    - La variable de entorno `RAW_DATA_DIR` debe apuntar al directorio donde
      se encuentran los archivos crudos de entrada.
      Ejemplo:
      >>> set RAW_DATA_DIR="data/raw"
    - El archivo Excel debe contener, como mínimo, las columnas:
        * `Codigo`: código único del departamento.
        * `Nombre`: descripción o nombre del departamento.

    Flujo de ejecución
    ------------------
    1. Construye la ruta absoluta del archivo Excel con base a `RAW_DATA_DIR`.
    2. Lee el contenido del archivo en un DataFrame de pandas.
    3. Filtra y conserva únicamente las columnas `Codigo` y `Nombre`.
    4. Renombra las columnas para coincidir con los nombres de la tabla SQL:
          - `Codigo`  → `departamento_cod`
          - `Nombre`  → `departamento_desc`
    5. Limpia registros nulos y elimina duplicados por código.
    6. Crea una conexión a la base de datos mediante `crear_conexion()`.
    7. Inserta los datos procesados en la tabla `dim_departamento`
       utilizando `pandas.to_sql()` (modo *append*).
    8. Registra mensajes informativos y de error mediante el logger.

    Excepciones
    -----------
    FileNotFoundError
        Si el archivo Excel no existe en el directorio especificado.
    Exception
        Si ocurre algún error durante la inserción en la base de datos.

    Ejemplo
    -------
    >>> cargar_departamentos("TablaReferencia_Departamento.xlsx", hoja="Hoja1")
    📂 Leyendo archivo Excel: data/raw/TablaReferencia_Departamento.xlsx
    ✅ Archivo leído correctamente: 33 filas, 20 columnas
    ✅ Datos cargados en dim_departamento (33 registros)
    """

    ruta_archivo = Path.joinpath(RAW_DATA_DIR, nombre_archivo)
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

    # Filtrar solo columnas necesarias
    dim_depto = df[["Codigo", "Nombre"]].copy()

    # Limpiar y preparar
    dim_depto = (
        dim_depto.dropna(subset=["Codigo", "Nombre"])
        .drop_duplicates(subset=["Codigo"])
        .rename(columns={"Codigo": "departamento_cod", "Nombre": "departamento_desc"})
        .sort_values(by="departamento_cod")
        .reset_index(drop=True)
    )

    # Insertar en la base de datos
    engine_db = crear_conexion(bd=True)

    try:
        with engine_db.begin() as conn:
            dim_depto.to_sql(
                "dim_departamento", con=conn, if_exists="append", index=False
            )
        logger.success(
            f"Datos cargados en dim_departamento ({len(dim_depto)} registros)"
        )
    except Exception as e:
        logger.error(f"Error al insertar en dim_departamento: {e}")

    return


# ======================================================
# Función: cargar_municipios
# ======================================================
def cargar_municipios(nombre_archivo: str, hoja: str = None):
    """
    Carga la información de municipios desde un archivo Excel y la inserta
    en la tabla `dim_municipio` de la base de datos MySQL.

    Esta función forma parte del proceso ETL para poblar las tablas de
    dimensiones a partir de archivos fuente almacenados en el directorio
    definido por la variable de entorno `RAW_DATA_DIR`.

    Parámetros
    ----------
    nombre_archivo : str
        Nombre del archivo Excel que contiene el catálogo de departamentos.
        Ejemplo: `'TablaReferencia_Municipio.xlsx'`
    hoja : str, opcional
        Nombre de la hoja dentro del archivo Excel que se desea leer.
        Si no se especifica, se cargará la primera hoja del libro.

    Requisitos
    ----------
    - La variable de entorno `RAW_DATA_DIR` debe apuntar al directorio donde
      se encuentran los archivos crudos de entrada.
      Ejemplo:
      >>> set RAW_DATA_DIR="data/raw"
    - El archivo Excel debe contener, como mínimo, las columnas:
        * `Codigo`: código único del municipio.
        * `Nombre`: descripción o nombre del municipio.
        * `Extra_I:Departamento`: código del departamento asociado

    Flujo de ejecución
    ------------------
    1. Construye la ruta absoluta del archivo Excel con base a `RAW_DATA_DIR`.
    2. Lee el contenido del archivo en un DataFrame de pandas.
    3. Filtra y conserva únicamente las columnas `Codigo`, `Nombre` y `Extra_I:Departamento`.
    4. Renombra las columnas para coincidir con los nombres de la tabla SQL:
          - `Codigo`  → `municipio_dane`
          - `Nombre`  → `municipio_desc`
          - `Extra_I:Departamento` → `departamento_cod`
    5. Limpia registros nulos y elimina duplicados por código.
    6. Crea una conexión a la base de datos mediante `crear_conexion()`.
    7. Inserta los datos procesados en la tabla `dim_municipio`
       utilizando `pandas.to_sql()` (modo *append*).
    8. Registra mensajes informativos y de error mediante el logger.

    Excepciones
    -----------
    FileNotFoundError
        Si el archivo Excel no existe en el directorio especificado.
    Exception
        Si ocurre algún error durante la inserción en la base de datos.

    Ejemplo
    -------
    >>> cargar_departamentos("TablaReferencia_Municipio.xlsx", hoja="Hoja1")
    📂 Leyendo archivo Excel: data/raw/TablaReferencia_Municipio.xlsx
    ✅ Archivo leído correctamente: 1125 filas, 22 columnas
    ✅ Datos cargados en dim_municipio (1125 registros)
    """

    ruta_archivo = Path.joinpath(RAW_DATA_DIR, nombre_archivo)
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

    # Filtrar solo columnas necesarias
    dim_muni = df[["Codigo", "Nombre", "Extra_I:Departamento"]].copy()

    # Limpiar y preparar
    dim_muni = (
        dim_muni.dropna(subset=["Codigo", "Nombre", "Extra_I:Departamento"])
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

    # Insertar en la base de datos
    engine_db = crear_conexion(bd=True)

    try:
        with engine_db.begin() as conn:
            dim_muni.to_sql("dim_municipio", con=conn, if_exists="append", index=False)
        logger.success(f"Datos cargados en dim_municipio ({len(dim_muni)} registros)")
    except Exception as e:
        logger.error(f"Error al insertar en dim_municipio: {e}")

    return


# ======================================================
# Función: edad_a_anios
# ======================================================
def edad_a_anios(edad, unidad):
    """
    Convierte una edad expresada en años, meses o días a años decimales.

    Parámetros
    ----------
    edad : int o float
        Valor numérico de la edad.
    unidad : int
        Unidad de medida:
        - 1 → Años
        - 2 → Meses
        - 3 → Días

    Retorna
    -------
    float
        Edad convertida a años. Retorna `np.nan` si los valores son nulos o no válidos.

    Ejemplo
    -------
    >>> edad_a_anios(6, 2)
    0.5
    >>> edad_a_anios(730, 1)
    2.0
    >>> edad_a_anios(None, 1)
    nan
    """
    # Validar valores nulos
    if pd.isna(edad) or pd.isna(unidad):
        return np.nan

    # Convertir según unidad
    if unidad == 1:  # Años
        return float(edad)
    if unidad == 2:  # Meses → años
        return float(edad) / 12.0
    if unidad == 3:  # Días → años
        return float(edad) / 365.25

    # En caso de unidad desconocida
    return np.nan


# ======================================================
# Función: preparacion_dataset
# ======================================================
def preparacion_dataset(df) -> bool:
    """
    Prepara el dataset de atenciones médicas y genera la tabla de hechos
    enlazando correctamente las llaves foráneas hacia las dimensiones
    de departamentos y municipios previamente insertadas en la base de datos.
    """

    # Cargar dimensiones base si no existen
    dim_depto = obtener_dimensiones_existentes("dim_departamento")
    if dim_depto.empty:
        cargar_departamentos("TablaReferencia_Departamento.xlsx")
        dim_depto = obtener_dimensiones_existentes("dim_departamento")

    dim_muni = obtener_dimensiones_existentes("dim_municipio")
    if dim_muni.empty:
        cargar_municipios("TablaReferencia_Municipio.xlsx")
        dim_muni = obtener_dimensiones_existentes("dim_municipio")

    df["COD_DANE"] = df["DEPARTAMENTO"].astype(str) + df["MUNICIPIO"].astype(str)

    # =========================
    # CATÁLOGOS (OPCIONALES) PARA ENRIQUECER DIMENSIONES
    #    (NO se guardan en la tabla de hechos; sirven para las dims)
    # =========================

    CAT_VIA_INGRESO = {
        1: "URGENCIAS",
        2: "CONSULTA EXTERNA",
        3: "REMITIDO",
        4: "NACIDO EN LA INSTITUCION",
    }
    CAT_CAUSA_EXT = {
        1: "ACCIDENTE DE TRABAJO",
        2: "ACCIDENTE DE TRÁNSITO",
        3: "ACCIDENTE RÁBICO",
        4: "ACCIDENTE OFÍDICO",
        5: "OTRO TIPO DE ACCIDENTE",
        6: "EVENTO CATASTRÓFICO",
        7: "LESIÓN POR AGRESIÓN",
        8: "LESIÓN AUTO INFLIGIDA",
        9: "SOSPECHA DE MALTRATO FÍSICO",
        10: "SOSPECHA DE ABUSO SEXUAL",
        11: "SOSPECHA DE VIOLENCIA SEXUAL",
        12: "SOSPECHA DE MALTRATO EMOCIONAL",
        13: "ENFERMEDAD GENERAL",
        14: "ENFERMEDAD PROFESIONAL",
        15: "OTRA",
    }

    # =========================
    # CONSTRUCCIÓN DE DIMENSIONES (con IDs sustitutos)
    # =========================

    # --- dim_via_ingreso ---
    dim_via = (
        df[["VIA INGRESO"]]
        .dropna()
        .drop_duplicates()
        .sort_values(by="VIA INGRESO")
        .rename(columns={"VIA INGRESO": "via_ingreso_cod"})
        .assign(
            via_ingreso_desc=lambda d: d["via_ingreso_cod"]
            .astype("Int64")
            .map(CAT_VIA_INGRESO)
        )
        .reset_index(drop=True)
    )
    dim_via.insert(0, "via_ingreso_id", range(1, len(dim_via) + 1))

    # --- dim_estado_salida ---
    # Estado_Salida llega como texto (clave natural de negocio). Creamos SK.
    dim_estado = (
        df[["Estado_Salida"]]
        .fillna("NO_INFO")
        .drop_duplicates()
        .sort_values(by="Estado_Salida")
        .rename(columns={"Estado_Salida": "estado_salida_cod"})
        .assign(
            estado_salida_desc=lambda d: d["estado_salida_cod"]
        )  # puedes mapear a cat oficial si lo tienes
        .reset_index(drop=True)
    )
    dim_estado.insert(0, "estado_salida_id", range(1, len(dim_estado) + 1))

    # --- dim_causa_ext ---
    dim_causa = (
        df[["CAUSA EXT"]]
        .dropna()
        .drop_duplicates()
        .sort_values(by="CAUSA EXT")
        .rename(columns={"CAUSA EXT": "causa_ext_cod"})
        .assign(
            causa_ext_desc=lambda d: d["causa_ext_cod"]
            .astype("Int64")
            .map(CAT_CAUSA_EXT)
        )
        .reset_index(drop=True)
    )
    dim_causa.insert(0, "causa_ext_id", range(1, len(dim_causa) + 1))

    # --- dim_edad ---
    # Aunque el usuario pidió EDAD como llave, para evitar ambigüedad (p.ej. 12 meses vs 1 año),
    # creamos la dimensión con (EDAD, UNIDAD). La FK apuntará a este SK.
    dim_edad = (
        df[["EDAD", "UNIDAD EDAD", "UNIDAD_EDAD_TXT"]]
        .drop_duplicates()
        .sort_values(by=["UNIDAD EDAD", "EDAD"])
        .rename(columns={"UNIDAD EDAD": "unidad_edad_cod"})
        .assign(
            edad_anios=lambda d: d.apply(
                lambda r: edad_a_anios(r["EDAD"], r["UNIDAD_EDAD_TXT"]), axis=1
            )
        )
        .reset_index(drop=True)
    )
    dim_edad.insert(0, "edad_id", range(1, len(dim_edad) + 1))

    # =========================
    # 5) MAPS DE CLAVE NATURAL -> SK (para poblar la tabla de hechos)
    # =========================
    map_via = dict(zip(dim_via["via_ingreso_cod"], dim_via["via_ingreso_id"]))
    map_estado = dict(
        zip(dim_estado["estado_salida_cod"], dim_estado["estado_salida_id"])
    )
    map_causa = dict(zip(dim_causa["causa_ext_cod"], dim_causa["causa_ext_id"]))

    # =========================
    # Enlace con departamentos y municipios reales
    # =========================
    # Crear mapas de código → ID para enlace
    map_depto = dict(zip(dim_depto["departamento_cod"], dim_depto["departamento_id"]))
    map_muni = dict(zip(dim_muni["municipio_dane"], dim_muni["municipio_id"]))

    # =========================
    # TENGO PROBLEMAS CON LA CONVERSIÓN
    # =========================
    # Para edad: clave compuesta (EDAD, UNIDAD EDAD)
    dim_edad["key"] = list(
        zip(
            dim_edad["EDAD"].astype("Int64"),
            dim_edad["unidad_edad_cod"].astype("Int64"),
        )
    )
    map_edad = dict(zip(dim_edad["key"], dim_edad["edad_id"]))

    # =========================
    # 6) TABLA DE HECHOS (con FKs)
    # =========================
    fact = df.copy()

    # FKs a dimensiones
    fact["via_ingreso_id"] = fact["VIA INGRESO"].map(map_via)
    fact["estado_salida_id"] = fact["Estado_Salida"].fillna("NO_INFO").map(map_estado)
    fact["causa_ext_id"] = fact["CAUSA EXT"].map(map_causa)

    fact["departamento_id"] = fact["DEPARTAMENTO"].map(map_depto)
    fact["municipio_id"] = fact["COD_DANE"].map(map_muni)
    """
    fact["edad_id"] = list(
        zip(fact["EDAD"].astype("Int64"), fact["UNIDAD EDAD"].astype("Int64"))
    )
    fact["edad_id"] = fact["edad_id"].map(map_edad)
    """

    # =========================
    # 8) CARGA DE DIMENSIONES Y HECHOS
    # =========================
    # Usamos to_sql con if_exists='append'; como ya existen las tablas, respeta las columnas
    engine_db = crear_conexion(bd=True)

    try:
        with engine_db.begin() as txn:
            dim_via.to_sql("dim_via_ingreso", con=txn, if_exists="append", index=False)
            dim_estado.to_sql(
                "dim_estado_salida", con=txn, if_exists="append", index=False
            )
            dim_causa.to_sql("dim_causa_ext", con=txn, if_exists="append", index=False)
            # dim_edad.to_sql("dim_edad", con=txn, if_exists="append", index=False)

            # Selección de columnas para la tabla de hechos
            fact_cols = [
                "Cod_IPS",
                "ID",
                "Fecha_Ingreso",
                "Fecha_Egreso",
                "Duracion_Dias",
                "via_ingreso_id",
                "estado_salida_id",
                "municipio_id",
                "causa_ext_id",
                "departamento_id",
                "VIA INGRESO",
                "Estado_Salida",
                "EDAD",
                "UNIDAD EDAD",
                "MUNICIPIO",
                "CAUSA EXT",
                "DEPARTAMENTO",
                "DIAGNOSTICO INGRESO",
                "Cod_Dx_Ppal_Egreso",
                "DIAG EGRESO REL 1",
                "DIAG EGRESO REL 2",
                "DIAG EGRESO REL 3",
                "DIAG COMPLICACION",
                "DIAG MUERTE",
                "AÑO",
            ]
            fact[fact_cols].to_sql(
                "fact_atenciones", con=txn, if_exists="append", index=False
            )
            logger.success("✅ Datos cargados correctamente con claves enlazadas.")
    except Exception as e:
        logger.error(f"❌ Error durante la carga de hechos: {e}")
        return False

    return True


# **Creación de Base de Datos**
# ======================================================
# Función: crear_base_datos
# ======================================================
def crear_base_datos():
    logger.info("Va a crear la conexión al motor de Base de datos...")
    engine_db = crear_conexion()

    if probar_conexion(engine_db):
        logger.success("Funciona la conexión...")

    # Validar si la BD existe y no crearla
    if not probar_conexion(engine_db, MYSQL_DB):
        ddl_statements = [
            f"CREATE DATABASE IF NOT EXISTS `{MYSQL_DB}` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;",
            f"USE `{MYSQL_DB}`;",
            # Dimensiones
            """
            CREATE TABLE IF NOT EXISTS dim_via_ingreso (
            via_ingreso_id   INT AUTO_INCREMENT PRIMARY KEY,
            via_ingreso_cod  SMALLINT NOT NULL,
            via_ingreso_desc VARCHAR(50)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """,
            """
            CREATE TABLE IF NOT EXISTS dim_estado_salida (
            estado_salida_id   INT AUTO_INCREMENT PRIMARY KEY,
            estado_salida_cod  VARCHAR(30) NOT NULL,
            estado_salida_desc VARCHAR(60)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """,
            """
            CREATE TABLE IF NOT EXISTS dim_causa_ext (
            causa_ext_id   INT AUTO_INCREMENT PRIMARY KEY,
            causa_ext_cod  SMALLINT NOT NULL,
            causa_ext_desc VARCHAR(60)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """,
            """
            CREATE TABLE IF NOT EXISTS dim_departamento (
            departamento_id   INT AUTO_INCREMENT PRIMARY KEY,
            departamento_cod  CHAR(2) NOT NULL,
            departamento_desc VARCHAR(60)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """,
            """
            CREATE TABLE IF NOT EXISTS dim_municipio (
            municipio_id     INT AUTO_INCREMENT PRIMARY KEY,
            municipio_dane   CHAR(5) NOT NULL,
            departamento_cod CHAR(2) NOT NULL,
            municipio_desc   VARCHAR(80)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """,
            """
            CREATE TABLE IF NOT EXISTS dim_edad (
            edad_id          INT AUTO_INCREMENT PRIMARY KEY,
            EDAD             SMALLINT,
            unidad_edad_cod  SMALLINT,         -- 1=Años, 2=Meses, 3=Días
            UNIDAD_EDAD_TXT  CHAR(1),
            edad_anios       DECIMAL(6,3)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """,
            # Hechos
            """
            CREATE TABLE IF NOT EXISTS fact_atenciones (
            fact_id              BIGINT AUTO_INCREMENT PRIMARY KEY,
            Cod_IPS              VARCHAR(20) NOT NULL,
            ID                   VARCHAR(40) NOT NULL,
            Fecha_Ingreso        DATE,
            Fecha_Egreso         DATE,
            Duracion_Dias        SMALLINT,

            -- Claves foráneas (SK)
            via_ingreso_id       INT,
            estado_salida_id     INT,
            edad_id              INT,
            municipio_id         INT,
            causa_ext_id         INT,
            departamento_id      INT,

            -- Campos de negocio adicionales (opcional mantener originales)
            `VIA INGRESO`        SMALLINT,
            `Estado_Salida`      VARCHAR(30),
            `EDAD`               SMALLINT,
            `UNIDAD EDAD`        SMALLINT,
            `MUNICIPIO`          SMALLINT,
            `CAUSA EXT`          SMALLINT,
            `DEPARTAMENTO`       CHAR(2),
            MUNICIPIO_DANE       CHAR(5),
            `DIAGNOSTICO INGRESO` VARCHAR(255),
            Cod_Dx_Ppal_Egreso   VARCHAR(10),
            `DIAG EGRESO REL 1`  VARCHAR(10),
            `DIAG EGRESO REL 2`  VARCHAR(10),
            `DIAG EGRESO REL 3`  VARCHAR(10),
            `DIAG COMPLICACION`  VARCHAR(10),
            `DIAG MUERTE`        VARCHAR(10),
            `AÑO`                SMALLINT
            
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """,
            # FKs (separadas para evitar problemas de orden y permitir cargas iniciales)
            """
            ALTER TABLE fact_atenciones
            ADD CONSTRAINT fk_fact_via     FOREIGN KEY (via_ingreso_id)   REFERENCES dim_via_ingreso(via_ingreso_id),
            ADD CONSTRAINT fk_fact_estado  FOREIGN KEY (estado_salida_id) REFERENCES dim_estado_salida(estado_salida_id),
            ADD CONSTRAINT fk_fact_causa   FOREIGN KEY (causa_ext_id)     REFERENCES dim_causa_ext(causa_ext_id),
            ADD CONSTRAINT fk_fact_depto   FOREIGN KEY (departamento_id)  REFERENCES dim_departamento(departamento_id),
            ADD CONSTRAINT fk_fact_muni    FOREIGN KEY (municipio_id)     REFERENCES dim_municipio(municipio_id),
            ADD CONSTRAINT fk_fact_edad    FOREIGN KEY (edad_id)          REFERENCES dim_edad(edad_id);
            """,
        ]

        try:
            # Ejecutar DDL
            with engine_db.connect() as conn:
                for stmt in ddl_statements:
                    for sub in [s for s in stmt.split(";") if s.strip()]:
                        conn.execute(text(sub + ";"))
            logger.success("✅ Base de datos creada, tablas generadas")
        except Exception as e:
            print(f"Ocurrió un error: {e}")
            logger.error(f"Ocurrió un error: {e}")

    return
