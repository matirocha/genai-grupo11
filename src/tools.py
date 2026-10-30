#!/usr/bin/env python3
"""
Herramientas del sistema de agentes (Deliverable 3)
---------------------------------------------------
Todas INFORMAN: calculan números sobre el estado y se los entregan a un agente. Ninguna busca una solución ni
filtra más que la solución de Deliverable 2, cuyo código (src/stepwise_solver.py) se reutiliza sin cambios.

  T1 opciones_viables   la de D2: filtro legal (HC1, HC2, HC5, HC6) + combinaciones (HC3, HC4) + chequeo hacia
                        adelante (future_ok), menos las opciones prohibidas por retrocesos anteriores.
  T2 perfilar           rasgos de cada opción (especialistas sobre cuota, opciones que deja en el turno siguiente,
                        turnos futuros sin margen de especialistas) y alertas de la propuesta frente a las alternativas.
  T3 sondear            continuaciones viables a 2 turnos de la propuesta y de la mejor alternativa (conteos).
  T4 explicar_callejon  qué requisito ya no se puede cubrir, qué médicos faltan y por qué (HC1/HC2/HC5), y qué
                        decisiones pasadas lo causaron: los candidatos para rehacer.
  T5 lecciones          memoria verbal (plantilla) que escribe el Diagnosticador y leen Asignador y Crítico.
"""

from collections import Counter
from typing import Dict, List, Optional, Tuple

from stepwise_solver import Option, Problem, State


# ----------------------------------------------------------------------------------------------
# T1: opciones viables (D2)
# ----------------------------------------------------------------------------------------------
def viable(st: State, k: int, lookahead: bool = True) -> List[Option]:
    opts = st.options(k)
    if not lookahead:
        return opts
    out = []
    for o in opts:
        st.apply(k, o)
        if st.future_ok(k):
            out.append(o)
        st.undo(k)
    return out


def opciones_viables(st: State, k: int, banned: List[Option], banned_docs: set, lookahead: bool = True
                     ) -> Tuple[List[Option], bool]:
    """Opciones de D2 menos las prohibidas. Si la prohibición por médico deja 0 opciones, se ignora (y se avisa)."""
    opts = [o for o in viable(st, k, lookahead) if o not in banned]
    if banned_docs:
        kept = [o for o in opts if not set(o) & banned_docs]
        if kept:
            return kept, False
        return opts, bool(opts)
    return opts, False


# ----------------------------------------------------------------------------------------------
# T2: perfilar
# ----------------------------------------------------------------------------------------------
def quota_specialties(p: Problem) -> set:
    """Especialidades escasas: las que tienen cuota en algún turno de la semana, salvo General (la cuota de
    General, cuando existe, la cubre el grueso del personal; no es un recurso escaso)."""
    return {sp for t in p.shifts for sp in p.spec_mins(t)} - {"General"}


def over_quota(p: Problem, k: int, opt: Option) -> int:
    """Especialistas (de una especialidad escasa) por encima de lo que exige este turno."""
    _, t = p.slots[k]
    mins, scarce = p.spec_mins(t), quota_specialties(p)
    cnt = Counter(p.by_id[i]["specialty"] for i in opt)
    return sum(max(0, n - mins.get(sp, 0)) for sp, n in cnt.items() if sp in scarce)


def tight_slots(st: State, k: int) -> int:
    """Turnos futuros (después de k) con alguna cuota de especialidad sin margen: tantos elegibles como exige."""
    p = st.p
    n = 0
    for j in range(k + 1, len(p.slots)):
        di, t = p.slots[j]
        for sp, need in p.spec_mins(t).items():
            elig = sum(1 for i in st.used if p.by_id[i]["specialty"] == sp and st.used[i] < p.max_shifts[i]
                       and st.can_work(i, di, t, check_hours=False))
            if elig <= need:
                n += 1
                break
    return n


def profile(st: State, k: int, opt: Option) -> Dict[str, int]:
    p = st.p
    st.apply(k, opt)
    nv = len(viable(st, k + 1)) if k + 1 < len(p.slots) else 1
    tight = tight_slots(st, k)
    st.undo(k)
    return {"sobre_cuota": over_quota(p, k, opt), "nv": nv, "sin_margen": tight}


