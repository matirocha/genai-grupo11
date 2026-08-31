#!/usr/bin/env python3
"""
Ejecutor Experimental de Línea Base (Prompting Directo Zero-Shot)
-----------------------------------------------------------------
Construye el prompt directo con el personal y la demanda de turnos,
simula la salida típica de un modelo open-weight y la evalúa
directamente en el ScheduleVerifier para cuantificar el fallo.
"""

import json
import os
import sys
from verifier import ScheduleVerifier


def build_direct_prompt(staff_data: dict, demands_data: dict) -> str:
    return f"""Eres un asistente automatizado para la asignación de turnos médicos hospitalarios.
Tu tarea es asignar médicos a los turnos de toda la semana (de lunes a domingo) bajo restricciones operativas estrictas.

### Personal Disponible:
{json.dumps(staff_data["staff"], indent=2)}

### Requerimientos de Turnos y Demandas:
{json.dumps(demands_data, indent=2)}

### Formato de Salida:
Retorna ÚNICAMENTE un objeto JSON válido con la planificación semanal sin explicaciones ni texto markdown adicional:
{{
  "Monday": {{ "Morning": ["DOC_ID", ...], "Afternoon": [...], "Night": [...] }},
  "Tuesday": {{ ... }},
  ...
  "Sunday": {{ ... }}
}}
"""


# Salida simulada de prompting directo en un modelo de ~3B (mostrando los modos de fallo autorregresivos clásicos:
# sobreasignación de médicos favoritos, violación de descanso nocturno el martes y exceso de horas semanales el viernes).
SAMPLE_FAILED_DIRECT_OUTPUT = {
    "Monday": {
        "Morning": ["DOC_03", "DOC_06"],
        "Afternoon": ["DOC_04", "DOC_08"],
        "Night": ["DOC_01", "DOC_05"]
    },
    "Tuesday": {
        "Morning": ["DOC_01", "DOC_03"],
        "Afternoon": ["DOC_04", "DOC_08"],
        "Night": ["DOC_02", "DOC_09"]
    },
    "Wednesday": {
        "Morning": ["DOC_03", "DOC_06"],
        "Afternoon": ["DOC_03", "DOC_10"],
        "Night": ["DOC_01", "DOC_05"]
    },
    "Thursday": {
        "Morning": ["DOC_04", "DOC_07"],
        "Afternoon": ["DOC_03", "DOC_08"],
        "Night": ["DOC_05", "DOC_02"]
    },
    "Friday": {
        "Morning": ["DOC_03", "DOC_06"],
        "Afternoon": ["DOC_04", "DOC_08"],
        "Night": ["DOC_01", "DOC_10"]
    },
    "Saturday": {
        "Morning": ["DOC_03", "DOC_07"],
        "Afternoon": ["DOC_05", "DOC_08"],
        "Night": ["DOC_04", "DOC_02"]
    },
    "Sunday": {
        "Morning": ["DOC_03", "DOC_07"],
        "Afternoon": ["DOC_04", "DOC_08"],
        "Night": ["DOC_01", "DOC_05"]
    }
}


def run_baseline_experiment():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    staff_path = os.path.join(base_dir, "data", "sample_staff.json")
    demands_path = os.path.join(base_dir, "data", "sample_demands.json")

    with open(staff_path, 'r', encoding='utf-8') as f:
        staff_data = json.load(f)
    with open(demands_path, 'r', encoding='utf-8') as f:
        demands_data = json.load(f)

    prompt = build_direct_prompt(staff_data, demands_data)
    print("=== PROMPT DIRECTO GENERADO (Longitud: {} caracteres) ===".format(len(prompt)))
    
    print("\nEvaluando Salida de Línea Base (Prompting Directo)...")
    verifier = ScheduleVerifier(staff_data, demands_data)
    results = verifier.evaluate(SAMPLE_FAILED_DIRECT_OUTPUT)

    print("=" * 60)
    print(f"RESULTADO DE LÍNEA BASE (PROMPTING DIRECTO): {'APROBADO' if results['is_valid'] else 'FALLIDO'}")
    print(f"Total de Violaciones a Restricciones Duras: {results['total_hard_violations']}")
    print("Violaciones Identificadas:")
    for v in results["violations"]:
        print(f"  - {v}")
    print("=" * 60)


if __name__ == "__main__":
    run_baseline_experiment()
