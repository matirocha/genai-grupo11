#!/usr/bin/env python3
"""
Evaluación sobre el conjunto de instancias (mismo verificador para todas las estrategias)
---------------------------------------------------------------------------------------
Estrategias:
  direct            Línea base de D1: prompting directo zero-shot (una llamada, semana completa en JSON).
  repair            Alternativa: direct + hasta 3 rondas de corrección con la lista de violaciones del verificador.
  stepwise          SOLUCIÓN: un turno por paso + estado externo + decodificación restringida + chequeo
                    hacia adelante + backtracking (presupuesto 30).
  stepwise_nosearch Ablación: igual que stepwise pero sin chequeo hacia adelante ni backtracking.
  random            Ablación sin LLM: andamiaje de stepwise con elección uniforme entre las opciones viables.
  random_nosearch   Ablación sin LLM y sin búsqueda.

Cada salida se guarda en results/<conjunto>/<modelo>/<estrategia>/<instancia>.json (horario, salida cruda,
verificación),
de modo que cada número del documento se puede rastrear hasta un archivo del repositorio.

Uso:
    python src/evaluate.py --model meta-llama/Llama-3.2-3B-Instruct --strategies direct,repair,stepwise,stepwise_nosearch
    python src/evaluate.py --strategies random,random_nosearch
    python src/evaluate.py --set stress --strategies direct,stepwise,random
    python src/evaluate.py --summary
"""

import argparse
import json
import os
import platform
import time
from typing import Any, Dict, List

from instances import BASE_DIR, instance_dir, list_instances, load_instance
from verifier import ScheduleVerifier, VIOLATION_TYPES

RESULTS_DIR = os.path.join(BASE_DIR, "results")
LLM_STRATEGIES = ["direct", "repair", "stepwise", "stepwise_nosearch"]
NOLLM_STRATEGIES = ["random", "random_nosearch"]
ORDER = ["direct", "repair", "stepwise_nosearch", "stepwise", "random_nosearch", "random"]


def model_tag(model_id: str) -> str:
    return model_id.split("/")[-1].lower().replace("-instruct", "")


def run_strategy(strategy: str, llm, staff_data, demands, inst_id: str, run_dir: str) -> Dict[str, Any]:
    from baseline_direct import run_direct
    from repair_loop import run_repair
    from stepwise_solver import llm_policy, random_policy, solve

    if strategy == "direct":
        return run_direct(llm, staff_data, demands)
    if strategy == "repair":
        first_path = os.path.join(run_dir, "direct", f"{inst_id}.json")
        if os.path.exists(first_path):
            with open(first_path, encoding="utf-8") as f:
                first = json.load(f)["output"]
        else:
            first = run_direct(llm, staff_data, demands)
        return run_repair(llm, staff_data, demands, first)
    search = not strategy.endswith("nosearch")
    if strategy.startswith("stepwise"):
        choose = llm_policy(llm)
    else:
        choose = random_policy(int(inst_id.split("_")[-1]))
    calls0 = llm.calls if llm else 0
    out = solve(staff_data, demands, choose, lookahead=search, max_backtracks=30 if search else 0)
    out["llm_calls"] = (llm.calls - calls0) if llm else 0
    return out


