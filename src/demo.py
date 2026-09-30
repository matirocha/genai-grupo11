#!/usr/bin/env python3
"""
Demostración de extremo a extremo (lo que muestra el video)
-----------------------------------------------------------
Sobre UNA misma instancia ejecuta en vivo:
  [1/2] la línea base de Deliverable 1 (prompting directo, salida transmitida token a token), y
  [2/2] la solución de Deliverable 2 (stepwise), mostrando cada decisión y cada retroceso,
y evalúa ambas salidas con el mismo verificador. Todo queda guardado en results/demo/.

Uso:
    python src/demo.py --random                         # instancia elegida al azar (conjunto principal)
    python src/demo.py --instance inst_00               # escenario original de Deliverable 1
    python src/demo.py --set stress --instance stress_07 --solo-solucion  # caso de falla
"""

import argparse
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

import json  # noqa: E402

from instances import BASE_DIR, instance_dir, list_instances, load_instance  # noqa: E402
from verifier import ScheduleVerifier  # noqa: E402

LINE = "=" * 78


def show_instance(inst_path: str):
    with open(inst_path, encoding="utf-8") as f:
        inst = json.load(f)
    print(LINE)
    print(f"INSTANCIA {inst['instance_id']} — {inst['source']}" + (f" (semilla {inst['seed']})" if inst["seed"] else ""))
    print(LINE)
    print(f"{'ID':<7}{'Nombre':<26}{'Especialidad':<16}{'Máx h':<7}Franjas bloqueadas")
    for s in inst["staff"]:
        print(f"{s['id']:<7}{s['name']:<26}{s['specialty']:<16}{s['max_weekly_hours']:<7}{', '.join(s['unavailable']) or '-'}")
    req = inst["demands"]["requirements_per_shift"]
    print("Demanda por turno: " + " | ".join(
        f"{t}: {r['required_total']} médicos" + "".join(f", >={n} {sp}" for sp, n in r["specialty_requirements"].items() if n)
        for t, r in req.items()))
    print("21 turnos (7 días x Mañana/Tarde/Noche). Correcto = 0 violaciones de HC1..HC6 según src/verifier.py")


def show_verification(res: dict, max_lines: int = 8):
    status = "APROBADO (0 violaciones)" if res["is_valid"] else f"FALLIDO — {res['total_hard_violations']} violaciones"
    print(f"\n>>> VERIFICADOR: {status}")
    if not res["is_valid"]:
        print("    por tipo: " + ", ".join(f"{k}={v}" for k, v in res["violations_by_type"].items() if v))
        for v in res["violations"][:max_lines]:
            print(f"    - {v}")
        if len(res["violations"]) > max_lines:
            print(f"    ... ({len(res['violations']) - max_lines} más)")


def show_grid(schedule: dict, days, shifts):
    print(f"\n{'':<11}" + "".join(f"{t:<22}" for t in shifts))
    for d in days:
        print(f"{d:<11}" + "".join(f"{', '.join(schedule[d][t]):<22}" for t in shifts))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--set", default="main", choices=["main", "stress"])
    ap.add_argument("--instance", default=None)
    ap.add_argument("--random", action="store_true", help="elige la instancia al azar (no escogida a mano)")
    ap.add_argument("--model", default="meta-llama/Llama-3.2-3B-Instruct")
    ap.add_argument("--solo-solucion", action="store_true", help="omite la línea base (para mostrar el caso de falla)")
    args = ap.parse_args()

    if args.random or not args.instance:
        inst_path = random.SystemRandom().choice(list_instances(args.set))
        print(f"Instancia elegida al azar entre {len(list_instances(args.set))}: {os.path.basename(inst_path)}")
    else:
        inst_path = os.path.join(instance_dir(args.set), f"{args.instance}.json")
    inst_id = os.path.splitext(os.path.basename(inst_path))[0]

    from transformers.utils import logging as hf_logging
    hf_logging.disable_progress_bar()
    from llm import LLM
    from baseline_direct import run_direct
    from stepwise_solver import llm_policy, solve

    t0 = time.time()
    llm = LLM(args.model)
    info = llm.info()
    print(f"\nModelo: {info['model_id']} (rev {str(info['revision'])[:10]}) | {info['params_B']}B parámetros | "
          f"4-bit NF4 | GPU {info['gpu']} | VRAM {info['vram_gb_after_load']} GB | carga {llm.load_seconds}s")

    show_instance(inst_path)
    staff_data, demands = load_instance(inst_path)
    verifier = ScheduleVerifier(staff_data, demands)

    base, base_res = None, None
    if not args.solo_solucion:
        print(f"\n{LINE}\n[1/2] LÍNEA BASE (Deliverable 1): prompting directo zero-shot (salida cruda del modelo)\n{LINE}")
        base = run_direct(llm, staff_data, demands, stream=True)
        if base["schedule"] is None:
            base_res = {"is_valid": False, "total_hard_violations": None, "violations_by_type": {}, "violations": []}
            print(f"\n>>> VERIFICADOR: FALLIDO — la salida no es JSON legible ({base['parse_error']})")
        else:
            base_res = verifier.evaluate(base["schedule"])
            show_verification(base_res)

    print(f"\n{LINE}\n[2/2] SOLUCIÓN (Deliverable 2): turno a turno + estado externo + decodificación restringida + backtracking\n{LINE}")
    calls0 = llm.calls
    sol = solve(staff_data, demands, llm_policy(llm), trace=print)
    sol_res = verifier.evaluate(sol["schedule"])
    show_grid(sol["schedule"], demands["days"], demands["shifts"])
    print(f"\nCertificado por la búsqueda: {'sí' if sol['certified'] else 'NO (presupuesto agotado, modo relajado)'}")
    show_verification(sol_res)

    print(f"\n{LINE}\nCOMPARACIÓN EN {inst_id}\n{LINE}")
    print(f"{'':<12}{'válido':<9}{'violaciones':<13}{'llamadas LLM':<14}{'retrocesos':<12}tiempo")
    if base is not None:
        nviol = base_res["total_hard_violations"]
        print(f"{'baseline':<12}{str(base_res['is_valid']):<9}{('sin JSON' if nviol is None else str(nviol)):<13}{1:<14}{'-':<12}{base['seconds']}s")
    print(f"{'solución':<12}{str(sol_res['is_valid']):<9}{sol_res['total_hard_violations']:<13}{llm.calls - calls0:<14}"
          f"{sol['backtracks']:<12}{sol['seconds']}s")

    out_dir = os.path.join(BASE_DIR, "results", "demo")
    os.makedirs(out_dir, exist_ok=True)
    stamp = time.strftime("%Y%m%d_%H%M%S")
    out_path = os.path.join(out_dir, f"{inst_id}_{stamp}.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump({"instance": inst_id, "set": args.set, "model": info,
                   "baseline": {"output": base, "verification": base_res} if base else None,
                   "solution": {"output": sol, "verification": sol_res}}, f, indent=1, ensure_ascii=False)
    print(f"\nSalidas guardadas en {os.path.relpath(out_path, BASE_DIR)} | tiempo total {round(time.time() - t0)}s")


if __name__ == "__main__":
    main()
