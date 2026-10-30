Corridas con búsqueda analizadas: 77 configuraciones, 2310 horarios, 124 fallidos.

1. Qué se rompe: HC1 24%, HC4 0%, HC5 73%, HC6 2% de las 383 violaciones finales.
2. Dónde se causa: la decisión culpable está 2–12 turnos antes del callejón (mediana 6.0); el callejón aparece Thursday 14, Friday 26, Saturday 80, Sunday 4.
3. Por qué el chequeo no lo ve: en el turno culpable dejaba pasar 820 opciones y solo 390 (48%) tenían completación real.
4. Qué forma el conflicto (quitar una familia lo resuelve): HC5 124/124, HC1 123/124, HC6 122/124, HC4 111/124.
5. Cuándo ocurre (holgura mínima de capacidad de la instancia, total o de una especialidad, en turnos): 0: 63/804 fallan, 1: 44/681 fallan, 2: 11/366 fallan, ≥3: 6/459 fallan.
6. En las 12 fallas del sistema de agentes con LLM y sus ablaciones, quién dejó pasar la decisión culpable: punto ciego: perfilar no alertó (4), el Crítico aceptó una propuesta fatal (3), otro (2), revisión agotada (2 rechazos, se fijó la tercera) (2), sin Crítico: la propuesta se fijó directo (1). En 10 de ellas ningún salto posterior volvió a la culpable; en 2 se la deshizo, pero el presupuesto se agotó en otra rama.

