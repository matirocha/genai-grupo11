#!/usr/bin/env python3
"""
Generador de Datos Sintéticos para el Problema de Asignación de Turnos Médicos (MSSP)
"""

import json, os

DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
SHIFTS = ["Morning", "Afternoon", "Night"]

DEFAULT_STAFF = {
    "staff": [
        {"id": "DOC_01", "name": "Dr. Carlos Silva", "specialty": "Anesthesiology", "max_weekly_hours": 40, "unavailable": ["Monday_Night", "Friday_Night"]},
        {"id": "DOC_02", "name": "Dra. Andrea Morales", "specialty": "Anesthesiology", "max_weekly_hours": 40, "unavailable": ["Tuesday_Morning"]},
        {"id": "DOC_03", "name": "Dr. Felipe Soto", "specialty": "Emergency", "max_weekly_hours": 40, "unavailable": ["Wednesday_Afternoon"]},
        {"id": "DOC_04", "name": "Dra. Valentina Castro", "specialty": "Emergency", "max_weekly_hours": 40, "unavailable": ["Saturday_Night", "Sunday_Night"]},
        {"id": "DOC_05", "name": "Dr. Matias Rocha", "specialty": "Emergency", "max_weekly_hours": 40, "unavailable": ["Thursday_Night"]},
        {"id": "DOC_06", "name": "Dra. Camila Fernandez", "specialty": "General", "max_weekly_hours": 32, "unavailable": ["Monday_Morning"]},
        {"id": "DOC_07", "name": "Dr. Ignacio Vega", "specialty": "General", "max_weekly_hours": 32, "unavailable": ["Sunday_Morning", "Sunday_Afternoon"]},
        {"id": "DOC_08", "name": "Dra. Paula Rivas", "specialty": "General", "max_weekly_hours": 40, "unavailable": []},
        {"id": "DOC_09", "name": "Dr. Javier Mena", "specialty": "General", "max_weekly_hours": 40, "unavailable": ["Tuesday_Night"]},
        {"id": "DOC_10", "name": "Dra. Sofia Araya", "specialty": "General", "max_weekly_hours": 40, "unavailable": ["Saturday_Morning"]}
    ]
}

DEFAULT_DEMANDS = {
    "shift_hours": 8,
    "days": DAYS,
    "shifts": SHIFTS,
    "requirements_per_shift": {
        "Morning": {"required_total": 2, "specialty_requirements": {"Emergency": 1, "General": 0, "Anesthesiology": 0}},
        "Afternoon": {"required_total": 2, "specialty_requirements": {"Emergency": 1, "General": 0, "Anesthesiology": 0}},
        "Night": {"required_total": 2, "specialty_requirements": {"Anesthesiology": 1, "Emergency": 0, "General": 0}}
    },
    "hard_constraints": [
        "HC1_MIN_REST: Minimum 16 hours of rest between shifts.",
        "HC2_NO_DOUBLE_SHIFT: At most 1 shift (8h) per calendar day.",
        "HC3_STAFFING_DEMAND: Exact required staff count per shift.",
        "HC4_SPECIALTY_COVERAGE: Required specialists presence per shift.",
        "HC5_MAX_HOURS: Total assigned hours <= max_weekly_hours.",
        "HC6_UNAVAILABLE_SLOTS: No assignment during blocked slots."
    ]
}


def save_datasets(target_dir: str = None):
    if target_dir is None:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        target_dir = os.path.join(base_dir, "data")
    os.makedirs(target_dir, exist_ok=True)
    with open(os.path.join(target_dir, "sample_staff.json"), "w", encoding="utf-8") as f:
        json.dump(DEFAULT_STAFF, f, indent=2, ensure_ascii=False)
    with open(os.path.join(target_dir, "sample_demands.json"), "w", encoding="utf-8") as f:
        json.dump(DEFAULT_DEMANDS, f, indent=2, ensure_ascii=False)
    print(f"Conjuntos de datos guardados exitosamente en: {target_dir}")


if __name__ == "__main__":
    save_datasets()
