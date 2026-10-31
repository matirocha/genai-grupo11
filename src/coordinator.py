#!/usr/bin/env python3
"""
Sistema de agentes de Deliverable 3: coordinador de turnos
---------------------------------------------------------
El coordinador de turnos es código, NO es un agente: lleva el estado (como en D2), llama a las herramientas y enruta el
trabajo según lo que deciden los agentes. Las decisiones de control las toman los agentes:

  turno k ──T1 opciones_viables──► 0 opciones ──T4 explicar_callejon──► Diagnosticador ──► saltar al turno j
     │                                                                        (o retroceder a k-1, como D2)
     ├── 1 opción: se aplica sin llamar al modelo (el trie la forzaría igual)
     └── ≥2 opciones ──► Asignador ──propuesta──T2 perfilar──► sin alertas: se fija, turno k+1
                              ▲                                 con alertas ──► Crítico ──aceptar──► se fija
                              └─────────── rechazar (máx. 2 por turno) ◄────────┘  └─sondear──T3──┘

Paradas: los 21 turnos fijados (horario certificado) o presupuesto agotado: 30 saltos, el mismo número que los 30
retrocesos de D2 (un salto puede deshacer hasta 12 decisiones; por eso se reporta también cuántas decisiones se
deshicieron y se compara con D2 al azar con 300 retrocesos). En ese caso se completa relajando reglas como en D2 y
se marca NO certificado. No hay tope de pasadas del modelo: el costo se reporta, no corta corridas.

Uso:
    python src/coordinator.py --set hard --instance hard_09
    python src/coordinator.py --set stress --instance stress_04 --strategy agents_sin_critico
"""

import argparse
import itertools
import json
import os
import time
from typing import Any, Dict, List, Optional

from agent_core import Trace
from agents import ACCEPT, PROBE, REJECT, Asignador, Config, Critico, Diagnosticador
from stepwise_solver import Option, Problem, State, random_policy
from tools import Lessons, explicar_callejon, opciones_viables, perfilar, sondear

ABLATIONS = {                       # nombre de la estrategia -> cambio respecto del sistema completo
    "agents": {},
    "agents_sin_diagnosticador": {"diag": False},
    "agents_sin_critico": {"critic": False},
    "agents_sin_memoria": {"memory": False},
    "agents_sin_fewshot": {"fewshot": False},
    "agents_sin_ensamble": {"ensemble": False},
    "agents_random": {"policy": "random"},
    "agents_rules": {"policy": "rules"},
    # prueba de continuidad: el mismo azar secuencial de D2, sin Crítico ni Diagnosticador -> idéntico a D2 al azar
    "agents_d2random": {"policy": "d2random", "critic": False, "diag": False},
}
MAX_REJECTIONS = 2


def snapshot(st: State) -> List:
    return [[k, list(o)] for k, o in sorted(st.assign.items())]


