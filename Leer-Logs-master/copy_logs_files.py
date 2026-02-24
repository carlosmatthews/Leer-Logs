import subprocess
from datetime import datetime
import os, json

# Cargar datos desde secrests.json
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
secrets_file = os.path.join(BASE_DIR, "secrets.json")
with open(secrets_file, "r") as f:
    secrets = json.load(f)

usuario = secrets["usuario"]
host = secrets["host"]
ruta_remota = secrets["ruta_remota"]
ruta_local = secrets["ruta_local"]

def obtener_fecha_formato_yyyymmdd():
    """
    Obtiene la fecha actual y la devuelve en formato YYYYMMDD.
    """
    fecha_actual = datetime.now()
    fecha_formateada = fecha_actual.strftime("%Y%m%d")
    return fecha_formateada
#define los nombres de los archivos de backup a copiar y buscar 
nombre_ultimo_backup = ["BACKUP-04B-TO-03-", "BACKUP-02-TO-04B-", "BACKUP-02-TO-04A-", "BACKUP-01B-TO-04B-", "BACKUP-01A-TO-04A-"]

def ejecutar_scp(usuario, host, ruta_remota, ruta_local):
    """Ejecuta el comando scp para copiar un archivo desde una máquina remota."""
    try:
        comando = [
            'wsl', 'scp',
            f'{usuario}@{host}:{ruta_remota}',
            ruta_local
        ]
        proceso = subprocess.Popen(comando, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        salida, error = proceso.communicate(timeout=15)  # Espera hasta 15 segundos

        if proceso.returncode == 0:
            print("Archivo copiado exitosamente." + ruta_remota )
            print("Salida:", salida.decode())
            return True
        else:
            print("Error al copiar el archivo.")
            print("Error:", error.decode())
            return False

    except FileNotFoundError:
        print("El comando 'scp' no se encontró en el sistema.")
        return False
    except subprocess.TimeoutExpired:
        print("Tiempo de espera agotado durante la ejecución de scp.")
        return False
    except Exception as e:
        print(f"Ocurrió un error: {e}")
        return False
def copy_logs():
    for e in nombre_ultimo_backup:
        # Generar la ruta completa del archivo remoto
        ruta_remota_completa = ruta_remota + e + obtener_fecha_formato_yyyymmdd() + ".log"
        ejecutar_scp(usuario, host, ruta_remota_completa, ruta_local)