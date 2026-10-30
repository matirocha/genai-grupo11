#!/usr/bin/env python3
"""
Demostración del sistema de agentes (lo que muestra el video de Deliverable 3)
------------------------------------------------------------------------------
Corre en vivo el sistema de agentes sobre UNA instancia y muestra, a medida que ocurren, los mensajes entre los
agentes (Asignador, Crítico, Diagnosticador) y las herramientas. Al final muestra la grilla semanal, el veredicto
del verificador y, para la misma instancia, el resultado guardado de la línea base y de la solución de D2.
La traza completa queda en results/demo/<instancia>_<fecha>.jsonl: cada mensaje entre agentes y herramientas, el
mensaje de usuario exacto que recibió cada agente y las secciones de su prompt de sistema (cuya versión y sha también
quedan registradas).

Uso:
    python src/demo_agents.py --random                       # instancia al azar del conjunto difícil
    python src/demo_agents.py --set stress --instance stress_04
"""

import argparse
import json
import logging
import os
import random
import sys
import time
import warnings

os.environ.setdefault("TRANSFORMERS_VERBOSITY", "error")
os.environ.setdefault("HF_HUB_DISABLE_PROGRESS_BARS", "1")
warnings.filterwarnings("ignore")
logging.getLogger("torch.utils.flop_counter").setLevel(logging.ERROR)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from agent_core import Trace  # noqa: E402
from demo import LINE, show_grid, show_instance, show_verification  # noqa: E402
from instances import BASE_DIR, instance_dir, list_instances, load_instance  # noqa: E402
from verifier import ScheduleVerifier  # noqa: E402


def pretty(ev) -> str:
    """Una línea legible por evento de la traza (las que se ven en el video)."""
    c, src, dst, kind = ev["contenido"], ev["de"], ev["a"], ev["tipo"]
    arrow = f"{src} → {dst}"
    if kind == "inicio":
        return ""
    if kind == "propuesta":
        return f"[{arrow}] {c['turno']}: propone {' + '.join(c['opcion'])} (opción {c.get('etiqueta', '-')} de {c['menu']})"
    if kind == "única opción":
        return f"[{arrow}] {c['turno']}: una sola opción viable → {' + '.join(c['opcion'])} (sin llamar al modelo)"
    if kind == "alertas":
        me, alt = c["propuesta"], c["alternativa"]
        alt_txt = (f"; mejor alternativa {' + '.join(alt['opcion'])} deja {alt['rasgos']['nv']}" if alt else "")
        return (f"[{arrow}] alertas {', '.join(c['alertas'])}: la propuesta deja {me['nv']} opciones al turno "
                f"siguiente, {me['sobre_cuota']} especialistas sobre la cuota{alt_txt}")
    if kind == "resultado":
        return f"[{arrow}] continuaciones a 2 turnos: propuesta {c['propuesta']} | alternativa {c.get('alternativa', '-')}"
    if kind in ("aceptar", "rechazar"):
        return f"[{arrow}] {kind.upper()}"
    if kind == "mantiene":
        return f"[{arrow}] MANTIENE su propuesta {' + '.join(c['opcion'])}"
    if kind == "explicación":
        cands = "; ".join(f"{n}. {x}" for n, x in enumerate(c["candidatos"], 1))
        return f"[{arrow}] CALLEJÓN: {c['causa']}. Candidatos: {cands}"
    if kind == "salto":
        ban = f"prohíbe a {c['prohibir']} ahí" if c.get("prohibir") else "prohíbe ahí la combinación anterior"
        return f"[{arrow}] SALTA a {c['a']} y {ban} (respuesta {c.get('etiqueta', '-')})"
    if kind == "sondear":
        return f"[{arrow}] SONDEAR (respuesta {c.get('etiqueta', '-')})"
    if kind == "callejón":
        return f"[{arrow}] callejón en {c['turno']}"
    if kind == "retroceso":
        return f"[{arrow}] RETROCEDE al turno anterior, {c['a']} (respuesta {c.get('etiqueta', '-')})"
    if kind == "escribe":
        return f"[{arrow}] lección: {c}"
    if kind == "presupuesto agotado":
        return f"[{arrow}] presupuesto agotado ({c['saltos']} saltos): se completa en modo relajado"
    if kind == "modo relajado":
        return f"[{arrow}] {c['turno']}: {' + '.join(c['opcion'])} (modo relajado)"
    if kind == "horario final":
        return f"[{arrow}] horario terminado: certificado={c['certificado']}, {c['saltos']} saltos, {c['pasadas_modelo']} pasadas del modelo"
    return Trace.render(ev)


