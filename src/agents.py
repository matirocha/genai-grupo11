#!/usr/bin/env python3
"""
Los tres agentes del sistema (Deliverable 3)
--------------------------------------------
Cada agente es una llamada al mismo modelo (Llama-3.2-3B-Instruct) con su rol, su prompt versionado
(prompts/<agente>.md) y una entrada/salida definidas. Su respuesta es UNA etiqueta de un menú numerado, elegida
con decodificación restringida de 1 token (LLM.score), y esa etiqueta decide qué pasa después:

  Asignador       elige la opción del turno (o, tras un rechazo, otra opción o mantener la suya).
  Crítico         con las alertas de `perfilar`: aceptar (se fija), rechazar (vuelve al Asignador) o sondear
                  (llama a la herramienta `sondear` y vuelve a decidir).
  Diagnosticador  ante un callejón, con la explicación de `explicar_callejon`: a qué turno pasado saltar y qué
                  médico prohibir allí, o retroceder solo al turno anterior (lo que hacía Deliverable 2).

Cada agente tiene además dos políticas de control sin LLM en el MISMO espacio de acciones: "random" (azar
uniforme) y "rules" (una heurística fija). Sirven para medir qué aporta el modelo.
"""

import random
import zlib
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from agent_core import Prompt, Trace
from stepwise_solver import Option, State
from tools import over_quota, profile

KEEP = "0"


@dataclass
class Config:
    policy: str = "llm"       # llm | random | rules
    critic: bool = True       # Crítico (CRITIC + Self-Refine)
    diag: bool = True         # Diagnosticador (si False: siempre retrocede al turno anterior, como D2)
    memory: bool = True       # lecciones (Reflexion)
    fewshot: bool = True      # ejemplos en los prompts (Few-Shot)
    ensemble: bool = True     # dos órdenes del menú del Asignador, se suman las log-probs (ensamble por permutación)
    seed: int = 0
    policies: Optional[Dict[str, str]] = None   # política por agente para controles mixtos, p. ej. {"A3": "rules"}


def stable_rng(*parts) -> random.Random:
    return random.Random(zlib.crc32("|".join(map(str, parts)).encode()))


def fmt_option(st: State, k: int, o: Option) -> str:
    p = st.p
    who = " + ".join(f"{i} ({p.by_id[i]['specialty']})" for i in o)
    return f"{who} | especialistas sobre la cuota: {over_quota(p, k, o)}"


def state_table(st: State, k: int, menu: List[Option]) -> List[str]:
    """La misma tabla de estado que recibía el LLM en Deliverable 2."""
    p = st.p
    di, t = p.slots[k]
    need, mins = p.req[t]["required_total"], p.spec_mins(t)
    req_txt = f"exactamente {need} médicos" + "".join(f", al menos {n} {sp}" for sp, n in mins.items())
    lines = [f"Turno actual: {p.days[di]} {t} (paso {k + 1} de {len(p.slots)}). Se requieren {req_txt}.",
             "Especialidades con cuota (turnos obligatorios que faltan incluyendo este | capacidad restante):"]
    for sp, dem, cap in st.scarcity(k):
        lines.append(f"- {sp}: {dem} | {cap}")
    lines.append("Médicos candidatos (ID | especialidad | turnos usados/máx | días futuros disponibles):")
    for i in sorted({i for o in menu for i in o}):
        fut = sum(1 for dj in range(di + 1, len(p.days))
                  if any(f"{p.days[dj]}_{tt}" not in p.blocked[i] for tt in p.shifts))
        lines.append(f"{i} | {p.by_id[i]['specialty']} | {st.used[i]}/{p.max_shifts[i]} | {fut}")
    return lines


class Agent:
    name = "?"
    prompt_name = "?"
    key = "?"

    def __init__(self, llm, cfg: Config, trace: Trace, inst_id: str):
        self.llm, self.cfg, self.trace, self.inst = llm, cfg, trace, inst_id
        self.policy = (cfg.policies or {}).get(self.key, cfg.policy)
        self.prompt = Prompt(self.prompt_name)
        self.calls = 0

    def sections(self) -> List[str]:
        out = ["Rol", "Reglas"]
        if self.cfg.fewshot:
            out.append("Ejemplos")
        if self.cfg.memory:
            out.append("Memoria")
        return out

    def ask(self, user: str, labels: List[str], extra: Optional[List[str]] = None) -> List[float]:
        """Una pasada del modelo. El prompt de sistema es la concatenación de las secciones `self.last_sections`
        del archivo prompts/<agente>.md (cuya versión y sha quedan en la traza)."""
        self.last_sections = self.sections() + (extra or [])
        system = self.prompt.build(self.last_sections)
        self.calls += 1
        return self.llm.score([{"role": "system", "content": system}, {"role": "user", "content": user}], labels)


