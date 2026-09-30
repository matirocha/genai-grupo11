#!/usr/bin/env python3
"""
Verificador de Asignación de Turnos Médicos (Schedule Verifier)
--------------------------------------------------------------
Evalúa las planificaciones semanales generadas frente a restricciones operativas y legales estrictas.
Actúa como el oráculo evaluador programático (Ground Truth) para las salidas del modelo.

Cambio respecto a Deliverable 1 (declarado en el README y en el documento técnico):
HC1 se evaluaba solo para el par Noche(d) -> Mañana(d+1). Ahora el descanso se calcula a partir
del horario de cada turno (Mañana 06-14, Tarde 14-22, Noche 22-06) y se exige >= 16h entre
turnos de días consecutivos, tal como lo define D1. Esto agrega Noche(d) -> Tarde(d+1)
(que el texto de D1 ya prohibía) y Tarde(d) -> Mañana(d+1) (8h de descanso).
El criterio es más estricto que el código de D1, nunca más permisivo.

Este módulo es independiente del código de la solución: no comparte lógica con src/stepwise_solver.py.
"""

import json
import sys
from typing import Dict, Any, List

DEFAULT_SHIFT_TIMES = {"Morning": [6, 14], "Afternoon": [14, 22], "Night": [22, 30]}
DEFAULT_MIN_REST = 16

VIOLATION_TYPES = [
    "HC1", "HC2", "HC3", "HC4", "HC5", "HC6",
    "ESTRUCTURA",  # días/turnos faltantes, formato inválido, IDs duplicados o inexistentes
]


