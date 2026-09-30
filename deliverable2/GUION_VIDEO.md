# Guion del video — Deliverable 2 (máx. 3:00)

La rúbrica exige:
1. El pipeline corriendo de extremo a extremo sobre una entrada **no elegida para favorecerlo**.
2. La **línea base visible sobre la misma entrada**.
3. Salidas trazables al repositorio.
4. Nada de edición que oculte la ejecución.

Solo se ven los primeros 3:00.

## Antes de grabar (fuera de cámara)

1. Cierra lo que use la GPU (Discord, navegador con video, juegos).
2. Abre la carpeta del repo en VS Code / Antigravity, o la carpeta `video/` en el Explorador de Windows.
3. Ejecuta una vez `video/paso1_demo.py` (botón ▶) o `video/1_demo.bat` (doble clic) **sin grabar**, para que el modelo quede en caché.
4. Agranda la letra de la terminal o de la ventana (Ctrl + rueda del mouse).
5. Graba con **OBS Studio** o **Win + Alt + R**, con el micrófono activado.
6. Ensaya una vez con cronómetro. Si te pasas de 3:00, acorta lo que narras, no la ejecución.

## Guion con tiempos

### [0:00 – 0:20] Presentación
> "Somos el Grupo 11. Nuestra tarea es la del Deliverable 1: armar el horario semanal de 10 médicos en 21 turnos. Un horario solo es correcto si el verificador automático encuentra cero violaciones de las 6 reglas: descanso, un turno por día, cantidad de médicos, especialistas, horas máximas y días bloqueados. Usamos Llama 3.2 de 3 mil millones de parámetros, en 4 bits, en nuestra RTX 5060."

### [0:20 – 1:20] Paso 1: `video/paso1_demo.py` (o `1_demo.bat`), unos 30–40 s
- Al inicio: *"El programa elige una instancia al azar entre las 30; no la escogimos nosotros."* Lee cuál salió.
- Tabla de médicos: *"Estos son los datos: especialidades, horas máximas y días bloqueados."*
- **[1/2] Línea base (Deliverable 1)**: *"Primero le pedimos al modelo el horario completo de una vez."* Cuando diga FALLIDO: *"Llena casi todos los turnos, pero rompe las reglas: especialistas, días bloqueados, descansos."*
- **[2/2] Solución (Deliverable 2)**: *"Ahora el modelo decide un turno a la vez. Solo puede elegir combinaciones de médicos que cumplen las reglas, y el programa lleva las cuentas de horas y descansos."* Si aparece una línea con ✗, es un retroceso.
- Cuando diga APROBADO: *"Cero violaciones, con el mismo modelo y el mismo verificador."* Señala la tabla comparativa.

### [1:20 – 1:45] Paso 2: `video/paso2_resultados.py` (o `2_resultados.bat`)
Las filas `llama-3.2-3b` son las estrategias con el LLM; las filas `no_llm` son el control con elección al azar.
> "Esto no es un solo ejemplo. En 30 instancias, pedirlo directo da 0 de 30; nuestra solución, 30 de 30. En 30 casos más difíciles, 28 de 30. Darle al modelo sus errores para que los corrija no alcanza, y sin el retroceso tampoco. Y como control, el mismo sistema eligiendo al azar llega a 30: la mejora viene sobre todo del sistema que construimos alrededor del modelo."

### [1:45 – 2:35] Pasos 3 y 4: caso de falla
**`video/paso3_caso_de_falla.py`** (unos 40 s):
> "En el conjunto normal no falla. Este caso, stress_04, es uno de los 2 difíciles donde sí falla: la búsqueda agota sus 30 retrocesos y el sistema avisa que el horario no está certificado."

**`video/paso4_diagnostico.py`** (unos 10 s):
> "El diagnóstico explica por qué. En esta instancia los urgenciólogos alcanzan justo para cubrir la semana. El modelo pone al mismo urgenciólogo todas las mañanas de lunes a viernes. Ya el miércoles la semana queda sin solución: al que queda le toca trabajar todas las tardes hasta el domingo, y el domingo en la tarde está bloqueado. El problema recién se nota el sábado, 10 turnos después, y para volver al miércoles habría que revisar unas 390 mil combinaciones; el límite es 30. Eligiendo al azar, en cambio, esta instancia se resuelve."

### [2:35 – 3:00] Cierre
> "En resumen: pedir el horario directo falla siempre; dividir el problema en pasos y darle herramientas al modelo lo resuelve en 30 de 30. Nuestro límite es que el modelo repite especialistas y el retroceso no alcanza errores lejanos; eso es lo que vamos a mejorar en el Deliverable 3. Todo se reproduce con el README del repositorio."

## Reglas importantes
- Si en el paso 1 sale una instancia con retrocesos (✗), no pasa nada: explícalo como "el sistema corrigió una decisión".
- **No cortes ni aceleres** mientras corren los programas; mientras esperas, sigue hablando.

## Después de grabar

1. Sube el video a **YouTube como "No listado"** o a **Google Drive** con "Cualquier persona con el enlace puede ver".
2. Abre el enlace en una ventana de incógnito para comprobar que se ve sin iniciar sesión.
3. Reemplaza `VIDEO_LINK` en `README.md` y en `deliverable2/deliverable2.tex` (encabezado). Vuelve a compilar el PDF y haz commit + push.
