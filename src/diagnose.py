#!/usr/bin/env python3
"""
Diagnóstico de fallas de la solución (herramienta de análisis offline, NO forma parte del pipeline)
-------------------------------------------------------------------------------------------------
Cuando stepwise agota su presupuesto de retrocesos, este script explica POR QUÉ:
  1. Toma el prefijo más profundo que la búsqueda logró construir (turnos antes del modo relajado).
  2. Con CP-SAT encuentra la primera decisión k tal que fijar los turnos 0..k deja la semana sin solución
     ("decisión culpable"). Antes de k la semana todavía era completable.
  3. Reporta la distancia entre la decisión culpable y el turno donde apareció el callejón sin salida,
     y qué familias de restricciones forman el conflicto (quitando una a la vez y viendo si se vuelve factible).

Uso:
    python src/diagnose.py --set stress --model llama-3.2-3b --instance stress_04
"""

import argparse
import json
import os
from typing import Dict, List, Optional, Set

from instances import BASE_DIR, DAYS, SHIFTS, instance_dir, load_instance, rest_hours, MIN_REST

FAMILIES = {
    "HC1": "descanso >=16h entre días consecutivos",
    "HC4": "cuota de especialidad",
    "HC5": "tope de horas semanales",
    "HC6": "franjas bloqueadas",
}


def completable(staff, demands, fixed: Dict[int, List[str]], drop: Optional[Set[str]] = None,
                time_limit: float = 20.0) -> bool:
    from ortools.sat.python import cp_model
    drop = drop or set()
    slots = [(d, t) for d in DAYS for t in SHIFTS]
    m = cp_model.CpModel()
    x = {(s["id"], d, t): m.NewBoolVar(f"x_{s['id']}_{d}_{t}") for s in staff for d in DAYS for t in SHIFTS}
    req = demands["requirements_per_shift"]
    for d in DAYS:
        for t in SHIFTS:
            m.Add(sum(x[s["id"], d, t] for s in staff) == req[t]["required_total"])
            if "HC4" not in drop:
                for spec, k in req[t]["specialty_requirements"].items():
                    if k > 0:
                        m.Add(sum(x[s["id"], d, t] for s in staff if s["specialty"] == spec) >= k)
    for s in staff:
        i = s["id"]
        for d in DAYS:
            m.Add(sum(x[i, d, t] for t in SHIFTS) <= 1)
        if "HC1" not in drop:
            for a, b in zip(DAYS, DAYS[1:]):
                for t1 in SHIFTS:
                    for t2 in SHIFTS:
                        if rest_hours(t1, t2) < MIN_REST:
                            m.Add(x[i, a, t1] + x[i, b, t2] <= 1)
        if "HC5" not in drop:
            m.Add(8 * sum(x[i, d, t] for d in DAYS for t in SHIFTS) <= s["max_weekly_hours"])
        if "HC6" not in drop:
            for slot in s.get("unavailable", []):
                d, t = slot.split("_")
                m.Add(x[i, d, t] == 0)
    for k, ids in fixed.items():
        d, t = slots[k]
        for s in staff:
            m.Add(x[s["id"], d, t] == (1 if s["id"] in ids else 0))
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = time_limit
    solver.parameters.num_workers = 8
    return solver.Solve(m) in (cp_model.OPTIMAL, cp_model.FEASIBLE)


def diagnose(inst_path: str, record: dict) -> dict:
    staff_data, demands = load_instance(inst_path)
    staff = staff_data["staff"]
    out = record["output"]
    slots = [(d, t) for d in DAYS for t in SHIFTS]
    prefix_len = len(slots) - out.get("relaxed_steps", 0)
    sched = out["schedule"]
    prefix = {k: sched[d][t] for k, (d, t) in enumerate(slots[:prefix_len])}
    culprit = None
    for k in range(prefix_len):
        if not completable(staff, demands, {j: prefix[j] for j in range(k + 1)}):
            culprit = k
            break
    report = {
        "instance": record["instance"], "backtracks": out.get("backtracks"),
        "first_dead_end": out.get("first_dead_end"),
        "deepest_step": prefix_len, "deepest_slot": " ".join(slots[prefix_len]) if prefix_len < len(slots) else None,
        "violations_final": record["verification"]["total_hard_violations"],
        "violations": record["verification"]["violations"],
    }
    if culprit is not None:
        fixed = {j: prefix[j] for j in range(culprit + 1)}
        # Opciones viables (filtro legal + chequeo hacia adelante) en cada paso entre la decisión culpable y el
        # callejón sin salida: el backtracking cronológico debe agotar este subárbol antes de revisar la culpable.
        from stepwise_solver import Problem, State
        st = State(Problem(staff_data, demands))
        branching = []
        culprit_viable, culprit_good = 0, 0
        for k in range(prefix_len):
            if k == culprit:
                # ¿cuántas opciones pasan el chequeo hacia adelante y cuántas tienen realmente completación?
                for o in st.options(k):
                    st.apply(k, o)
                    if st.future_ok(k):
                        culprit_viable += 1
                        culprit_good += completable(staff, demands, {**{j: prefix[j] for j in range(k)}, k: list(o)})
                    st.undo(k)
            if k > culprit:
                viable = 0
                for o in st.options(k):
                    st.apply(k, o)
                    viable += st.future_ok(k)
                    st.undo(k)
                branching.append(viable)
            st.apply(k, tuple(prefix[k]))
        subtree = 1
        for b in branching:
            subtree *= max(b, 1)
        report.update({
            "culprit_step": culprit, "culprit_slot": " ".join(slots[culprit]), "culprit_choice": prefix[culprit],
            "gap_steps": prefix_len - culprit, "branching_between": branching, "subtree_estimate": subtree,
            "culprit_viable_options": culprit_viable, "culprit_completable_options": culprit_good,
            "conflict_families": [f for f in FAMILIES if completable(staff, demands, fixed, drop={f})],
        })
    return report


