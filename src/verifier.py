#!/usr/bin/env python3
"""
Verificador de Asignación de Turnos Médicos (Schedule Verifier)
--------------------------------------------------------------
Evalúa las planificaciones semanales generadas frente a restricciones operativas y legales estrictas.
Actúa como el oráculo evaluador programático (Ground Truth) para las salidas del modelo.
"""

import json
import sys
from typing import Dict, Any, List, Tuple


class ScheduleVerifier:
    def __init__(self, staff_data: Dict[str, Any], demands_data: Dict[str, Any]):
        self.staff_dict = {doc["id"]: doc for doc in staff_data["staff"]}
        self.demands = demands_data
        self.shift_hours = demands_data.get("shift_hours", 8)
        self.days = demands_data.get("days", ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"])
        self.shifts = demands_data.get("shifts", ["Morning", "Afternoon", "Night"])

    def evaluate(self, schedule: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evalúa un diccionario de horario semanal.
        Retorna:
            Dict con booleano de validez, total de violaciones duras, distribución de horas y detalle de fallos.
        """
        violations = []
        assigned_hours = {doc_id: 0 for doc_id in self.staff_dict}
        daily_assignments = {doc_id: set() for doc_id in self.staff_dict}

        # Lista cronológica de turnos para verificar tiempos de descanso obligatorio
        chronological_shifts: List[Tuple[str, str, List[str]]] = []

        # 1. Validación de adherencia estructural y presencia de turnos
        for day in self.days:
            if day not in schedule:
                violations.append(f"FALTA_DIA: El día {day} no está presente en el horario.")
                continue

            for shift in self.shifts:
                if shift not in schedule[day]:
                    violations.append(f"FALTA_TURNO: El turno {shift} del día {day} no está presente.")
                    continue

                assigned_docs = schedule[day][shift]
                if not isinstance(assigned_docs, list):
                    violations.append(f"FORMATO_INVALIDO: El turno {day} {shift} no es una lista de identificadores de médicos.")
                    continue

                chronological_shifts.append((day, shift, assigned_docs))

                # Verificar identificadores duplicados en un mismo turno
                if len(assigned_docs) != len(set(assigned_docs)):
                    violations.append(f"DUPLICADO_EN_TURNO: Médico duplicado asignado en {day} {shift}: {assigned_docs}")

                # Verificar que cada médico exista en la nómina
                for doc_id in assigned_docs:
                    if doc_id not in self.staff_dict:
                        violations.append(f"MEDICO_DESCONOCIDO: {doc_id} asignado en {day} {shift} no existe en la nómina de personal.")
                    else:
                        assigned_hours[doc_id] += self.shift_hours
                        daily_assignments[doc_id].add(day)

                        # HC6: Indisponibilidad solicitada
                        slot_str = f"{day}_{shift}"
                        if slot_str in self.staff_dict[doc_id].get("unavailable", []):
                            violations.append(f"HC6_INDISPONIBILIDAD: {doc_id} ({self.staff_dict[doc_id]['name']}) asignado en franja bloqueada {slot_str}.")

                # HC3: Demanda total de dotación
                req_total = self.demands["requirements_per_shift"][shift]["required_total"]
                if len(assigned_docs) != req_total:
                    violations.append(f"HC3_DEMANDA_DOTACION: {day} {shift} requiere {req_total} médicos, pero tiene {len(assigned_docs)}.")

                # HC4: Cobertura obligatoria por especialidad
                spec_counts = {}
                for doc_id in assigned_docs:
                    if doc_id in self.staff_dict:
                        spec = self.staff_dict[doc_id]["specialty"]
                        spec_counts[spec] = spec_counts.get(spec, 0) + 1

                for req_spec, min_count in self.demands["requirements_per_shift"][shift]["specialty_requirements"].items():
                    actual_count = spec_counts.get(req_spec, 0)
                    if actual_count < min_count:
                        violations.append(f"HC4_COBERTURA_ESPECIALIDAD: {day} {shift} requiere al menos {min_count} {req_spec}(s), pero cuenta con {actual_count}.")

        # HC2: Turno único diario (máximo 1 turno por médico por día calendario)
        for day in self.days:
            if day not in schedule:
                continue
            day_docs = []
            for shift in self.shifts:
                if shift in schedule[day] and isinstance(schedule[day][shift], list):
                    for doc_id in schedule[day][shift]:
                        if doc_id in day_docs:
                            violations.append(f"HC2_TURNO_UNICO_DIARIO: El médico {doc_id} fue asignado a múltiples turnos el {day}.")
                        day_docs.append(doc_id)

        # HC1: Descanso obligatorio entre turnos consecutivos
        # Secuencias prohibidas: Noche(día_t) -> Mañana(día_t+1) o Tarde(día_t+1) (< 16 horas de descanso)
        for i in range(len(chronological_shifts) - 1):
            curr_day, curr_shift, curr_docs = chronological_shifts[i]
            next_day, next_shift, next_docs = chronological_shifts[i + 1]

            if curr_shift == "Night" and next_shift in ["Morning", "Afternoon"]:
                overlap = set(curr_docs).intersection(set(next_docs))
                for doc_id in overlap:
                    violations.append(f"HC1_DESCANSO_OBLIGATORIO: El médico {doc_id} trabajó de Noche ({curr_day}) y fue asignado inmediatamente a {next_shift} ({next_day}) sin el descanso continuo reglamentario (>=16h).")

        # HC5: Límite legal semanal de horas por contrato
        for doc_id, hours in assigned_hours.items():
            max_h = self.staff_dict[doc_id]["max_weekly_hours"]
            if hours > max_h:
                violations.append(f"HC5_LIMITE_LEGAL_HORAS: {doc_id} ({self.staff_dict[doc_id]['name']}) tiene {hours}h asignadas, superando el tope de {max_h}h por {hours - max_h}h.")

        is_valid = (len(violations) == 0)
        return {
            "is_valid": is_valid,
            "total_hard_violations": len(violations),
            "assigned_hours_distribution": assigned_hours,
            "violations": violations
        }


def main():
    if len(sys.argv) < 4:
        print("Uso: python verifier.py <personal.json> <demandas.json> <horario.json>")
        sys.exit(1)

    with open(sys.argv[1], 'r', encoding='utf-8') as f:
        staff_data = json.load(f)
    with open(sys.argv[2], 'r', encoding='utf-8') as f:
        demands_data = json.load(f)
    with open(sys.argv[3], 'r', encoding='utf-8') as f:
        schedule_data = json.load(f)

    verifier = ScheduleVerifier(staff_data, demands_data)
    result = verifier.evaluate(schedule_data)

    print("=" * 60)
    print(f"RESULTADO DE VERIFICACIÓN: {'APROBADO (0 VIOLACIONES)' if result['is_valid'] else 'FALLIDO'}")
    print(f"Total de Violaciones a Restricciones Duras: {result['total_hard_violations']}")
    print("=" * 60)
    if result["violations"]:
        print("DETALLE DE VIOLACIONES IDENTIFICADAS:")
        for idx, v in enumerate(result["violations"], 1):
            print(f"  [{idx}] {v}")
    print("=" * 60)


if __name__ == "__main__":
    main()