def perfilar(st: State, k: int, menu: List[Option], proposal: Option) -> Dict:
    """Rasgos de la propuesta frente a LA mejor alternativa que sigue en el menú: la que deja más opciones viables al
    turno siguiente (a igualdad, menos especialistas sobre la cuota y menos turnos sin margen). Las tres alertas
    comparan contra esa misma alternativa, que es la que ve el Crítico y la que se sondea."""
    feats = {o: profile(st, k, o) for o in menu}
    me = feats[proposal]
    alts = {o: f for o, f in feats.items() if o != proposal}
    report = {"propuesta": list(proposal), "rasgos": me, "alertas": [], "alternativa": None, "mejor": None}
    if not alts:
        return report
    best = max(alts, key=lambda o: (alts[o]["nv"], -alts[o]["sobre_cuota"], -alts[o]["sin_margen"]))
    report["alternativa"] = {"opcion": list(best), "rasgos": alts[best]}
    mejor = alts[best]
    report["mejor"] = mejor
    if me["sobre_cuota"] > mejor["sobre_cuota"]:
        report["alertas"].append("R1")
    if me["nv"] < 0.5 * mejor["nv"] or (me["nv"] <= 1 and mejor["nv"] >= 2):
        report["alertas"].append("R2")
    if me["sin_margen"] > mejor["sin_margen"]:
        report["alertas"].append("R3")
    return report


# ----------------------------------------------------------------------------------------------
# T3: sondear (2 turnos)
# ----------------------------------------------------------------------------------------------
def two_step(st: State, k: int, opt: Option) -> int:
    p = st.p
    if k + 1 >= len(p.slots):
        return 1
    st.apply(k, opt)
    total = 0
    nxt = viable(st, k + 1)
    if k + 2 >= len(p.slots):
        total = len(nxt)
    else:
        for o in nxt:
            st.apply(k + 1, o)
            total += len(viable(st, k + 2))
            st.undo(k + 1)
    st.undo(k)
    return total


def sondear(st: State, k: int, proposal: Option, alternative: Optional[Option]) -> Dict:
    out = {"propuesta": two_step(st, k, proposal)}
    if alternative is not None:
        out["alternativa"] = two_step(st, k, alternative)
    return out


# ----------------------------------------------------------------------------------------------
# T4: explicar_callejon
# ----------------------------------------------------------------------------------------------
def future_reason(st: State, k: int) -> Optional[Dict]:
    """Misma lógica que State.future_ok(k), pero devuelve la primera condición que falla (o None)."""
    p = st.p
    future = range(k + 1, len(p.slots))
    rem = {i: p.max_shifts[i] - st.used[i] for i in st.used}
    pot = {}
    for j in future:
        di, t = p.slots[j]
        ids = [i for i in rem if rem[i] > 0 and st.can_work(i, di, t, check_hours=False)]
        if len(ids) < p.req[t]["required_total"]:
            return {"tipo": "turno", "turno": j, "especialidad": None,
                    "faltan": p.req[t]["required_total"] - len(ids)}
        for sp, n in p.spec_mins(t).items():
            have = sum(p.by_id[i]["specialty"] == sp for i in ids)
            if have < n:
                return {"tipo": "turno", "turno": j, "especialidad": sp, "faltan": n - have}
        pot[j] = ids
    total = 0
    for i in rem:
        days = {p.slots[j][0] for j in future if i in pot[j]}
        total += min(rem[i], len(days))
    demand = sum(p.req[p.slots[j][1]]["required_total"] for j in future)
    if total < demand:
        return {"tipo": "capacidad", "turno": None, "especialidad": None, "faltan": demand - total}
    for sp in sorted({s["specialty"] for s in p.staff}):
        dem = sum(p.spec_mins(p.slots[j][1]).get(sp, 0) for j in future)
        if dem == 0:
            continue
        cap = 0
        for i in rem:
            if p.by_id[i]["specialty"] != sp:
                continue
            days = {p.slots[j][0] for j in future if p.spec_mins(p.slots[j][1]).get(sp) and i in pot[j]}
            cap += min(rem[i], len(days))
        if cap < dem:
            return {"tipo": "capacidad", "turno": None, "especialidad": sp, "faltan": dem - cap}
    return None


