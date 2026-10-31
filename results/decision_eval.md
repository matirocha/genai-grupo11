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
