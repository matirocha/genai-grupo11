#!/usr/bin/env python3
"""
Solución D2: Descomposición por turno + estado externo + decodificación restringida + backtracking
---------------------------------------------------------------------------------------------------
Cada componente ataca uno de los tres fallos diagnosticados en Deliverable 1:

  Fallo D1-2 (deriva de estado y aritmética)  -> el estado (horas usadas, turno del día anterior,
      bloqueos) lo lleva el código, no el modelo. En cada paso se le muestra al LLM una tabla ya calculada
      y solo los candidatos legales para ese turno (HC1, HC2, HC5, HC6).
  Fallo D1-3 (alucinación de esquema e IDs)    -> el LLM decide UN turno por llamada y su salida está
      restringida por un trie de tokens a combinaciones válidas de IDs (HC3 cantidad exacta, HC4
      especialidad). El JSON semanal lo arma el código.
  Fallo D1-1 (decisión voraz sin backtracking) -> antes de ofrecer una opción, un chequeo de
      factibilidad hacia adelante (condiciones necesarias de capacidad) la descarta si deja la semana
      sin solución; si un turno queda sin opciones se retrocede al turno anterior y se prohíbe la
      elección que llevó al callejón sin salida (presupuesto de retrocesos acotado).

Si se agota el presupuesto, el sistema completa la semana relajando restricciones y marca el
resultado como NO certificado (el verificador externo cuenta las violaciones).

Uso:
    python src/stepwise_solver.py --instance data/instances/inst_00.json
"""

import argparse
import itertools
import json
import os
import random
import time
from typing import Any, Callable, Dict, List, Optional, Tuple

from instances import BASE_DIR, load_instance

Option = Tuple[str, ...]


