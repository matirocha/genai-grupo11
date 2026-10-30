@echo off
chcp 65001 >nul
cd /d "%~dp0.."
set HF_HUB_OFFLINE=1
set PYTHONIOENCODING=utf-8
cls
echo ==============================================================
echo  PASO 4 - Análisis general de fallas y caso de falla
echo ==============================================================
python src\report.py --fallas
echo.
pause
