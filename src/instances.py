#!/usr/bin/env python3
"""
Conjunto de instancias de evaluación para el MSSP
-------------------------------------------------
Conjunto principal (data/instances/, N=30):
- inst_00 es exactamente el escenario de Deliverable 1 (data/sample_staff.json + data/sample_demands.json).
- inst_01..inst_29 se generan con semillas fijas, a la misma escala de D1 (10 médicos, 7 días x 3 turnos),
  variando especialidades, contratos (32/40h), indisponibilidades y cuotas de especialidad.
Conjunto de estrés (data/instances_stress/, N=30): mismo generador + 1 a 3 franjas bloqueadas extra por médico
  (semillas 5000+). Se usa para estudiar dónde se quiebra la solución.

Cada instancia se certifica como FACTIBLE con OR-Tools CP-SAT antes de aceptarse, para que un fallo
del sistema sea atribuible al método y no a una instancia imposible. CP-SAT se usa SOLO aquí
(construcción del dataset); ni el baseline ni la solución lo invocan.

Uso:
    python src/instances.py                     # regenera data/instances/inst_00..inst_29.json
    python src/instances.py --profile stress    # regenera data/instances_stress/stress_00..stress_29.json
"""

import argparse
import json
import os
import random
from typing import Any, Dict, List, Tuple

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
SHIFTS = ["Morning", "Afternoon", "Night"]
SHIFT_TIMES = {"Morning": [6, 14], "Afternoon": [14, 22], "Night": [22, 30]}
MIN_REST = 16
SPECIALTIES = ["Anesthesiology", "Emergency", "General"]

HARD_CONSTRAINTS = [
    "HC1_MIN_REST: Minimum 16 hours of rest between shifts (Morning 06-14, Afternoon 14-22, Night 22-06). "
    "A Night shift cannot be followed by a Morning or Afternoon shift on the next day, and an Afternoon shift "
    "cannot be followed by a Morning shift on the next day.",
    "HC2_NO_DOUBLE_SHIFT: A staff member can only work at most 1 shift (8 hours) per calendar day.",
    "HC3_STAFFING_DEMAND: Each shift must have exactly the required total staff count.",
    "HC4_SPECIALTY_COVERAGE: Each shift must meet the minimum number of required specialists.",
    "HC5_MAX_HOURS: Total assigned hours per staff member in the week must not exceed their max_weekly_hours.",
    "HC6_UNAVAILABLE_SLOTS: No staff member can be assigned to a shift listed in their unavailable array.",
]

FIRST_NAMES = ["Carlos", "Andrea", "Felipe", "Valentina", "Matias", "Camila", "Ignacio", "Paula", "Javier",
               "Sofia", "Tomas", "Josefa", "Diego", "Antonia", "Benjamin", "Isidora", "Vicente", "Martina",
               "Cristobal", "Florencia", "Joaquin", "Catalina", "Nicolas", "Fernanda"]
LAST_NAMES = ["Silva", "Morales", "Soto", "Castro", "Rocha", "Fernandez", "Vega", "Rivas", "Mena", "Araya",
              "Munoz", "Rojas", "Diaz", "Perez", "Contreras", "Sepulveda", "Torres", "Flores", "Espinoza",
              "Valenzuela", "Tapia", "Reyes", "Gutierrez", "Pizarro"]


def rest_hours(prev_shift: str, next_shift: str) -> int:
    return 24 + SHIFT_TIMES[next_shift][0] - SHIFT_TIMES[prev_shift][1]


def make_demands(requirements: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "shift_hours": 8,
        "days": DAYS,
        "shifts": SHIFTS,
        "shift_times": SHIFT_TIMES,
        "min_rest_hours": MIN_REST,
        "requirements_per_shift": requirements,
        "hard_constraints": HARD_CONSTRAINTS,
    }


def load_instance(path: str) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """Devuelve (staff_data, demands_data) con el mismo formato que usa ScheduleVerifier."""
    with open(path, "r", encoding="utf-8") as f:
        inst = json.load(f)
    return {"staff": inst["staff"]}, inst["demands"]


def instance_dir(name: str = "main") -> str:
    return os.path.join(BASE_DIR, "data", "instances" if name == "main" else "instances_stress")


def list_instances(name: str = "main") -> List[str]:
    d = instance_dir(name)
    return sorted(os.path.join(d, f) for f in os.listdir(d) if f.endswith(".json"))


# ----------------------------------------------------------------------------------------------
# Certificación de factibilidad (solo para construir el dataset)
# ----------------------------------------------------------------------------------------------
def certify_feasible(staff: List[Dict[str, Any]], demands: Dict[str, Any], time_limit: float = 20.0) -> bool:
    from ortools.sat.python import cp_model

    m = cp_model.CpModel()
    x = {(s["id"], d, t): m.NewBoolVar(f"x_{s['id']}_{d}_{t}") for s in staff for d in DAYS for t in SHIFTS}
    req = demands["requirements_per_shift"]
    for d in DAYS:
        for t in SHIFTS:
            m.Add(sum(x[s["id"], d, t] for s in staff) == req[t]["required_total"])                 # HC3
            for spec, k in req[t]["specialty_requirements"].items():                                  # HC4
                if k > 0:
                    m.Add(sum(x[s["id"], d, t] for s in staff if s["specialty"] == spec) >= k)
    for s in staff:
        i = s["id"]
        for d in DAYS:
            m.Add(sum(x[i, d, t] for t in SHIFTS) <= 1)                                              # HC2
        for a, b in zip(DAYS, DAYS[1:]):
            for t1 in SHIFTS:
                for t2 in SHIFTS:
                    if rest_hours(t1, t2) < MIN_REST:
                        m.Add(x[i, a, t1] + x[i, b, t2] <= 1)                                        # HC1
        m.Add(8 * sum(x[i, d, t] for d in DAYS for t in SHIFTS) <= s["max_weekly_hours"])            # HC5
        for slot in s.get("unavailable", []):                                                         # HC6
            d, t = slot.split("_")
            m.Add(x[i, d, t] == 0)
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = time_limit
    solver.parameters.num_workers = 8
    status = solver.Solve(m)
    return status in (cp_model.OPTIMAL, cp_model.FEASIBLE)


