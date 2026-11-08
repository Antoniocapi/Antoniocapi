@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo Instalando lo necesario (solo tarda la primera vez)...
python -m pip install -q -r requirements.txt
echo.
python fm.py todo
echo.
echo Listo. Los informes estan en la carpeta "informes".
pause
