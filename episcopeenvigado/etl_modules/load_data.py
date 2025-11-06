# Importar bibliotecas necesarias
from pathlib import Path
import pandas as pd
import numpy as np
import pymysql
import re
from io import StringIO
from sqlalchemy import Engine, create_engine, text
from sqlalchemy.exc import OperationalError
from urllib.parse import quote_plus
from etl_modules._config import (
    MYSQL_USER,
    MYSQL_HOST,
    MYSQL_PORT,
    MYSQL_DB,
    MYSQL_PASSWORD_URL,
)

from episcopeenvigado.config import PROCESSED_DATA_DIR, RAW_DATA_DIR
from episcopeenvigado.etl_modules import extractor_data as ed
from episcopeenvigado.etl_modules import transform_data as td
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
    except OperationalError as e:
        if e.orig.args[0] == 1049:
            logger.warning(f"[Error 1049] La base de datos {e.orig.args} no existe.")
        else:
            logger.error(f" No se pudo establecer/verificar la conexión: {e.orig.args}")
        return False
    except Exception as e:
        logger.error(f"[ERROR] Inesperado: {e}")
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
def cargar_departamentos(ruta_archivo: str, hoja: str = None) -> pd.DataFrame:
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

    dim_depto = obtener_dimensiones_existentes("dim_departamento")
    if dim_depto.empty:
        df_depto = ed.extraer_departamentos(ruta_archivo)
        df_depto_limpio = td.limpieza_departamentos(df_depto)

        # Insertar en la base de datos
        engine_db = crear_conexion(bd=True)
        try:
            with engine_db.begin() as conn:
                df_depto_limpio.to_sql(
                    "dim_departamento", con=conn, if_exists="append", index=False
                )
            logger.success(
                f"Datos cargados en dim_departamento ({len(df_depto_limpio)} registros)"
            )
            return df_depto_limpio
        except Exception as e:
            logger.error(f"Error al insertar en dim_departamento: {e}")

    return dim_depto


# ======================================================
# Función: cargar_municipios
# ======================================================
def cargar_municipios(ruta_archivo, hoja: str = None) -> pd.DataFrame:
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

    dim_muni = obtener_dimensiones_existentes("dim_municipio")
    if dim_muni.empty:
        df_muni = ed.extraer_municipios(ruta_archivo)
        df_muni_limpio = td.limpieza_municipios(df_muni)

        # Insertar en la base de datos
        engine_db = crear_conexion(bd=True)
        try:
            with engine_db.begin() as conn:
                df_muni_limpio.to_sql(
                    "dim_municipio", con=conn, if_exists="append", index=False
                )
            logger.success(
                f"Datos cargados en dim_municipio ({len(df_muni_limpio)} registros)"
            )
            return df_muni_limpio
        except Exception as e:
            logger.error(f"Error al insertar en dim_municipio: {e}")

    return dim_muni