def tightness(staff: List[Dict[str, Any]], demands: Dict[str, Any]) -> Dict[str, float]:
    req = demands["requirements_per_shift"]
    demand = sum(req[t]["required_total"] for t in SHIFTS) * len(DAYS)
    capacity = sum(s["max_weekly_hours"] // 8 for s in staff)
    out = {"demand_shifts": demand, "capacity_shifts": capacity, "global_ratio": round(demand / capacity, 3)}
    for spec in SPECIALTIES:
        need = sum(req[t]["specialty_requirements"].get(spec, 0) for t in SHIFTS) * len(DAYS)
        if need:
            cap = sum(s["max_weekly_hours"] // 8 for s in staff if s["specialty"] == spec)
            out[f"{spec}_ratio"] = round(need / cap, 3)
    return out


# ----------------------------------------------------------------------------------------------
# Generación
# ----------------------------------------------------------------------------------------------
def d1_instance() -> Dict[str, Any]:
    with open(os.path.join(BASE_DIR, "data", "sample_staff.json"), encoding="utf-8") as f:
        staff = json.load(f)["staff"]
    with open(os.path.join(BASE_DIR, "data", "sample_demands.json"), encoding="utf-8") as f:
        req = json.load(f)["requirements_per_shift"]
    return {"instance_id": "inst_00", "source": "Escenario original de Deliverable 1", "seed": None,
            "staff": staff, "demands": make_demands(req)}


def random_instance(seed: int, n_staff: int = 10, stress: bool = False) -> Dict[str, Any]:
    rng = random.Random(seed)
    n_anes = rng.choice([2, 2, 3])
    n_emer = rng.choice([3, 3, 4])
    specs = ["Anesthesiology"] * n_anes + ["Emergency"] * n_emer + ["General"] * (n_staff - n_anes - n_emer)
    names = rng.sample([(f, l) for f in FIRST_NAMES for l in LAST_NAMES], n_staff)
    all_slots = [f"{d}_{t}" for d in DAYS for t in SHIFTS]
    staff = []
    for k, spec in enumerate(specs, 1):
        first, last = names[k - 1]
        title = "Dra." if first.endswith("a") else "Dr."
        staff.append({
            "id": f"DOC_{k:02d}",
            "name": f"{title} {first} {last}",
            "specialty": spec,
            "max_weekly_hours": rng.choices([40, 32], weights=[0.75, 0.25])[0],
            "unavailable": sorted(rng.sample(all_slots, rng.choice([0, 1, 1, 2, 2, 3])),
                                  key=all_slots.index),
        })
    req = {
        "Morning": {"required_total": 2, "specialty_requirements": {"Emergency": 1, "General": 0, "Anesthesiology": 0}},
        "Afternoon": {"required_total": 2, "specialty_requirements": {"Emergency": 1, "General": 0, "Anesthesiology": 0}},
        "Night": {"required_total": 2, "specialty_requirements": {"Anesthesiology": 1, "Emergency": 0, "General": 0}},
    }
    # Variantes de cuotas (siempre dentro del mismo esquema de D1)
    if rng.random() < 0.3:
        req["Morning"]["specialty_requirements"]["General"] = 1
    if rng.random() < 0.25:
        req["Night"]["specialty_requirements"]["Emergency"] = 1
    source = "Generada (misma escala que Deliverable 1)"
    if stress:
        rng2 = random.Random(seed * 7 + 1)
        for s in staff:
            extra = rng2.sample(all_slots, rng2.choice([1, 2, 3]))
            s["unavailable"] = sorted(set(s["unavailable"]) | set(extra), key=all_slots.index)
        source = "Generada, perfil de estrés (+1..3 franjas bloqueadas por médico)"
    return {"instance_id": None, "source": source, "seed": seed, "staff": staff, "demands": make_demands(req)}


def build_dataset(n: int, out_dir: str, profile: str = "main"):
    os.makedirs(out_dir, exist_ok=True)
    stress = profile == "stress"
    instances = [] if stress else [d1_instance()]
    prefix = "stress" if stress else "inst"
    seed, rejected = (5000 if stress else 1000), 0
    while len(instances) < n:
        inst = random_instance(seed, stress=stress)
        seed += 1
        if certify_feasible(inst["staff"], inst["demands"]):
            inst["instance_id"] = f"{prefix}_{len(instances):02d}"
            instances.append(inst)
        else:
            rejected += 1
    for inst in instances:
        assert certify_feasible(inst["staff"], inst["demands"]), inst["instance_id"]
        inst["certified_feasible"] = True
        inst["tightness"] = tightness(inst["staff"], inst["demands"])
        with open(os.path.join(out_dir, f"{inst['instance_id']}.json"), "w", encoding="utf-8") as f:
            json.dump(inst, f, indent=2, ensure_ascii=False)
    print(f"{len(instances)} instancias factibles guardadas en {out_dir} ({rejected} candidatas infactibles descartadas)")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=30)
    ap.add_argument("--profile", choices=["main", "stress"], default="main")
    args = ap.parse_args()
    out = os.path.join(BASE_DIR, "data", "instances" if args.profile == "main" else "instances_stress")
    build_dataset(args.n, out, args.profile)
