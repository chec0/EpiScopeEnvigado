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
├── LICENSE            <- Licencia de código abierto (si aplica)
├── Makefile           <- Makefile con comandos útiles como make data o make train
├── README.md          <- Archivo principal de documentación para desarrolladores. Estás aquí 🚀
├── data
│   ├── external       <- Datos provenientes de fuentes externas.
│   ├── interim        <- Datos intermedios que han sido transformados.
│   ├── processed      <- Conjuntos de datos finales y listos para modelar.
│   └── raw            <- Datos originales, sin procesar e inmutables.
│
├── docs               <- Proyecto base para documentación con mkdocs; ver www.mkdocs.org para más detalles
│
├── models             <- Modelos entrenados y serializados, predicciones o resúmenes de modelos
│
├── notebooks          <- Notebooks de Jupyter. Convención de nombres: número (para ordenar),
│                         iniciales del autor y una breve descripción separada por guiones, por ejemplo:
│                         1.0-jqp-exploracion-inicial-datos.
│
├── pyproject.toml     <- Dependencias del proyecto (gestionadas con uv)
│
├── references         <- Diccionarios de datos, manuales y otros materiales de referencia.
│
├── reports            <- Análisis generados en formato HTML, PDF, LaTeX, etc.
│   └── figures        <- Gráficos y figuras generadas para los reportes
│
├── requirements.txt   <- Archivo de dependencias para reproducir el entorno de análisis, por ejemplo:
│                         generado con pip freeze > requirements.txt
│
├── setup.cfg          <- Archivo de configuración para flake8
│
└── {{ cookiecutter.module_name }}   <- Código fuente utilizado en este proyecto.
│
├── init.py             <- Convierte {{ cookiecutter.module_name }} en un módulo de Python
│
├── config.py               <- Variables y configuraciones útiles
│
├── dataset.py              <- Scripts para descargar o generar datos
│
├── features.py             <- Código para crear características (features) para modelado
│
├── modeling
│   ├── init.py
│   ├── predict.py          <- Código para ejecutar inferencias con modelos entrenados
│   └── train.py            <- Código para entrenar modelos
│
└── plots.py                <- Código para generar visualizaciones
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