#!/usr/bin/env python3
"""
Ejemplos few-shot del Diagnosticador (Deliverable 3), sacados SOLO del conjunto de calibración
---------------------------------------------------------------------------------------------
Corre el sistema de agentes con la política al azar (sin modelo) sobre data/instances_calib/, junta los
callejones, reconstruye cada estado y usa CP-SAT (offline) para encontrar la decisión culpable. Imprime los
callejones en los que la culpable está entre los candidatos, ya en el formato exacto que ve el Diagnosticador
(misma herramienta T4, misma función de observación) y con la respuesta correcta: el candidato que deshace la
culpable con el salto más corto. De ahí se eligieron a mano los ejemplos de prompts/diagnosticador.md.

Uso:
    python src/build_fewshot.py --max 6
"""

import argparse
import os
import sys

from agent_core import Trace
from agents import Config, Diagnosticador
from diagnose import completable
from instances import instance_dir, list_instances, load_instance
from orchestrator import run_agents
from stepwise_solver import Problem, State
from tools import explicar_callejon


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--max", type=int, default=6)
    ap.add_argument("--seeds", type=int, default=3)
    args = ap.parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    shown = 0
    diag = Diagnosticador(None, Config(memory=False), Trace(), "-")
    for seed in range(args.seeds):
        for path in list_instances("calib"):
            iid = os.path.basename(path)[:-5]
            sd, dm = load_instance(path)
            tr = Trace()
            run_agents(sd, dm, None, Config(policy="random", seed=seed), iid, tr)
            for ev in tr.events:
                if ev["de"] != "explicar_callejon":
                    continue
                prefix = {k: ids for k, ids in ev["estado"]}
                k = ev["contenido"]["paso"]
                culprit = next((c for c in range(k) if not completable(sd["staff"], dm, {j: prefix[j] for j in range(c + 1)})), None)
                if culprit is None or culprit not in ev["pasos"]:
                    continue
                st = State(Problem(sd, dm))
                for j, ids in sorted(prefix.items()):
                    st.apply(j, tuple(ids))
                expl = explicar_callejon(st, k)
                answer = [c["paso"] for c in expl["candidatos"]].index(culprit) + 1
                print(f"===== {iid} (semilla {seed}) tipo={expl['razon']['tipo']} respuesta={answer} "
                      f"de {len(expl['candidatos'])} (culpable: {st.p.slot_name(culprit)})")
                print(diag.observe(expl, []))
                print()
                shown += 1
                if shown >= args.max:
                    return


if __name__ == "__main__":
    main()
