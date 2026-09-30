| conjunto | modelo | estrategia | N | válidos | JSON ok | viol. media | llamadas LLM | seg. | retrocesos | sobreuso esp. | fallidas |
|---|---|---|---|---|---|---|---|---|---|---|---|
| main | llama-3.2-3b | direct | 30 | 0/30 | 30/30 | 23.4 | 1.0 | 12.8 | - | - | 30 instancias |
| main | llama-3.2-3b | repair | 30 | 0/30 | 30/30 | 26.57 | 4.0 | 36.8 | - | - | 30 instancias |
| main | llama-3.2-3b | stepwise_nosearch | 30 | 3/30 | 30/30 | 3.3 | 21.0 | 10.8 | 0.0 | 0.242 | 27 instancias |
| main | llama-3.2-3b | stepwise | 30 | 30/30 | 30/30 | 0.0 | 21.9 | 11.9 | 0.93 | 0.165 | - |
| main | no_llm | random_nosearch | 30 | 6/30 | 30/30 | 2.57 | 0.0 | 0.0 | 0.0 | 0.08 | 24 instancias |
| main | no_llm | random | 30 | 30/30 | 30/30 | 0.0 | 0.0 | 0.0 | 0.07 | 0.057 | - |
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
| stress | no_llm | random_nosearch | 30 | 2/30 | 30/30 | 2.63 | 0.0 | 0.0 | 0.0 | 0.082 | 28 instancias |
| stress | no_llm | random | 30 | 26/30 | 30/30 | 0.27 | 0.0 | 0.0 | 4.3 | 0.078 | stress_07, stress_13, stress_18, stress_25 |
| stress | phi-3.5-mini | stepwise | 30 | 27/30 | 30/30 | 0.33 | 26.1 | 12.8 | 5.1 | 0.177 | stress_01, stress_04, stress_25 |
| stress | qwen2.5-0.5b | stepwise | 30 | 27/30 | 30/30 | 0.57 | 25.9 | 15.4 | 5.03 | 0.077 | stress_01, stress_04, stress_17 |
| stress | qwen2.5-1.5b | stepwise | 30 | 27/30 | 30/30 | 0.47 | 26.9 | 25.9 | 5.9 | 0.116 | stress_04, stress_07, stress_25 |
| stress | qwen2.5-3b | direct | 30 | 0/30 | 30/30 | 41.47 | 1.0 | 12.9 | - | - | 30 instancias |
| stress | qwen2.5-3b | stepwise | 30 | 26/30 | 30/30 | 0.37 | 26.1 | 22.7 | 5.2 | 0.25 | stress_01, stress_04, stress_15, stress_25 |

Nota sobre `seg.`: todas las corridas de `llama-3.2-3b` y `main/qwen2.5-3b/{direct,stepwise}` se midieron con la GPU dedicada. Las demás compartieron la GPU con otros procesos de evaluación, así que sus tiempos están inflados. Los demás campos no dependen de eso (decodificación greedy).

Violaciones totales por tipo (sobre salidas con JSON legible):

| conjunto | modelo | estrategia | HC1 | HC2 | HC3 | HC4 | HC5 | HC6 | ESTRUCTURA |
|---|---|---|---|---|---|---|---|---|---|
| main | llama-3.2-3b | direct | 105 | 66 | 52 | 276 | 80 | 123 | 0 |
| main | llama-3.2-3b | repair | 140 | 99 | 75 | 263 | 95 | 125 | 0 |
| main | llama-3.2-3b | stepwise_nosearch | 16 | 0 | 0 | 0 | 81 | 2 | 0 |
| main | llama-3.2-3b | stepwise | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| main | no_llm | random_nosearch | 18 | 0 | 0 | 2 | 51 | 6 | 0 |
| main | no_llm | random | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
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
| stress | no_llm | random_nosearch | 17 | 0 | 0 | 2 | 46 | 14 | 0 |
| stress | no_llm | random | 3 | 0 | 0 | 0 | 5 | 0 | 0 |
| stress | phi-3.5-mini | stepwise | 3 | 0 | 0 | 0 | 7 | 0 | 0 |
| stress | qwen2.5-0.5b | stepwise | 4 | 0 | 0 | 0 | 12 | 1 | 0 |
| stress | qwen2.5-1.5b | stepwise | 3 | 0 | 0 | 0 | 10 | 1 | 0 |
| stress | qwen2.5-3b | direct | 0 | 0 | 622 | 567 | 7 | 48 | 0 |
| stress | qwen2.5-3b | stepwise | 1 | 0 | 0 | 0 | 10 | 0 | 0 |
