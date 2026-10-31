"""Paso 2 del video de Deliverable 3: sistema de agentes en vivo sobre hard_29 (actúan los tres agentes: propuestas,
rechazos, sondeos y dos saltos del Diagnosticador). Es una instancia donde la solución de D2 falla (agota sus 30
retrocesos y queda con 1 violación) y el sistema de agentes llega a un horario certificado y válido.
La primera ejecución descarga el modelo (por eso este paso no fuerza el modo offline)."""
import os
import runpy
import sys

SCRIPT = "demo_agents.py"
ARGS = ["--set", "hard", "--instance", "hard_29"]

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding="utf-8")
os.chdir(ROOT)
sys.path.insert(0, os.path.join(ROOT, "src"))
sys.argv = [SCRIPT, *ARGS]
runpy.run_path(os.path.join(ROOT, "src", SCRIPT), run_name="__main__")
