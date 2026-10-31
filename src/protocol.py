#!/usr/bin/env python3
"""
Protocolo de evaluación (lo que muestra el paso 1 del video)
-----------------------------------------------------------
Imprime, a partir de los datos del repositorio, cómo se evalúa CADA estrategia: qué entradas, qué juez, qué
criterio y qué métricas. Responde al comentario del profesor sobre Deliverable 2 ("no queda claro cómo se
evalúa el modelo"). No ejecuta el modelo.

Uso:
    python src/protocol.py
"""

import os
import sys
import textwrap
from typing import List, Optional, Sequence

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from instances import SET_DIRS, instance_dir, list_instances, load_instance  # noqa: E402

LINE = "=" * 130
SETS = {
    "main": ("Principal", "escala de D1 (10 médicos, 21 turnos); inst_00 = escenario exacto de D1"),
    "stress": ("Estrés", "el mismo generador + 1..3 franjas bloqueadas extra por médico"),
    "hard": ("Difícil (nuevo en D3)", "capacidad total = demanda + 0..2 y Urgencia = cuota + 0..2 turnos"),
}
RULES = [
    ("HC1", "descanso >= 16 h entre días seguidos (prohibido Noche->Mañana, Noche->Tarde, Tarde->Mañana)"),
    ("HC2", "a lo más 1 turno por médico por día"),
    ("HC3", "dotación exacta de cada turno"),
    ("HC4", "cuota mínima de especialistas del turno (p. ej. >= 1 de Urgencia de día)"),
    ("HC5", "horas semanales <= contrato (32 h o 40 h = 4 o 5 turnos)"),
    ("HC6", "nadie trabaja en una franja que bloqueó"),
    ("Estructura", "JSON ilegible, días/turnos faltantes, IDs inexistentes o repetidos"),
]


def grid(headers: Sequence[str], rows: List[Optional[Sequence[str]]], widths: Sequence[int]) -> str:
    """Tabla con bordes; las celdas largas se parten en varias líneas. Una fila None es un separador."""
    def rule(left, mid, right):
        return left + mid.join("─" * (w + 2) for w in widths) + right

    def line(cells):
        cols = [textwrap.wrap(str(c), w) or [""] for c, w in zip(cells, widths)]
        return ["│" + "│".join(f" {(col[i] if i < len(col) else ''):<{w}} " for col, w in zip(cols, widths)) + "│"
                for i in range(max(len(col) for col in cols))]

    out = [rule("┌", "┬", "┐"), *line(headers), rule("├", "┼", "┤")]
    for r in rows:
        out += [rule("├", "┼", "┤")] if r is None else line(r)
    return "\n".join(out + [rule("└", "┴", "┘")])


def main():
    print(LINE)
    print("CÓMO SE EVALÚA (idéntico para línea base, solución D2, sistema de agentes y ablaciones)")
    print(LINE)

    print("\n1. ENTRADAS: instancias fijas, todas factibles (certificadas con CP-SAT al crearlas; "
          "CP-SAT no participa en ninguna estrategia)")
    rows, total = [], 0
    for name, (label, desc) in SETS.items():   # los evaluados (data/instances_calib/ solo ajusta los prompts)
        if not os.path.isdir(instance_dir(name)):
            continue
        n = len(list_instances(name))
        total += n
        rows.append((label, f"data/{SET_DIRS[name]}", str(n), desc))
    rows += [None, ("Total", "", str(total), "cada estrategia con LLM corre UNA vez por instancia (greedy, "
                                             "determinista); los controles al azar, con 5 semillas")]
    print(grid(("Conjunto", "Carpeta", "N", "Qué contiene"), rows, (21, 22, 3, 72)))

    print("\n2. JUEZ: src/verifier.py, independiente del código de las soluciones; cuenta violaciones de:")
    print(grid(("Regla", "Qué exige"), RULES, (10, 113)))

    _, demands = load_instance(list_instances("main")[0])
    req = demands["requirements_per_shift"]
    seats = sum(r["required_total"] for r in req.values()) * len(demands["days"])
    print("\n3. CRITERIO Y MÉTRICAS")
    print(grid(("Aspecto", "Definición"), [
        ("Salida evaluada", f"el horario final en JSON {{día: {{turno: [IDs]}}}}, {len(demands['days'])} días x "
                            f"{len(demands['shifts'])} turnos, {seats} plazas"),
        ("CORRECTO", "si y solo si el juez cuenta 0 violaciones. No hay crédito parcial"),
        ("No certificado", "un horario que el sistema marca 'no certificado' se evalúa igual y cuenta como "
                           "incorrecto si viola algo"),
        ("Métricas", "por estrategia y conjunto: horarios correctos de 30, violaciones medias por horario, saltos, "
                     "decisiones deshechas, llamadas al LLM y segundos por horario (RTX 5060)"),
    ], (16, 107)))

    print("\n4. EVALUACIÓN DEL MODELO, decisión por decisión (offline, desde las trazas; CP-SAT solo para evaluar)")
    print(grid(("Agente", "Qué se mide", "Se compara con"), [
        ("Asignador", "% de elecciones FATALES (después la semana ya no tiene solución), sola y después del "
                      "Crítico, en los estados donde la elección importa", "el azar en el MISMO menú"),
        ("Crítico", "cuántas propuestas fatales rechaza y cuántos rechazos eran innecesarios",
                    "aceptar todo (la ablación sin Crítico)"),
        ("Diagnosticador", "% de saltos ÚTILES: deshacen la decisión culpable y dejan en ese turno una opción con "
                           "solución que no quedó prohibida", "el azar entre los mismos candidatos y retroceder "
                                                              "1 turno (D2)"),
        ("Sistema", "horarios correctos con los agentes reemplazados por azar o por reglas fijas",
                    "los controles de la tabla de resultados"),
    ], (14, 72, 35)))
    print(LINE)


if __name__ == "__main__":
    main()