class ScheduleVerifier:
    def __init__(self, staff_data: Dict[str, Any], demands_data: Dict[str, Any]):
        self.staff_dict = {doc["id"]: doc for doc in staff_data["staff"]}
        self.demands = demands_data
        self.shift_hours = demands_data.get("shift_hours", 8)
        self.days = demands_data.get("days", ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"])
        self.shifts = demands_data.get("shifts", ["Morning", "Afternoon", "Night"])
        self.shift_times = demands_data.get("shift_times", DEFAULT_SHIFT_TIMES)
        self.min_rest = demands_data.get("min_rest_hours", DEFAULT_MIN_REST)

    def _rest_hours(self, prev_shift: str, next_shift: str) -> int:
        """Horas de descanso entre prev_shift (día d) y next_shift (día d+1)."""
        return 24 + self.shift_times[next_shift][0] - self.shift_times[prev_shift][1]

    def evaluate(self, schedule: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evalúa un diccionario de horario semanal.
        Retorna:
            Dict con booleano de validez, total de violaciones duras, conteo por tipo,
            distribución de horas y detalle de fallos.
        """
        violations: List[str] = []
        by_type = {t: 0 for t in VIOLATION_TYPES}

        def add(kind: str, msg: str):
            by_type[kind] += 1
            violations.append(msg)

        if not isinstance(schedule, dict):
            add("ESTRUCTURA", "FORMATO_INVALIDO: el horario no es un objeto JSON {día: {turno: [ids]}}.")
            return self._result(violations, by_type, {d: 0 for d in self.staff_dict})

        assigned_hours = {doc_id: 0 for doc_id in self.staff_dict}
        # clean[day][shift] = lista de IDs conocidos (para HC1/HC2)
        clean: Dict[str, Dict[str, List[str]]] = {}

        # 1. Validación estructural, HC3, HC4, HC6
        for day in self.days:
            clean[day] = {}
            if day not in schedule or not isinstance(schedule[day], dict):
                add("ESTRUCTURA", f"FALTA_DIA: El día {day} no está presente en el horario.")
                continue

            for shift in self.shifts:
                if shift not in schedule[day]:
                    add("ESTRUCTURA", f"FALTA_TURNO: El turno {shift} del día {day} no está presente.")
                    continue

                assigned_docs = schedule[day][shift]
                if not isinstance(assigned_docs, list) or not all(isinstance(x, str) for x in assigned_docs):
                    add("ESTRUCTURA", f"FORMATO_INVALIDO: El turno {day} {shift} no es una lista de identificadores de médicos.")
                    continue

                if len(assigned_docs) != len(set(assigned_docs)):
                    add("ESTRUCTURA", f"DUPLICADO_EN_TURNO: Médico duplicado asignado en {day} {shift}: {assigned_docs}")

                known = []
                for doc_id in dict.fromkeys(assigned_docs):
                    if doc_id not in self.staff_dict:
                        add("ESTRUCTURA", f"MEDICO_DESCONOCIDO: {doc_id} asignado en {day} {shift} no existe en la nómina de personal.")
                        continue
                    known.append(doc_id)
                    assigned_hours[doc_id] += self.shift_hours

                    # HC6: Indisponibilidad solicitada
                    slot_str = f"{day}_{shift}"
                    if slot_str in self.staff_dict[doc_id].get("unavailable", []):
                        add("HC6", f"HC6_INDISPONIBILIDAD: {doc_id} ({self.staff_dict[doc_id]['name']}) asignado en franja bloqueada {slot_str}.")
                clean[day][shift] = known

                # HC3: Demanda total de dotación
                req_total = self.demands["requirements_per_shift"][shift]["required_total"]
                if len(assigned_docs) != req_total:
                    add("HC3", f"HC3_DEMANDA_DOTACION: {day} {shift} requiere {req_total} médicos, pero tiene {len(assigned_docs)}.")

                # HC4: Cobertura obligatoria por especialidad
                spec_counts: Dict[str, int] = {}
                for doc_id in known:
                    spec = self.staff_dict[doc_id]["specialty"]
                    spec_counts[spec] = spec_counts.get(spec, 0) + 1
                for req_spec, min_count in self.demands["requirements_per_shift"][shift]["specialty_requirements"].items():
                    actual_count = spec_counts.get(req_spec, 0)
                    if actual_count < min_count:
                        add("HC4", f"HC4_COBERTURA_ESPECIALIDAD: {day} {shift} requiere al menos {min_count} {req_spec}(s), pero cuenta con {actual_count}.")

        # HC2: Turno único diario (máximo 1 turno por médico por día calendario)
        for day in self.days:
            seen: Dict[str, int] = {}
            for shift in self.shifts:
                for doc_id in clean[day].get(shift, []):
                    seen[doc_id] = seen.get(doc_id, 0) + 1
            for doc_id, n in seen.items():
                if n > 1:
                    add("HC2", f"HC2_TURNO_UNICO_DIARIO: El médico {doc_id} fue asignado a {n} turnos el {day}.")

        # HC1: Descanso obligatorio >= min_rest horas entre turnos de días consecutivos
        for i in range(len(self.days) - 1):
            day, next_day = self.days[i], self.days[i + 1]
            for s1 in self.shifts:
                for s2 in self.shifts:
                    rest = self._rest_hours(s1, s2)
                    if rest >= self.min_rest:
                        continue
                    overlap = set(clean[day].get(s1, [])) & set(clean[next_day].get(s2, []))
                    for doc_id in sorted(overlap):
                        add("HC1", f"HC1_DESCANSO_OBLIGATORIO: El médico {doc_id} trabajó {s1} ({day}) y {s2} ({next_day}) con solo {rest}h de descanso (<{self.min_rest}h).")

        # HC5: Límite legal semanal de horas por contrato
        for doc_id, hours in assigned_hours.items():
            max_h = self.staff_dict[doc_id]["max_weekly_hours"]
            if hours > max_h:
                add("HC5", f"HC5_LIMITE_LEGAL_HORAS: {doc_id} ({self.staff_dict[doc_id]['name']}) tiene {hours}h asignadas, superando el tope de {max_h}h por {hours - max_h}h.")

        return self._result(violations, by_type, assigned_hours)

    @staticmethod
    def _result(violations, by_type, assigned_hours):
        return {
            "is_valid": len(violations) == 0,
            "total_hard_violations": len(violations),
            "violations_by_type": by_type,
            "assigned_hours_distribution": assigned_hours,
            "violations": violations,
        }


def main():
    if len(sys.argv) not in (3, 4):
        print("Uso: python verifier.py <personal.json> <demandas.json> <horario.json>\n"
              "     python verifier.py <instancia.json> <horario.json | resultado en results/>")
        sys.exit(1)

    if len(sys.argv) == 4:
        with open(sys.argv[1], 'r', encoding='utf-8') as f:
            staff_data = json.load(f)
        with open(sys.argv[2], 'r', encoding='utf-8') as f:
            demands_data = json.load(f)
    else:
        with open(sys.argv[1], 'r', encoding='utf-8') as f:
            inst = json.load(f)
        staff_data, demands_data = {"staff": inst["staff"]}, inst["demands"]
    with open(sys.argv[-1], 'r', encoding='utf-8') as f:
        schedule_data = json.load(f)
    # Acepta también los registros guardados por src/evaluate.py ({"output": {"schedule": ...}})
    if isinstance(schedule_data, dict) and isinstance(schedule_data.get("output"), dict) \
            and "schedule" in schedule_data["output"]:
        schedule_data = schedule_data["output"]["schedule"]

    verifier = ScheduleVerifier(staff_data, demands_data)
    result = verifier.evaluate(schedule_data)

    print("=" * 60)
    print(f"RESULTADO DE VERIFICACIÓN: {'APROBADO (0 VIOLACIONES)' if result['is_valid'] else 'FALLIDO'}")
    print(f"Total de Violaciones a Restricciones Duras: {result['total_hard_violations']}")
    print("Por tipo: " + ", ".join(f"{k}={v}" for k, v in result["violations_by_type"].items() if v))
    print("=" * 60)
    if result["violations"]:
        print("DETALLE DE VIOLACIONES IDENTIFICADAS:")
        for idx, v in enumerate(result["violations"], 1):
            print(f"  [{idx}] {v}")
    print("=" * 60)


if __name__ == "__main__":
    main()
