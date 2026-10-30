# Prompts de los agentes (Deliverable 3)

Cada agente tiene su prompt en un archivo propio y versionado, fuera del código. `src/agent_core.py` (`Prompt`) lo lee. Cada resultado (`results/.../agents*/<instancia>.json`, campo `output.prompts`) y cada traza registran el archivo, su versión y su hash (sha1). Las trazas guardan también las secciones usadas en cada llamada y el mensaje de usuario exacto.

| Archivo | Agente | Versión evaluada | Salida (restringida a 1 token) |
|---|---|---|---|
| [`asignador.md`](asignador.md) | A1 Asignador | 2 | número de una opción del menú, o `0` para mantener su propuesta tras un rechazo |
| [`critico.md`](critico.md) | A2 Crítico | 3 | `1` aceptar, `2` rechazar, `3` sondear |
| [`diagnosticador.md`](diagnosticador.md) | A3 Diagnosticador | 4 | número de la decisión pasada que se rehace |

El prompt de sistema se arma con las secciones `## …` del archivo. La observación (el mensaje de usuario) la construye el código con los números de las herramientas. Cada técnica que se ablaciona es una sección o un paso del agente, así que quitarla no cambia nada más:

| Sección o paso | Técnica (The Prompt Report, Schulhoff et al. 2024) | Agentes | Estrategia que la quita |
|---|---|---|---|
| `Rol` | Role prompting (zero-shot) | todos | — (base) |
| `Reglas` + salida de 1 token | Answer engineering: espacio de respuesta restringido | todos | — (base; sin ella es la línea base directa) |
| `Ejemplos` | Few-shot (in-context learning) | todos | `agents_sin_fewshot` |
| `Memoria` + lecciones en la observación | Reflexion (memoria verbal entre intentos) | todos | `agents_sin_memoria` |
| `Revisión` + rechazo del Crítico | Self-Refine / CRITIC (crítica anclada en herramientas) | A1 + A2 | `agents_sin_critico` |
| dos órdenes del menú, se suman las log-probs | Ensembling por permutación del orden (mitiga la sensibilidad al orden) | A1 | `agents_sin_ensamble` |
| observación de `explicar_callejon` → acción | ReAct basado en observaciones (sin texto libre) | A3 | `agents_sin_diagnosticador` (retroceso cronológico de D2) |

Ningún ejemplo sale de una instancia evaluada. Los del Asignador y del Crítico son sintéticos, escritos a mano. Los del Diagnosticador son salidas reales de la herramienta T4 sobre el conjunto de **calibración** (`data/instances_calib/`, que no entra en la evaluación), etiquetadas con CP-SAT y generadas con `python src/build_fewshot.py`.

## Historial

Los prompts se ajustaron solo con el conjunto de calibración.

| Versión | Qué cambió | Corridas |
|---|---|---|
| asignador 1, critico 1, diagnosticador 1 | primera versión; T4 proponía como candidatas las asignaciones más recientes de los médicos del conflicto, lo que solo permitía saltar unos pocos turnos atrás. Ojo: el piloto quedó mezclado; calib_00..13 se corrieron con esta versión y calib_14..19 ya con la siguiente (ver `output.prompts` de cada JSON) | `results/calib/llama-3.2-3b/agents_piloto_v1/` |
| asignador 1\*, critico 1, diagnosticador 2 | T4 pasa a una ventana con las últimas 12 decisiones; se reordena un ejemplo del Asignador para que las respuestas no sean siempre la misma posición (\*mismo número de versión, otro sha) | `results/calib/llama-3.2-3b/agents_piloto_v2/` |
| asignador 2, critico 2, diagnosticador 3 | la revisión del código encontró que General contaba como especialidad escasa y otros defectos de las herramientas (ver el README principal); el Crítico pasó a ver cada rasgo frente al mejor valor de ese rasgo; los ejemplos del Diagnosticador se rehicieron con salidas reales de T4 y sus reglas pedían saltos de 4 a 8 turnos | `results/calib/llama-3.2-3b/agents_piloto_v3/` |
| asignador 2, critico 2, diagnosticador 4 | en calibración, los saltos de la v3 se acortaron (3.6 turnos de media) y solo la mitad deshacía la culpable, menos que el azar entre los mismos candidatos; se volvió al criterio de la v2: el candidato más temprano que involucra a un médico del conflicto | `results/calib/llama-3.2-3b/agents_piloto_v4/` |
| **asignador 2, critico 3, diagnosticador 4** (evaluada) | el Crítico vuelve a comparar contra UNA alternativa (la que deja más opciones al turno siguiente), y ahora las tres alertas se calculan contra esa misma alternativa, que es la que ve | `results/calib/llama-3.2-3b/agents/` (calibración) y `results/<conjunto>/llama-3.2-3b/agents*/` (evaluación) |
