@echo off
chcp 65001 >nul
cd /d "%~dp0.."
set PYTHONIOENCODING=utf-8
cls
echo ==============================================================
echo  PRESENTACION HTML del video de Deliverable 3 (ejecuta los pasos 1 a 4)
echo ==============================================================
python video\servidor_video.py
echo.
pause
