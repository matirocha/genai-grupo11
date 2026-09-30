@echo off
chcp 65001 >nul
cd /d "%~dp0.."
set HF_HUB_OFFLINE=1
set PYTHONIOENCODING=utf-8
cls
echo ==============================================================
echo  PASO 3 - Caso de falla: stress_04
echo ==============================================================
python src\demo.py --set stress --instance stress_04 --solo-solucion
echo.
pause