def evaluate(strategies: List[str], model_id: str = None, instances: List[str] = None, quant: str = "nf4",
             inst_set: str = "main"):
    llm, tag = None, "no_llm"
    if any(s in LLM_STRATEGIES for s in strategies):
        from llm import LLM
        llm = LLM(model_id, quant=quant)
        tag = model_tag(model_id)
    run_dir = os.path.join(RESULTS_DIR, inst_set, tag)
    os.makedirs(run_dir, exist_ok=True)
    if llm:
        import torch, transformers
        info = {**llm.info(), "torch": torch.__version__, "transformers": transformers.__version__,
                "python": platform.python_version(), "date": time.strftime("%Y-%m-%d %H:%M")}
        with open(os.path.join(run_dir, "run_info.json"), "w", encoding="utf-8") as f:
            json.dump(info, f, indent=2)
        print(json.dumps(info))
    paths = instances or list_instances(inst_set)
    for strategy in strategies:
        out_dir = os.path.join(run_dir, strategy)
        os.makedirs(out_dir, exist_ok=True)
        for path in paths:
            inst_id = os.path.splitext(os.path.basename(path))[0]
            out_path = os.path.join(out_dir, f"{inst_id}.json")
            if os.path.exists(out_path):
                continue
            staff_data, demands = load_instance(path)
            out = run_strategy(strategy, llm, staff_data, demands, inst_id, run_dir)
            if out.get("schedule") is not None:
                res = ScheduleVerifier(staff_data, demands).evaluate(out["schedule"])
            else:
                res = {"is_valid": False, "total_hard_violations": None, "violations_by_type": None, "violations": []}
            record = {"instance": inst_id, "set": inst_set, "strategy": strategy, "model": model_id if llm else None,
                      "output": out, "verification": res}
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(record, f, indent=1, ensure_ascii=False)
            print(f"[{inst_set}/{tag}/{strategy}] {inst_id}: valid={res['is_valid']} violations={res['total_hard_violations']} "
                  f"t={out.get('seconds')}s calls={out.get('llm_calls')}", flush=True)


def specialist_overuse(record: dict, inst_set: str):
    """(turnos con más especialistas de la cuota que los exigidos, turnos con cuota de especialidad).
    Mide si la política gasta especialistas escasos donde un médico General habría bastado."""
    staff_data, demands = load_instance(os.path.join(instance_dir(inst_set), f"{record['instance']}.json"))
    spec = {s["id"]: s["specialty"] for s in staff_data["staff"]}
    extra = total = 0
    for day, shifts in record["output"]["schedule"].items():
        for t, ids in shifts.items():
            for sp, n in demands["requirements_per_shift"][t]["specialty_requirements"].items():
                if n > 0:
                    total += 1
                    extra += sum(spec.get(i) == sp for i in ids) > n
    return extra, total


