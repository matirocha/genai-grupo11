# Asignación Automatizada de Turnos Médicos con LLMs Open-Weight

**Generative Artificial Intelligence (580694) · Universidad de Concepción · Grupo 11**
**Deliverable 2: Primera solución funcionando** — sobre la tarea y el fallo definidos en Deliverable 1.

- 🎥 **Video (≤3 min):** [youtu.be/B9UK7B3sv48](https://youtu.be/B9UK7B3sv48)
- 📄 **Documento técnico (1 página, LaTeX):** [`deliverable2/deliverable2.pdf`](deliverable2/deliverable2.pdf) · fuente [`deliverable2/deliverable2.tex`](deliverable2/deliverable2.tex)
- 📁 Entrega anterior: [`deliverable1/`](deliverable1/)

---

## 1. Resumen

| | Línea base (prompting directo, Deliverable 1) | Solución Deliverable 2 (turno a turno + herramientas) |
|---|---|---|
| Horarios válidos (0 violaciones), conjunto principal, N=30 | **0/30** | **30/30** |
| Horarios válidos, conjunto de estrés, N=30 | **0/30** | **28/30** |
| Violaciones duras por horario (media, principal) | 23.4 | 0 |
| Llamadas al LLM por horario | 1 | 21.9 |
| Tiempo por horario (RTX 5060) | 12.8 s | 11.9 s |

Modelo: **meta-llama/Llama-3.2-3B-Instruct** (3.21B parámetros, revisión `0cb88a4f764b7a12671c53f0838cd831a0843b95`), uno de los tres candidatos de Deliverable 1. Corre en 4-bit NF4 con bitsandbytes y decodificación greedy, en la **RTX 5060 8 GB** declarada en Deliverable 1 (≈2.4 GB de VRAM).
Mismo verificador (`src/verifier.py`) y mismas instancias para todas las estrategias. Todas las salidas crudas están en `results/`.

## 2. Cómo reproducir lo que muestra el video

### 2.1 Instalación (Windows o Linux, GPU NVIDIA)
```bash
pip install torch==2.13.0 --index-url https://download.pytorch.org/whl/cu130
pip install -r requirements.txt
```
**Acceso al modelo:** Llama-3.2 tiene licencia de Meta. Hay que hacer esto una sola vez:
1. Aceptar la licencia en [huggingface.co/meta-llama/Llama-3.2-3B-Instruct](https://huggingface.co/meta-llama/Llama-3.2-3B-Instruct), con una cuenta de Hugging Face.
2. Crear un token de lectura (Settings → Access Tokens).
3. Iniciar sesión con `hf auth login`.

La primera ejecución descarga el modelo (~6 GB). Sin GPU local se puede usar Colab T4: [`notebooks/D2_Demo_Colab.ipynb`](notebooks/D2_Demo_Colab.ipynb).

### 2.2 Demostración en vivo: línea base y solución sobre la misma instancia
```bash
python src/demo.py --random
```
Elige una instancia al azar entre las 30 del conjunto principal (no la escogemos nosotros), carga el modelo y ejecuta:
1. **[1/2] Línea base (Deliverable 1)**: el prompt directo; la salida del modelo se transmite token a token y se evalúa con el verificador.
2. **[2/2] Solución (Deliverable 2)**: una línea por turno (21 decisiones del LLM) y una línea `✗ ... retrocede` por cada retroceso; al final, la grilla semanal, el verificador y una tabla comparativa.

Cada ejecución queda guardada en `results/demo/<instancia>_<fecha>.json`. Para una instancia fija: `python src/demo.py --instance inst_00` (inst_00 es el escenario exacto de Deliverable 1).

Los mismos pasos del video están en `video/` como archivos que se ejecutan sin argumentos: `paso1_demo.py` … `paso4_diagnostico.py` (botón ▶ del IDE), o `1_demo.bat` … `4_diagnostico.bat` (doble clic).

### 2.3 Resultados sobre todo el conjunto (lo que muestra la tabla del video)
```bash
python src/evaluate.py --summary --only llama-3.2-3b,no_llm
```
Muestra la vista corta del video (modelo elegido + ablación sin LLM). Sin `--only` imprime la tabla completa de todos los modelos. En ambos casos reescribe `results/summary.md` a partir de los JSON guardados. Para regenerarlos desde cero (≈60 min en la RTX 5060; la reparación es lo más lento):
```bash
python src/evaluate.py --strategies direct,repair,stepwise,stepwise_nosearch
python src/evaluate.py --set stress --strategies direct,stepwise
python src/evaluate.py --strategies random,random_nosearch
python src/evaluate.py --set stress --strategies random
```
(El modelo por defecto es Llama-3.2-3B; `--model` permite correr los modelos de comparación. `evaluate.py` salta las instancias que ya tienen resultado; para re-ejecutar, mover o borrar `results/`.)

### 2.4 Caso de falla y su diagnóstico
```bash
python src/demo.py --set stress --instance stress_04 --solo-solucion
python src/diagnose.py --set stress --instance stress_04
python src/diagnose.py --set main --position-bias
```
El primero muestra la solución agotando sus 30 retrocesos y entregando un horario **marcado como no certificado**. El segundo usa CP-SAT (solo como herramienta de análisis) para localizar la decisión que dejó la semana sin solución. El tercero mide el sesgo de posición del LLM.

## 3. Continuidad con Deliverable 1 y desviaciones declaradas

**Igual que en Deliverable 1:** la tarea (planificación semanal de 10 médicos en 21 turnos Mañana/Tarde/Noche, salida JSON), la entrada (`data/sample_staff.json`, `data/sample_demands.json` = `inst_00`), el criterio de corrección (0 violaciones de HC1–HC6 según el verificador programático) y el modelo (uno de los tres candidatos de Deliverable 1).

**Desviaciones (todas hacen la evaluación más exigente u honesta, no más fácil):**
1. **HC1 en el verificador.** El código de Deliverable 1 solo detectaba Noche(d)→Mañana(d+1), aunque su texto prohíbe también Noche→Tarde. Ahora el descanso se calcula con los horarios de turno (06–14, 14–22, 22–06) y se exige ≥16 h entre días consecutivos: se prohíben Noche→Mañana, Noche→Tarde y Tarde→Mañana. Los horarios se agregaron a `sample_demands.json` para que el modelo reciba la regla explícita.
2. **La evidencia de línea base de Deliverable 1 era simulada.** `baseline_direct.py` evaluaba una salida escrita a mano, y las cifras de Deliverable 1 (0/10 válidos, 7.4 violaciones/intento) no provenían de ejecuciones reales. Ahora la línea base ejecuta el modelo real con el mismo prompt: **0/30 válidos, con 23.4 violaciones de media** (rango 10–49). El modelo llena casi todas las plazas (40 de 42), pero rompe las reglas: cuota de especialidad (HC4, 39 % de las violaciones), bloqueos (HC6, 18 %), descanso (HC1, 15 %), horas (HC5, 11 %) y turno doble (HC2, 9 %). Son los fallos F1 y F2 diagnosticados en Deliverable 1.
3. **Más instancias.** Deliverable 1 usaba un escenario. Deliverable 2 evalúa 30 instancias factibles a la misma escala (`data/instances/`, inst_00 = Deliverable 1) y 30 instancias "de estrés" con más franjas bloqueadas (`data/instances_stress/`). Cada instancia se certificó como factible con OR-Tools CP-SAT **solo al construir el dataset** (`src/instances.py`), para que un fallo se deba al método y no a una instancia imposible.

## 4. La solución (`src/stepwise_solver.py`)

```
instancia ─► [1 estado externo] ─► [2 opciones legales] ─► [3 factibilidad futura] ─► [4 LLM elige 1 opción] ─► turno k+1 ... ─► JSON ─► verificador
                     ▲                                          │ 0 opciones
                     └──────────── [5 retroceso: prohibir elección previa, máx. 30] ◄┘
```

| Fallo diagnosticado en Deliverable 1 | Componente que lo ataca |
|---|---|
| **F2** Deriva de estado y aritmética (horas acumuladas, turnos del día) | **1.** El código lleva el estado (horas usadas, turno del día anterior, bloqueos). En cada paso el LLM recibe una tabla ya calculada y solo candidatos legales (HC1, HC2, HC5, HC6). |
| **F3** Alucinación de esquema e IDs en salidas largas | **2+4.** El LLM decide un turno por llamada. Su salida está **restringida por un trie de tokens** (`src/llm.py`) a combinaciones válidas de IDs con la dotación exacta y la cuota de especialidad (HC3, HC4). El JSON lo arma el código. |
| **F1** Decisión voraz sin retroceso | **3+5.** Antes de ofrecer una opción, un chequeo de capacidad restante (por turno, por especialidad y global) descarta las que dejan la semana sin salida. Si un turno queda sin opciones, se retrocede al anterior y se prohíbe esa elección. |

Si se agotan los 30 retrocesos, el sistema completa la semana relajando restricciones y **declara el resultado como no certificado**. El verificador (independiente, no comparte código con la solución) cuenta las violaciones. En los resultados, el sistema nunca certificó un horario inválido (`certified_but_invalid = 0`).

## 5. Resultados (N = 30 por conjunto, mismo verificador)

Llama-3.2-3B, decodificación greedy (determinista). "Viol." = violaciones duras medias por horario. La tabla completa, con todas las corridas y el conteo por tipo de restricción, está en [`results/summary.md`](results/summary.md).

| Estrategia | Conjunto | Válidos | Viol. | Llamadas LLM | Retrocesos |
|---|---|---|---|---|---|
| `direct` (línea base) | principal | 0/30 | 23.4 | 1 | – |
| `repair` (3 rondas con el verificador) | principal | 0/30 | 26.6 | 4 | – |
| `stepwise_nosearch` (sin pasos 3 y 5) | principal | 3/30 | 3.3 | 21 | – |
| **`stepwise` (solución)** | principal | **30/30** | **0** | 21.9 | 0.93 |
| `direct` (línea base) | estrés | 0/30 | 26.0 | 1 | – |
| **`stepwise` (solución)** | estrés | **28/30** | 0.20 | 25.2 | 4.17 |
| `random` (pasos 1–5 al azar, sin LLM) | principal / estrés | 30/30 / 26/30 | 0 / 0.27 | 0 | 0.07 / 4.30 |

**Estrategias alternativas evaluadas**
- `repair`: prompting directo, más hasta 3 rondas en que el verificador le devuelve al modelo sus violaciones (la opción "CoT con verificación intermedia" del plan de Deliverable 1). No mejora, e incluso empeora: 26.6 violaciones por horario, frente a 23.4 del directo. En 80 de 90 rondas (89 %) las violaciones no cambian y ninguna instancia termina mejor que como empezó, porque el modelo reescribe casi el mismo horario aunque recibe la lista exacta de errores.
- `stepwise_nosearch`: la solución sin chequeo hacia adelante ni retroceso. F2 y F3 desaparecen (0 errores de HC2, HC3, HC4 o de formato), pero solo 3/30 son válidos. El 82 % de las violaciones son HC5 y el 16 % HC1: sin retroceso, el LLM pone más especialistas de los exigidos en el 24 % de los turnos con cuota, agota sus horas y el fin de semana queda sin opciones legales. Es la decisión voraz (F1) que describió Deliverable 1.
- `random`: el mismo andamiaje eligiendo **al azar** en lugar del LLM. Llega a 30/30 y 26/30: la corrección la aportan sobre todo el estado externo, el filtro y la búsqueda; Llama suma 2 instancias en estrés.

**Comparación de modelos (mismo pipeline, mismas instancias)**

| Modelo | Parámetros | Directo | Solución (principal) | Solución (estrés) | Sesgo de posición |
|---|---|---|---|---|---|
| **Llama-3.2-3B-Instruct (elegido)** | 3.21B | 0/30 | **30/30** | **28/30** | 33 % |
| Qwen2.5-3B-Instruct (candidato Deliverable 1) | 3.09B | 0/30 | 29/30 | 26/30 | 47 % |
| Phi-3.5-mini-instruct (candidato Deliverable 1) | 3.82B | 0/30 | 30/30 | 27/30 | 18 % |
| Qwen2.5-1.5B-Instruct (ablación) | 1.54B | 0/30 | 25/30 | 27/30 | 42 % |
| Qwen2.5-0.5B-Instruct (ablación) | 0.49B | 0/30 (16 con JSON) | 29/30 | 27/30 | 59 % |

"Sesgo de posición" = porcentaje de decisiones en que el modelo eligió exactamente los primeros candidatos de la lista (con elección al azar sería 17 %).

**Por qué Llama-3.2-3B sobre los otros dos candidatos:** las instrucciones piden justificar la elección frente a los otros dos candidatos de Deliverable 1 y permiten compararlos, así que corrimos los tres con el mismo pipeline, instancias y verificador. Llama es el que más horarios resuelve:
- **Frente a Qwen2.5-3B:** resuelve 3 instancias más (1 en el principal, 2 en estrés), con solo un 4 % más de parámetros y menos sesgo de posición.
- **Frente a Phi-3.5-mini:** es un 16 % más pequeño y resuelve una instancia más de estrés.

Con N = 30 las diferencias son pequeñas (el azar también llega a 30/30 con el mismo andamiaje), así que pesó que Llama casi no cuesta tamaño frente al más pequeño. El costo es la licencia de Meta (§2.1). La ablación muestra que el pipeline funciona incluso con Qwen 0.5B, porque el LLM solo elige entre opciones legales; esa reducción de tamaño queda medida para Deliverable 3.

Revisiones exactas usadas: Llama-3.2-3B `0cb88a4f764b7a12671c53f0838cd831a0843b95`, Qwen2.5-3B `aa8e72537993ba99e69dfaafa59ed015b17504d1`, Phi-3.5-mini `2fe192450127e6a83f7441aef6e3ca586c338b77` (ver `results/*/<modelo>/run_info.json`).

## 6. Caso de falla y límites

En el conjunto principal Llama no falla (30/30). Bajo estrés falla en 2 de 30: `stress_04` y `stress_25`.

**Caso de falla: `stress_04`.** La solución agota sus 30 retrocesos y entrega un horario **marcado como no certificado**, con 4 violaciones HC5 (médicos sobre su tope de horas). Por qué falla (`python src/diagnose.py --set stress --instance stress_04`):
1. **Instancia al límite.** Los 14 turnos de día exigen un urgenciólogo, y los 3 urgenciólogos suman exactamente 14 turnos de capacidad (5 + 4 + 5). Cada turno de Urgencia tiene que caer en el lugar justo.
2. **El modelo repite al mismo especialista.** Asigna a DOC_04 todas las mañanas de lunes a viernes. CP-SAT (solo como herramienta de diagnóstico) muestra que la semana deja de tener solución en la tercera de ellas, el miércoles Mañana. A DOC_04 y DOC_05 les quedan 4 turnos para las 9 plazas que faltan, así que DOC_06 debe trabajar los 5 días restantes, empezando el miércoles en la tarde. La regla Tarde→Mañana (16 h) lo obliga a seguir en la tarde cada día, hasta el domingo en la tarde, justo cuando está bloqueado. Si se quita el bloqueo o la regla de descanso, la semana vuelve a tener solución.
3. **El chequeo hacia adelante no lo ve.** Compara totales (9 turnos disponibles para 9 plazas: cuadra) y no si cada médico puede tomar cada turno concreto. Ese miércoles admitió 6 opciones y solo 3 permitían terminar la semana.
4. **El retroceso no alcanza.** El choque aparece 10 turnos después (sábado Tarde). Para volver al miércoles, el retroceso cronológico tendría que agotar ~390 000 combinaciones intermedias, con un presupuesto de 30.

**Evidencia:** con el mismo andamiaje, la elección al azar reparte a los urgenciólogos y resuelve `stress_04` sin retroceder, mientras que los 5 LLMs probados fallan. `stress_25` falla también con el azar: ahí el límite es solo del andamiaje. Qwen2.5-3B, con más sesgo de posición (47 %), falla además en `inst_28` del conjunto principal por el mismo mecanismo (repite a DOC_04 todas las mañanas y agota a los urgenciólogos antes del fin de semana). Es el fallo F1 de Deliverable 1 reapareciendo *dentro* de la elección del modelo.

**Límites conocidos**
- El chequeo hacia adelante verifica condiciones necesarias de capacidad, no factibilidad real, y el retroceso cronológico no llega a errores lejanos: bajo estrés, 28/30.
- La mejora proviene sobre todo del andamiaje: el azar llega a 30/30 en el conjunto principal.
- El modelo elegido requiere aceptar la licencia de Meta para reproducir (§2.1).
- Se evalúa una semana aislada (sin la transición domingo→lunes), igual que en Deliverable 1.
- El número de opciones crece como C(n,k)·k! (permutaciones en el trie). Con 30 médicos y 3 por turno serían ~24 000 cadenas por paso.
- Próximos pasos (Deliverable 3): presentar los candidatos en orden aleatorio o por holgura, retroceso no cronológico (*backjumping*) y fine-tuning LoRA sobre trazas de decisiones válidas (plan de Deliverable 1).

## 7. Estructura del repositorio
```text
.
├── README.md
├── requirements.txt
├── data/
│   ├── sample_staff.json, sample_demands.json   # escenario de Deliverable 1 (= inst_00)
│   ├── instances/          inst_00..inst_29     # conjunto principal (certificado factible)
│   └── instances_stress/   stress_00..stress_29 # conjunto de estrés (+ franjas bloqueadas)
├── src/
│   ├── verifier.py          # oráculo: HC1–HC6 (ground truth)
│   ├── instances.py         # generación y certificación CP-SAT del dataset
│   ├── llm.py               # carga 4-bit NF4 + decodificación restringida (trie)
│   ├── baseline_direct.py   # línea base (prompt directo de Deliverable 1, modelo real)
│   ├── repair_loop.py       # alternativa: reparación con feedback del verificador
│   ├── stepwise_solver.py   # SOLUCIÓN Deliverable 2
│   ├── evaluate.py          # corre estrategias sobre los conjuntos y resume
│   ├── demo.py              # demostración del video
│   └── diagnose.py          # análisis de fallas (CP-SAT) y sesgo de posición
├── video/                   # los 4 pasos del video, ejecutables sin argumentos (.py y .bat)
├── results/                 # salidas crudas por conjunto/modelo/estrategia/instancia + summary.md
├── notebooks/               # Colab_Feasibility.ipynb (Deliverable 1), D2_Demo_Colab.ipynb (Deliverable 2)
├── deliverable1/            # entrega 1
└── deliverable2/            # documento técnico (tex + pdf) y guion del video
```

## 8. Verificador por línea de comandos
Cualquier salida guardada se puede volver a verificar de forma independiente:
```bash
python src/verifier.py data/instances_stress/stress_04.json results/stress/llama-3.2-3b/stepwise/stress_04.json
```
También acepta el formato de Deliverable 1: `python src/verifier.py data/sample_staff.json data/sample_demands.json <horario.json>`.