| configuración | horarios | fallidos | distancia culpable→callejón |
|---|---|---|---|
| main/llama-3.2-3b/agents | 30 | 0 | - |
| main/llama-3.2-3b/agents_sin_critico | 30 | 0 | - |
| main/llama-3.2-3b/agents_sin_diagnosticador | 30 | 0 | - |
| main/llama-3.2-3b/agents_sin_ensamble | 30 | 0 | - |
| main/llama-3.2-3b/agents_sin_fewshot | 30 | 0 | - |
| main/llama-3.2-3b/agents_sin_memoria | 30 | 0 | - |
| main/llama-3.2-3b/stepwise | 30 | 0 | - |
| main/no_llm/agents_random | 30 | 0 | - |
| main/no_llm/agents_random_s1 | 30 | 0 | - |
| main/no_llm/agents_random_s2 | 30 | 0 | - |
| main/no_llm/agents_random_s3 | 30 | 0 | - |
| main/no_llm/agents_random_s4 | 30 | 0 | - |
| main/no_llm/agents_rules | 30 | 1 | 5 |
| main/no_llm/random | 30 | 0 | - |
| main/no_llm/random_b300 | 30 | 0 | - |
| main/no_llm/random_b300_s1 | 30 | 0 | - |
| main/no_llm/random_b300_s2 | 30 | 0 | - |
| main/no_llm/random_b300_s3 | 30 | 0 | - |
| main/no_llm/random_b300_s4 | 30 | 1 | 7 |
| main/no_llm/random_s1 | 30 | 0 | - |
| main/no_llm/random_s2 | 30 | 0 | - |
| main/no_llm/random_s3 | 30 | 0 | - |
| main/no_llm/random_s4 | 30 | 1 | 7 |
| main/phi-3.5-mini/stepwise | 30 | 0 | - |
| main/qwen2.5-0.5b/stepwise | 30 | 1 | 3 |
| main/qwen2.5-1.5b/stepwise | 30 | 5 | 4, 7, 7, 6, 4 |
| main/qwen2.5-3b/stepwise | 30 | 1 | 4 |
| stress/llama-3.2-3b/agents | 30 | 0 | - |
| stress/llama-3.2-3b/agents_sin_critico | 30 | 0 | - |
| stress/llama-3.2-3b/agents_sin_diagnosticador | 30 | 1 | 5 |
| stress/llama-3.2-3b/agents_sin_ensamble | 30 | 0 | - |
| stress/llama-3.2-3b/agents_sin_fewshot | 30 | 0 | - |
| stress/llama-3.2-3b/agents_sin_memoria | 30 | 0 | - |
| stress/llama-3.2-3b/stepwise | 30 | 2 | 10, 6 |
| stress/no_llm/agents_random | 30 | 0 | - |
| stress/no_llm/agents_random_s1 | 30 | 0 | - |
| stress/no_llm/agents_random_s2 | 30 | 0 | - |
| stress/no_llm/agents_random_s3 | 30 | 0 | - |
| stress/no_llm/agents_random_s4 | 30 | 0 | - |
| stress/no_llm/agents_rules | 30 | 5 | 7, 3, 5, 6, 8 |
| stress/no_llm/random | 30 | 4 | 6, 7, 6, 4 |
| stress/no_llm/random_b300 | 30 | 3 | 6, 7, 6 |
| stress/no_llm/random_b300_s1 | 30 | 1 | 6 |
| stress/no_llm/random_b300_s2 | 30 | 2 | 12, 10 |
| stress/no_llm/random_b300_s3 | 30 | 0 | - |
| stress/no_llm/random_b300_s4 | 30 | 3 | 7, 6, 6 |
| stress/no_llm/random_s1 | 30 | 3 | 4, 6, 4 |
| stress/no_llm/random_s2 | 30 | 2 | 12, 10 |
| stress/no_llm/random_s3 | 30 | 1 | 4 |
| stress/no_llm/random_s4 | 30 | 3 | 7, 6, 6 |
| stress/phi-3.5-mini/stepwise | 30 | 3 | 2, 10, 6 |
| stress/qwen2.5-0.5b/stepwise | 30 | 3 | 8, 7, 8 |
| stress/qwen2.5-1.5b/stepwise | 30 | 3 | 10, 6, 6 |
| stress/qwen2.5-3b/stepwise | 30 | 4 | 6, 10, 6, 6 |
| hard/llama-3.2-3b/agents | 30 | 0 | - |
| hard/llama-3.2-3b/agents_sin_critico | 30 | 1 | 8 |
| hard/llama-3.2-3b/agents_sin_diagnosticador | 30 | 7 | 6, 7, 6, 12, 10, 6, 10 |
| hard/llama-3.2-3b/agents_sin_ensamble | 30 | 0 | - |
| hard/llama-3.2-3b/agents_sin_fewshot | 30 | 3 | 4, 6, 4 |
| hard/llama-3.2-3b/agents_sin_memoria | 30 | 0 | - |
| hard/llama-3.2-3b/stepwise | 30 | 8 | 6, 6, 6, 8, 5, 6, 9, 5 |
| hard/no_llm/agents_random | 30 | 0 | - |
| hard/no_llm/agents_random_s1 | 30 | 0 | - |
| hard/no_llm/agents_random_s2 | 30 | 0 | - |
| hard/no_llm/agents_random_s3 | 30 | 0 | - |
| hard/no_llm/agents_random_s4 | 30 | 0 | - |
| hard/no_llm/agents_rules | 30 | 10 | 7, 3, 8, 4, 10, 7, 8, 10, 8, 9 |
| hard/no_llm/random | 30 | 8 | 4, 6, 12, 8, 6, 6, 6, 4 |
| hard/no_llm/random_b300 | 30 | 5 | 7, 12, 8, 6, 6 |
| hard/no_llm/random_b300_s1 | 30 | 2 | 7, 7 |
| hard/no_llm/random_b300_s2 | 30 | 3 | 7, 6, 6 |
| hard/no_llm/random_b300_s3 | 30 | 3 | 10, 5, 7 |
| hard/no_llm/random_b300_s4 | 30 | 2 | 6, 6 |
| hard/no_llm/random_s1 | 30 | 6 | 6, 7, 5, 7, 3, 7 |
| hard/no_llm/random_s2 | 30 | 4 | 7, 4, 6, 6 |
| hard/no_llm/random_s3 | 30 | 4 | 10, 5, 5, 7 |
| hard/no_llm/random_s4 | 30 | 5 | 5, 4, 4, 6, 6 |
