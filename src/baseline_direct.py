#!/usr/bin/env python3
"""
Línea Base: Prompting Directo Zero-Shot (mismo prompt de Deliverable 1)
----------------------------------------------------------------------
Envía al modelo el personal y la demanda completos y le pide el horario semanal en un solo JSON.
La salida cruda del modelo se parsea y se evalúa con ScheduleVerifier.

En D1 este script evaluaba una salida de ejemplo escrita a mano; en D2 ejecuta el modelo real.

Uso:
    python src/baseline_direct.py --instance data/instances/inst_00.json
"""

import argparse
import json
import os
import re
import time
from typing import Any, Dict, Optional, Tuple

from instances import BASE_DIR, load_instance
from verifier import ScheduleVerifier


def build_direct_prompt(staff_data: dict, demands_data: dict) -> str:
    return f"""Eres un asistente automatizado para la asignación de turnos médicos hospitalarios.
Tu tarea es asignar médicos a los turnos de toda la semana (de lunes a domingo) bajo restricciones operativas estrictas.

### Personal Disponible:
{json.dumps(staff_data["staff"], indent=2, ensure_ascii=False)}

### Requerimientos de Turnos y Demandas:
{json.dumps(demands_data, indent=2, ensure_ascii=False)}

### Formato de Salida:
Retorna ÚNICAMENTE un objeto JSON válido con la planificación semanal sin explicaciones ni texto markdown adicional:
{{
  "Monday": {{ "Morning": ["DOC_ID", ...], "Afternoon": [...], "Night": [...] }},
  "Tuesday": {{ ... }},
  ...
  "Sunday": {{ ... }}
}}
"""


def extract_json(text: str) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """Extrae el primer objeto JSON de la respuesta (tolera ```json ... ``` y texto alrededor)."""
    text = re.sub(r"```(?:json)?", "", text)
    start = text.find("{")
    if start < 0:
        return None, "sin objeto JSON en la respuesta"
    depth, in_str, esc = 0, False, False
    for i in range(start, len(text)):
        c = text[i]
        if in_str:
            esc = (c == "\\") and not esc
            if c == '"' and not esc:
                in_str = False
            continue
        if c == '"':
            in_str = True
        elif c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                try:
                    return json.loads(text[start:i + 1]), None
                except json.JSONDecodeError as e:
                    return None, f"JSON inválido: {e}"
    return None, "JSON truncado (llaves sin cerrar)"


def run_direct(llm, staff_data: dict, demands_data: dict, stream: bool = False) -> Dict[str, Any]:
    t0 = time.time()
    tokens0 = llm.generated_tokens
    raw = llm.generate([{"role": "user", "content": build_direct_prompt(staff_data, demands_data)}],
                       max_new_tokens=1500, stream=stream)
    schedule, parse_error = extract_json(raw)
    return {"schedule": schedule, "raw_output": raw, "parse_error": parse_error, "llm_calls": 1,
            "generated_tokens": llm.generated_tokens - tokens0, "seconds": round(time.time() - t0, 1)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--instance", default=os.path.join(BASE_DIR, "data", "instances", "inst_00.json"))
    ap.add_argument("--model", default=None)
    args = ap.parse_args()

    from llm import LLM, DEFAULT_MODEL
    llm = LLM(args.model or DEFAULT_MODEL)
    staff_data, demands_data = load_instance(args.instance)
    print(f"=== LÍNEA BASE (prompting directo) | {llm.model_id} | {os.path.basename(args.instance)} ===")
    out = run_direct(llm, staff_data, demands_data, stream=True)
    if out["schedule"] is None:
        print(f"\nRESULTADO: FALLIDO — {out['parse_error']}")
        return
    res = ScheduleVerifier(staff_data, demands_data).evaluate(out["schedule"])
    print("=" * 60)
    print(f"RESULTADO DE LÍNEA BASE: {'APROBADO' if res['is_valid'] else 'FALLIDO'}")
    print(f"Total de Violaciones a Restricciones Duras: {res['total_hard_violations']}")
    for v in res["violations"]:
        print(f"  - {v}")
    print("=" * 60)


if __name__ == "__main__":
    main()
