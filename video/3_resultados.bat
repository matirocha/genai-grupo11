@echo off
chcp 65001 >nul
cd /d "%~dp0.."
set HF_HUB_OFFLINE=1
set PYTHONIOENCODING=utf-8
cls
echo ==============================================================
echo  PASO 3 - Resultados: línea base, D2, agentes y ablaciones (mismas 90 instancias)
echo ==============================================================
python src\report.py 
echo.
pause
