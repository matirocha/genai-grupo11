@echo off
chcp 65001 >nul
cd /d "%~dp0.."
set HF_HUB_OFFLINE=1
set PYTHONIOENCODING=utf-8
cls
echo ==============================================================
echo  PASO 4 - Por que falla stress_04
echo ==============================================================
python src\diagnose.py --set stress --model llama-3.2-3b --instance stress_04
echo.
pause
