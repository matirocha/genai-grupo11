"""Paso 2 del video de Deliverable 3: sistema de agentes en vivo sobre hard_22 (actúan los tres agentes: propuestas,
rechazos, sondeos y dos saltos del Diagnosticador; es la misma instancia del caso de falla, para compararla).
La primera ejecución descarga el modelo (por eso este paso no fuerza el modo offline)."""
import os
import runpy
import sys

SCRIPT = "demo_agents.py"
ARGS = ["--set", "hard", "--instance", "hard_22"]

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding="utf-8")
os.chdir(ROOT)
sys.path.insert(0, os.path.join(ROOT, "src"))
sys.argv = [SCRIPT, *ARGS]
runpy.run_path(os.path.join(ROOT, "src", SCRIPT), run_name="__main__")
