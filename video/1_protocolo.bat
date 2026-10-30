@echo off
chcp 65001 >nul
cd /d "%~dp0.."
set HF_HUB_OFFLINE=1
set PYTHONIOENCODING=utf-8
cls
echo ==============================================================
echo  PASO 1 - Cómo se evalúa (protocolo, igual para todas las estrategias)
echo ==============================================================
python src\protocol.py 
echo.
pause