# ======================================================
# Función: cargar_cie10
# ======================================================
def cargar_cie10(ruta_archivo: str, hoja: str = "Final") -> pd.DataFrame:
    """
    Carga el catálogo CIE-10 (Clasificación Internacional de Enfermedades, 10ª revisión)
    en la tabla `dim_cie10` de la base de datos MySQL.

    Esta función forma parte del proceso ETL para poblar la tabla de dimensión
    `dim_cie10`, la cual almacena información jerárquica y descriptiva de los
    códigos CIE-10 usados para clasificar diagnósticos médicos.

    Flujo de ejecución
    ------------------
    1. Crea una conexión a la base de datos mediante `crear_conexion(bd=True)`.
    2. Verifica si la tabla `dim_cie10` ya contiene registros:
         - Si existen datos, no realiza recarga y retorna un DataFrame vacío.
         - Si no existe o está vacía, continúa el proceso.
    3. Extrae los datos desde el archivo Excel utilizando `ed.extraer_cie10()`.
    4. Limpia y transforma los datos usando `td.limpieza_cie10()`.
    5. Crea la tabla `dim_cie10` en MySQL si no existe, con su estructura estándar.
    6. Inserta los datos procesados en la tabla mediante `pandas.to_sql()`.
    7. Registra en el log el resultado del proceso (éxito o error).

    Parámetros
    ----------
    ruta_archivo : str
        Ruta completa o relativa del archivo Excel que contiene el catálogo CIE-10.
        Ejemplo: `'data/raw/CIE10_Catalogo.xlsx'`
    hoja : str, opcional
        Nombre de la hoja dentro del archivo Excel a leer.
        Por defecto es `"Final"`.

    Retorna
    -------
    pandas.DataFrame
        DataFrame con los registros del catálogo CIE-10 cargados correctamente.
        Si la tabla ya existe con datos o ocurre un error, retorna un DataFrame vacío.

    Excepciones
    -----------
    Exception
        Captura cualquier error ocurrido durante la verificación, creación o inserción
        de datos en la tabla `dim_cie10`.

    Ejemplo
    -------
    >>> df_cie10 = cargar_cie10("data/raw/CIE10_Catalogo.xlsx", hoja="Final")
    📂 Extrayendo catálogo CIE-10...
    ✅ Catálogo CIE-10 cargado correctamente (14,400 registros)

    Notas
    -----
    - La tabla `dim_cie10` incluye información jerárquica por capítulos y categorías
      de diagnóstico, junto con campos adicionales (`extra_i_aplicaASexo`, `extra_ii_edadMinima`, etc.)
      que permiten validar condiciones específicas de cada código.
    - Si la tabla ya contiene datos, el proceso se omite para evitar duplicados.
    """
    engine_db = crear_conexion(bd=True)

    # Verificar si la tabla ya tiene datos
    try:
        with engine_db.begin() as conn:
            existing = pd.read_sql("SELECT COUNT(*) AS n FROM dim_cie10;", con=conn)
            if existing["n"].iloc[0] > 0:
                logger.info("ℹ️ La tabla dim_cie10 ya contiene datos, no se recargará.")
                return pd.DataFrame()
    except Exception:
        logger.info(
            "⚠️ La tabla dim_cie10 no existe aún o no tiene datos. Se creará y poblará."
        )

    # Extraer y transformar
    df_raw = ed.extraer_cie10(ruta_archivo, hoja)
    df_limpio = td.limpieza_cie10(df_raw)

    # Crear tabla si no existe
    ddl = """
    CREATE TABLE IF NOT EXISTS dim_cie10 (
    cie_4cat             VARCHAR(10) PRIMARY KEY,
    capitulo             SMALLINT,
    nombre_cap           VARCHAR(255),
    cie_3cat             VARCHAR(10),
    desc_3cat            TEXT,
    desc_4cat            TEXT,
    extra_i_aplicaASexo  VARCHAR(10),
    extra_ii_edadMinima  SMALLINT,
    extra_iii_edadMaxima SMALLINT,
    extra_viii_subGrupo  VARCHAR(50),
    extra_x_sexo         VARCHAR(10)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """

    try:
        with engine_db.begin() as conn:
            conn.execute(text(ddl))
            df_limpio.to_sql("dim_cie10", con=conn, if_exists="append", index=False)
        logger.success(
            f"✅ Catálogo CIE-10 cargado correctamente ({len(df_limpio)} registros)"
        )
        return df_limpio
    except Exception as e:
        logger.error(f"❌ Error al cargar catálogo CIE-10: {e}")
        return pd.DataFrame()


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
        return 0

    # Convertir según unidad
    if unidad == 1:  # Años
        return float(edad)
    if unidad == 2:  # Meses → años
        return float(edad) / 12.0
    if unidad == 3:  # Días → años
        return float(edad) / 365.25

    # En caso de unidad desconocida
    return 0


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
    dim_muni = obtener_dimensiones_existentes("dim_municipio")

    df["MUNICIPIO_DANE"] = df["DEPARTAMENTO"].astype(str) + df["MUNICIPIO"].astype(str)

    df["EDAD_ANIOS"] = df.apply(
        lambda r: edad_a_anios(r["EDAD"], r["UNIDAD EDAD"]), axis=1
    )
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
    # 6) TABLA DE HECHOS (con FKs)
    # =========================
    fact = df.copy()

    # FKs a dimensiones
    fact["via_ingreso_id"] = fact["VIA INGRESO"].map(map_via)
    fact["estado_salida_id"] = fact["Estado_Salida"].fillna("NO_INFO").map(map_estado)
    fact["causa_ext_id"] = fact["CAUSA EXT"].map(map_causa)

    fact["departamento_id"] = fact["DEPARTAMENTO"].map(map_depto)
    fact["municipio_id"] = fact["MUNICIPIO_DANE"].map(map_muni)

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
                "EDAD_ANIOS",
                "SEXO",
                "MUNICIPIO_DANE",
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


# ======================================================
# Función: validar_base_datos()
# ======================================================
def validar_base_datos() -> bool:
    engine_db = crear_conexion(bd=True)
    if not probar_conexion(engine_db, MYSQL_DB):
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
            CREATE TABLE IF NOT EXISTS dim_cie10 (
            cie_4cat             VARCHAR(10) PRIMARY KEY,
            capitulo             SMALLINT,
            nombre_cap           VARCHAR(255),
            cie_3cat             VARCHAR(10),
            desc_3cat            TEXT,
            desc_4cat            TEXT,
            extra_i_aplicaASexo  VARCHAR(10),
            extra_ii_edadMinima  SMALLINT,
            extra_iii_edadMaxima SMALLINT,
            extra_viii_subGrupo  VARCHAR(50),
            extra_x_sexo         VARCHAR(10)
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
            municipio_id         INT,
            causa_ext_id         INT,
            departamento_id      INT,

            -- Campos de negocio adicionales (opcional mantener originales)
            `VIA INGRESO`        SMALLINT,
            `Estado_Salida`      VARCHAR(30),
            `EDAD`               SMALLINT,
            `UNIDAD EDAD`        SMALLINT,
            `EDAD_ANIOS`         DECIMAL(6,3),
            `SEXO`               CHAR(1),
            `MUNICIPIO`          SMALLINT,
            `CAUSA EXT`          SMALLINT,
            `DEPARTAMENTO`       CHAR(2),
            `MUNICIPIO_DANE`     CHAR(5),
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
            ADD CONSTRAINT fk_fact_muni    FOREIGN KEY (municipio_id)     REFERENCES dim_municipio(municipio_id);
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
