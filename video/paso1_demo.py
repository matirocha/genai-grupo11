"""Paso 1 del video: línea base de Deliverable 1 vs solución de Deliverable 2 en una instancia al azar."""
import os
import runpy
import sys

SCRIPT = "demo.py"
ARGS = ["--random"]

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("HF_HUB_OFFLINE", "1")
sys.stdout.reconfigure(encoding="utf-8")
os.chdir(ROOT)
sys.path.insert(0, os.path.join(ROOT, "src"))
sys.argv = [SCRIPT, *ARGS]
runpy.run_path(os.path.join(ROOT, "src", SCRIPT), run_name="__main__")
