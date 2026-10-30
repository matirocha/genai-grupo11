#!/usr/bin/env python3
"""
Evaluación del modelo decisión por decisión (offline; CP-SAT solo como oráculo)
-------------------------------------------------------------------------------
Responde al comentario del profesor sobre Deliverable 2 ("cómo se evalúa el modelo"). Además del resultado final
(horario correcto o no), se juzga CADA decisión de cada agente reconstruyendo el estado desde su traza:

  Asignador       ¿la opción elegida deja la semana con solución? Solo cuenta en estados "discriminantes": el
                  prefijo aún tiene solución y el menú trae opciones fatales y opciones completables. Se compara con
                  lo que haría el azar en el MISMO menú (fracción de opciones fatales).
  Crítico         matriz de confusión: rechazar una propuesta fatal es un acierto; rechazar una completable, un error.
  Diagnosticador  un salto es útil si deshace la decisión culpable (el prefijo que queda vuelve a tener solución).
                  Se compara con el azar entre los mismos candidatos y con retroceder solo al turno anterior (D2).

Uso:
    python src/oracle_eval.py --runs hard/llama-3.2-3b/agents,hard/no_llm/agents_random
    python src/oracle_eval.py --runs "*/llama-3.2-3b/agents"        # los tres conjuntos evaluados juntos
    python src/oracle_eval.py --runs ... --out parcial.json; python src/oracle_eval.py --merge a.json,b.json
"""

import argparse
import json
import os
import sys
from collections import defaultdict
from typing import Dict, List

from diagnose import completable
from instances import BASE_DIR, instance_dir, load_instance

RESULTS_DIR = os.path.join(BASE_DIR, "results")
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


class Oracle:
    def __init__(self, staff, demands):
        self.staff, self.demands = staff, demands
        self.cache: Dict = {}

    def ok(self, fixed: Dict[int, List[str]]) -> bool:
        key = tuple(sorted((k, tuple(sorted(v))) for k, v in fixed.items()))
        if key not in self.cache:
            self.cache[key] = completable(self.staff, self.demands, fixed)
        return self.cache[key]

    def repairable(self, prefix: Dict[int, List[str]], x: int, doc) -> bool:
        """¿Hay en el turno x una opción viable con solución distinta de la anterior (y sin `doc`, si queda alguna)?"""
        from stepwise_solver import Problem, State
        from tools import viable
        base = {j: prefix[j] for j in range(x)}
        if not self.ok(base):
            return False
        st = State(Problem({"staff": self.staff}, self.demands))
        for j in range(x):
            st.apply(j, tuple(prefix[j]))
        opts = [o for o in viable(st, x) if set(o) != set(prefix[x])]
        if doc:
            kept = [o for o in opts if doc not in o]
            opts = kept or opts
        return any(self.ok({**base, x: list(o)}) for o in opts)