# ----------------------------------------------------------------------------------------------
class Asignador(Agent):
    name, prompt_name, key = "Asignador", "asignador", "A1"

    def observe(self, st: State, k: int, menu: List[Option], lessons: List[str],
                feedback: Optional[str]) -> str:
        lines = state_table(st, k, menu)
        if self.cfg.memory and lessons:
            lines += ["Lecciones de callejones anteriores:"] + [f"- {x}" for x in lessons]
        if feedback:
            lines += [feedback]
        lines.append("Opciones:")
        lines += [f"{n}. {fmt_option(st, k, o)}" for n, o in enumerate(menu, 1)]
        if feedback:
            lines.append(f"{KEEP}. Mantener mi propuesta anterior.")
        lines.append("Responde solo con el número de la opción.")
        return "\n".join(lines)

    def choose(self, st: State, k: int, menu: List[Option], lessons: List[str], visit: int,
               feedback: Optional[str] = None, rejected: Optional[Option] = None) -> Tuple[Optional[Option], Dict]:
        """Devuelve (opción elegida, info). Con `feedback` (tras un rechazo), None = mantener la propuesta."""
        rng = stable_rng(self.cfg.seed, self.inst, k, visit, len(menu), "A1")
        if self.policy == "random":
            pick = rng.randrange(len(menu) + (1 if feedback else 0))
            return (menu[pick] if pick < len(menu) else None), {"politica": "azar"}
        if self.policy == "rules":
            feats = {o: profile(st, k, o) for o in menu}
            best = min(menu, key=lambda o: (feats[o]["sobre_cuota"] > 0, -feats[o]["nv"], feats[o]["sin_margen"]))
            return best, {"politica": "reglas"}
        order = list(range(len(menu)))
        rng.shuffle(order)
        orders = [order, order[::-1]] if self.cfg.ensemble and len(menu) > 1 else [order]
        total = [0.0] * (len(menu) + 1)
        texts = []
        for od in orders:
            shown = [menu[i] for i in od]
            labels = [str(n) for n in range(1, len(shown) + 1)] + ([KEEP] if feedback else [])
            user = self.observe(st, k, shown, lessons, feedback)
            lp = self.ask(user, labels, extra=["Revisión"] if feedback else None)
            for pos, i in enumerate(od):
                total[i] += lp[pos]
            if feedback:
                total[-1] += lp[-1]
            texts.append(user)
        cands = range(len(menu) + (1 if feedback else 0))
        pick = max(cands, key=lambda i: total[i])
        info = {"politica": "llm", "ordenes": len(orders), "logprob": round(total[pick] / len(orders), 3),
                "etiqueta": str(orders[0].index(pick) + 1) if pick < len(menu) else KEEP,
                "secciones": self.last_sections, "observacion": texts}
        return (menu[pick] if pick < len(menu) else None), info


# ----------------------------------------------------------------------------------------------
ACCEPT, REJECT, PROBE = "aceptar", "rechazar", "sondear"
CRITIC_LABELS = {"1": ACCEPT, "2": REJECT, "3": PROBE}


