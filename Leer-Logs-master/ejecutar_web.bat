@echo off
cd /d "%~dp0"

if not exist "venv" (
    echo ERROR: El entorno virtual no existe.
    echo Ejecuta primero setup_venv.bat para crearlo.
    pause
    exit /b 1
)

call venv\Scripts\streamlit run web_backup_monitor.py