def summarize() -> str:
    rows = []
    runs = [(st, tag) for st in ("main", "stress") if os.path.isdir(os.path.join(RESULTS_DIR, st))
            for tag in sorted(os.listdir(os.path.join(RESULTS_DIR, st)))]
    for inst_set, tag in runs:
        tdir = os.path.join(RESULTS_DIR, inst_set, tag)
        if not os.path.isdir(tdir):
            continue
        for strategy in ORDER:
            sdir = os.path.join(tdir, strategy)
            if not os.path.isdir(sdir):
                continue
            recs = []
            for fn in sorted(os.listdir(sdir)):
                with open(os.path.join(sdir, fn), encoding="utf-8") as f:
                    recs.append(json.load(f))
            n = len(recs)
            parsed = [r for r in recs if r["verification"]["total_hard_violations"] is not None]
            viol = [r["verification"]["total_hard_violations"] for r in parsed]
            by_type = {t: sum(r["verification"]["violations_by_type"][t] for r in parsed) for t in VIOLATION_TYPES}
            out = [r["output"] for r in recs]
            row = {
                "set": inst_set, "model": tag, "strategy": strategy, "N": n,
                "valid": sum(r["verification"]["is_valid"] for r in recs),
                "json_ok": len(parsed),
                "mean_violations": round(sum(viol) / len(viol), 2) if viol else None,
                "median_violations": sorted(viol)[len(viol) // 2] if viol else None,
                "mean_llm_calls": round(sum(o.get("llm_calls", 0) for o in out) / n, 1),
                "mean_seconds": round(sum(o.get("seconds", 0) for o in out) / n, 1),
                "mean_backtracks": round(sum(o.get("backtracks", 0) for o in out) / n, 2) if "backtracks" in out[0] else None,
                "failed_instances": [r["instance"] for r in recs if not r["verification"]["is_valid"]],
                **{f"viol_{t}": v for t, v in by_type.items()},
            }
            if "certified" in out[0]:
                row["certified"] = sum(o["certified"] for o in out)
                row["certified_but_invalid"] = sum(o["certified"] and not r["verification"]["is_valid"]
                                                   for o, r in zip(out, recs))
                over = [specialist_overuse(r, inst_set) for r in recs]
                row["specialist_overuse"] = round(sum(a for a, _ in over) / sum(b for _, b in over), 3)
            rows.append(row)
    with open(os.path.join(RESULTS_DIR, "summary.json"), "w", encoding="utf-8") as f:
        json.dump(rows, f, indent=1)
    lines = ["| conjunto | modelo | estrategia | N | válidos | JSON ok | viol. media | llamadas LLM | seg. | retrocesos | sobreuso esp. | fallidas |",
             "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        failed = ", ".join(r["failed_instances"]) if len(r["failed_instances"]) <= 4 else f"{len(r['failed_instances'])} instancias"
        lines.append(f"| {r['set']} | {r['model']} | {r['strategy']} | {r['N']} | {r['valid']}/{r['N']} | {r['json_ok']}/{r['N']} | "
                     f"{r['mean_violations']} | {r['mean_llm_calls']} | {r['mean_seconds']} | {r['mean_backtracks'] if r['mean_backtracks'] is not None else '-'} | "
                     f"{r.get('specialist_overuse', '-')} | {failed or '-'} |")
    lines += ["", "Nota sobre `seg.`: todas las corridas de `llama-3.2-3b` y `main/qwen2.5-3b/{direct,stepwise}` se "
              "midieron con la GPU dedicada. Las demás compartieron la GPU con otros procesos de evaluación, así que sus "
              "tiempos están inflados. Los demás campos no dependen de eso (decodificación greedy).",
              "", "Violaciones totales por tipo (sobre salidas con JSON legible):", "",
              "| conjunto | modelo | estrategia | " + " | ".join(VIOLATION_TYPES) + " |", "|---|---|---|" + "---|" * len(VIOLATION_TYPES)]
    for r in rows:
        lines.append(f"| {r['set']} | {r['model']} | {r['strategy']} | " + " | ".join(str(r[f'viol_{t}']) for t in VIOLATION_TYPES) + " |")
    table = "\n".join(lines)
    with open(os.path.join(RESULTS_DIR, "summary.md"), "w", encoding="utf-8") as f:
        f.write(table + "\n")
    return table, rows


def compact(rows, models) -> str:
    """Vista corta para pantalla (la usa el video): solo los modelos pedidos."""
    out = [f"{'conjunto':<9}{'modelo':<14}{'estrategia':<19}{'válidos':<9}{'viol.':<8}{'llamadas':<10}retrocesos",
           "-" * 78]
    for r in rows:
        if r["model"] in models:
            bt = r["mean_backtracks"] if r["mean_backtracks"] is not None else "-"
            out.append(f"{r['set']:<9}{r['model']:<14}{r['strategy']:<19}{str(r['valid']) + '/' + str(r['N']):<9}"
                       f"{str(r['mean_violations']):<8}{str(r['mean_llm_calls']):<10}{bt}")
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="meta-llama/Llama-3.2-3B-Instruct")
    ap.add_argument("--quant", default="nf4", choices=["nf4", "bf16"])
    ap.add_argument("--strategies", default="direct,repair,stepwise,stepwise_nosearch")
    ap.add_argument("--set", default="main", choices=["main", "stress"])
    ap.add_argument("--instances", default=None, help="lista separada por comas, ej. inst_00,inst_07")
    ap.add_argument("--summary", action="store_true")
    ap.add_argument("--only", default=None, help="vista corta solo de estos modelos, ej. llama-3.2-3b,no_llm")
    args = ap.parse_args()
    if not args.summary:
        paths = None
        if args.instances:
            paths = [os.path.join(instance_dir(args.set), f"{i}.json") for i in args.instances.split(",")]
        evaluate(args.strategies.split(","), args.model, paths, args.quant, args.set)
    table, rows = summarize()
    print(compact(rows, args.only.split(",")) if args.only else table)


if __name__ == "__main__":
    main()
