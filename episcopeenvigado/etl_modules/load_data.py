# Importar bibliotecas necesarias
import pandas as pd
import numpy as np
import pymysql
import re
from io import StringIO
from sqlalchemy import create_engine, text
from urllib.parse import quote_plus
from etl_modules._config import (
    MYSQL_USER,
    MYSQL_HOST,
    MYSQL_PORT,
    MYSQL_DB,
    MYSQL_PASSWORD_URL,
)


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
def probar_conexion(engine):
    """
    Ejecuta una consulta simple para verificar la conexión a la base de datos.

    Parámetros
    ----------
    engine : sqlalchemy.Engine
        Motor de conexión a la base de datos.

    Comportamiento
    --------------
    - Ejecuta el comando SQL `SELECT NOW();` para obtener la fecha/hora del servidor.
    - Si la conexión es exitosa, imprime el resultado en consola.
    - Si falla, lanzará una excepción capturada por SQLAlchemy.

    Retorna
    -------
    None
        La función no retorna ningún valor; imprime la fecha actual del servidor.

    Ejemplo
    -------
    >>> engine = crear_conexion(bd=True)
    >>> probar_conexion(engine)
    ('2025-10-16 21:48:00',)

    """
    with engine.connect() as conn:
        result = conn.execute(text("SELECT NOW();"))
        for row in result:
            print(row)


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


# **Creación de Base de Datos**
def preparacion_dataset(df, engine_db):
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

    ##############################################################################################
    #                                                                                             #
    # 🚨🚨🚨  L E E R   A N T E S   D E   E J E C U T A R   🚨🚨🚨
    # ------------------------------------------------------------------------------------------- #
    # ⚠️
    # ⚠️  NOS FALTA CARGAR LA TABLA DE MUNICIPIOS Y DEPARTAMENTOS                                 #
    # ⚠️  Cualquier error aquí puede afectar la ejecución completa de la carga.                   #
    # ------------------------------------------------------------------------------------------- #
    # 💡  Sugerencia: marca esta sección con un bookmark en VS Code (Ctrl+K, Ctrl+L)              #
    # 💡  o agrega un TODO para revisarla antes de correr el proceso.                             #
    #                                                                                             #
    ##############################################################################################

    CAT_DEPARTAMENTO = {"05": "ANTIOQUIA"}
    # Si tienes nombres de municipio, cárgalos aquí. Ejemplo:
    CAT_MUNICIPIO_DANE = {
        "05266": "ENVIGADO"  # demo; ajusta a tu catálogo
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

    # --- dim_departamento ---
    dim_depto = (
        df[["DEPARTAMENTO"]]
        .dropna()
        .drop_duplicates()
        .sort_values(by="DEPARTAMENTO")
        .rename(columns={"DEPARTAMENTO": "departamento_cod"})
        .assign(departamento_desc=lambda d: d["departamento_cod"].map(CAT_DEPARTAMENTO))
        .reset_index(drop=True)
    )
    dim_depto.insert(0, "departamento_id", range(1, len(dim_depto) + 1))

    # --- dim_municipio ---
    # Clave natural preferida: DANE (5 dígitos). También guardamos dep/muni separados.
    dim_muni = (
        df[["MUNICIPIO_DANE", "DEPARTAMENTO", "MUNICIPIO"]]
        .dropna()
        .drop_duplicates()
        .sort_values(by="MUNICIPIO_DANE")
        .rename(
            columns={
                "MUNICIPIO_DANE": "municipio_dane",
                "DEPARTAMENTO": "departamento_cod",
                "MUNICIPIO": "municipio_cod",
            }
        )
        .assign(municipio_desc=lambda d: d["municipio_dane"].map(CAT_MUNICIPIO_DANE))
        .reset_index(drop=True)
    )
    dim_muni.insert(0, "municipio_id", range(1, len(dim_muni) + 1))

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
    map_depto = dict(zip(dim_depto["departamento_cod"], dim_depto["departamento_id"]))
    map_muni = dict(zip(dim_muni["municipio_dane"], dim_muni["municipio_id"]))

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
    fact["municipio_id"] = fact["MUNICIPIO_DANE"].map(map_muni)
    fact["edad_id"] = list(
        zip(fact["EDAD"].astype("Int64"), fact["UNIDAD EDAD"].astype("Int64"))
    )
    fact["edad_id"] = fact["edad_id"].map(map_edad)

    # =========================
    # 8) CARGA DE DIMENSIONES Y HECHOS
    # =========================
    # Usamos to_sql con if_exists='append'; como ya existen las tablas, respeta las columnas
    try:
        with engine_db.begin() as txn:
            dim_via.to_sql("dim_via_ingreso", con=txn, if_exists="append", index=False)
            dim_estado.to_sql(
                "dim_estado_salida", con=txn, if_exists="append", index=False
            )
            dim_causa.to_sql("dim_causa_ext", con=txn, if_exists="append", index=False)
            dim_depto.to_sql(
                "dim_departamento", con=txn, if_exists="append", index=False
            )
            dim_muni.to_sql("dim_municipio", con=txn, if_exists="append", index=False)
            dim_edad.to_sql("dim_edad", con=txn, if_exists="append", index=False)

            # Selección de columnas para la tabla de hechos
            fact_cols = [
                "Cod_IPS",
                "ID",
                "Fecha_Ingreso",
                "Fecha_Egreso",
                "Duracion_Dias",
                "via_ingreso_id",
                "estado_salida_id",
                "edad_id",
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
                "MUNICIPIO_DANE",
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
    except Exception as e:
        print(f"Ocurrió otro error: {e}")

    return True


def crear_base_datos(df):
    print("Va a crear la conexión al motor de Base de datos...")
    engine_db = crear_conexion()

    probar_conexion(engine_db)
    print("Funciona la conexión...")

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
        municipio_cod    SMALLINT,
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
        `AÑO`                SMALLINT,

        UNIQUE KEY uq_fact (Cod_IPS, ID)
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

    # Ejecutar DDL
    with engine_db.connect() as conn:
        for stmt in ddl_statements:
            for sub in [s for s in stmt.split(";") if s.strip()]:
                conn.execute(text(sub + ";"))
    print("✅ Base de datos creada, tablas generadas")

    print("Preparación de Datos...")
    preparacion_dataset(df, engine_db)

    print("Datos cargados correctamente.")
    return True
