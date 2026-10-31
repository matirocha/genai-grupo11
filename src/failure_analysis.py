#!/usr/bin/env python3
"""
Análisis GENERAL de fallas (herramienta offline, NO forma parte del sistema)
---------------------------------------------------------------------------
Responde al comentario del profesor sobre Deliverable 2: en vez de explicar una sola instancia, junta TODAS las
corridas fallidas de las estrategias con búsqueda (solución D2, azar, sistema de agentes y sus ablaciones) y
mide qué tienen en común. Para cada falla usa src/diagnose.py (CP-SAT solo como oráculo de análisis):
  - decisión culpable: primer turno tras el cual la semana ya no tiene solución;
  - distancia (en turnos) entre la decisión culpable y el callejón sin salida;
  - precisión del chequeo hacia adelante en el turno culpable (opciones que dejaba pasar vs. completables);
  - familias de restricciones que forman el conflicto;
  - tipo de violación final y holgura de capacidad de la instancia.

Uso:
    python src/failure_analysis.py                                   # todas las corridas con búsqueda
    python src/failure_analysis.py --runs stress/llama-3.2-3b/stepwise,hard/llama-3.2-3b/stepwise
"""

import argparse
import json
import os
import sys
import re
from collections import Counter
from statistics import median
from typing import Dict, List, Optional

from diagnose import diagnose
from instances import BASE_DIR, DAYS, instance_dir, load_instance
from verifier import VIOLATION_TYPES

RESULTS_DIR = os.path.join(BASE_DIR, "results")
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
SEARCH_STRATEGIES = ("stepwise", "random", "agents")


