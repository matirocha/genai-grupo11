#!/usr/bin/env python3
"""
Baseline Direct Prompting Runner & Experiment Script
---------------------------------------------------
Constructs the raw direct prompt containing staff and shift demands,
queries the target open-weight model (or simulated baseline), and feeds
the structured JSON output directly into the ScheduleVerifier.
"""

import json
import os
import sys
from verifier import ScheduleVerifier


def build_direct_prompt(staff_data: dict, demands_data: dict) -> str:
    return f"""You are an automated medical scheduling assistant.
Your task is to assign doctors to hospital shifts for an entire week (Monday through Sunday) under strict operational constraints.

### Available Staff:
{json.dumps(staff_data["staff"], indent=2)}

### Shift Requirements and Demands:
{json.dumps(demands_data, indent=2)}

### Output Format:
Return ONLY a valid JSON object matching the weekly schedule without additional markdown explanations:
{{
  "Monday": {{ "Morning": ["DOC_ID", ...], "Afternoon": [...], "Night": [...] }},
  "Tuesday": {{ ... }},
  ...
  "Sunday": {{ ... }}
}}
"""


# Simulated direct prompting output from a 3B model (exhibiting classic autoregressive failure modes:
# overbooking favorite doctors, violating night rest on Tuesday, exceeding weekly hours by Friday).
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
    print("=== DIRECT PROMPT GENERATED (Length: {} chars) ===".format(len(prompt)))
    
    print("\nEvaluating Simulated Direct Prompting Baseline Output...")
    verifier = ScheduleVerifier(staff_data, demands_data)
    results = verifier.evaluate(SAMPLE_FAILED_DIRECT_OUTPUT)

    print("=" * 60)
    print(f"DIRECT PROMPTING BASELINE RESULT: {'PASSED' if results['is_valid'] else 'FAILED'}")
    print(f"Total Hard Violations: {results['total_hard_violations']}")
    print("Violations Identified:")
    for v in results["violations"]:
        print(f"  - {v}")
    print("=" * 60)


if __name__ == "__main__":
    run_baseline_experiment()
