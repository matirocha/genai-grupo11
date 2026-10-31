@echo off
chcp 65001 >nul
cd /d "%~dp0.."
set PYTHONIOENCODING=utf-8
cls
echo ==============================================================
echo  PASO 2 - Sistema de agentes en vivo sobre hard_29 (D2 falla, los agentes no)
echo ==============================================================
python src\demo_agents.py --set hard --instance hard_29
echo.
pause