def saved(inst_set: str, strategy: str, inst_id: str):
    path = os.path.join(BASE_DIR, "results", inst_set, "llama-3.2-3b", strategy, f"{inst_id}.json")
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--set", default="hard", choices=["main", "stress", "hard"])
    ap.add_argument("--instance", default=None)
    ap.add_argument("--random", action="store_true", help="elige la instancia al azar (no escogida a mano)")
    ap.add_argument("--strategy", default="agents")
    args = ap.parse_args()

    if args.random or not args.instance:
        inst_path = random.SystemRandom().choice(list_instances(args.set))
        print(f"Instancia elegida al azar entre {len(list_instances(args.set))} del conjunto '{args.set}': "
              f"{os.path.basename(inst_path)}")
    else:
        inst_path = os.path.join(instance_dir(args.set), f"{args.instance}.json")
    inst_id = os.path.splitext(os.path.basename(inst_path))[0]

    from transformers.utils import logging as hf_logging
    hf_logging.disable_progress_bar()
    from agents import Config
    from llm import LLM
    from orchestrator import ABLATIONS, run_agents

    t0 = time.time()
    llm = LLM()
    info = llm.info()
    print(f"\nModelo (el mismo para los 3 agentes): {info['model_id']} | {info['params_B']}B parámetros | 4-bit NF4 | "
          f"GPU {info['gpu']} | carga {llm.load_seconds}s")
    show_instance(inst_path)
    staff_data, demands = load_instance(inst_path)

    print(f"\n{LINE}\nSISTEMA DE AGENTES: Asignador, Crítico y Diagnosticador (mensajes en vivo)\n{LINE}")
    trace = Trace(echo=lambda line: print(line, flush=True), formatter=pretty)
    cfg = Config(**ABLATIONS[args.strategy])
    out = run_agents(staff_data, demands, llm, cfg, inst_id, trace)
    res = ScheduleVerifier(staff_data, demands).evaluate(out["schedule"])
    show_grid(out["schedule"], demands["days"], demands["shifts"])
    print(f"\nCertificado por el sistema: {'sí' if out['certified'] else 'NO (presupuesto agotado, modo relajado)'}")
    show_verification(res)

    print(f"\n{LINE}\nCOMPARACIÓN EN {inst_id} (mismo verificador)\n{LINE}")
    print(f"{'':<34}{'válido':<9}{'violaciones':<13}{'llamadas LLM':<14}{'retrocesos/saltos':<12}")
    for label, strat in (("línea base (directo)", "direct"), ("solución D2", "stepwise")):
        rec = saved(args.set, strat, inst_id)
        if rec:
            v = rec["verification"]
            print(f"{label + ' [guardado]':<34}{str(v['is_valid']):<9}{str(v['total_hard_violations']):<13}"
                  f"{rec['output'].get('llm_calls', 1):<14}{rec['output'].get('backtracks', '-')}")
    print(f"{'sistema de agentes [en vivo]':<34}{str(res['is_valid']):<9}{res['total_hard_violations']:<13}{out['llm_calls']:<14}"
          f"{out['backtracks']}")

    out_dir = os.path.join(BASE_DIR, "results", "demo")
    os.makedirs(out_dir, exist_ok=True)
    stamp = time.strftime("%Y%m%d_%H%M%S")
    trace.save(os.path.join(out_dir, f"{inst_id}_{stamp}.jsonl"))
    with open(os.path.join(out_dir, f"{inst_id}_{stamp}_agentes.json"), "w", encoding="utf-8") as f:
        json.dump({"instance": inst_id, "set": args.set, "model": info, "strategy": args.strategy,
                   "output": out, "verification": res}, f, indent=1, ensure_ascii=False)
    print(f"\nTraza guardada en results/demo/{inst_id}_{stamp}.jsonl | tiempo total {round(time.time() - t0)}s")


if __name__ == "__main__":
    main()
