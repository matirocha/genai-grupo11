@echo off
chcp 65001 >nul
cd /d "%~dp0.."
set HF_HUB_OFFLINE=1
set PYTHONIOENCODING=utf-8
cls
echo ==============================================================
echo  PASO 2 - Resultados sobre las 30 instancias
echo ==============================================================
python src\evaluate.py --summary --only llama-3.2-3b,no_llm
echo.
pause