class Critico(Agent):
    name, prompt_name, key = "Crítico", "critico", "A2"

    def observe(self, st: State, k: int, report: Dict, probe: Optional[Dict], lessons: List[str]) -> str:
        p = st.p
        me, alt = report["rasgos"], report["alternativa"]
        best = report["mejor"] or {"sobre_cuota": "-", "nv": "-", "sin_margen": "-"}
        nxt = p.slot_name(k + 1) if k + 1 < len(p.slots) else "fin de semana"
        lines = [f"Turno actual: {p.slot_name(k)} (paso {k + 1} de {len(p.slots)}).",
                 f"Propuesta del Asignador: {' + '.join(report['propuesta'])}. Alertas: {', '.join(report['alertas'])}.",
                 (f"Mejor alternativa (la que deja más opciones al turno siguiente): {' + '.join(alt['opcion'])}."
                  if alt else "No hay alternativa."),
                 f"- Especialistas sobre la cuota: propuesta {me['sobre_cuota']} | mejor alternativa {best['sobre_cuota']}",
                 f"- Opciones viables en el turno siguiente ({nxt}): propuesta {me['nv']} | mejor alternativa {best['nv']}",
                 f"- Turnos futuros sin margen de especialistas: propuesta {me['sin_margen']} | mejor alternativa {best['sin_margen']}"]
        if probe:
            lines.append(f"- Sondeo (continuaciones viables a 2 turnos): propuesta {probe['propuesta']} | "
                         f"mejor alternativa {probe.get('alternativa', '-')}")
        if self.cfg.memory and lessons:
            lines += ["Lecciones de callejones anteriores:"] + [f"- {x}" for x in lessons]
        lines.append("Responde 1 (aceptar), 2 (rechazar)" + ("." if probe else " o 3 (sondear)."))
        return "\n".join(lines)

    def decide(self, st: State, k: int, report: Dict, probe: Optional[Dict], lessons: List[str],
               visit: int) -> Tuple[str, Dict]:
        labels = ["1", "2"] + ([] if probe else ["3"])
        if self.policy == "random":
            rng = stable_rng(self.cfg.seed, self.inst, k, visit, len(report["alertas"]), probe is None, "A2")
            return CRITIC_LABELS[rng.choice(labels)], {"politica": "azar"}
        if self.policy == "rules":
            return (REJECT if "R2" in report["alertas"] else ACCEPT), {"politica": "reglas"}
        user = self.observe(st, k, report, probe, lessons)
        lp = self.ask(user, labels)
        pick = labels[max(range(len(labels)), key=lambda i: lp[i])]
        return CRITIC_LABELS[pick], {"politica": "llm", "etiqueta": pick, "logprob": round(max(lp), 3),
                                     "secciones": self.last_sections, "observacion": user}


# ----------------------------------------------------------------------------------------------
class Diagnosticador(Agent):
    name, prompt_name, key = "Diagnosticador", "diagnosticador", "A3"

    def observe(self, expl: Dict, lessons: List[str]) -> str:
        sp = expl["razon"]["especialidad"]
        lines = [f"Callejón en {expl['turno_callejon']} (paso {expl['paso'] + 1} de 21). Causa: {expl['causa']}.",
                 f"Médicos de {sp}:" if sp else "Médicos:"]
        for d in expl["medicos"]:
            worked = f" Trabajó {', '.join(d['turnos'])}." if d["turnos"] else ""
            lines.append(f"- {d['id']}: {'; '.join(d['por_que'])}.{worked}")
        lines.append("Candidatos (decisiones pasadas que se pueden rehacer; elegir una deshace todo desde ese turno):")
        for n, c in enumerate(expl["candidatos"], 1):
            inv = f"involucra a {', '.join(c['involucra'])}" if c["involucra"] else "no involucra a médicos del conflicto"
            over = ", ".join(c["sobre_cuota"]) if c["sobre_cuota"] else "nadie"
            lines.append(f"{n}. {c['turno']} | {' + '.join(c['asignados'])} | {inv} | sobre la cuota: {over} | "
                         f"{c['distancia']} turnos atrás")
        if self.cfg.memory and lessons:
            lines += ["Lecciones de callejones anteriores:"] + [f"- {x}" for x in lessons]
        lines.append("Responde solo con el número del candidato.")
        return "\n".join(lines)

    def decide(self, expl: Dict, lessons: List[str], visit: int) -> Tuple[Optional[Dict], Dict]:
        """Devuelve el candidato elegido, o None para retroceder al turno anterior."""
        cands = expl["candidatos"]
        if not self.cfg.diag or not cands:
            return None, {"politica": "anterior"}
        if self.policy == "random":
            rng = stable_rng(self.cfg.seed, self.inst, expl["paso"], visit, len(cands), "A3")
            return rng.choice(cands), {"politica": "azar"}
        if self.policy == "rules":
            # backjumping dirigido por conflicto: la decisión más reciente que involucra a un médico del conflicto
            inv = [c for c in cands if c["medico"]]
            return max(inv or cands, key=lambda c: c["paso"]), {"politica": "reglas"}
        labels = [str(n) for n in range(1, len(cands) + 1)]
        user = self.observe(expl, lessons)
        lp = self.ask(user, labels)
        best = max(range(len(labels)), key=lambda i: lp[i])
        info = {"politica": "llm", "etiqueta": labels[best], "logprob": round(lp[best], 3),
                "secciones": self.last_sections, "observacion": user}
        return cands[best], info
