#!/usr/bin/env python3
"""
Estrategia alternativa evaluada: bucle de reparación guiado por el verificador
------------------------------------------------------------------------------
Parte de la salida del prompting directo y, mientras el horario sea inválido (hasta R rondas),
le devuelve al modelo su propio JSON junto con la lista de violaciones del verificador y le pide
el horario completo corregido. Es la opción "CoT multietapa con verificación intermedia" del plan de D1:
el modelo sigue generando la semana entera de una vez, pero con retroalimentación externa.
"""

import json
import time
from typing import Any, Dict

from baseline_direct import build_direct_prompt, extract_json
from verifier import ScheduleVerifier

MAX_LISTED_VIOLATIONS = 20


def run_repair(llm, staff_data: dict, demands_data: dict, first: Dict[str, Any], rounds: int = 3) -> Dict[str, Any]:
    """`first` es el resultado de run_direct sobre la misma instancia (se reutiliza, no se regenera)."""
    t0 = time.time()
    verifier = ScheduleVerifier(staff_data, demands_data)
    schedule, raw = first["schedule"], first["raw_output"]
    history = []
    calls, tokens0 = 1, llm.generated_tokens
    done = False
    for r in range(1, rounds + 1):
        if schedule is not None:
            res = verifier.evaluate(schedule)
            history.append(res["total_hard_violations"])
            if res["is_valid"]:
                done = True
                break
            feedback = "\n".join(f"- {v}" for v in res["violations"][:MAX_LISTED_VIOLATIONS])
            if len(res["violations"]) > MAX_LISTED_VIOLATIONS:
                feedback += f"\n- ... y {len(res['violations']) - MAX_LISTED_VIOLATIONS} violaciones más"
            previous = json.dumps(schedule, ensure_ascii=False)
        else:
            history.append(None)
            feedback = f"- La respuesta no se pudo leer como JSON ({first['parse_error'] if r == 1 else 'JSON inválido'})."
            previous = raw[:3000]
        msgs = [
            {"role": "user", "content": build_direct_prompt(staff_data, demands_data)},
            {"role": "assistant", "content": previous},
            {"role": "user", "content": "Un verificador automático revisó tu horario y encontró estas violaciones "
                                        f"a las restricciones duras:\n{feedback}\n\nCorrige TODAS las violaciones sin "
                                        "introducir otras nuevas. Retorna ÚNICAMENTE el objeto JSON completo de la semana."},
        ]
        raw = llm.generate(msgs, max_new_tokens=1500)
        calls += 1
        parsed, _ = extract_json(raw)
        if parsed is not None:
            schedule = parsed
    if not done:
        history.append(verifier.evaluate(schedule)["total_hard_violations"] if schedule is not None else None)
    return {"schedule": schedule, "raw_output": raw, "parse_error": None if schedule is not None else "sin JSON válido",
            "llm_calls": calls, "violations_per_round": history,
            "generated_tokens": first["generated_tokens"] + llm.generated_tokens - tokens0,
            "seconds": round(first["seconds"] + time.time() - t0, 1)}
