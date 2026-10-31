"""Ejecuta un paso del video para la presentación HTML (lo lanza servidor_video.py, no hace falta correrlo a mano).

Corre el archivo pasoN_*.py tal cual, pero antes intercepta Trace.log: además de la línea legible que ya imprime
demo_agents.py, cada evento de la traza (mensaje entre agentes y herramientas) sale por stdout como una línea
"\\x1e" + JSON. Así el HTML puede dibujar los mensajes intermedios sin cambiar el código de src/.

Uso: python -u video/ejecutar_paso.py video/paso2_agentes.py
"""
import json
import os
import runpy
import sys

MARCA = "\x1e"

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
sys.path.insert(0, os.path.join(ROOT, "src"))

from agent_core import Trace  # noqa: E402  (el mismo módulo que después importa demo_agents.py)

_log = Trace.log


def log(self, src, dst, kind, content, **extra):
    _log(self, src, dst, kind, content, **extra)
    print(MARCA + json.dumps(self.events[-1], ensure_ascii=False, default=str), flush=True)


Trace.log = log

paso = os.path.abspath(sys.argv[1])
sys.argv = [paso]
runpy.run_path(paso, run_name="__main__")
