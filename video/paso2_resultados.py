"""Paso 2 del video: resultados de Deliverable 1 y Deliverable 2 sobre las 30 instancias y las 30 de estrés."""
import os
import runpy
import sys

SCRIPT = "evaluate.py"
ARGS = ["--summary", "--only", "llama-3.2-3b,no_llm"]

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("HF_HUB_OFFLINE", "1")
sys.stdout.reconfigure(encoding="utf-8")
os.chdir(ROOT)
sys.path.insert(0, os.path.join(ROOT, "src"))
sys.argv = [SCRIPT, *ARGS]
runpy.run_path(os.path.join(ROOT, "src", SCRIPT), run_name="__main__")