def dead_end_reason(st: State, k: int) -> Dict:
    """Por qué el turno k quedó sin opciones: todas sus opciones viables ya se prohibieron, o una condición futura
    falla (con el chequeo hacia adelante activo, el propio turno k nunca queda sin candidatos: ya lo verificó
    future_ok(k-1); esas ramas quedan por si se corre sin chequeo)."""
    p = st.p
    if viable(st, k):
        return {"tipo": "prohibidas", "turno": k, "especialidad": None, "faltan": 0}
    di, t = p.slots[k]
    cands = [s["id"] for s in p.staff if st.can_work(s["id"], di, t)]
    if len(cands) < p.req[t]["required_total"]:
        return {"tipo": "turno", "turno": k, "especialidad": None, "faltan": p.req[t]["required_total"] - len(cands)}
    for sp, n in p.spec_mins(t).items():
        have = sum(p.by_id[i]["specialty"] == sp for i in cands)
        if have < n:
            return {"tipo": "turno", "turno": k, "especialidad": sp, "faltan": n - have}
    reason = future_reason(st, k - 1)  # el turno k cuenta como futuro: prefijo 0..k-1
    if reason:
        return reason
    # cada opción del turno k falla por su cuenta: se toma la causa más común
    reasons, deficit = Counter(), {}
    for o in st.options(k):
        st.apply(k, o)
        r = future_reason(st, k)
        st.undo(k)
        if r:
            key = (r["tipo"], r["turno"], r["especialidad"])
            reasons[key] += 1
            deficit[key] = min(deficit.get(key, r["faltan"]), r["faltan"])
    if not reasons:
        return {"tipo": "prohibidas", "turno": k, "especialidad": None, "faltan": 0}
    key, _ = reasons.most_common(1)[0]
    tipo, turno, sp = key
    return {"tipo": tipo, "turno": turno, "especialidad": sp, "faltan": deficit[key]}


def explicar_callejon(st: State, k: int, window: int = 12) -> Dict:
    """Qué requisito ya no se puede cubrir, qué médicos podrían cubrirlo y por qué no pueden (con las decisiones
    pasadas que lo causaron). Los candidatos para rehacer son TODAS las decisiones de los últimos `window` turnos
    (el análisis general de fallas midió la culpable entre 2 y 12 turnos antes del callejón), en orden cronológico
    y sin ranking: cada una dice qué médicos del conflicto involucra. El agente decide."""
    p = st.p
    reason = dead_end_reason(st, k)
    sp = reason["especialidad"]
    target = reason["turno"] if reason["tipo"] == "turno" else None
    pool = [] if reason["tipo"] == "prohibidas" else [s["id"] for s in p.staff if sp is None or s["specialty"] == sp]
    slot_of: Dict[str, List[int]] = {}
    for j, opt in st.assign.items():
        for i in opt:
            slot_of.setdefault(i, []).append(j)
    future = range(k, len(p.slots))
    doctors, resp = [], {}
    for i in pool:
        steps = sorted(slot_of.get(i, []))
        rem = p.max_shifts[i] - st.used[i]
        why, causes = [], []
        if target is not None and f"{p.days[p.slots[target][0]]}_{p.slots[target][1]}" in p.blocked[i]:
            # bloqueado en el turno que falta: ninguna decisión pasada lo habría liberado
            doctors.append({"id": i, "especialidad": p.by_id[i]["specialty"], "por_que": ["bloqueado (HC6, fijo)"],
                            "turnos": [p.slot_name(j) for j in steps]})
            continue
        if rem <= 0:
            why.append(f"sin horas (HC5): {st.used[i]}/{p.max_shifts[i]} turnos usados")
            causes += [(j, "HC5") for j in steps]
        if target is not None:
            dj, tj = p.slots[target]
            for j in steps:
                dd, tt = p.slots[j]
                if dd == dj and j != target:
                    why.append(f"ya trabaja ese día (HC2): {p.slot_name(j)}")
                    causes.append((j, "HC2"))
                elif dd == dj - 1 and not p.rest_ok[(tt, tj)]:
                    why.append(f"descanso (HC1): trabajó {p.slot_name(j)}")
                    causes.append((j, "HC1"))
                elif dd == dj + 1 and not p.rest_ok[(tj, tt)]:
                    why.append(f"descanso (HC1): trabaja {p.slot_name(j)}")
                    causes.append((j, "HC1"))
            if not why:
                why.append("libre para ese turno, pero las opciones del turno actual lo ocupan o dejan otro hueco")
        else:
            # misma medida que future_reason: días con algún turno elegible (con cuota de sp, si la causa es de sp)
            days = len({p.slots[j][0] for j in future
                        if (sp is None or p.spec_mins(p.slots[j][1]).get(sp))
                        and st.can_work(i, p.slots[j][0], p.slots[j][1], check_hours=False)})
            if 0 < days < rem:
                why.append(f"le quedan {rem} turnos pero solo {days} días posibles (capacidad perdida)")
            elif rem > 0:
                why.append(f"le quedan {rem} turnos")
        if why:
            doctors.append({"id": i, "especialidad": p.by_id[i]["specialty"], "por_que": why,
                            "turnos": [p.slot_name(j) for j in steps]})
        for j, cause in causes:
            resp.setdefault(j, []).append((i, cause))
    priority = {"HC5": 0, "HC1": 1, "HC2": 2}
    cands = []
    for j in range(max(0, k - window), k):
        opt = st.assign[j]
        inv = sorted(resp.get(j, []), key=lambda x: priority[x[1]])
        cands.append({"paso": j, "turno": p.slot_name(j), "asignados": list(opt),
                      "medico": inv[0][0] if inv else None, "causa": inv[0][1] if inv else None,
                      "involucra": [f"{i} ({c})" for i, c in inv], "sobre_cuota": sorted(_over_ids(p, j, opt)),
                      "distancia": k - j})
    return {"turno_callejon": p.slot_name(k), "paso": k, "causa": _reason_text(p, reason), "razon": reason,
            "medicos": doctors, "candidatos": cands}


