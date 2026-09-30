@echo off
chcp 65001 >nul
cd /d "%~dp0.."
set HF_HUB_OFFLINE=1
set PYTHONIOENCODING=utf-8
cls
echo ==============================================================
echo  PASO 1 - Linea base vs solucion (instancia elegida al azar)
echo ==============================================================
python src\demo.py --random
echo.
pause