def read_trace(path: str) -> List[Dict]:
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def eval_instance(inst_set: str, inst_id: str, events: List[Dict]) -> Dict:
    staff_data, demands = load_instance(os.path.join(instance_dir(inst_set), f"{inst_id}.json"))
    orc = Oracle(staff_data["staff"], demands)
    out = {"a1": [], "a2": [], "a3": []}
    last_prop = {}
    last_expl = None
    visit = None     # decisión en curso: estado, menú y opción finalmente fijada (tras el Crítico)

    def close_visit():
        if visit and visit.get("disc") is not None:
            final_ok = orc.ok({**visit["prefix"], visit["k"]: visit["final"]})
            out["a1"][visit["idx"]]["final_fatal"] = not final_ok

    for ev in events:
        if ev["de"] == "Asignador" and ev["tipo"] == "mantiene" and visit:
            visit["final"] = ev["contenido"]["opcion"]
            continue
        if ev["de"] == "Asignador" and ev["tipo"] == "propuesta" and "estado" in ev:
            prefix = {k: ids for k, ids in ev["estado"]}
            k = ev["contenido"]["paso"]
            if ev.get("ronda", 0) > 0 or "opciones" not in ev:
                last_prop = {"prefix": prefix, "k": k, "opcion": ev["contenido"]["opcion"]}
                if visit and visit["k"] == k:
                    visit["final"] = ev["contenido"]["opcion"]
                continue
            close_visit()
            visit = None
            if not orc.ok(prefix):
                last_prop = {"prefix": prefix, "k": k, "opcion": ev["contenido"]["opcion"], "perdido": True}
                continue
            labels = [orc.ok({**prefix, k: o}) for o in ev["opciones"]]
            chosen_ok = orc.ok({**prefix, k: ev["contenido"]["opcion"]})
            out["a1"].append({"k": k, "n": len(labels), "fatal_frac": 1 - sum(labels) / len(labels),
                              "chosen_fatal": not chosen_ok, "final_fatal": not chosen_ok,
                              "disc": 0 < sum(labels) < len(labels)})
            visit = {"prefix": prefix, "k": k, "final": ev["contenido"]["opcion"], "idx": len(out["a1"]) - 1,
                     "disc": out["a1"][-1]["disc"]}
            last_prop = {"prefix": prefix, "k": k, "opcion": ev["contenido"]["opcion"]}
        elif ev["de"] == "Crítico" and ev["tipo"] in ("aceptar", "rechazar") and last_prop:
            if last_prop.get("perdido") or not orc.ok(last_prop["prefix"]):
                continue
            fatal = not orc.ok({**last_prop["prefix"], last_prop["k"]: last_prop["opcion"]})
            out["a2"].append({"k": last_prop["k"], "rechaza": ev["tipo"] == "rechazar", "fatal": fatal})
        elif ev["de"] == "explicar_callejon" or ev["tipo"] == "callejón":
            last_expl = ev
        elif ev["de"] in ("Diagnosticador", "Orquestador") and ev["tipo"] in ("salto", "retroceso") and last_expl:
            prefix = {k: ids for k, ids in last_expl["estado"]}
            k = last_expl["contenido"]["paso"]
            culprit = None
            for c in range(k):
                if not orc.ok({j: prefix[j] for j in range(c + 1)}):
                    culprit = c
                    break
            j = ev["contenido"]["paso"]
            pasos = last_expl.get("pasos", [])
            medicos = last_expl.get("medicos", [None] * len(pasos))

            def useful(x, doc):
                """El salto a x sirve si deshace la culpable (x <= culpable) y en x queda alguna opción con solución
                que el salto no prohíbe (se prohíbe la opción anterior de x y, si se aplica, al médico)."""
                if culprit is None or x > culprit:
                    return False
                return orc.repairable(prefix, x, doc)
            # el azar elige uniforme entre los candidatos de T4 (que ya incluyen el turno k-1)
            choices = list(zip(pasos, medicos)) or [(k - 1, None)]
            util = useful(j, ev["contenido"].get("prohibir"))
            out["a3"].append({"k": k, "j": j, "culprit": culprit, "util": util,
                              "azar": sum(useful(x, d) for x, d in choices) / len(choices),
                              "anterior_util": useful(k - 1, None),
                              "algun_candidato_util": any(useful(x, d) for x, d in choices),
                              "salto": ev["tipo"] == "salto"})
            last_expl = None
    close_visit()
    return out