def _over_ids(p: Problem, k: int, opt: Option) -> set:
    """Médicos del turno k cuya especialidad escasa está por encima de la cuota del turno (todos los de esa
    especialidad en el turno: no hay un criterio para decir cuál de ellos sobra)."""
    _, t = p.slots[k]
    mins, scarce = p.spec_mins(t), quota_specialties(p)
    cnt = Counter(p.by_id[i]["specialty"] for i in opt)
    return {i for i in opt if p.by_id[i]["specialty"] in scarce
            and cnt[p.by_id[i]["specialty"]] > mins.get(p.by_id[i]["specialty"], 0)}


def _reason_text(p: Problem, r: Dict) -> str:
    sp = r["especialidad"]
    if r["tipo"] == "turno":
        who = f"médicos de {sp}" if sp else "médicos"
        return f"{p.slot_name(r['turno'])} se queda sin {who} disponibles (faltan {r['faltan']})"
    if r["tipo"] == "capacidad":
        who = f"de {sp}" if sp else "total"
        return f"la capacidad {who} que queda no alcanza para la demanda restante (faltan {r['faltan']} turnos)"
    return "las opciones que quedan en este turno ya se probaron y llevaron a callejones (están prohibidas)"


# ----------------------------------------------------------------------------------------------
# T5: lecciones (memoria verbal)
# ----------------------------------------------------------------------------------------------
class Lessons:
    def __init__(self, keep: int = 3):
        self.items: List[str] = []
        self.keep = keep

    def write(self, expl: Dict, cand: Dict, banned_doc: bool):
        """`banned_doc`: si la prohibición del médico se pudo aplicar (si dejaba 0 opciones, no se aplica)."""
        sp = expl["razon"]["especialidad"]
        text = f"Callejón en {expl['turno_callejon']}: {expl['causa']}. Se volvió a {cand['turno']}"
        if cand["medico"] and banned_doc:
            text += (f" y se prohibió ahí a {cand['medico']} ({cand['causa']}). Evita gastar a {cand['medico']}"
                     + (f" ni a otros médicos de {sp}" if sp else "") + " por encima de la cuota antes de ese turno.")
        else:
            text += f" y se prohibió ahí la combinación anterior ({' + '.join(cand['asignados'])})."
        self.items.append(text)

    def recent(self) -> List[str]:
        return self.items[-self.keep:]
