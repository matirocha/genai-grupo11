| conjunto | modelo | estrategia | N | válidos | JSON ok | viol. media | llamadas LLM | seg. | retrocesos | sobreuso esp. | fallidas |
|---|---|---|---|---|---|---|---|---|---|---|---|
| main | llama-3.2-3b | direct | 30 | 0/30 | 30/30 | 23.4 | 1.0 | 12.8 | - | - | 30 instancias |
| main | llama-3.2-3b | repair | 30 | 0/30 | 30/30 | 26.57 | 4.0 | 36.8 | - | - | 30 instancias |
| main | llama-3.2-3b | stepwise_nosearch | 30 | 3/30 | 30/30 | 3.3 | 21.0 | 10.8 | 0.0 | 0.242 | 27 instancias |
| main | llama-3.2-3b | stepwise | 30 | 30/30 | 30/30 | 0.0 | 21.9 | 11.9 | 0.93 | 0.165 | - |
| main | llama-3.2-3b | agents | 30 | 30/30 | 30/30 | 0.0 | 63.2 | 6.8 | 0.0 | 0.074 | - |
| main | llama-3.2-3b | agents_sin_diagnosticador | 30 | 30/30 | 30/30 | 0.0 | 63.2 | 6.8 | 0.0 | 0.074 | - |
| main | llama-3.2-3b | agents_sin_critico | 30 | 30/30 | 30/30 | 0.0 | 42.6 | 5.1 | 0.1 | 0.071 | - |
| main | llama-3.2-3b | agents_sin_memoria | 30 | 30/30 | 30/30 | 0.0 | 77.6 | 8.6 | 0.0 | 0.09 | - |
| main | llama-3.2-3b | agents_sin_fewshot | 30 | 30/30 | 30/30 | 0.0 | 91.8 | 10.0 | 0.03 | 0.068 | - |
| main | llama-3.2-3b | agents_sin_ensamble | 30 | 30/30 | 30/30 | 0.0 | 39.1 | 4.1 | 0.0 | 0.065 | - |
| main | no_llm | random_nosearch | 30 | 6/30 | 30/30 | 2.57 | 0.0 | 0.0 | 0.0 | 0.08 | 24 instancias |
| main | no_llm | random | 30 | 30/30 | 30/30 | 0.0 | 0.0 | 0.0 | 0.07 | 0.057 | - |
| main | no_llm | random_s1 | 30 | 30/30 | 30/30 | 0.0 | 0.0 | 0.0 | 0.2 | 0.06 | - |
| main | no_llm | random_s2 | 30 | 30/30 | 30/30 | 0.0 | 0.0 | 0.0 | 0.23 | 0.075 | - |
| main | no_llm | random_s3 | 30 | 30/30 | 30/30 | 0.0 | 0.0 | 0.0 | 0.07 | 0.087 | - |
| main | no_llm | random_s4 | 30 | 29/30 | 30/30 | 0.17 | 0.0 | 0.0 | 1.23 | 0.065 | inst_07 |
| main | no_llm | random_b300 | 30 | 30/30 | 30/30 | 0.0 | 0.0 | 0.0 | 0.07 | 0.057 | - |
| main | no_llm | random_b300_s1 | 30 | 30/30 | 30/30 | 0.0 | 0.0 | 0.0 | 0.2 | 0.06 | - |
| main | no_llm | random_b300_s2 | 30 | 30/30 | 30/30 | 0.0 | 0.0 | 0.0 | 0.23 | 0.075 | - |
| main | no_llm | random_b300_s3 | 30 | 30/30 | 30/30 | 0.0 | 0.0 | 0.0 | 0.07 | 0.087 | - |
| main | no_llm | random_b300_s4 | 30 | 29/30 | 30/30 | 0.2 | 0.0 | 0.0 | 10.23 | 0.065 | inst_07 |
| main | no_llm | agents_random | 30 | 30/30 | 30/30 | 0.0 | 0.0 | 0.2 | 0.03 | 0.068 | - |
| main | no_llm | agents_random_s1 | 30 | 30/30 | 30/30 | 0.0 | 0.0 | 0.2 | 0.1 | 0.059 | - |
| main | no_llm | agents_random_s2 | 30 | 30/30 | 30/30 | 0.0 | 0.0 | 0.2 | 0.13 | 0.054 | - |
| main | no_llm | agents_random_s3 | 30 | 30/30 | 30/30 | 0.0 | 0.0 | 0.2 | 0.03 | 0.06 | - |
| main | no_llm | agents_random_s4 | 30 | 30/30 | 30/30 | 0.0 | 0.0 | 0.2 | 0.13 | 0.062 | - |
| main | no_llm | agents_rules | 30 | 29/30 | 30/30 | 0.1 | 0.0 | 0.3 | 2.5 | 0.035 | inst_17 |
| main | phi-3.5-mini | direct | 30 | 0/30 | 29/30 | 39.62 | 1.0 | 22.9 | - | - | 30 instancias |
| main | phi-3.5-mini | stepwise | 30 | 30/30 | 30/30 | 0.0 | 21.2 | 12.1 | 0.2 | 0.15 | - |
| main | qwen2.5-0.5b | direct | 30 | 0/30 | 16/30 | 15.62 | 1.0 | 39.3 | - | - | 30 instancias |
| main | qwen2.5-0.5b | stepwise | 30 | 29/30 | 30/30 | 0.2 | 23.3 | 24.2 | 2.3 | 0.08 | inst_17 |
| main | qwen2.5-1.5b | direct | 30 | 0/30 | 30/30 | 41.57 | 1.0 | 13.9 | - | - | 30 instancias |
| main | qwen2.5-1.5b | stepwise | 30 | 25/30 | 30/30 | 0.57 | 27.3 | 20.0 | 6.3 | 0.094 | 5 instancias |
| main | qwen2.5-3b | direct | 30 | 0/30 | 29/30 | 39.62 | 1.0 | 14.4 | - | - | 30 instancias |
| main | qwen2.5-3b | repair | 30 | 0/30 | 30/30 | 39.5 | 4.0 | 70.2 | - | - | 30 instancias |
| main | qwen2.5-3b | stepwise_nosearch | 30 | 0/30 | 30/30 | 6.33 | 21.0 | 19.0 | 0.0 | 0.582 | 30 instancias |
| main | qwen2.5-3b | stepwise | 30 | 29/30 | 30/30 | 0.07 | 22.3 | 15.2 | 1.33 | 0.221 | inst_28 |
| stress | llama-3.2-3b | direct | 30 | 0/30 | 30/30 | 26.0 | 1.0 | 14.7 | - | - | 30 instancias |
| stress | llama-3.2-3b | stepwise | 30 | 28/30 | 30/30 | 0.2 | 25.2 | 13.6 | 4.17 | 0.193 | stress_04, stress_25 |
| stress | llama-3.2-3b | agents | 30 | 30/30 | 30/30 | 0.0 | 71.3 | 7.5 | 0.07 | 0.069 | - |
| stress | llama-3.2-3b | agents_sin_diagnosticador | 30 | 29/30 | 30/30 | 0.1 | 69.7 | 7.1 | 1.03 | 0.068 | stress_25 |
| stress | llama-3.2-3b | agents_sin_critico | 30 | 30/30 | 30/30 | 0.0 | 48.4 | 5.4 | 0.47 | 0.072 | - |
| stress | llama-3.2-3b | agents_sin_memoria | 30 | 30/30 | 30/30 | 0.0 | 80.9 | 8.5 | 0.13 | 0.08 | - |
| stress | llama-3.2-3b | agents_sin_fewshot | 30 | 30/30 | 30/30 | 0.0 | 102.4 | 13.9 | 0.57 | 0.078 | - |
| stress | llama-3.2-3b | agents_sin_ensamble | 30 | 30/30 | 30/30 | 0.0 | 54.5 | 5.9 | 0.4 | 0.072 | - |
| stress | no_llm | random_nosearch | 30 | 2/30 | 30/30 | 2.63 | 0.0 | 0.0 | 0.0 | 0.082 | 28 instancias |
| stress | no_llm | random | 30 | 26/30 | 30/30 | 0.27 | 0.0 | 0.0 | 4.3 | 0.078 | stress_07, stress_13, stress_18, stress_25 |
| stress | no_llm | random_s1 | 30 | 27/30 | 30/30 | 0.4 | 0.0 | 0.0 | 4.07 | 0.059 | stress_05, stress_18, stress_19 |
| stress | no_llm | random_s2 | 30 | 28/30 | 30/30 | 0.17 | 0.0 | 0.0 | 3.0 | 0.077 | stress_19, stress_20 |
| stress | no_llm | random_s3 | 30 | 29/30 | 30/30 | 0.17 | 0.0 | 0.0 | 1.23 | 0.081 | stress_13 |
| stress | no_llm | random_s4 | 30 | 27/30 | 30/30 | 0.23 | 0.0 | 0.0 | 3.37 | 0.082 | stress_13, stress_18, stress_23 |
| stress | no_llm | random_b300 | 30 | 27/30 | 30/30 | 0.37 | 0.0 | 0.0 | 32.0 | 0.078 | stress_07, stress_13, stress_18 |
| stress | no_llm | random_b300_s1 | 30 | 29/30 | 30/30 | 0.03 | 0.0 | 0.0 | 17.93 | 0.056 | stress_18 |
| stress | no_llm | random_b300_s2 | 30 | 28/30 | 30/30 | 0.13 | 0.0 | 0.0 | 21.0 | 0.078 | stress_19, stress_20 |
| stress | no_llm | random_b300_s3 | 30 | 30/30 | 30/30 | 0.0 | 0.0 | 0.0 | 6.5 | 0.08 | - |
| stress | no_llm | random_b300_s4 | 30 | 27/30 | 30/30 | 0.23 | 0.0 | 0.0 | 30.37 | 0.08 | stress_13, stress_18, stress_23 |
| stress | no_llm | agents_random | 30 | 30/30 | 30/30 | 0.0 | 0.0 | 0.2 | 0.5 | 0.078 | - |
| stress | no_llm | agents_random_s1 | 30 | 30/30 | 30/30 | 0.0 | 0.0 | 0.1 | 0.57 | 0.077 | - |
| stress | no_llm | agents_random_s2 | 30 | 30/30 | 30/30 | 0.0 | 0.0 | 0.2 | 0.57 | 0.068 | - |
| stress | no_llm | agents_random_s3 | 30 | 30/30 | 30/30 | 0.0 | 0.0 | 0.2 | 1.2 | 0.06 | - |
| stress | no_llm | agents_random_s4 | 30 | 30/30 | 30/30 | 0.0 | 0.0 | 0.1 | 0.2 | 0.081 | - |
| stress | no_llm | agents_rules | 30 | 25/30 | 30/30 | 0.4 | 0.0 | 0.2 | 6.2 | 0.053 | 5 instancias |
| stress | phi-3.5-mini | stepwise | 30 | 27/30 | 30/30 | 0.33 | 26.1 | 12.8 | 5.1 | 0.177 | stress_01, stress_04, stress_25 |
| stress | qwen2.5-0.5b | stepwise | 30 | 27/30 | 30/30 | 0.57 | 25.9 | 15.4 | 5.03 | 0.077 | stress_01, stress_04, stress_17 |
| stress | qwen2.5-1.5b | stepwise | 30 | 27/30 | 30/30 | 0.47 | 26.9 | 25.9 | 5.9 | 0.116 | stress_04, stress_07, stress_25 |
| stress | qwen2.5-3b | direct | 30 | 0/30 | 30/30 | 41.47 | 1.0 | 12.9 | - | - | 30 instancias |
| stress | qwen2.5-3b | stepwise | 30 | 26/30 | 30/30 | 0.37 | 26.1 | 22.7 | 5.2 | 0.25 | stress_01, stress_04, stress_15, stress_25 |
| hard | llama-3.2-3b | direct | 30 | 0/30 | 30/30 | 25.87 | 1.0 | 13.4 | - | - | 30 instancias |
| hard | llama-3.2-3b | stepwise | 30 | 22/30 | 30/30 | 0.63 | 31.2 | 15.8 | 10.47 | 0.136 | 8 instancias |
| hard | llama-3.2-3b | agents | 30 | 30/30 | 30/30 | 0.0 | 97.7 | 11.9 | 0.83 | 0.05 | - |
| hard | llama-3.2-3b | agents_sin_diagnosticador | 30 | 23/30 | 30/30 | 0.8 | 66.1 | 7.4 | 7.6 | 0.063 | 7 instancias |
| hard | llama-3.2-3b | agents_sin_critico | 30 | 29/30 | 30/30 | 0.07 | 96.8 | 13.0 | 2.97 | 0.043 | hard_10 |
| hard | llama-3.2-3b | agents_sin_memoria | 30 | 30/30 | 30/30 | 0.0 | 99.0 | 10.1 | 1.4 | 0.054 | - |
| hard | llama-3.2-3b | agents_sin_fewshot | 30 | 27/30 | 30/30 | 0.43 | 141.2 | 16.7 | 4.93 | 0.053 | hard_04, hard_10, hard_16 |
| hard | llama-3.2-3b | agents_sin_ensamble | 30 | 30/30 | 30/30 | 0.0 | 51.5 | 5.7 | 0.53 | 0.057 | - |
| hard | no_llm | random | 30 | 22/30 | 30/30 | 0.7 | 0.0 | 0.0 | 9.93 | 0.051 | 8 instancias |
| hard | no_llm | random_s1 | 30 | 24/30 | 30/30 | 0.5 | 0.0 | 0.0 | 8.9 | 0.044 | 6 instancias |
| hard | no_llm | random_s2 | 30 | 26/30 | 30/30 | 0.57 | 0.0 | 0.0 | 5.83 | 0.053 | hard_08, hard_11, hard_12, hard_16 |
| hard | no_llm | random_s3 | 30 | 26/30 | 30/30 | 0.3 | 0.0 | 0.0 | 5.97 | 0.053 | hard_08, hard_18, hard_28, hard_29 |
| hard | no_llm | random_s4 | 30 | 25/30 | 30/30 | 0.63 | 0.0 | 0.0 | 7.87 | 0.05 | 5 instancias |
| hard | no_llm | random_b300 | 30 | 25/30 | 30/30 | 0.47 | 0.0 | 0.0 | 61.3 | 0.054 | 5 instancias |
| hard | no_llm | random_b300_s1 | 30 | 28/30 | 30/30 | 0.17 | 0.0 | 0.0 | 38.57 | 0.04 | hard_10, hard_29 |
| hard | no_llm | random_b300_s2 | 30 | 27/30 | 30/30 | 0.43 | 0.0 | 0.0 | 35.23 | 0.054 | hard_08, hard_12, hard_16 |
| hard | no_llm | random_b300_s3 | 30 | 27/30 | 30/30 | 0.17 | 0.0 | 0.0 | 35.9 | 0.053 | hard_08, hard_18, hard_29 |
| hard | no_llm | random_b300_s4 | 30 | 28/30 | 30/30 | 0.3 | 0.0 | 0.0 | 29.33 | 0.054 | hard_16, hard_22 |
| hard | no_llm | agents_random | 30 | 30/30 | 30/30 | 0.0 | 0.0 | 0.2 | 1.9 | 0.074 | - |
| hard | no_llm | agents_random_s1 | 30 | 30/30 | 30/30 | 0.0 | 0.0 | 0.2 | 3.0 | 0.061 | - |
| hard | no_llm | agents_random_s2 | 30 | 30/30 | 30/30 | 0.0 | 0.0 | 0.2 | 1.13 | 0.051 | - |
| hard | no_llm | agents_random_s3 | 30 | 30/30 | 30/30 | 0.0 | 0.0 | 0.2 | 2.67 | 0.05 | - |
| hard | no_llm | agents_random_s4 | 30 | 30/30 | 30/30 | 0.0 | 0.0 | 0.2 | 1.93 | 0.049 | - |
| hard | no_llm | agents_rules | 30 | 20/30 | 30/30 | 0.87 | 0.0 | 0.3 | 11.17 | 0.059 | 10 instancias |

