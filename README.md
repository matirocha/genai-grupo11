# Automated Hospital Staff Scheduling with Small Open-Weight LLMs (<8B)

**Generative Artificial Intelligence (580694) - Spring 2026**  
**Universidad de Concepción**  
**Deliverable 1: Problem Definition, Failure Diagnosis & Feasibility**

---

## 👥 Grupo 11 - Integrantes
- **Integrante 1:** Matías Rocha (matiasrocha@udec.cl)
- **Integrante 2:** [Integrante 2]
- **Integrante 3:** [Integrante 3]
- **Integrante 4:** [Integrante 4]

---

## 📌 Project Overview
The **Medical Staff Scheduling Problem (MSSP)** is a mission-critical, combinatorial constraint satisfaction problem (CSP) in healthcare operations. The goal is to generate a valid weekly hospital shift schedule assigning medical personnel to shifts while strictly satisfying hard operational and legal constraints (rest periods, weekly working hour caps, specialty coverage) and optimizing soft preferences.

When prompted directly, small open-weight language models ($\le 8\text{B}$) **consistently fail** due to their autoregressive nature, inability to perform multi-step lookahead / backtracking, and state tracking drift.

---

## 🎯 Task Specification & Ground Truth
- **Input:** Staff roster (IDs, specialties, weekly maximum hour limits, unavailable slots) and shift requirements (required headcount and specialty minimums across 21 weekly shifts).
- **Output:** A strict JSON object containing the complete 7-day schedule.
- **Ground Truth Evaluation:** Evaluated via a deterministic programmatic verifier (`src/verifier.py`):
  1. `HC1_MIN_REST`: $\ge 16$ hours continuous rest between consecutive shifts.
  2. `HC2_NO_DOUBLE_SHIFT`: Maximum 1 shift per staff member per calendar day.
  3. `HC3_STAFFING_DEMAND`: Exact required personnel count per shift.
  4. `HC4_SPECIALTY_COVERAGE`: Mandatory specialty presence (e.g., Anesthesiologists on Night shifts).
  5. `HC5_MAX_HOURS`: No doctor exceeds their weekly legal limit.
  6. `HC6_UNAVAILABLE_SLOTS`: No staff member scheduled during pre-requested off-slots.

---

## 🔬 Candidate Models (<8B & Size Bonus)

To target the **bonus points** for selecting models meaningfully smaller than the 8B ceiling, we propose three high-performing compact models in the **3B–3.8B** range:

| Candidate Model | Parameters | Context | Key Benchmark Highlights |
| :--- | :---: | :---: | :--- |
| **Qwen 2.5 3B-Instruct** | 3.09B | 32k / 128k | MMLU: 65.4%, GSM8k: 84.5%. Superior structured JSON formatting and reasoning. |
| **Phi-3.5-mini-Instruct** | 3.82B | 128k | GSM8k: 86.0%, HumanEval: 70.1%. Synthetic high-reasoning data curriculum. |
| **Llama 3.2 3B-Instruct** | 3.21B | 128k | MMLU: 63.4%, MATH: 48.0%. Highly efficient instruction-following and LoRA fine-tuning. |

---

## ⚡ Execution Feasibility
- **VRAM Profile (4-bit QLoRA/NF4):** $\approx 2.2 - 2.8\text{ GB}$ VRAM.
- **VRAM Profile (16-bit FP16/BF16):** $\approx 6.2 - 7.5\text{ GB}$ VRAM.
- **Target Platform:** Google Colab Free Tier (Nvidia T4 GPU, 15 GB VRAM) providing $> 100\%$ safety margin for long context evaluation and fast inference ($\approx 35\text{ tokens/s}$).

---

## 📂 Repository Structure
```text
.
├── README.md                   # Project overview, team, benchmarks & feasibility
├── data/
│   ├── sample_staff.json       # Personnel profiles, specialties, limits and constraints
│   └── sample_demands.json     # 21 weekly shifts, staffing demands, and hard constraints
├── src/
│   ├── verifier.py             # Programmatic Ground Truth constraint checker
│   └── baseline_direct.py      # Baseline direct prompting runner & failure showcase
├── notebooks/
│   └── Colab_Feasibility.ipynb # End-to-end executable notebook on Colab T4
└── deliverable1/
    ├── deliverable1.tex        # Single-page LaTeX poster / executive summary source
    └── Deliverable 1.pdf       # Original task assignment specification
```

---

## 🚀 Quick Start

### 1. Run the Programmatic Verifier:
```bash
python3 src/verifier.py data/sample_staff.json data/sample_demands.json <schedule_output.json>
```

### 2. Run the Direct Prompting Baseline:
```bash
python3 src/baseline_direct.py
```

### 3. Open in Google Colab:
Open `notebooks/Colab_Feasibility.ipynb` directly in [Google Colab](https://colab.research.google.com/) with a free T4 GPU runtime.