def run_agents(staff_data, demands, llm, cfg: Config, inst_id: str = "?", trace: Optional[Trace] = None,
               max_jumps: int = 30, max_passes: Optional[int] = None) -> Dict[str, Any]:
    t0 = time.time()
    trace = trace or Trace()
    p = Problem(staff_data, demands)
    st = State(p)
    n = len(p.slots)
    a1, a2, a3 = (Asignador(llm, cfg, trace, inst_id), Critico(llm, cfg, trace, inst_id),
                  Diagnosticador(llm, cfg, trace, inst_id))
    lessons = Lessons()
    banned: Dict[int, List[Option]] = {k: [] for k in range(n)}
    banned_docs: Dict[int, set] = {k: set() for k in range(n)}
    visits: Dict[int, int] = {k: 0 for k in range(n)}
    stats = {"decisions": 0, "backtracks": 0, "dead_ends": 0, "relaxed_steps": 0, "first_dead_end": None,
             "skipped_single": 0, "alerts": 0, "rejections": 0, "probes": 0, "keeps": 0, "forced": 0,
             "jumps": [], "nogood_relaxed": 0, "undone": 0, "stop": None}
    best: Dict[int, Option] = {}
    calls0 = llm.calls if llm else 0
    d2choose = random_policy(cfg.seed) if cfg.policy == "d2random" else None

    def passes():
        return (llm.calls - calls0) if llm else 0

    trace.log("Coordinador", "-", "inicio", {"instancia": inst_id, "config": cfg.__dict__,
                                              "prompts": {a.name: a.prompt.info() for a in (a1, a2, a3)}})
    k, exhausted = 0, False
    while k < n:
        menu, _ = opciones_viables(st, k, banned[k], banned_docs[k])
        if not menu:
            # ---------------- callejón: T4 + Diagnosticador ----------------
            stats["dead_ends"] += 1
            if stats["first_dead_end"] is None:
                stats["first_dead_end"] = p.slot_name(k)
            if k == 0 or stats["backtracks"] >= max_jumps or (max_passes is not None and passes() >= max_passes):
                exhausted = True
                stats["stop"] = "k0" if k == 0 else ("saltos" if stats["backtracks"] >= max_jumps else "pasadas")
                trace.log("Coordinador", "-", "presupuesto agotado",
                          {"saltos": stats["backtracks"], "pasadas": passes(), "motivo": stats["stop"]})
                break
            # T4 es una herramienta (sin LLM): siempre explica el callejón. La usa el Diagnosticador para decidir y,
            # con o sin él, la lección (T5) que leen el Asignador y el Crítico.
            expl = explicar_callejon(st, k)
            pasos = [c["paso"] for c in expl["candidatos"]]
            if cfg.diag:
                trace.log("explicar_callejon", "Diagnosticador", "explicación",
                          {"paso": k, "causa": expl["causa"], "candidatos": [
                              f"{c['turno']} | {' + '.join(c['asignados'])}"
                              + (f" | {c['medico']} ({c['causa']})" if c["medico"] else "") for c in expl["candidatos"]]},
                          estado=snapshot(st), pasos=pasos, medicos=[c["medico"] for c in expl["candidatos"]])
                cand, info = a3.decide(expl, lessons.recent(), stats["dead_ends"])
            else:   # ablación: sin Diagnosticador, el retroceso cronológico de D2 (la lección se escribe igual)
                trace.log("explicar_callejon", "Coordinador", "callejón",
                          {"paso": k, "turno": p.slot_name(k), "causa": expl["causa"]},
                          estado=snapshot(st), pasos=pasos, medicos=[c["medico"] for c in expl["candidatos"]])
                cand, info = None, {"politica": "anterior"}
            target = cand or {"paso": k - 1, "turno": p.slot_name(k - 1), "asignados": list(st.assign[k - 1]),
                              "medico": None, "causa": None}
            j = target["paso"]
            trace.log("Diagnosticador" if cfg.diag else "Coordinador", "Coordinador", "salto" if cand else "retroceso",
                      {"a": p.slot_name(j), "paso": j, "prohibir": target["medico"], "rehace": target["asignados"],
                       **{x: v for x, v in info.items() if x != "observacion"}},
                      observacion=info.get("observacion"))
            prev = None
            for s in range(k - 1, j - 1, -1):
                prev = st.assign[s]
                st.undo(s)
                if s > j:
                    banned[s], banned_docs[s] = [], set()
            banned[k], banned_docs[k] = [], set()
            banned[j].append(prev)
            applied = False
            if target["medico"]:
                before, _ = opciones_viables(st, j, banned[j], banned_docs[j])
                banned_docs[j].add(target["medico"])
                after, relaxed = opciones_viables(st, j, banned[j], banned_docs[j])
                applied = (not relaxed) and len(after) < len(before)
                if not applied:   # la prohibición del médico no restringe nada (o dejaría 0 opciones): se quita
                    banned_docs[j].discard(target["medico"])
                    stats["nogood_relaxed"] += 1
            if cfg.memory:
                lessons.write(expl, target, applied)
                trace.log("Diagnosticador" if cfg.diag else "Coordinador", "lecciones", "escribe", lessons.items[-1])
            stats["backtracks"] += 1
            stats["undone"] += k - j
            stats["jumps"].append({"desde": k, "hasta": j, "medico": target["medico"] if applied else None,
                                   "politica": info["politica"]})
            k = j
            continue

        visits[k] += 1
        if d2choose:
            choice = d2choose(st, k, menu, banned[k])
        elif len(menu) == 1:
            choice = menu[0]
            stats["skipped_single"] += 1
            trace.log("opciones_viables", "Coordinador", "única opción", {"paso": k, "turno": p.slot_name(k),
                                                                           "opcion": list(choice)})
        else:
            choice = assign_step(st, k, menu, a1, a2, cfg, lessons.recent(), visits[k], stats, trace)
        stats["decisions"] += 1
        st.apply(k, choice)
        if len(st.assign) > len(best):
            best = dict(st.assign)
        k += 1

    certified = not exhausted
    if exhausted:
        st = State(p)
        for kk in sorted(best):
            st.apply(kk, best[kk])
        for kk in range(len(best), n):
            for relax in ({}, {"check_hours": False, "check_rest": False},
                          {"check_hours": False, "check_rest": False, "check_block": False}):
                opts = st.options(kk, **relax)
                if opts:
                    break
            else:
                di, t = p.slots[kk]
                free = [s["id"] for s in p.staff if di not in st.worked[s["id"]]]
                opts = list(itertools.combinations(free, p.req[t]["required_total"]))
            if d2choose:
                choice = d2choose(st, kk, opts, [])
            else:
                choice, _ = a1.choose(st, kk, opts, [], visit=-1) if len(opts) > 1 else (opts[0], {})
            stats["decisions"] += 1
            stats["relaxed_steps"] += 1
            st.apply(kk, choice)
            trace.log("Asignador", "Coordinador", "modo relajado", {"paso": kk, "turno": p.slot_name(kk),
                                                                    "opcion": list(choice)})
    stats["seconds"] = round(time.time() - t0, 1)
    stats["llm_calls"] = passes()
    stats["agent_calls"] = {a.name: a.calls for a in (a1, a2, a3)}
    trace.log("Coordinador", "verificador", "horario final", {"certificado": certified,
                                                              "saltos": stats["backtracks"],
                                                              "pasadas_modelo": stats["llm_calls"]})
    return {"schedule": st.schedule(), "certified": certified, **stats,
            "prompts": {a.name: a.prompt.info() for a in (a1, a2, a3)}}


