#!/usr/bin/env python3
"""
Reporte de Deliverable 3 (paso 3 del video; con --fallas, el análisis de fallas)
------------------------------------------------
Lee los resultados guardados en results/ (no ejecuta el modelo) y muestra:
  (por defecto) la tabla principal: línea base, solución D2, sistema de agentes, cada ablación y los controles sin
                LLM, sobre las mismas 90 instancias y con el mismo verificador; además, horarios correctos según el
                presupuesto de saltos y la evaluación por decisión con CP-SAT (results/decision_eval.json).
  --fallas      el análisis general de fallas (results/failure_analysis.json) y la traza del caso de falla.

Uso:
    python src/report.py
    python src/report.py --fallas
    python src/report.py --markdown      # imprime en markdown y escribe results/d3_summary.md
"""

import argparse
import glob
import json
import os
import sys
from statistics import mean
from typing import Dict, List, Optional

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from instances import BASE_DIR  # noqa: E402

RESULTS = os.path.join(BASE_DIR, "results")
SETS = ["main", "stress", "hard"]
LLM = "llama-3.2-3b"
ROWS = [  # (etiqueta, modelo, estrategia, semillas)
    ("Línea base: prompt directo (D1)", LLM, "direct", 1),
    ("Solución D2 (turno a turno + retroceso)", LLM, "stepwise", 1),
    ("Sistema de agentes (completo)", LLM, "agents", 1),
    ("  sin Diagnosticador (ReAct): retrocede 1 turno", LLM, "agents_sin_diagnosticador", 1),
    ("  sin Crítico (CRITIC + Self-Refine)", LLM, "agents_sin_critico", 1),
    ("  sin memoria de lecciones (Reflexion)", LLM, "agents_sin_memoria", 1),
    ("  sin ejemplos (Few-Shot)", LLM, "agents_sin_fewshot", 1),
    ("  sin ensamble por permutación", LLM, "agents_sin_ensamble", 1),
    ("Control: D2 eligiendo al azar (5 semillas)", "no_llm", "random", 5),
    ("Control: D2 al azar con 300 retrocesos (5 semillas)", "no_llm", "random_b300", 5),
    ("Control: agentes al azar (5 semillas)", "no_llm", "agents_random", 5),
    ("Control: agentes con reglas fijas", "no_llm", "agents_rules", 1),
]


def load(inst_set: str, model: str, strategy: str) -> List[Dict]:
    return [json.load(open(f, encoding="utf-8"))
            for f in sorted(glob.glob(os.path.join(RESULTS, inst_set, model, strategy, "*.json")))]


def runs(model: str, strategy: str, seeds: int) -> List[Dict[str, List[Dict]]]:
    out = []
    for s in range(seeds):
        name = strategy if s == 0 else f"{strategy}_s{s}"
        out.append({st: load(st, model, name) for st in SETS})
    return out


def fmt_valid(vals: List[int], n: int) -> str:
    if not n:
        return "-"
    if len(vals) == 1:
        return f"{vals[0]}/{n}"
    return f"{mean(vals):.1f}/{n} ({min(vals)}–{max(vals)})"


