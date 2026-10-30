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

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from instances import SET_DIRS, instance_dir, list_instances, load_instance  # noqa: E402

LINE = "=" * 78
SETS = {
    "main": "principal: escala de D1 (10 médicos, 21 turnos); inst_00 = escenario exacto de D1",
    "stress": "estrés: el mismo generador + 1..3 franjas bloqueadas extra por médico",
    "hard": "difícil (nuevo en D3): capacidad total = demanda + 0..2 y Urgencia = cuota + 0..2 turnos",
}
RULES = [
    ("HC1", "descanso >= 16 h entre días seguidos (prohibido Noche->Mañana, Noche->Tarde, Tarde->Mañana)"),
    ("HC2", "a lo más 1 turno por médico por día"),
    ("HC3", "dotación exacta de cada turno"),
    ("HC4", "cuota mínima de especialistas del turno (p. ej. >= 1 de Urgencia de día)"),
    ("HC5", "horas semanales <= contrato (32 h o 40 h = 4 o 5 turnos)"),
    ("HC6", "nadie trabaja en una franja que bloqueó"),
]


def main():
    print(LINE)
    print("CÓMO SE EVALÚA (idéntico para línea base, solución D2, sistema de agentes y ablaciones)")
    print(LINE)
    total = 0
    print("1. ENTRADAS: instancias fijas del repositorio, todas certificadas factibles con CP-SAT al crearlas")
    print("   (existe al menos un horario correcto; CP-SAT no participa en ninguna estrategia).")
    for name in SETS:   # los conjuntos evaluados (data/instances_calib/ solo se usa para ajustar los prompts)
        if not os.path.isdir(instance_dir(name)):
            continue
        n = len(list_instances(name))
        total += n
        print(f"   - data/{SET_DIRS[name]:<17} {n:>3} instancias  {SETS[name]}")
    print(f"   Total: {total} instancias. Cada estrategia con LLM corre UNA vez por instancia, con decodificación greedy")
    print("   (determinista); los controles al azar, con 5 semillas.")
    _, demands = load_instance(list_instances("main")[0])
    req = demands["requirements_per_shift"]
    print("2. SALIDA EVALUADA: el horario final en JSON {día: {turno: [IDs]}}, "
          f"{len(demands['days'])} días x {len(demands['shifts'])} turnos, "
          f"{sum(r['required_total'] for r in req.values()) * len(demands['days'])} plazas.")
    print("3. JUEZ: src/verifier.py, independiente del código de las soluciones. Cuenta violaciones de 6 reglas duras:")
    for code, text in RULES:
        print(f"   {code}  {text}")
    print("   + ESTRUCTURA: JSON ilegible, días/turnos faltantes, IDs inexistentes o repetidos.")
    print("4. CRITERIO: un horario es CORRECTO si y solo si tiene 0 violaciones. No hay crédito parcial.")
    print("   Un horario que el sistema marca 'no certificado' se evalúa igual y cuenta como incorrecto si viola algo.")
    print("5. MÉTRICAS por estrategia y conjunto: horarios correctos de 30, violaciones medias por horario, saltos,")
    print("   decisiones deshechas, llamadas al LLM y segundos por horario (RTX 5060).")
    print("6. EVALUACIÓN DEL MODELO, decisión por decisión (offline, CP-SAT solo como oráculo, desde las trazas):")
    print("   - Asignador: % de elecciones FATALES (después la semana ya no tiene solución) en los estados donde")
    print("     la elección importa, sola y después del Crítico;")
    print("   - Crítico: cuántas propuestas fatales rechaza y cuántos rechazos eran innecesarios;")
    print("   - Diagnosticador: % de saltos útiles (deshacen la decisión culpable y dejan en ese turno una opción")
    print("     con solución que no quedó prohibida), frente al azar entre los mismos candidatos y a retroceder 1 turno;")
    print("   - Asignador frente al azar en el MISMO menú; además, los agentes al azar y con reglas fijas como controles.")
    print(LINE)


if __name__ == "__main__":
    main()