class Problem:
    def __init__(self, staff_data: Dict[str, Any], demands: Dict[str, Any]):
        self.staff = staff_data["staff"]
        self.by_id = {s["id"]: s for s in self.staff}
        self.days = demands["days"]
        self.shifts = demands["shifts"]
        self.req = demands["requirements_per_shift"]
        self.hours = demands.get("shift_hours", 8)
        times = demands.get("shift_times", {"Morning": [6, 14], "Afternoon": [14, 22], "Night": [22, 30]})
        min_rest = demands.get("min_rest_hours", 16)
        # rest_ok[(turno_d, turno_d+1)] según horarios reales de cada turno
        self.rest_ok = {(a, b): 24 + times[b][0] - times[a][1] >= min_rest for a in self.shifts for b in self.shifts}
        self.slots = [(di, t) for di in range(len(self.days)) for t in self.shifts]
        self.max_shifts = {s["id"]: s["max_weekly_hours"] // self.hours for s in self.staff}
        self.blocked = {s["id"]: set(s.get("unavailable", [])) for s in self.staff}

    def slot_name(self, k: int) -> str:
        di, t = self.slots[k]
        return f"{self.days[di]} {t}"

    def spec_mins(self, t: str) -> Dict[str, int]:
        return {sp: n for sp, n in self.req[t]["specialty_requirements"].items() if n > 0}


class State:
    def __init__(self, p: Problem):
        self.p = p
        self.assign: Dict[int, Option] = {}
        self.used = {s["id"]: 0 for s in p.staff}
        self.worked: Dict[str, Dict[int, str]] = {s["id"]: {} for s in p.staff}  # id -> {día: turno}

    def apply(self, k: int, opt: Option):
        di, t = self.p.slots[k]
        self.assign[k] = opt
        for i in opt:
            self.used[i] += 1
            self.worked[i][di] = t

    def undo(self, k: int):
        di, _ = self.p.slots[k]
        for i in self.assign.pop(k):
            self.used[i] -= 1
            del self.worked[i][di]

    def schedule(self) -> Dict[str, Dict[str, List[str]]]:
        out = {d: {t: [] for t in self.p.shifts} for d in self.p.days}
        for k, opt in self.assign.items():
            di, t = self.p.slots[k]
            out[self.p.days[di]][t] = list(opt)
        return out

    # --- legalidad local (HC1, HC2, HC5, HC6) -------------------------------------------------
    def can_work(self, i: str, di: int, t: str, check_hours=True, check_rest=True, check_block=True) -> bool:
        p = self.p
        if di in self.worked[i]:                                                        # HC2
            return False
        if check_block and f"{p.days[di]}_{t}" in p.blocked[i]:                         # HC6
            return False
        if check_hours and self.used[i] >= p.max_shifts[i]:                            # HC5
            return False
        if check_rest:                                                                  # HC1
            prev = self.worked[i].get(di - 1)
            if prev is not None and not p.rest_ok[(prev, t)]:
                return False
            nxt = self.worked[i].get(di + 1)
            if nxt is not None and not p.rest_ok[(t, nxt)]:
                return False
        return True

    def options(self, k: int, **relax) -> List[Option]:
        """Combinaciones con la cantidad exacta (HC3) y la cuota de especialidad (HC4) cumplidas."""
        p = self.p
        di, t = p.slots[k]
        cands = [s["id"] for s in p.staff if self.can_work(s["id"], di, t, **relax)]
        need, mins = p.req[t]["required_total"], p.spec_mins(t)
        opts = []
        for combo in itertools.combinations(cands, need):
            if all(sum(p.by_id[i]["specialty"] == sp for i in combo) >= n for sp, n in mins.items()):
                opts.append(combo)
        return opts

    # --- chequeo de factibilidad hacia adelante (condiciones necesarias) -----------------------
    def future_ok(self, k: int) -> bool:
        p = self.p
        future = range(k + 1, len(p.slots))
        rem = {i: p.max_shifts[i] - self.used[i] for i in self.used}
        pot = {}
        for j in future:
            di, t = p.slots[j]
            ids = [i for i in rem if rem[i] > 0 and self.can_work(i, di, t, check_hours=False)]
            if len(ids) < p.req[t]["required_total"]:
                return False
            for sp, n in p.spec_mins(t).items():
                if sum(p.by_id[i]["specialty"] == sp for i in ids) < n:
                    return False
            pot[j] = ids
        # capacidad agregada: cada médico aporta a lo más min(turnos restantes, días distintos en que puede)
        def capacity(slot_filter) -> int:
            total = 0
            for i in rem:
                days = {p.slots[j][0] for j in future if slot_filter(j) and i in pot[j]}
                total += min(rem[i], len(days))
            return total
        if capacity(lambda j: True) < sum(p.req[p.slots[j][1]]["required_total"] for j in future):
            return False
        for sp in {s["specialty"] for s in p.staff}:
            demand = sum(p.spec_mins(p.slots[j][1]).get(sp, 0) for j in future)
            if demand == 0:
                continue
            cap = 0
            for i in rem:
                if p.by_id[i]["specialty"] != sp:
                    continue
                days = {p.slots[j][0] for j in future if p.spec_mins(p.slots[j][1]).get(sp) and i in pot[j]}
                cap += min(rem[i], len(days))
            if cap < demand:
                return False
        return True

    def scarcity(self, k: int) -> List[Tuple[str, int, int]]:
        """(especialidad, turnos obligatorios restantes desde k, capacidad restante del personal)."""
        p = self.p
        rows = []
        for sp in sorted({s["specialty"] for s in p.staff}):
            demand = sum(p.spec_mins(p.slots[j][1]).get(sp, 0) for j in range(k, len(p.slots)))
            if demand:
                cap = sum(p.max_shifts[i] - self.used[i] for i in self.used if p.by_id[i]["specialty"] == sp)
                rows.append((sp, demand, cap))
        return rows


# ----------------------------------------------------------------------------------------------
# Políticas de elección
# ----------------------------------------------------------------------------------------------
SYSTEM_PROMPT = """Eres un planificador de turnos médicos hospitalarios. La semana se arma turno por turno.
Un verificador externo ya calculó el estado de la semana y filtró a los candidatos legales de este turno
(descanso mínimo de 16h, un turno por día, tope de horas semanales y franjas bloqueadas).
Tu tarea es elegir quiénes cubren ESTE turno pensando en el resto de la semana:
- cumple exactamente la dotación y la cuota de especialidad pedida;
- no gastes especialistas escasos (capacidad restante cercana a la demanda restante) si un médico General puede cubrir el cupo;
- prefiere a quienes tienen más turnos disponibles y a quienes tendrán pocas oportunidades más adelante.
Responde SOLO con una lista JSON de IDs, por ejemplo ["DOC_01", "DOC_02"]."""


def build_step_prompt(st: State, k: int, opts: List[Option], banned: List[Option]) -> str:
    p = st.p
    di, t = p.slots[k]
    need, mins = p.req[t]["required_total"], p.spec_mins(t)
    req_txt = f"exactamente {need} médicos" + "".join(f", al menos {n} {sp}" for sp, n in mins.items())
    cands = sorted({i for o in opts for i in o})
    lines = [f"Turno actual: {p.days[di]} {t} (paso {k + 1} de {len(p.slots)}). Se requieren {req_txt}.", "",
             "Especialidades con cuota (turnos obligatorios que faltan incluyendo este | capacidad restante):"]
    for sp, dem, cap in st.scarcity(k):
        lines.append(f"- {sp}: {dem} | {cap}")
    lines += ["", "Candidatos legales para este turno:", "ID | especialidad | turnos usados/máx | días futuros disponibles"]
    for i in cands:
        fut = sum(1 for dj in range(di + 1, len(p.days))
                  if any(f"{p.days[dj]}_{tt}" not in p.blocked[i] for tt in p.shifts))
        lines.append(f"{i} | {p.by_id[i]['specialty']} | {st.used[i]}/{p.max_shifts[i]} | {fut}")
    if banned:
        lines += ["", "Estas combinaciones ya se probaron y llevan a un callejón sin salida: "
                  + ", ".join(json.dumps(list(b)) for b in banned)]
    lines += ["", f"Elige {need} IDs de la lista de candidatos."]
    return "\n".join(lines)


def option_strings(opts: List[Option]) -> Dict[str, Option]:
    """Todas las permutaciones de cada opción, como texto JSON, para el trie de decodificación."""
    table = {}
    for o in opts:
        for perm in itertools.permutations(o):
            table[json.dumps(list(perm))] = o
    return table


def llm_policy(llm) -> Callable:
    def choose(st: State, k: int, opts: List[Option], banned: List[Option]) -> Option:
        table = option_strings(opts)
        msgs = [{"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": build_step_prompt(st, k, opts, banned)}]
        text = llm.generate(msgs, allowed=list(table)).strip()
        return table[text]
    return choose


def random_policy(seed: int) -> Callable:
    rng = random.Random(seed)
    return lambda st, k, opts, banned: rng.choice(opts)


# ----------------------------------------------------------------------------------------------
# Búsqueda
# ----------------------------------------------------------------------------------------------
def solve(staff_data, demands, choose: Callable, lookahead: bool = True, max_backtracks: int = 30,
          trace: Optional[Callable[[str], None]] = None) -> Dict[str, Any]:
    t0 = time.time()
    p = Problem(staff_data, demands)
    st = State(p)
    n = len(p.slots)
    banned: Dict[int, List[Option]] = {k: [] for k in range(n)}
    stats = {"decisions": 0, "backtracks": 0, "dead_ends": 0, "relaxed_steps": 0, "first_dead_end": None}
    best: Dict[int, Option] = {}
    log = trace or (lambda s: None)

    k = 0
    exhausted = False
    while k < n:
        opts = [o for o in st.options(k) if o not in banned[k]]
        if lookahead:
            viable = []
            for o in opts:
                st.apply(k, o)
                if st.future_ok(k):
                    viable.append(o)
                st.undo(k)
            opts = viable
        if not opts:
            stats["dead_ends"] += 1
            if stats["first_dead_end"] is None:
                stats["first_dead_end"] = p.slot_name(k)
            if k == 0 or stats["backtracks"] >= max_backtracks:
                exhausted = True
                break
            banned[k] = []
            k -= 1
            prev = st.assign[k]
            st.undo(k)
            banned[k].append(prev)
            stats["backtracks"] += 1
            log(f"  ✗ {p.slot_name(k + 1)}: sin opciones viables -> retrocede a {p.slot_name(k)} y prohíbe {list(prev)}")
            continue
        choice = choose(st, k, opts, banned[k])
        stats["decisions"] += 1
        st.apply(k, choice)
        log(f"  {p.slot_name(k):<20} -> {list(choice)}   ({len(opts)} opciones viables)")
        if len(st.assign) > len(best):
            best = dict(st.assign)
        k += 1

    certified = not exhausted
    if exhausted:
        # Se retoma el avance más profundo y se completa relajando restricciones (resultado no certificado)
        log(f"  ! presupuesto de retrocesos agotado ({stats['backtracks']}); se completa en modo relajado")
        st = State(p)
        for kk in sorted(best):
            st.apply(kk, best[kk])
        for kk in range(len(best), n):
            for relax in ({}, {"check_hours": False, "check_rest": False}, {"check_hours": False, "check_rest": False, "check_block": False}):
                opts = st.options(kk, **relax)
                if opts:
                    break
            else:
                di, t = p.slots[kk]
                free = [s["id"] for s in p.staff if di not in st.worked[s["id"]]]
                opts = list(itertools.combinations(free, p.req[t]["required_total"]))
            choice = choose(st, kk, opts, [])
            stats["decisions"] += 1
            stats["relaxed_steps"] += 1
            st.apply(kk, choice)
            log(f"  {p.slot_name(kk):<20} -> {list(choice)}   (modo relajado)")

    stats["seconds"] = round(time.time() - t0, 1)
    return {"schedule": st.schedule(), "certified": certified, **stats}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--instance", default=os.path.join(BASE_DIR, "data", "instances", "inst_00.json"))
    ap.add_argument("--model", default=None)
    ap.add_argument("--policy", choices=["llm", "random"], default="llm")
    ap.add_argument("--no-lookahead", action="store_true")
    ap.add_argument("--max-backtracks", type=int, default=30)
    args = ap.parse_args()

    from verifier import ScheduleVerifier
    staff_data, demands = load_instance(args.instance)
    if args.policy == "llm":
        from llm import LLM, DEFAULT_MODEL
        llm = LLM(args.model or DEFAULT_MODEL)
        choose = llm_policy(llm)
    else:
        choose = random_policy(0)
    out = solve(staff_data, demands, choose, lookahead=not args.no_lookahead,
                max_backtracks=args.max_backtracks, trace=print)
    res = ScheduleVerifier(staff_data, demands).evaluate(out["schedule"])
    print(json.dumps({k: v for k, v in out.items() if k != "schedule"}, ensure_ascii=False))
    print(f"VERIFICADOR: {'APROBADO' if res['is_valid'] else 'FALLIDO'} — {res['total_hard_violations']} violaciones")
    for v in res["violations"]:
        print("  -", v)


if __name__ == "__main__":
    main()
