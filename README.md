# Asignación Automatizada de Turnos Médicos con LLMs Open-Weight

**Generative Artificial Intelligence - **  
**Universidad de Concepción**  
**Deliverable 1: Definición de Tarea, Diagnóstico de Fallo y Factibilidad**

---

## 👥 Grupo 11 - Integrantes
- **Integrante 1:** Matías Rocha
- **Integrante 2:** Benjamin Grandon

---

## 📌 Descripción del Proyecto
El **Problema de Asignación de Turnos Médicos** (*Medical Staff Scheduling Problem*, MSSP) es un problema combinatorio de satisfacción de restricciones (CSP) crítico en la gestión y operaciones hospitalarias. El objetivo es generar una planificación semanal de turnos para el personal médico que satisfaga estrictamente las restricciones duras legales y operativas (periodos de descanso obligatorio, límites de horas semanales por contrato, cobertura mínima de especialidades) y optimice las preferencias blandas.

Al ser consultados directamente (*zero-shot prompting*), los modelos de lenguaje pequeños de pesos abiertos ($\le 8\text{B}$) **fallan sistemáticamente** debido a su naturaleza autorregresiva, la incapacidad de realizar búsqueda con retroceso (*backtracking*) o planificación a futuro, y la deriva en el seguimiento del estado y la aritmética.

---

## 🎯 Especificación de la Tarea y Ground Truth
- **Entrada:** Nómina del personal médico (identificadores, especialidades, límites de horas semanales, franjas no disponibles) y requerimientos de turnos (dotación requerida y mínimos por especialidad a lo largo de 21 turnos semanales).
- **Salida:** Un objeto JSON estricto y válido con la planificación completa de los 7 días (21 turnos).
- **Evaluación Ground Truth:** Evaluado mediante un verificador programático determinista (`src/verifier.py`):
  1. `HC1_MIN_REST`: $\ge 16$ horas de descanso continuo obligatorio entre turnos consecutivos.
  2. `HC2_NO_DOUBLE_SHIFT`: Máximo 1 turno por profesional al día calendario.
  3. `HC3_STAFFING_DEMAND`: Dotación exacta de personal requerida por turno.
  4. `HC4_SPECIALTY_COVERAGE`: Presencia obligatoria de especialistas requeridos (ej. Anestesiólogos en turno Noche).
  5. `HC5_MAX_HOURS`: Ningún médico puede exceder su límite de horas semanales por contrato ($\le 40$h).
  6. `HC6_UNAVAILABLE_SLOTS`: Cero asignaciones en franjas horarias bloqueadas por solicitud previa.

---

## 🔬 Modelos Candidatos y Justificación (<8B)

Para abordar la tarea con alta eficiencia computacional y rápida iteración, seleccionamos tres modelos compactos de última generación en el rango de **3.0B a 3.8B** (dentro del límite de 8B):

| Modelo Candidato | Parámetros | Contexto | Aspectos Clave de Benchmarks |
| :--- | :---: | :---: | :--- |
| **Qwen 2.5 3B-Instruct** | 3.09B | 32k / 128k | MMLU: 65.4%, GSM8k: 84.5%. Rendimiento SOTA en formato estructurado JSON y seguimiento de restricciones lógicas. |
| **Phi-3.5-mini-Instruct** | 3.82B | 128k | GSM8k: 86.0%, HumanEval: 70.1%. Curado con datos sintéticos de alto razonamiento y lógica paso a paso. |
| **Llama 3.2 3B-Instruct** | 3.21B | 128k | MMLU: 63.4%, MATH: 48.0%. Excelente seguimiento de instrucciones y altamente eficiente para *fine-tuning* con LoRA. |

---

## ⚡ Factibilidad de Ejecución
- **Hardware Local Dedicado:** Estación de trabajo equipada con procesador **AMD Ryzen 7 7700**, tarjeta gráfica **Nvidia RTX 5060 (8 GB VRAM)** y **32 GB RAM DDR5**. Permite inferencia nativa rápida en FP16 ($\approx 6.2 - 7.5\text{ GB}$) y cuantizada en 4-bit NF4 ($\approx 2.2 - 2.8\text{ GB}$), además de posibilitar *fine-tuning* con LoRA/QLoRA localmente sin limitaciones de cuotas de cómputo en la nube.
- **Entorno en la Nube (Google Colab Gratuito):** GPU Nvidia T4 (15 GB VRAM), proporcionando un entorno 100% reproducible con un margen de seguridad $> 100\%$ de VRAM para evaluación con contexto largo e inferencia veloz ($\approx 35\text{--}45\text{ tokens/s}$).

---

## 📂 Estructura del Repositorio
```text
.
├── README.md                   # Descripción general, equipo, modelos y factibilidad
├── data/
│   ├── sample_staff.json       # Perfiles del personal, especialidades, límites y restricciones
│   └── sample_demands.json     # 21 turnos semanales, demanda de dotación y restricciones duras
├── src/
│   ├── verifier.py             # Verificador programático de restricciones (Ground Truth)
│   └── baseline_direct.py      # Script de evaluación de línea base zero-shot y análisis de fallos
├── notebooks/
│   └── Colab_Feasibility.ipynb # Cuaderno ejecutable de principio a fin en Google Colab T4
└── deliverable1/
    ├── deliverable1.tex        # Código fuente LaTeX del póster / resumen ejecutivo (1 página)
    └── Deliverable 1.pdf       # Pauta original del entregable
```

---

## 🚀 Inicio Rápido

### 1. Ejecutar el Verificador Programático:
```bash
python3 src/verifier.py data/sample_staff.json data/sample_demands.json <schedule_output.json>
```

### 2. Ejecutar la Línea Base Directa (Zero-Shot):
```bash
python3 src/baseline_direct.py
```

### 3. Abrir en Google Colab:
Abre `notebooks/Colab_Feasibility.ipynb` directamente en [Google Colab](https://colab.research.google.com/) con entorno de ejecución GPU T4 gratuita.