def position_bias(rdir: str, inst_set: str):
    """Reproduce las decisiones de corridas sin retrocesos y mide cuántas veces la política eligió exactamente
    los primeros k candidatos de la lista mostrada (ordenada por ID; los especialistas tienen los IDs más bajos)."""
    from stepwise_solver import Problem, State
    first = total = 0
    for fn in sorted(os.listdir(rdir)):
        with open(os.path.join(rdir, fn), encoding="utf-8") as f:
            rec = json.load(f)
        if rec["output"].get("backtracks", 0) or not rec["output"].get("certified", False):
            continue  # con retrocesos el orden de decisiones no se reconstruye desde el horario final
        staff_data, demands = load_instance(os.path.join(instance_dir(inst_set), fn))
        p = Problem(staff_data, demands)
        st = State(p)
        for k, (di, t) in enumerate(p.slots):
            viable = []
            for o in st.options(k):
                st.apply(k, o)
                if st.future_ok(k):
                    viable.append(o)
                st.undo(k)
            chosen = rec["output"]["schedule"][p.days[di]][t]
            if len(viable) > 1:
                cands = sorted({i for o in viable for i in o})
                total += 1
                first += set(chosen) == set(cands[:len(chosen)])
            st.apply(k, tuple(chosen))
    return first, total


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--set", default="stress", choices=["main", "stress"])
    ap.add_argument("--model", default="llama-3.2-3b", help="carpeta en results/<set>/ (ej. llama-3.2-3b o no_llm)")
    ap.add_argument("--strategy", default=None, help="por defecto stepwise (o random si --model no_llm)")
    ap.add_argument("--instance", default=None, help="si se omite, diagnostica todas las instancias fallidas")
    ap.add_argument("--position-bias", action="store_true",
                    help="mide el sesgo de posición de la política (elige los primeros candidatos listados)")
    args = ap.parse_args()
    strategy = args.strategy or ("random" if args.model == "no_llm" else "stepwise")
    rdir = os.path.join(BASE_DIR, "results", args.set, args.model, strategy)
    if args.position_bias:
        a, b = position_bias(rdir, args.set)
        print(f"{args.set}/{args.model}/{strategy}: eligió exactamente los primeros candidatos listados en {a}/{b} "
              f"decisiones con más de una opción ({a / b:.1%}); instancias sin retrocesos")
        return
    names = [f"{args.instance}.json"] if args.instance else sorted(os.listdir(rdir))
    reports = []
    for fn in names:
        with open(os.path.join(rdir, fn), encoding="utf-8") as f:
            rec = json.load(f)
        if rec["verification"]["is_valid"]:
            continue
        rep = diagnose(os.path.join(instance_dir(args.set), fn), rec)
        reports.append(rep)
        print(f"\n=== {rep['instance']} ({args.model}/{strategy}) ===")
        print(f"Retrocesos usados: {rep['backtracks']} | primer callejón sin salida: {rep['first_dead_end']} | "
              f"avance más profundo: paso {rep['deepest_step']} ({rep['deepest_slot']})")
        if "culprit_step" in rep:
            print(f"Decisión culpable (CP-SAT): paso {rep['culprit_step']} = {rep['culprit_slot']} -> {rep['culprit_choice']}")
            print(f"  Hasta el paso {rep['culprit_step'] - 1} la semana aún tenía solución; desde ahí ninguna completación existe.")
            print(f"  En ese turno el chequeo hacia adelante dejaba pasar {rep['culprit_viable_options']} opciones, pero solo "
                  f"{rep['culprit_completable_options']} tenían completación real.")
            print(f"  El conflicto se detecta {rep['gap_steps']} turnos después de causarse.")
            print(f"  Opciones viables en los turnos intermedios: {rep['branching_between']} -> subárbol de "
                  f"~{rep['subtree_estimate']:,} ramas que el retroceso cronológico debe agotar antes de revisar la "
                  f"decisión culpable (presupuesto: 30).")
            fams = ", ".join(f"{f} ({FAMILIES[f]})" for f in rep["conflict_families"]) or "ninguna familia sola"
            print(f"  Quitar UNA de estas familias vuelve factible la completación: {fams}")
        print(f"Violaciones finales (modo relajado): {rep['violations_final']}")
        for v in rep["violations"]:
            print(f"  - {v}")
    out_path = os.path.join(BASE_DIR, "results", args.set, args.model, f"diagnosis_{strategy}.json")
    if not args.instance:
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(reports, f, indent=1, ensure_ascii=False)


if __name__ == "__main__":
    main()
