"""Paso 4 del video de Deliverable 3: Análisis general de fallas y caso de falla."""
import os
import runpy
import sys

SCRIPT = "report.py"
ARGS = ['--fallas']

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("HF_HUB_OFFLINE", "1")
sys.stdout.reconfigure(encoding="utf-8")
os.chdir(ROOT)
sys.path.insert(0, os.path.join(ROOT, "src"))
sys.argv = [SCRIPT, *ARGS]
runpy.run_path(os.path.join(ROOT, "src", SCRIPT), run_name="__main__")
