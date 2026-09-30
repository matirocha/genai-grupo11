"""Paso 4 del video: diagnóstico de por qué falla la solución de Deliverable 2 en stress_04."""
import os
import runpy
import sys

SCRIPT = "diagnose.py"
ARGS = ["--set", "stress", "--model", "llama-3.2-3b", "--instance", "stress_04"]

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("HF_HUB_OFFLINE", "1")
sys.stdout.reconfigure(encoding="utf-8")
os.chdir(ROOT)
sys.path.insert(0, os.path.join(ROOT, "src"))
sys.argv = [SCRIPT, *ARGS]
runpy.run_path(os.path.join(ROOT, "src", SCRIPT), run_name="__main__")