Nota sobre `seg.`: todas las corridas de `llama-3.2-3b` y `main/qwen2.5-3b/{direct,stepwise}` se midieron con la GPU dedicada. Las demás compartieron la GPU con otros procesos de evaluación, así que sus tiempos están inflados. Los demás campos no dependen de eso (decodificación greedy).

Violaciones totales por tipo (sobre salidas con JSON legible):

| conjunto | modelo | estrategia | HC1 | HC2 | HC3 | HC4 | HC5 | HC6 | ESTRUCTURA |
|---|---|---|---|---|---|---|---|---|---|
| main | llama-3.2-3b | direct | 105 | 66 | 52 | 276 | 80 | 123 | 0 |
| main | llama-3.2-3b | repair | 140 | 99 | 75 | 263 | 95 | 125 | 0 |
| main | llama-3.2-3b | stepwise_nosearch | 16 | 0 | 0 | 0 | 81 | 2 | 0 |
| main | llama-3.2-3b | stepwise | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| main | llama-3.2-3b | agents | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| main | llama-3.2-3b | agents_sin_diagnosticador | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| main | llama-3.2-3b | agents_sin_critico | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| main | llama-3.2-3b | agents_sin_memoria | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| main | llama-3.2-3b | agents_sin_fewshot | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| main | llama-3.2-3b | agents_sin_ensamble | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| main | no_llm | random_nosearch | 18 | 0 | 0 | 2 | 51 | 6 | 0 |
| main | no_llm | random | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| main | no_llm | random_s1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| main | no_llm | random_s2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| main | no_llm | random_s3 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| main | no_llm | random_s4 | 2 | 0 | 0 | 0 | 3 | 0 | 0 |
| main | no_llm | random_b300 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| main | no_llm | random_b300_s1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| main | no_llm | random_b300_s2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| main | no_llm | random_b300_s3 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| main | no_llm | random_b300_s4 | 2 | 0 | 0 | 0 | 4 | 0 | 0 |
| main | no_llm | agents_random | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| main | no_llm | agents_random_s1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| main | no_llm | agents_random_s2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| main | no_llm | agents_random_s3 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| main | no_llm | agents_random_s4 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| main | no_llm | agents_rules | 0 | 0 | 0 | 0 | 3 | 0 | 0 |
| main | phi-3.5-mini | direct | 74 | 135 | 436 | 408 | 39 | 57 | 0 |
| main | phi-3.5-mini | stepwise | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| main | qwen2.5-0.5b | direct | 0 | 0 | 38 | 47 | 0 | 3 | 162 |
| main | qwen2.5-0.5b | stepwise | 1 | 0 | 0 | 0 | 5 | 0 | 0 |
| main | qwen2.5-1.5b | direct | 58 | 21 | 618 | 508 | 4 | 32 | 6 |
| main | qwen2.5-1.5b | stepwise | 2 | 0 | 0 | 0 | 15 | 0 | 0 |
| main | qwen2.5-3b | direct | 1 | 0 | 576 | 543 | 0 | 29 | 0 |
| main | qwen2.5-3b | repair | 5 | 0 | 599 | 552 | 0 | 29 | 0 |
| main | qwen2.5-3b | stepwise_nosearch | 28 | 0 | 0 | 0 | 156 | 6 | 0 |
| main | qwen2.5-3b | stepwise | 0 | 0 | 0 | 0 | 2 | 0 | 0 |
| stress | llama-3.2-3b | direct | 77 | 16 | 52 | 318 | 73 | 244 | 0 |
| stress | llama-3.2-3b | stepwise | 0 | 0 | 0 | 0 | 6 | 0 | 0 |
| stress | llama-3.2-3b | agents | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| stress | llama-3.2-3b | agents_sin_diagnosticador | 1 | 0 | 0 | 0 | 2 | 0 | 0 |
| stress | llama-3.2-3b | agents_sin_critico | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| stress | llama-3.2-3b | agents_sin_memoria | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| stress | llama-3.2-3b | agents_sin_fewshot | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| stress | llama-3.2-3b | agents_sin_ensamble | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| stress | no_llm | random_nosearch | 17 | 0 | 0 | 2 | 46 | 14 | 0 |
| stress | no_llm | random | 3 | 0 | 0 | 0 | 5 | 0 | 0 |
| stress | no_llm | random_s1 | 4 | 0 | 0 | 0 | 6 | 2 | 0 |
| stress | no_llm | random_s2 | 2 | 0 | 0 | 0 | 3 | 0 | 0 |
| stress | no_llm | random_s3 | 2 | 0 | 0 | 0 | 3 | 0 | 0 |
| stress | no_llm | random_s4 | 2 | 0 | 0 | 0 | 5 | 0 | 0 |
| stress | no_llm | random_b300 | 7 | 0 | 0 | 0 | 4 | 0 | 0 |
| stress | no_llm | random_b300_s1 | 0 | 0 | 0 | 0 | 1 | 0 | 0 |
| stress | no_llm | random_b300_s2 | 2 | 0 | 0 | 0 | 2 | 0 | 0 |
| stress | no_llm | random_b300_s3 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| stress | no_llm | random_b300_s4 | 3 | 0 | 0 | 0 | 4 | 0 | 0 |
| stress | no_llm | agents_random | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| stress | no_llm | agents_random_s1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| stress | no_llm | agents_random_s2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| stress | no_llm | agents_random_s3 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| stress | no_llm | agents_random_s4 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| stress | no_llm | agents_rules | 0 | 0 | 0 | 0 | 11 | 1 | 0 |
| stress | phi-3.5-mini | stepwise | 3 | 0 | 0 | 0 | 7 | 0 | 0 |
| stress | qwen2.5-0.5b | stepwise | 4 | 0 | 0 | 0 | 12 | 1 | 0 |
| stress | qwen2.5-1.5b | stepwise | 3 | 0 | 0 | 0 | 10 | 1 | 0 |
| stress | qwen2.5-3b | direct | 0 | 0 | 622 | 567 | 7 | 48 | 0 |
| stress | qwen2.5-3b | stepwise | 1 | 0 | 0 | 0 | 10 | 0 | 0 |
| hard | llama-3.2-3b | direct | 86 | 31 | 29 | 288 | 105 | 237 | 0 |
| hard | llama-3.2-3b | stepwise | 1 | 0 | 0 | 0 | 18 | 0 | 0 |
| hard | llama-3.2-3b | agents | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| hard | llama-3.2-3b | agents_sin_diagnosticador | 4 | 0 | 0 | 0 | 19 | 1 | 0 |
| hard | llama-3.2-3b | agents_sin_critico | 1 | 0 | 0 | 0 | 1 | 0 | 0 |
| hard | llama-3.2-3b | agents_sin_memoria | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| hard | llama-3.2-3b | agents_sin_fewshot | 4 | 0 | 0 | 0 | 9 | 0 | 0 |
| hard | llama-3.2-3b | agents_sin_ensamble | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| hard | no_llm | random | 5 | 0 | 0 | 0 | 16 | 0 | 0 |
| hard | no_llm | random_s1 | 4 | 0 | 0 | 0 | 11 | 0 | 0 |
| hard | no_llm | random_s2 | 6 | 0 | 0 | 0 | 10 | 1 | 0 |
| hard | no_llm | random_s3 | 3 | 0 | 0 | 0 | 6 | 0 | 0 |
| hard | no_llm | random_s4 | 5 | 0 | 0 | 1 | 13 | 0 | 0 |
| hard | no_llm | random_b300 | 4 | 0 | 0 | 0 | 9 | 1 | 0 |
| hard | no_llm | random_b300_s1 | 1 | 0 | 0 | 0 | 4 | 0 | 0 |
| hard | no_llm | random_b300_s2 | 4 | 0 | 0 | 0 | 9 | 0 | 0 |
| hard | no_llm | random_b300_s3 | 2 | 0 | 0 | 0 | 3 | 0 | 0 |
| hard | no_llm | random_b300_s4 | 2 | 0 | 0 | 0 | 7 | 0 | 0 |
| hard | no_llm | agents_random | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| hard | no_llm | agents_random_s1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| hard | no_llm | agents_random_s2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| hard | no_llm | agents_random_s3 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| hard | no_llm | agents_random_s4 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| hard | no_llm | agents_rules | 3 | 0 | 0 | 0 | 23 | 0 | 0 |
