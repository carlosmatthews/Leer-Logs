import os
import subprocess
from datetime import datetime

# Configuración
logs_folder = os.path.join(os.path.expanduser('~'), 'Desktop', 'Logs')  # Ruta a la carpeta de logs
keywords = ['error', 'fail', 'warning', 'critical', 'exception']  # Palabras clave para buscar
seven_zip_path = r'C:\Program Files\7-Zip\7z.exe'  # Ruta al ejecutable de 7-Zip

# Crear el archivo de salida con la fecha actual
output_file = os.path.join(logs_folder, f"Logs_status_{datetime.now().strftime('%Y%m%d')}.txt")

# Función para escribir en el archivo y en la consola
def log_message(message):
    with open(output_file, 'a', encoding='utf-8') as f:
        f.write(message + '\n')
    print(message)  # Mostrar también en la consola

# Función para buscar errores en un archivo
def search_errors_in_file(file_path):
    print("###############################", file_path)
    errors_found = []
    with open(file_path, 'r', encoding='utf-8') as file:
        for line_number, line in enumerate(file, start=1):
            # Ignorar líneas con "INFO"
            if "INFO" in line:
                continue
            # Buscar palabras clave
            if any(keyword.lower() in line.lower() for keyword in keywords):
                errors_found.append((line_number, line.strip()))
    return errors_found

# Función para descomprimir archivos con 7-Zip
def decompress_with_7zip(file_path, extract_folder):
    try:
        # Comando para descomprimir con 7-Zip
        command = [seven_zip_path, 'x', file_path, f'-o{extract_folder}', '-y']
        subprocess.run(command, check=True)
        log_message(f"Archivo {os.path.basename(file_path)} descomprimido en {extract_folder}.")
    except subprocess.CalledProcessError as e:
        log_message(f"Error al descomprimir {os.path.basename(file_path)}: {e}")

# Recorrer todos los archivos en la carpeta de logs
for root, dirs, files in os.walk(logs_folder):
    for file_name in files:
        if file_name.endswith('.txt') and file_name.startswith('Logs_status'):
            pass
        
        file_path = os.path.join(root, file_name)
        
        # Descomprimir si es un archivo comprimido 
        if file_name.endswith('.zip') or file_name.endswith('.7z'):
            extract_folder = os.path.join(root, 'extracted')
            os.makedirs(extract_folder, exist_ok=True)  # Crear carpeta para extraer
            decompress_with_7zip(file_path, extract_folder)
            
            # Analizar los archivos extraídos
            for extracted_root, _, extracted_files in os.walk(extract_folder):
                for extracted_file in extracted_files:
                    extracted_file_path = os.path.join(extracted_root, extracted_file)
                    log_message(f"Analizando archivo extraído: {extracted_file}...")
                    
                    errors = search_errors_in_file(extracted_file_path)
                    if errors:
                        log_message(f"Se encontraron {len(errors)} errores en {extracted_file}:")
                        for line_number, error_line in errors:
                            log_message(f"  Línea {line_number}: {error_line}")
                    else:
                        log_message(f"No se encontraron errores en {extracted_file}.")
                    log_message("-" * 50)  # Separador entre archivos
        if file_name.endswith('log'):
            # Analizar archivos no comprimidos
            log_message(f"Analizando archivo: {file_name}...")
            
            errors = search_errors_in_file(file_path)
            if errors:
                log_message(f"Se encontraron {len(errors)} errores en {file_name}:")
                for line_number, error_line in errors:
                    log_message(f"  Línea {line_number}: {error_line}")
            else:
                log_message(f"No se encontraron errores en {file_name}.")
            log_message("-" * 50)  # Separador entre archivos