def row_stats(rs: List[Dict[str, List[Dict]]]) -> Optional[Dict]:
    if not any(rs[0][st] for st in SETS):
        return None
    out = {"valid": {}, "n": {}}
    for st in SETS + ["total"]:
        vals, n = [], 0
        for r in rs:
            recs = [x for s in SETS for x in r[s]] if st == "total" else r[st]
            if not recs:
                continue
            vals.append(sum(x["verification"]["is_valid"] for x in recs))
            n = len(recs)
        out["valid"][st], out["n"][st] = vals, n
    allrecs = [x for r in rs for s in SETS for x in r[s]]
    viol = [x["verification"]["total_hard_violations"] for x in allrecs if x["verification"]["total_hard_violations"] is not None]
    out["viol"] = mean(viol) if viol else None
    out["calls"] = mean(x["output"].get("llm_calls", 0) for x in allrecs)
    bts = [x["output"]["backtracks"] for x in allrecs if "backtracks" in x["output"]]
    out["bt"] = mean(bts) if bts else None
    # decisiones deshechas: en D2 cada retroceso deshace 1; en los agentes un salto deshace k-j
    und = [x["output"].get("undone", x["output"].get("backtracks")) for x in allrecs if "backtracks" in x["output"]]
    out["undone"] = mean(und) if und else None
    out["sec"] = mean(x["output"].get("seconds", 0) for x in allrecs)
    # correctos con presupuesto de saltos B (las políticas son deterministas: la trayectoria con presupuesto B es
    # la misma que con 30 hasta el salto B+1, así que basta con contar los que terminaron con <= B saltos)
    out["budget"] = {}
    for b in (0, 5, 10, 30, 300):
        vals = [sum(x["verification"]["is_valid"] and x["output"].get("backtracks", 0) <= b
                    for s in SETS for x in r[s]) for r in rs]
        out["budget"][b] = vals
    return out


def main_table(markdown: bool = False) -> str:
    lines = []
    head = ["Estrategia", "Principal", "Estrés", "Difícil", "Total (90)", "Viol./horario", "Saltos", "Deshechas",
            "Pasadas LLM", "Seg."]
    rows = []
    for label, model, strat, seeds in ROWS:
        st = row_stats(runs(model, strat, seeds))
        if st is None:
            continue
        rows.append([label] + [fmt_valid(st["valid"][s], st["n"][s]) for s in SETS + ["total"]] +
                    [f"{st['viol']:.2f}" if st["viol"] is not None else "-",
                     f"{st['bt']:.1f}" if st["bt"] is not None else "-",
                     f"{st['undone']:.1f}" if st["undone"] is not None else "-",
                     f"{st['calls']:.0f}", f"{st['sec']:.0f}"])
    if markdown:
        lines += ["| " + " | ".join(head) + " |", "|" + "---|" * len(head)]
        lines += ["| " + " | ".join(r) + " |" for r in rows]
    else:
        w = [max(len(str(r[i])) for r in rows + [head]) for i in range(len(head))]
        lines.append("  ".join(h.ljust(w[i]) for i, h in enumerate(head)))
        lines.append("-" * (sum(w) + 2 * len(w)))
        lines += ["  ".join(str(c).ljust(w[i]) for i, c in enumerate(r)) for r in rows]
    return "\n".join(lines)


def budget_table(markdown: bool = False) -> str:
    head = ["Estrategia", "≤0 saltos", "≤5", "≤10", "≤30", "≤300"]
    rows = []
    for label, model, strat, seeds in ROWS[1:]:
        st = row_stats(runs(model, strat, seeds))
        if st is None or st["bt"] is None:
            continue
        # con tope de 30 saltos no se sabe qué habría pasado con 300: solo el control random_b300 se corrió con 300
        rows.append([label.strip()] + [fmt_valid(st["budget"][b], st["n"]["total"])
                                       if b <= 30 or strat == "random_b300" else "–" for b in (0, 5, 10, 30, 300)])
    if markdown:
        return "\n".join(["| " + " | ".join(head) + " |", "|" + "---|" * len(head)] +
                         ["| " + " | ".join(r) + " |" for r in rows])
    w = [max(len(str(r[i])) for r in rows + [head]) for i in range(len(head))]
    return "\n".join(["  ".join(h.ljust(w[i]) for i, h in enumerate(head)), "-" * (sum(w) + 2 * len(w))] +
                     ["  ".join(str(c).ljust(w[i]) for i, c in enumerate(r)) for r in rows])


def decision_table() -> str:
    path = os.path.join(RESULTS, "decision_eval.md")
    return open(path, encoding="utf-8").read().strip() if os.path.exists(path) else "(sin results/decision_eval.md)"