def summarize(run: str, per_inst: Dict[str, Dict]) -> Dict:
    a1 = [d for r in per_inst.values() for d in r["a1"]]
    disc = [d for d in a1 if d["disc"]]
    a2 = [d for r in per_inst.values() for d in r["a2"]]
    a3 = [d for r in per_inst.values() for d in r["a3"] if d["culprit"] is not None]
    s = {"run": run, "instancias": len(per_inst),
         "a1_decisiones": len(a1), "a1_discriminantes": len(disc),
         "a1_fatal": round(sum(d["chosen_fatal"] for d in disc) / len(disc), 3) if disc else None,
         "a1a2_fatal": round(sum(d["final_fatal"] for d in disc) / len(disc), 3) if disc else None,
         "a1_fatal_azar": round(sum(d["fatal_frac"] for d in disc) / len(disc), 3) if disc else None}
    if a2:
        tp = sum(d["rechaza"] and d["fatal"] for d in a2)
        fp = sum(d["rechaza"] and not d["fatal"] for d in a2)
        fn = sum(not d["rechaza"] and d["fatal"] for d in a2)
        tn = sum(not d["rechaza"] and not d["fatal"] for d in a2)
        s.update({"a2_decisiones": len(a2), "a2_vp": tp, "a2_fp": fp, "a2_fn": fn, "a2_vn": tn,
                  "a2_tasa_rechazo": round((tp + fp) / len(a2), 3),
                  "a2_fatales": tp + fn,
                  "a2_recall": round(tp / (tp + fn), 3) if tp + fn else None,
                  "a2_precision": round(tp / (tp + fp), 3) if tp + fp else None})
    if a3:
        s.update({"a3_callejones": len(a3),
                  "a3_util": round(sum(d["util"] for d in a3) / len(a3), 3),
                  "a3_util_azar": round(sum(d["azar"] for d in a3) / len(a3), 3),
                  "a3_util_anterior": round(sum(d["anterior_util"] for d in a3) / len(a3), 3),
                  "a3_cobertura": round(sum(d["algun_candidato_util"] for d in a3) / len(a3), 3)})
    return s


def table(rows: List[Dict]) -> str:
    def f(x):
        return "-" if x is None else (f"{100 * x:.0f}%" if isinstance(x, float) else str(x))
    lines = ["| configuración | estados que deciden | elección fatal: Asignador / tras el Crítico / azar en el mismo menú | Crítico: rechazos de fatales / rechazos, fatales interceptadas | saltos útiles (azar entre candidatos, retroceder 1) |",
             "|---|---|---|---|---|"]
    for r in rows:
        a1 = (f"{f(r['a1_fatal'])} / {f(r.get('a1a2_fatal'))} / {f(r['a1_fatal_azar'])}"
              if r["a1_discriminantes"] else "-")
        a2 = (f"{r['a2_vp']}/{r['a2_vp'] + r['a2_fp']}, {r['a2_vp']}/{r['a2_fatales']}" if r.get("a2_decisiones") else "-")
        a3 = (f"{f(r['a3_util'])} ({f(r['a3_util_azar'])}, {f(r['a3_util_anterior'])}) en {r['a3_callejones']} callejones"
              if r.get("a3_callejones") else "-")
        lines.append(f"| {r['run']} | {r['a1_discriminantes']} | {a1} | {a2} | {a3} |")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", default=None,
                    help="conjunto/modelo/estrategia separados por comas; '*' como conjunto junta principal, estrés y difícil")
    ap.add_argument("--out", default=os.path.join(RESULTS_DIR, "oracle_eval.json"),
                    help="JSON de salida (por defecto results/oracle_eval.json, que se reescribe)")
    ap.add_argument("--merge", default=None, help="une JSON parciales (separados por comas) en results/oracle_eval.*")
    args = ap.parse_args()
    rows = []
    if args.merge:
        for path in args.merge.split(","):
            with open(path, encoding="utf-8") as f:
                rows += json.load(f)
        args.out = os.path.join(RESULTS_DIR, "oracle_eval.json")
    else:
        for run in args.runs.split(","):
            inst_sets, rest = run.split("/", 1)
            per = {}
            for inst_set in (["main", "stress", "hard"] if inst_sets == "*" else [inst_sets]):
                tdir = os.path.join(RESULTS_DIR, "traces", inst_set, rest)
                if not os.path.isdir(tdir):
                    continue
                for fn in sorted(os.listdir(tdir)):
                    per[f"{inst_set}/{fn[:-6]}"] = eval_instance(inst_set, fn[:-6], read_trace(os.path.join(tdir, fn)))
            rows.append(summarize(run, per))
            print(json.dumps(rows[-1], ensure_ascii=False), flush=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(rows, f, indent=1, ensure_ascii=False)
    if os.path.abspath(args.out) == os.path.abspath(os.path.join(RESULTS_DIR, "oracle_eval.json")):
        text = table(rows)
        with open(os.path.join(RESULTS_DIR, "oracle_eval.md"), "w", encoding="utf-8") as f:
            f.write(text + "\n")
        print(text)


if __name__ == "__main__":
    main()
