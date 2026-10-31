#!/usr/bin/env python3
"""
Pruebas de continuidad de Deliverable 3 (CPU, sin modelo)
---------------------------------------------------------
1. El coordinador de turnos "en modo D2" (mismo azar secuencial que la política aleatoria de D2, sin Crítico y sin
   Diagnosticador) reproduce EXACTAMENTE los horarios y retrocesos guardados en results/<conjunto>/no_llm/random:
   el sistema de agentes está construido sobre la solución de D2, no al lado de ella.
2. El verificador acepta un horario correcto (el de la corrida guardada) y detecta una perturbación de cada tipo
   (HC1..HC6): el juez funciona igual para todas las estrategias.

Uso:
    python src/test_continuity.py
"""

import copy
import json
import os
import sys

from agents import Config
from instances import BASE_DIR, list_instances, load_instance
from coordinator import ABLATIONS, run_agents
from verifier import ScheduleVerifier


def test_d2_mode() -> bool:
    same = total = 0
    for s in ("main", "stress", "hard"):
        for path in list_instances(s):
            iid = os.path.basename(path)[:-5]
            ref_path = os.path.join(BASE_DIR, "results", s, "no_llm", "random", iid + ".json")
            if not os.path.exists(ref_path):
                continue
            sd, dm = load_instance(path)
            out = run_agents(sd, dm, None, Config(**ABLATIONS["agents_d2random"], seed=int(iid.split("_")[-1])), iid)
            with open(ref_path, encoding="utf-8") as f:
                ref = json.load(f)["output"]
            total += 1
            same += out["schedule"] == ref["schedule"] and out["backtracks"] == ref["backtracks"]
    print(f"[1] modo D2: {same}/{total} horarios y retrocesos idénticos a D2 (política al azar)")
    return total > 0 and same == total


def test_verifier() -> bool:
    path = list_instances("main")[0]
    sd, dm = load_instance(path)
    with open(os.path.join(BASE_DIR, "results", "main", "no_llm", "random", "inst_00.json"), encoding="utf-8") as f:
        good = json.load(f)["output"]["schedule"]
    v = ScheduleVerifier(sd, dm)
    ok = v.evaluate(good)["is_valid"]
    staff = {x["id"]: x for x in sd["staff"]}
    days, shifts = dm["days"], dm["shifts"]
    caught = {}

    def first_slot_with(pred):
        for d in days:
            for t in shifts:
                for i in good[d][t]:
                    if pred(d, t, i):
                        return d, t, i
        return None

    # HC1: alguien de Noche el lunes pasa a la Mañana del martes
    bad = copy.deepcopy(good)
    i = bad["Monday"]["Night"][0]
    bad["Tuesday"]["Morning"][0] = i
    caught["HC1"] = v.evaluate(bad)["violations_by_type"]["HC1"] > 0
    # HC2: el mismo médico en dos turnos del lunes
    bad = copy.deepcopy(good)
    bad["Monday"]["Afternoon"][0] = bad["Monday"]["Morning"][0]
    caught["HC2"] = v.evaluate(bad)["violations_by_type"]["HC2"] > 0
    # HC3: falta un médico
    bad = copy.deepcopy(good)
    bad["Wednesday"]["Morning"] = bad["Wednesday"]["Morning"][:1]
    caught["HC3"] = v.evaluate(bad)["violations_by_type"]["HC3"] > 0
    # HC4: se cambia al especialista exigido por un General
    bad = copy.deepcopy(good)
    t = next(t for t in shifts if any(n for n in dm["requirements_per_shift"][t]["specialty_requirements"].values()))
    sp = next(sp for sp, n in dm["requirements_per_shift"][t]["specialty_requirements"].items() if n)
    gen = next(x["id"] for x in sd["staff"] if x["specialty"] == "General" and x["id"] not in sum(bad["Thursday"].values(), []))
    bad["Thursday"][t] = [gen if staff[i]["specialty"] == sp else i for i in bad["Thursday"][t]]
    caught["HC4"] = v.evaluate(bad)["violations_by_type"]["HC4"] > 0
    # HC5: un médico en todos los turnos de mañana (7 > tope)
    bad = copy.deepcopy(good)
    for d in days:
        bad[d]["Morning"][0] = "DOC_10"
    caught["HC5"] = v.evaluate(bad)["violations_by_type"]["HC5"] > 0
    # HC6: alguien en una franja que bloqueó
    bad = copy.deepcopy(good)
    blocked = next((x["id"], x["unavailable"][0]) for x in sd["staff"] if x["unavailable"])
    d, t = blocked[1].split("_")
    bad[d][t][0] = blocked[0]
    caught["HC6"] = v.evaluate(bad)["violations_by_type"]["HC6"] > 0
    print(f"[2] verificador: horario correcto aceptado={ok}; perturbaciones detectadas: "
          + ", ".join(f"{k}={'sí' if c else 'NO'}" for k, c in caught.items()))
    return ok and all(caught.values())


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    results = [test_d2_mode(), test_verifier()]
    print("TODAS LAS PRUEBAS PASAN" if all(results) else "HAY PRUEBAS QUE FALLAN")
    sys.exit(0 if all(results) else 1)
