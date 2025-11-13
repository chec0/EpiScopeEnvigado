# 🧠 EpiScopeEnvigad
## Proyecto Final Talento Tech - Análisis de Datos Innovador

<a target="_blank" href="https://cookiecutter-data-science.drivendata.org/">
    <img src="https://img.shields.io/badge/CCDS-Project%20template-328F97?logo=cookiecutter" />
</a>

Es un proyecto de analítica predictiva que aprovecha los registros individuales de prestación de servicios de salud —los RIPS 2023 y 2024— para detectar patrones en los diagnósticos CIE-10 y anticipar tendencias. En otras palabras, nos permite ver lo que está por ocurrir.

---

## 📘 Descripción general

Este repositorio sigue la estructura de **[Cookiecutter Data Science](https://drivendata.github.io/cookiecutter-data-science/)** con una configuración de entorno moderna que utiliza [`uv`](https://github.com/astral-sh/uv) como gestor de paquetes y entornos virtuales.

Proporciona una base reproducible, modular y colaborativa para desarrollar proyectos de ciencia de datos en Python.

---

## 🗂️ Estructura del proyecto
```
EPISCOPEENVIGADO
├── .venv/                  <- Entorno virtual creado automáticamente por uv
│
├── data
│   ├── processed           <- Conjuntos de datos finales y listos para modelar.
│   └── raw                 <- Datos originales, sin procesar e inmutables.
│
├── docs                    <- Documento final del proyecto.
│
├── episcopeenvigado        <- Proceso ETL y modelos.
│   ├── init.py             <- Convierte episcopeenvigado en un módulo de Python.
│   ├── app.py              <- Modulo principal del proyecto.
│   ├── config.py           <- Variables globales, rutas, parámetros de configuración.
│   ├── dataset.py          <- Scripts para descargar o generar datos.
│   └── diagnosticoOp.py    <- Modulo para el análisis de coocurrencias.
│   
├── notebooks               <- Notebooks de Jupyter de soporte para los procesos y las validaciones.
│
├── streamlit_app           <- Creación del dashboard de visualización y exploración interactiva en Streamlit 
│
├── .gitignore              <- Ignora .venv/, data grandes, checkpoints, etc.
│
├── Makefile                <- Makefile con comandos útiles como make data o make train
│
├── pyproject.toml          <- Dependencias del proyecto (gestionadas con uv)
│
├── README.md               <- Archivo principal de documentación.
│
├── setup.cfg               <- Archivo de configuración para flake8
│
└── uv.lock                 <- Archivo de bloqueo con versiones exactas de dependencias
```
---
## ⚙️ Instrucciones de configuración

### 1. Clonar el repositorio
```bash
git clone https://github.com/chec0/EpiScopeEnvigado.git
cd <nombre_del_repositorio>
```
### 2. Instalar dependencias con uv

```bash
uv sync
```
Esto realizará lo siguiente:
* Creará un entorno virtual en .venv/
* Instalará todas las dependencias definidas en pyproject.toml
* Bloqueará las versiones exactas en uv.lock

Si aún no tienes instalado uv:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

🧩 Uso del proyecto

Activar el entorno:

```bash
uv run python
```