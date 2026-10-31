## Horarios correctos (0 violaciones) por conjunto

| Estrategia | Principal | Estrés | Difícil | Total (90) | Viol./horario | Saltos | Deshechas | Pasadas LLM | Seg. |
|---|---|---|---|---|---|---|---|---|---|
| Línea base: prompt directo (D1) | 0/30 | 0/30 | 0/30 | 0/90 | 25.09 | - | - | 1 | 14 |
| Solución D2 (turno a turno + retroceso) | 30/30 | 28/30 | 22/30 | 80/90 | 0.28 | 5.2 | 5.2 | 26 | 14 |
| Sistema de agentes (completo) | 30/30 | 30/30 | 30/30 | 90/90 | 0.00 | 0.3 | 3.3 | 77 | 9 |
|   sin Diagnosticador (ReAct): retrocede 1 turno | 30/30 | 29/30 | 23/30 | 82/90 | 0.30 | 2.9 | 2.9 | 66 | 7 |
|   sin Crítico (CRITIC + Self-Refine) | 30/30 | 30/30 | 29/30 | 89/90 | 0.02 | 1.2 | 12.2 | 63 | 8 |
|   sin memoria de lecciones (Reflexion) | 30/30 | 30/30 | 30/30 | 90/90 | 0.00 | 0.5 | 4.1 | 86 | 9 |
|   sin ejemplos (Few-Shot) | 30/30 | 30/30 | 27/30 | 87/90 | 0.14 | 1.8 | 6.2 | 112 | 14 |
|   sin ensamble por permutación | 30/30 | 30/30 | 30/30 | 90/90 | 0.00 | 0.3 | 3.3 | 48 | 5 |
| Control: D2 eligiendo al azar (5 semillas) | 29.8/30 (29–30) | 27.4/30 (26–29) | 24.6/30 (22–26) | 81.8/90 (78–85) | 0.27 | 3.8 | 3.8 | 0 | 0 |
| Control: D2 al azar con 300 retrocesos (5 semillas) | 29.8/30 (29–30) | 28.2/30 (27–30) | 27.0/30 (25–28) | 85.0/90 (82–87) | 0.17 | 21.3 | 21.3 | 0 | 0 |
| Control: agentes al azar (5 semillas) | 30.0/30 (30–30) | 30.0/30 (30–30) | 30.0/30 (30–30) | 90.0/90 (90–90) | 0.00 | 0.9 | 5.6 | 0 | 0 |
| Control: agentes con reglas fijas | 29/30 | 25/30 | 20/30 | 74/90 | 0.46 | 6.6 | 8.2 | 0 | 0 |

## Correctos según el presupuesto de saltos (90 instancias)

| Estrategia | ≤0 saltos | ≤5 | ≤10 | ≤30 | ≤300 |
|---|---|---|---|---|---|
| Solución D2 (turno a turno + retroceso) | 42/90 | 71/90 | 77/90 | 80/90 | – |
| Sistema de agentes (completo) | 78/90 | 90/90 | 90/90 | 90/90 | – |
| sin Diagnosticador (ReAct): retrocede 1 turno | 78/90 | 80/90 | 82/90 | 82/90 | – |
| sin Crítico (CRITIC + Self-Refine) | 57/90 | 86/90 | 89/90 | 89/90 | – |
| sin memoria de lecciones (Reflexion) | 81/90 | 87/90 | 89/90 | 90/90 | – |
| sin ejemplos (Few-Shot) | 67/90 | 83/90 | 86/90 | 87/90 | – |
| sin ensamble por permutación | 76/90 | 90/90 | 90/90 | 90/90 | – |
| Control: D2 eligiendo al azar (5 semillas) | 62.0/90 (57–67) | 76.6/90 (73–82) | 79.8/90 (77–83) | 81.8/90 (78–85) | – |
| Control: D2 al azar con 300 retrocesos (5 semillas) | 62.0/90 (57–67) | 76.6/90 (73–82) | 79.8/90 (77–83) | 81.8/90 (78–85) | 85.0/90 (82–87) |
| Control: agentes al azar (5 semillas) | 65.6/90 (62–68) | 86.6/90 (84–89) | 88.8/90 (88–90) | 90.0/90 (90–90) | – |
| Control: agentes con reglas fijas | 57/90 | 67/90 | 71/90 | 74/90 | – |

## Evaluación por decisión (CP-SAT offline)

| configuración | estados que deciden | elección fatal: Asignador / tras el Crítico / azar en el mismo menú | Crítico: rechazos de fatales / rechazos, fatales interceptadas | saltos útiles (azar entre candidatos, retroceder 1) |
|---|---|---|---|---|
| */llama-3.2-3b/agents | 101 | 48% / 27% / 45% | 47/488, 47/52 | 100% (69%, 18%) en 27 callejones |
| */llama-3.2-3b/agents_sin_diagnosticador | 70 | 56% / 19% / 44% | 38/301, 38/43 | 2% (53%, 2%) en 259 callejones |
| */llama-3.2-3b/agents_sin_critico | 178 | 58% / 58% / 48% | - | 98% (83%, 46%) en 103 callejones |
| */llama-3.2-3b/agents_sin_memoria | 126 | 48% / 25% / 44% | 49/622, 49/59 | 70% (65%, 2%) en 46 callejones |
| */llama-3.2-3b/agents_sin_fewshot | 183 | 53% / 35% / 47% | 120/1195, 120/124 | 38% (68%, 12%) en 160 callejones |
| */llama-3.2-3b/agents_sin_ensamble | 95 | 43% / 27% / 43% | 42/475, 42/47 | 93% (72%, 21%) en 28 callejones |
| */no_llm/agents_random | 142 | 42% / 37% / 44% | 21/360, 21/45 | 73% (72%, 27%) en 70 callejones |
| */no_llm/agents_rules | 191 | 30% / 26% / 44% | 18/53, 18/23 | 6% (64%, 3%) en 596 callejones |