def show_failures():
    from demo_agents import pretty
    path = os.path.join(RESULTS, "failure_analysis.md")
    print("=" * 78)
    print("ANÁLISIS GENERAL DE FALLAS (todas las corridas con búsqueda, CP-SAT solo como evaluador offline)")
    print("=" * 78)
    print(open(path, encoding="utf-8").read().split("\n| configuración")[0].strip() if os.path.exists(path)
          else "(falta results/failure_analysis.md)")
    case = os.path.join(RESULTS, "failure_case.json")
    if not os.path.exists(case):
        return
    with open(case, encoding="utf-8") as f:
        fc = json.load(f)
    print("\n" + "=" * 78)
    print(f"CASO DE FALLA (ilustra el patrón general): {fc['set']}/{fc['instance']} con {fc['strategy']}")
    print(f"{fc['por_que']}")
    print("=" * 78)
    tpath = os.path.join(RESULTS, "traces", fc["set"], fc["model"], fc["strategy"], f"{fc['instance']}.jsonl")
    evs = [json.loads(line) for line in open(tpath, encoding="utf-8")]
    first = next((e for e in evs if e["tipo"] in ("explicación", "callejón")), None)
    if first:
        print(pretty(first)[:230] if first["tipo"] == "explicación" else
              f"[{first['de']} → {first['a']}] CALLEJÓN en {first['contenido']['turno']}: {first['contenido'].get('causa', '')}"[:230])
    back = [e["contenido"]["paso"] for e in evs if e["tipo"] in ("salto", "retroceso")]
    if back:
        from stepwise_solver import Problem
        from instances import instance_dir, load_instance
        p = Problem(*load_instance(os.path.join(instance_dir(fc["set"]), f"{fc['instance']}.json")))
        print(f"{len(back)} retrocesos o saltos; el más lejano volvió hasta {p.slot_name(min(back))} "
              f"(la decisión culpable está en {fc.get('culpable', '?')}).")
    for e in evs:
        if e["tipo"] in ("presupuesto agotado", "horario final"):
            print(pretty(e)[:230])
    rec_path = os.path.join(RESULTS, fc["set"], fc["model"], fc["strategy"], f"{fc['instance']}.json")
    with open(rec_path, encoding="utf-8") as f:
        v = json.load(f)["verification"]
    print(f">>> VERIFICADOR: {v['total_hard_violations']} violaciones: " + "; ".join(v["violations"][:2]))
    full = os.path.join(RESULTS, "traces", fc["set"], fc["model"], "agents", f"{fc['instance']}.jsonl")
    if fc["strategy"] != "agents" and os.path.exists(full):
        print(f"\nLa misma instancia con el sistema completo (con Diagnosticador):")
        fevs = [json.loads(line) for line in open(full, encoding="utf-8")]
        shown = [e for e in fevs if e["tipo"] in ("explicación", "salto", "horario final")]
        for e in shown[:9]:
            print(pretty(e)[:230])
        with open(os.path.join(RESULTS, fc["set"], fc["model"], "agents", f"{fc['instance']}.json"), encoding="utf-8") as f:
            fv = json.load(f)["verification"]
        print(f">>> VERIFICADOR: {'APROBADO (0 violaciones)' if fv['is_valid'] else fv['total_hard_violations']}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fallas", action="store_true")
    ap.add_argument("--markdown", action="store_true")
    args = ap.parse_args()
    if args.fallas:
        show_failures()
        return
    md = "\n\n".join(["## Horarios correctos (0 violaciones) por conjunto", main_table(True),
                      "## Correctos según el presupuesto de saltos (90 instancias)", budget_table(True),
                      "## Evaluación por decisión (CP-SAT offline)", decision_table()])
    if args.markdown:
        with open(os.path.join(RESULTS, "d3_summary.md"), "w", encoding="utf-8") as f:
            f.write(md + "\n")
        print(md)
        return
    print("=" * 78)
    print("RESULTADOS (mismas 90 instancias, mismo verificador; correcto = 0 violaciones)")
    print("=" * 78)
    print(main_table())
    print("\nCorrectos según el presupuesto de saltos (de 90):")
    print(budget_table())


if __name__ == "__main__":
    main()