def slack(inst_set: str, inst_id: str) -> Dict[str, int]:
    """Holgura de capacidad (turnos) total y de la especialidad más justa."""
    staff_data, demands = load_instance(os.path.join(instance_dir(inst_set), f"{inst_id}.json"))
    staff, req = staff_data["staff"], demands["requirements_per_shift"]
    cap = sum(s["max_weekly_hours"] // 8 for s in staff)
    out = {"global": cap - sum(r["required_total"] for r in req.values()) * len(DAYS)}
    tight = None
    for sp in {s["specialty"] for s in staff}:
        need = sum(r["specialty_requirements"].get(sp, 0) for r in req.values()) * len(DAYS)
        if need:
            gap = sum(s["max_weekly_hours"] // 8 for s in staff if s["specialty"] == sp) - need
            tight = gap if tight is None else min(tight, gap)
    out["specialty"] = tight
    out["min"] = min(out["global"], tight) if tight is not None else out["global"]
    return out


def discover_runs() -> List[str]:
    runs = []
    for inst_set in ("main", "stress", "hard"):
        sdir = os.path.join(RESULTS_DIR, inst_set)
        if not os.path.isdir(sdir):
            continue
        for model in sorted(os.listdir(sdir)):
            mdir = os.path.join(sdir, model)
            if not os.path.isdir(mdir):
                continue
            for strategy in sorted(os.listdir(mdir)):
                if strategy.startswith(SEARCH_STRATEGIES) and os.path.isdir(os.path.join(mdir, strategy)) \
                        and "nosearch" not in strategy:
                    runs.append(f"{inst_set}/{model}/{strategy}")
    return runs


def attribute(events: List[Dict], c: int, choice: List[str], deepest: int, has_critic: bool) -> Dict:
    """Sistema de agentes: qué eslabón dejó pasar la decisión culpable c y si después se deshizo.
    diagnose() analiza el horario parcial MÁS PROFUNDO que alcanzó la búsqueda (`deepest` turnos). Se toma la última
    visita al turno c, anterior a ese punto, cuya opción fijada es la culpable; luego se mira si algún salto o
    retroceso posterior volvió a c o antes (la deshizo) aunque el presupuesto se agotara en otra rama."""
    target = set(choice)
    visits, cur = [], None
    reached = None                                   # índice del evento en que se fijó por primera vez el turno deepest-1
    for idx, ev in enumerate(events):
        c_ = ev["contenido"] if isinstance(ev["contenido"], dict) else {}
        paso = c_.get("paso")
        if ev["tipo"] in ("propuesta", "única opción") and ev.get("ronda", 0) == 0:
            if cur:
                visits.append(cur)
            cur = None
            if reached is None and paso == deepest - 1:
                reached = idx
            if paso == c:
                cur = {"start": idx, "final": set(c_["opcion"]), "unica": ev["tipo"] == "única opción",
                       "alertas": False, "veredicto": None, "rondas": 0, "mantiene": False}
        elif cur and paso == c:
            if ev["tipo"] == "propuesta":
                cur["final"], cur["rondas"] = set(c_["opcion"]), cur["rondas"] + 1
            elif ev["tipo"] == "alertas":
                cur["alertas"] = True
            elif ev["tipo"] in ("aceptar", "rechazar"):
                cur["veredicto"] = ev["tipo"]
            elif ev["tipo"] == "mantiene":
                cur["final"], cur["mantiene"] = set(c_["opcion"]), True
    if cur:
        visits.append(cur)
    limit = reached if reached is not None else len(events)
    good = [v for v in visits if v["final"] == target and v["start"] <= limit]
    if not good:
        return {"categoria": "sin traza de la decisión"}
    last = good[-1]
    if last["unica"]:
        cat = "opción única (las prohibiciones dejaron solo la fatal)"
    elif not has_critic:
        cat = "sin Crítico: la propuesta se fijó directo"
    elif not last["alertas"]:
        cat = "punto ciego: perfilar no alertó"
    elif last["mantiene"]:
        cat = "el Asignador mantuvo la propuesta rechazada"
    elif last["rondas"] >= 2 and last["veredicto"] == "rechazar":
        cat = "revisión agotada (2 rechazos, se fijó la tercera)"
    elif last["veredicto"] == "aceptar":
        cat = "el Crítico aceptó una propuesta fatal"
    else:
        cat = "otro"
    jumps = [ev["contenido"]["paso"] for ev in events[last["start"]:]
             if ev["tipo"] in ("salto", "retroceso") and isinstance(ev["contenido"], dict)]
    return {"categoria": cat, "saltos_despues": len(jumps), "deshecha": any(j <= c for j in jumps),
            "mas_cerca": min((j - c for j in jumps), default=None)}


def analyze(runs: List[str]) -> Dict:
    failures, totals = [], Counter()
    by_slack = Counter()       # holgura mínima (total o de especialidad) -> horarios corridos
    fail_slack = Counter()     # holgura mínima -> horarios fallidos
    for run in runs:
        inst_set, model, strategy = run.split("/")
        rdir = os.path.join(RESULTS_DIR, inst_set, model, strategy)
        for fn in sorted(os.listdir(rdir)):
            with open(os.path.join(rdir, fn), encoding="utf-8") as f:
                rec = json.load(f)
            sl = slack(inst_set, rec["instance"])
            totals[run] += 1
            by_slack[min(sl["min"], 3)] += 1
            if rec["verification"]["is_valid"]:
                continue
            fail_slack[min(sl["min"], 3)] += 1
            rep = diagnose(os.path.join(instance_dir(inst_set), fn), rec)
            rep.update({"run": run, "set": inst_set, "slack": sl,
                        "violations_by_type": rec["verification"]["violations_by_type"]})
            tpath = os.path.join(RESULTS_DIR, "traces", inst_set, model, strategy, fn[:-5] + ".jsonl")
            if "culprit_step" in rep and os.path.exists(tpath):
                from coordinator import ABLATIONS
                has_critic = ABLATIONS.get(re.sub(r"_s\d+$", "", strategy), {}).get("critic", True)
                with open(tpath, encoding="utf-8") as f:
                    rep["eslabon"] = attribute([json.loads(x) for x in f if x.strip()], rep["culprit_step"],
                                               rep["culprit_choice"], rep["deepest_step"], has_critic)
            failures.append(rep)
            print(f"  {run}/{rec['instance']}: culpable {rep.get('culprit_slot')} -> callejón {rep.get('first_dead_end')}"
                  f" (distancia {rep.get('gap_steps')})", flush=True)
    return {"runs": runs, "totals": dict(totals), "failures": failures,
            "by_slack": {str(k): v for k, v in sorted(by_slack.items())},
            "fail_slack": {str(k): v for k, v in sorted(fail_slack.items())}}


def summarize(res: Dict) -> str:
    fl = res["failures"]
    n_runs = sum(res["totals"].values())
    lines = [f"Corridas con búsqueda analizadas: {len(res['runs'])} configuraciones, {n_runs} horarios, "
             f"{len(fl)} fallidos.", ""]
    if not fl:
        return "\n".join(lines)
    viol = Counter()
    for r in fl:
        viol.update({k: v for k, v in r["violations_by_type"].items() if v})
    tot = sum(viol.values())
    lines.append("1. Qué se rompe: " + ", ".join(f"{k} {100 * viol[k] / tot:.0f}%" for k in VIOLATION_TYPES if viol[k])
                 + f" de las {tot} violaciones finales.")
    gaps = [r["gap_steps"] for r in fl if "gap_steps" in r]
    # el callejón que se mide es el del horario parcial más profundo (el mismo de la distancia)
    dead_days = Counter(r["deepest_slot"].split()[0] for r in fl if r.get("deepest_slot") and "gap_steps" in r)
    if gaps:
        lines.append(f"2. Dónde se causa: la decisión culpable está {min(gaps)}–{max(gaps)} turnos antes del callejón "
                     f"(mediana {median(gaps)}); el punto más profundo que alcanza la búsqueda (el callejón final) cae " +
                     ", ".join(f"{d} {n}" for d, n in sorted(dead_days.items(), key=lambda x: DAYS.index(x[0]))) + ".")
    prec = [(r["culprit_completable_options"], r["culprit_viable_options"]) for r in fl
            if r.get("culprit_viable_options")]
    if prec:
        lines.append(f"3. Por qué el chequeo no lo ve: en el turno culpable dejaba pasar {sum(b for _, b in prec)} opciones "
                     f"y solo {sum(a for a, _ in prec)} ({100 * sum(a for a, _ in prec) / sum(b for _, b in prec):.0f}%) "
                     "tenían completación real.")
    fams = Counter(f for r in fl for f in r.get("conflict_families", []))
    with_culprit = sum("culprit_step" in r for r in fl)
    if with_culprit:
        lines.append("4. Qué forma el conflicto (quitar una familia lo resuelve): " +
                     ", ".join(f"{f} {n}/{with_culprit}" for f, n in fams.most_common()) + ".")
    lines.append("5. Cuándo ocurre (holgura mínima de capacidad de la instancia, total o de una especialidad, en turnos): " +
                 ", ".join(f"{'≥3' if k == '3' else k}: {res['fail_slack'].get(k, 0)}/{v} fallan"
                           for k, v in res["by_slack"].items()) + ".")
    att = [r for r in fl if "eslabon" in r and "saltos_despues" in r["eslabon"] and r["run"].split("/")[1] != "no_llm"]
    if att:
        cats = Counter(r["eslabon"]["categoria"] for r in att)
        undone = sum(r["eslabon"]["deshecha"] for r in att)
        lines.append(f"6. En las {len(att)} fallas del sistema de agentes con LLM y sus ablaciones, quién dejó pasar la "
                     "decisión culpable: " + ", ".join(f"{k} ({v})" for k, v in cats.most_common()) +
                     f". En {len(att) - undone} de ellas ningún salto posterior volvió a la culpable; en {undone} "
                     "se la deshizo, pero el presupuesto se agotó en otra rama.")
    lines += ["", "| configuración | horarios | fallidos | distancia culpable→callejón |", "|---|---|---|---|"]
    for run in res["runs"]:
        g = [r["gap_steps"] for r in fl if r["run"] == run and "gap_steps" in r]
        nf = sum(r["run"] == run for r in fl)
        lines.append(f"| {run} | {res['totals'].get(run, 0)} | {nf} | {', '.join(map(str, g)) or '-'} |")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", default=None, help="lista conjunto/modelo/estrategia separada por comas")
    ap.add_argument("--summary", action="store_true",
                    help="no recalcula: rehace failure_analysis.md y failure_case.json desde failure_analysis.json")
    args = ap.parse_args()
    out_json = os.path.join(RESULTS_DIR, "failure_analysis.json")
    if args.summary and os.path.exists(out_json):
        with open(out_json, encoding="utf-8") as f:
            res = json.load(f)
    else:
        runs = args.runs.split(",") if args.runs else discover_runs()
        res = analyze(runs)
        with open(out_json, "w", encoding="utf-8") as f:
            json.dump(res, f, indent=1, ensure_ascii=False)
    text = summarize(res)
    with open(os.path.join(RESULTS_DIR, "failure_analysis.md"), "w", encoding="utf-8") as f:
        f.write(text + "\n")
    print(text)
    case = pick_failure_case(res)
    if case:
        with open(os.path.join(RESULTS_DIR, "failure_case.json"), "w", encoding="utf-8") as f:
            json.dump(case, f, indent=1, ensure_ascii=False)
        print(f"\nCaso de falla elegido: {case['set']}/{case['model']}/{case['strategy']}/{case['instance']} — {case['por_que']}")


def pick_failure_case(res: Dict) -> Optional[Dict]:
    """Caso de falla del video: una falla del sistema de agentes completo con LLM (si no tiene, de la ablación con
    LLM que más falla), de la categoría de eslabón más frecuente; a igualdad, la de mayor distancia culpable→callejón.
    Es una ilustración del patrón general, no el análisis."""
    llm = [r for r in res["failures"] if "eslabon" in r and "saltos_despues" in r["eslabon"]
           and r["run"].split("/")[1] != "no_llm"]
    pool = [r for r in llm if r["run"].split("/")[2] == "agents"]
    if not pool:
        by_run = Counter(r["run"].split("/")[2] for r in llm)
        if not by_run:
            return None
        worst = by_run.most_common(1)[0][0]
        pool = [r for r in llm if r["run"].split("/")[2] == worst]
    top = Counter(r["eslabon"]["categoria"] for r in pool).most_common(1)[0][0]
    r = max((x for x in pool if x["eslabon"]["categoria"] == top), key=lambda x: x.get("gap_steps", 0))
    inst_set, model, strategy = r["run"].split("/")
    return {"instance": r["instance"], "set": inst_set, "model": model, "strategy": strategy,
            "culpable": r["culprit_slot"],
            "por_que": f"decisión culpable {r['culprit_slot']} ({' + '.join(r['culprit_choice'])}); el horario más "
                       f"profundo llega a {r['deepest_slot']}, {r['gap_steps']} turnos después; eslabón: {top}",
            "max_lineas": 14}


if __name__ == "__main__":
    main()
