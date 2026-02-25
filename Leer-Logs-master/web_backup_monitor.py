import os
import streamlit as st
from datetime import datetime
import subprocess

st.set_page_config(page_title="Monitor de Backups", layout="wide")

def get_backup_list():
    from copy_logs_files import nombre_ultimo_backup
    return list(dict.fromkeys(nombre_ultimo_backup))

def get_latest_log_file(logs_folder):
    if not os.path.exists(logs_folder):
        return None
    log_files = []
    for f in os.listdir(logs_folder):
        if f.startswith('Logs_status') and f.endswith('.txt'):
            log_files.append(os.path.join(logs_folder, f))
    if log_files:
        return max(log_files, key=os.path.getmtime)
    return None

def load_results(logs_folder, backup_list):
    backup_data = {bp: {'errores': [], 'tiene_backup': False, 'archivo': '', 'es_parcial': False} for bp in backup_list}
    
    latest_file = get_latest_log_file(logs_folder)
    current_backup = None
    
    if latest_file and os.path.exists(latest_file):
        with open(latest_file, 'r', encoding='utf-8') as f:
            for line in f:
                line_stripped = line.strip()
                
                if line_stripped.startswith("Analizando archivo:"):
                    filename = line_stripped.replace("Analizando archivo:", "").strip().replace("...", "")
                    current_backup = None
                    for bp in backup_list:
                        if filename.startswith(bp):
                            backup_data[bp]['tiene_backup'] = True
                            backup_data[bp]['archivo'] = filename
                            current_backup = bp
                            break
                
                elif "code 23" in line_stripped:
                    if current_backup and current_backup in backup_data:
                        backup_data[current_backup]['es_parcial'] = True
                
                elif line_stripped.startswith("Línea ") and "rsync error:" not in line_stripped:
                    if current_backup and current_backup in backup_data:
                        mensaje = line_stripped.split(":", 1)[1].strip() if ":" in line_stripped else line_stripped
                        backup_data[current_backup]['errores'].append({
                            'linea': line_stripped.split()[1].replace(":", ""),
                            'mensaje': mensaje[:200]
                        })
    
    return backup_data, latest_file

def run_monitoring(logs_folder):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    script_path = os.path.join(script_dir, 'readlogs02.py')
    if os.path.exists(script_path):
        subprocess.run(['python', script_path, logs_folder], check=True, cwd=script_dir)
        return True
    return False

st.title("📊 Monitor de Estado de Backups")

logs_folder = os.path.join(os.path.expanduser('~'), 'Desktop', "Leer-Logs-master", 'Logs')

with st.sidebar:
    st.header("Configuración")
    
    selected_folder = st.text_input("Carpeta de Logs:", value=logs_folder)
    
    if st.button("Ejecutar Monitoreo", type="primary"):
        with st.spinner("Ejecutando monitoreo..."):
            success = run_monitoring(selected_folder)
            if success:
                st.success("Monitoreo completado!")
            else:
                st.error("Error al ejecutar monitoreo")
    
    if st.button("Actualizar"):
        st.rerun()

backup_list = get_backup_list()
backup_data, latest_file = load_results(selected_folder, backup_list)

if latest_file:
    file_time = datetime.fromtimestamp(os.path.getmtime(latest_file))
    st.caption(f"Última actualización: {file_time.strftime('%Y-%m-%d %H:%M:%S')}")

backups_found = sum(1 for d in backup_data.values() if d['tiene_backup'])
partial_count = sum(1 for d in backup_data.values() if d.get('es_parcial'))
real_errors_count = sum(1 for d in backup_data.values() if d['errores'] and not d.get('es_parcial'))

col1, col2, col3 = st.columns(3)
col1.metric("Backups encontrados", backups_found)
col2.metric("Parciales (code 23)", partial_count, delta_color="off")
col3.metric("Errores reales", real_errors_count, delta_color="inverse")

st.divider()

st.subheader("📁 Backups")

for bp in backup_list:
    data = backup_data[bp]
    backup_name = bp.replace('-', ' → ').replace('_', ' ').strip().upper()
    backup_name = backup_name[:-1] if backup_name.endswith(' → ') else backup_name
    
    with st.expander(f"{backup_name}", expanded=bool(data.get('errores')) or not data['tiene_backup']):
        if not data['tiene_backup']:
            st.error("✗ Sin backup")
        elif data.get('es_parcial'):
            st.warning(f"⚠ Parcial ({len(data['errores'])} archivos no transferidos)")
            if data['errores']:
                for e in data['errores'][:5]:
                    st.text(f"Línea {e['linea']}: {e['mensaje'][:100]}...")
                if len(data['errores']) > 5:
                    st.caption(f"... y {len(data['errores']) - 5} más")
        elif data['errores']:
            st.error(f"✗ Error ({len(data['errores'])} errores)")
            for e in data['errores'][:5]:
                st.text(f"Línea {e['linea']}: {e['mensaje'][:100]}...")
        else:
            st.success("✓ Sin errores")
            st.caption(f"Archivo: {data['archivo']}")
