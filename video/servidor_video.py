#!/usr/bin/env python3
"""
Servidor local de la presentación del video de Deliverable 3
------------------------------------------------------------
Un navegador no puede ejecutar Python, así que este servidor (solo biblioteca estándar) sirve "video/Deliverable 3 Representacion Video.html"
y corre los pasos del video cuando el HTML lo pide. La salida se transmite en vivo como NDJSON, una línea por objeto:
  {"t": "linea", "x": "..."}   una línea de stdout/stderr del script, tal cual
  {"t": "ev", "e": {...}}      un evento de la traza (mensaje entre agentes y herramientas; ver ejecutar_paso.py)
  {"t": "fin", "rc": 0, "s": 12.3}

Rutas:
  GET /                         la presentación
  GET /api/correr?paso=1..3     ejecuta video/pasoN_*.py y transmite su salida
  GET /api/resultado?f=<nombre> horario final, verificación, instancia y resultados guardados de D1 y D2
                                de una corrida del paso 2 (results/demo/<nombre>_agentes.json)

Uso:
    python video/servidor_video.py              # abre http://localhost:8765 en el navegador
    python video/servidor_video.py --port 9000 --no-abrir
"""

import argparse
import json
import os
import subprocess
import sys
import threading
import time
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

VIDEO = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(VIDEO)
DEMO = os.path.join(ROOT, "results", "demo")
HTML = os.path.join(VIDEO, "Deliverable 3 Representacion Video.html")
sys.path.insert(0, os.path.join(ROOT, "src"))
from instances import instance_dir  # noqa: E402

PASOS = {"1": "paso1_protocolo.py", "2": "paso2_agentes.py", "3": "paso3_resultados.py"}
MARCA = "\x1e"

_lock = threading.Lock()
_proc = None                     # un solo paso a la vez: correr otro detiene el anterior


def _detener():
    global _proc
    with _lock:
        if _proc and _proc.poll() is None:
            _proc.kill()
        _proc = None


def _leer(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _nombre_traza(f):
    """Nombre de una traza de results/demo sin extensión; rechaza rutas."""
    f = os.path.basename(f or "")
    for ext in ("_agentes.json", ".jsonl"):
        if f.endswith(ext):
            f = f[: -len(ext)]
    if not f or not os.path.exists(os.path.join(DEMO, f + ".jsonl")):
        raise FileNotFoundError(f)
    return f


def guardado(inst_set, strategy, inst_id):
    p = os.path.join(ROOT, "results", inst_set, "llama-3.2-3b", strategy, f"{inst_id}.json")
    return _leer(p) if os.path.exists(p) else None


def resultado(f):
    f = _nombre_traza(f)
    d = _leer(os.path.join(DEMO, f + "_agentes.json"))
    inst = _leer(os.path.join(instance_dir(d["set"]), f"{d['instance']}.json"))
    comp = {}
    for nombre, strat in (("direct", "direct"), ("stepwise", "stepwise")):
        rec = guardado(d["set"], strat, d["instance"])
        if rec:
            o, v = rec["output"], rec["verification"]
            comp[nombre] = {"is_valid": v["is_valid"], "violaciones": v["total_hard_violations"],
                            "llm_calls": o.get("llm_calls", 1), "backtracks": o.get("backtracks"),
                            "seconds": o.get("seconds")}
    o = {k: v for k, v in d["output"].items() if k != "prompts"}
    return {"f": f, "instance": d["instance"], "set": d["set"], "model": d["model"], "output": o,
            "verification": d["verification"], "staff": inst["staff"], "demands": inst["demands"],
            "comparacion": comp}


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass

    def _json(self, obj, code=200):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        u = urlparse(self.path)
        q = {k: v[0] for k, v in parse_qs(u.query).items()}
        try:
            if u.path == "/":
                with open(HTML, "rb") as fh:
                    body = fh.read()
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.send_header("Cache-Control", "no-store")
                self.end_headers()
                self.wfile.write(body)
            elif u.path == "/api/correr":
                self._correr(q.get("paso", ""))
            elif u.path == "/api/detener":
                _detener()
                self._json({"ok": True})
            elif u.path == "/api/ping":
                self._json({"ok": True})
            elif u.path == "/api/resultado":
                self._json(resultado(q.get("f")))
            else:
                self._json({"error": "no existe"}, 404)
        except FileNotFoundError:
            self._json({"error": "no existe"}, 404)
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
            pass

    def _correr(self, paso):
        global _proc
        if paso not in PASOS:
            return self._json({"error": f"paso inválido: {paso}"}, 400)
        _detener()
        env = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUNBUFFERED="1")
        cmd = [sys.executable, "-u", os.path.join(VIDEO, "ejecutar_paso.py"), os.path.join(VIDEO, PASOS[paso])]
        t0 = time.time()
        proc = subprocess.Popen(cmd, cwd=ROOT, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                text=True, encoding="utf-8", errors="replace", bufsize=1,
                                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        with _lock:
            _proc = proc
        self.send_response(200)
        self.send_header("Content-Type", "application/x-ndjson; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Accel-Buffering", "no")
        self.end_headers()

        def send(obj):
            self.wfile.write((json.dumps(obj, ensure_ascii=False) + "\n").encode("utf-8"))
            self.wfile.flush()

        try:
            send({"t": "inicio", "cmd": f"python video/{PASOS[paso]}"})
            for raw in proc.stdout:
                line = raw.rstrip("\n").split("\r")[-1]
                if line.startswith(MARCA):
                    send({"t": "ev", "e": json.loads(line[1:])})
                else:
                    send({"t": "linea", "x": line})
            rc = proc.wait()
            send({"t": "fin", "rc": rc, "s": round(time.time() - t0, 1)})
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
            proc.kill()            # el navegador cortó (otro paso o recarga): no dejar el modelo corriendo
        finally:
            with _lock:
                if _proc is proc:
                    _proc = None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--no-abrir", action="store_true", help="no abre el navegador")
    args = ap.parse_args()
    # en Windows SO_REUSEADDR deja que dos servidores escuchen el mismo puerto: abrir la presentación dos veces
    # dejaría el navegador hablando con cualquiera de los dos, así que el segundo debe fallar
    ThreadingHTTPServer.allow_reuse_address = os.name != "nt"
    try:
        srv = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    except OSError:
        sys.exit(f"El puerto {args.port} ya está en uso: probablemente la presentación ya está abierta en otra ventana. "
                 f"Ciérrala (Ctrl+C) y vuelve a lanzarla, o usa --port.")
    srv.daemon_threads = True
    url = f"http://localhost:{args.port}/"
    print(f"Presentación del video de Deliverable 3 en {url}  (Ctrl+C para cerrar)", flush=True)
    if not args.no_abrir:
        threading.Timer(0.6, lambda: webbrowser.open(url)).start()
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        _detener()


if __name__ == "__main__":
    main()
