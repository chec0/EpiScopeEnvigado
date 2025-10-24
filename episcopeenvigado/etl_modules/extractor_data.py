# Importar bibliotecas necesarias
import pandas as pd


# **01. Carga de Datos**
def cargar_datos(input_path):
    try:
        data = pd.read_excel(input_path)
        print("Datos cargados correctamente de archivo local!")
    except FileNotFoundError:
        print(f"Error: El archivo no ha sido encontrado en la ruta: {input_path}")
    except Exception as e:
        print(f"Ocurrió otro error: {e}")

    return data