def assign_step(st: State, k: int, menu: List[Option], a1: Asignador, a2: Critico, cfg: Config,
                lessons: List[str], visit: int, stats: Dict, trace: Trace) -> Option:
    """Asignador propone; perfilar revisa; con alertas decide el Crítico (ciclo de revisión, máx. 2 rechazos)."""
    p = st.p
    feedback, rejected = None, None
    for round_ in range(MAX_REJECTIONS + 1):
        choice, info = a1.choose(st, k, menu, lessons, visit * 10 + round_, feedback, rejected)
        if choice is None:                      # mantener la propuesta rechazada
            stats["keeps"] += 1
            trace.log("Asignador", "Coordinador", "mantiene", {"paso": k, "opcion": list(rejected)})
            return rejected
        trace.log("Asignador", "perfilar" if cfg.critic else "Coordinador", "propuesta",
                  {"paso": k, "turno": p.slot_name(k), "opcion": list(choice), "menu": len(menu),
                   **{x: v for x, v in info.items() if x != "observacion"}},
                  estado=snapshot(st), opciones=[list(o) for o in menu], ronda=round_,
                  observacion=info.get("observacion"))
        if not cfg.critic or round_ == MAX_REJECTIONS:
            if round_ == MAX_REJECTIONS:
                stats["forced"] += 1
            return choice
        report = perfilar(st, k, menu, choice)
        if not report["alertas"]:
            return choice
        stats["alerts"] += 1
        trace.log("perfilar", "Crítico", "alertas", {"paso": k, "alertas": report["alertas"],
                                                       "propuesta": report["rasgos"], "mejor": report["mejor"],
                                                       "alternativa": report["alternativa"]})
        probe = None
        verdict, cinfo = a2.decide(st, k, report, probe, lessons, visit * 10 + round_)
        if verdict == PROBE:
            trace.log("Crítico", "sondear", "sondear", {"paso": k, **{x: v for x, v in cinfo.items() if x != "observacion"}},
                      observacion=cinfo.get("observacion"))
            stats["probes"] += 1
            alt = tuple(report["alternativa"]["opcion"]) if report["alternativa"] else None
            probe = sondear(st, k, choice, alt)
            trace.log("sondear", "Crítico", "resultado", {"paso": k, **probe})
            verdict, cinfo = a2.decide(st, k, report, probe, lessons, visit * 10 + round_)
        trace.log("Crítico", "Coordinador" if verdict == ACCEPT else "Asignador", verdict,
                  {"paso": k, **{x: v for x, v in cinfo.items() if x != "observacion"}},
                  observacion=cinfo.get("observacion"))
        if verdict == ACCEPT:
            return choice
        stats["rejections"] += 1
        rejected = choice
        menu = [o for o in menu if o != choice]
        if not menu:
            stats["forced"] += 1
            return choice
        me, best = report["rasgos"], report["mejor"] or {}
        feedback = (f"El Crítico rechazó tu propuesta {' + '.join(choice)} (alertas {', '.join(report['alertas'])}: "
                    f"deja {me['nv']} opciones para el turno siguiente, frente a {best.get('nv', '-')} de la mejor "
                    f"alternativa, y usa {me['sobre_cuota']} especialistas sobre la cuota). Ya no está en el menú.")
    return choice


def main():
    from instances import instance_dir, load_instance
    from verifier import ScheduleVerifier
    ap = argparse.ArgumentParser()
    ap.add_argument("--set", default="hard", choices=["main", "stress", "hard", "calib"])
    ap.add_argument("--instance", default="hard_09")
    ap.add_argument("--strategy", default="agents", choices=list(ABLATIONS))
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()
    staff_data, demands = load_instance(os.path.join(instance_dir(args.set), f"{args.instance}.json"))
    cfg = Config(**ABLATIONS[args.strategy])
    llm = None
    if cfg.policy == "llm":
        from llm import LLM
        llm = LLM()
    trace = Trace(echo=None if args.quiet else print)
    out = run_agents(staff_data, demands, llm, cfg, args.instance, trace)
    res = ScheduleVerifier(staff_data, demands).evaluate(out["schedule"])
    print(json.dumps({k: v for k, v in out.items() if k not in ("schedule", "jumps", "prompts")}, ensure_ascii=False))
    print(f"VERIFICADOR: {'APROBADO' if res['is_valid'] else 'FALLIDO'} — {res['total_hard_violations']} violaciones")


if __name__ == "__main__":
    main()
