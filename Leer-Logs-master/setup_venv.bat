@echo off
echo ========================================
echo   Configuracion de Entorno Virtual
echo ========================================
echo.

cd /d "%~dp0"

REM Verificar si el venv existe y tiene Python
if exist "venv\Scripts\python.exe" (
    echo El entorno virtual ya existe.
) else (
    echo Creando entorno virtual...
    py -m venv venv
    if exist "venv\Scripts\python.exe" (
        echo Entorno virtual creado correctamente.
    ) else (
        echo ERROR: No se pudo crear el entorno virtual.
        echo Asegurate de tener Python instalado.
        pause
        exit /b 1
    )
)

echo.
echo Instalando dependencias...
if exist "venv\Scripts\pip.exe" (
    call venv\Scripts\pip install -r requirements.txt
    if errorlevel 1 (
        echo ERROR: Fallo al instalar dependencias.
        pause
        exit /b 1
    )
) else (
    echo ERROR: No se encontro pip en el entorno virtual.
    pause
    exit /b 1
)

echo.
echo ========================================
echo   Configuracion completada!
echo ========================================
echo.
echo Para ejecutar la GUI:
echo   ejecutar_gui.bat
echo.
echo Para ejecutar la Web:
echo   ejecutar_web.bat
echo.
pause
