# Patrones de comportamiento estudiantil entre universidades

**Análisis descriptivo sobre tres clientes de EdMachina · Documento crudo para el informe pre-riesgo**

Versión 1 · 23-09-2026 · Datos: Europea Madrid (snapshot 17-09-2026), Europeia Portugal (histórico semanal 11-2025 → 09-2026, con backfill 2022-2025), UDIMA (snapshot 03-08-2026)

> Este documento no usa ninguna salida de modelo (probabilidades, niveles de riesgo, `full_facts`, explicador). Todo lo que se reporta son hechos observados: matrículas, edades, notas registradas, pagos, fechas y estados administrativos. El objetivo es describir cómo se comportan los alumnos y las titulaciones, no predecir.

---

## 0. Resumen ejecutivo

Sobre **86.747 matrículas** de tres universidades privadas en dos países (España y Portugal), con modalidades presencial y online y todos los niveles (ciclos, grado, posgrado), aparecen **siete patrones que se repiten en al menos dos instituciones** y que no dependen del sistema de origen, del país ni del modelo de negocio:

| # | Patrón transversal | Dónde se valida |
|---|---|---|
| P1 | **El alumno online no es el alumno presencial en digital.** En grado tiene 10-14 años más; en posgrado, 2-7 años más. | Madrid, Portugal, UDIMA |
| P2 | **La baja es un fenómeno del primer año.** El nuevo ingreso se da de baja entre 3,4 y 8,3 veces más que el reingreso y aporta el 74-91 % de las bajas. En Portugal, el 70 % de las bajas ocurre antes del mes 12. | Madrid, Portugal, UDIMA |
| P3 | **El posgrado online es el segmento más estable** (RR 0,36 en dos universidades). El grado presencial de alumno con edad atípica (25+) es el más frágil donde se puede medir en cursada. | Madrid, Portugal, UDIMA |
| P4 | **Pagar y avanzar son dimensiones independientes** (correlación ≈ 0 en las tres), pero el **pago parcial anticipa la baja** incluso cuando el motivo declarado no es la deuda. | Madrid, Portugal, UDIMA (independencia); Portugal (anticipación) |
| P5 | **El alumno internacional duplica la baja de nuevo ingreso** y su motivo se desplaza hacia lo financiero y la no renovación. | Portugal (PALOP, otros), UDIMA (Latinoamérica) |
| P6 | **Psicología es la única disciplina con baja superior a la media en las tres universidades.** Educación/Profesorado, Marketing-Comunicación y Ciencias sociales/Deporte están por debajo en las tres. | Madrid, Portugal, UDIMA |
| P7 | **Cuando el alumno se mueve, se queda cerca:** el 73-82 % de los cambios internos ocurre dentro de la misma disciplina y el cambio de modalidad va hacia online 3 de cada 4 veces. Una parte de las "bajas" son aplazamientos: el alumno vuelve a los pocos meses. | Madrid, Portugal (grafos de trayectoria) |

Y **cuatro hallazgos de un solo cliente** que funcionan como hipótesis fuertes para replicar: el primer suspenso multiplica la baja ×7 (Portugal); la fecha registrada de la baja es administrativa y llega en lotes, meses después del abandono real (Portugal); el 43 % de las anulaciones pre-inicio no son pérdidas sino movimientos internos (Madrid); el reloj de bajas es bimodal (octubre y marzo) en una universidad 100 % online (UDIMA).

---

## 1. Datos, estandarización y método

### 1.1 Qué se analizó

| Cliente | Formato de origen | Matrículas | Alumnos | Titulaciones | Ventana | Unidad temporal |
|---|---|---|---|---|---|---|
| Europea Madrid (Universidad Europea, 5 sedes) | Parquet, salida RP | 43.885 | 41.919 | 830 | Curso 2026-27, snapshot 17-09-2026 | Una fila por matrícula |
| Europeia Portugal (Universidade Europeia, IADE, IPAM Lisboa, IPAM Porto) | CSV pipe, 527.521 filas | 24.635 | 23.691 | 634 | Cursos 2022-2026, ejecuciones semanales desde 11-2025 | Una fila por matrícula × semana |
| UDIMA | Parquet, salida RP | 18.227 | 17.426 | 104 | Matrículas 2023, 2024, 2025 (+ 2026 sin cursado), snapshot 03-08-2026 | Una fila por matrícula |

Los tres archivos son salidas de Retention Partner, pero **solo se usaron sus columnas de hechos** (académicas, financieras, demográficas, administrativas y de fechas). Se descartaron todas las columnas de modelo. UDIMA incluía nombre, email, teléfono y DNI: se eliminaron antes de cualquier procesamiento y el DNI se pseudonimizó.

### 1.2 Esquema común

Se estandarizaron 30 variables en un esquema único (`cliente`, `tipo_estudiante` nuevo_ingreso/reingreso, `tipo_titulo` grado/posgrado/ciclo-otro, `modalidad` online/presencial, `edad`, `nacionalidad`, `disciplina`, `asignaturas_aprobadas/suspendidas`, `pct_avance_aprob`, `pct_pago_real`, `baja`, `fecha_baja`, `fecha_inicio`, `tipo_baja_original`, …). Las titulaciones se agruparon en **10 disciplinas** mediante reglas de palabras clave sobre el nombre (multilingüe ES/PT/EN); la tasa de "sin clasificar" quedó en 0,2-1,5 % por cliente.

### 1.3 Definición de "baja" y poblaciones cerradas

La comparabilidad exige ser explícitos sobre qué se cuenta como baja en cada cliente, porque **no es el mismo evento**:

| Cliente | Evento contado como baja | Población para tasas | Qué significa |
|---|---|---|---|
| Madrid | `estado = Anulado` (2.479) | Todo el snapshot | **Anulación pre-inicio o inicio de curso** (el 69 % fechada julio-septiembre 2026). No es abandono en cursada. |
| Portugal | `estado = inscrito_nulo` en la fila anual | **Matrícula-año del curso 2024** (9.948) | Baja registrada durante el año académico ya cerrado. Se reconstruyó una fila por matrícula y año porque el `tipo_estudiante` de la última fila confunde con la supervivencia (quien continúa pasa a "reingreso"). |
| UDIMA | `estado = baja` | Matrículas 2023 y 2024 (7.949) | Baja en cursada de años ya cerrados. |

Las tasas absolutas **no son comparables entre clientes**; sí lo son las razones dentro de cada cliente (riesgo relativo, RR, frente a la media del propio cliente). Todo el documento trabaja así.

### 1.4 Métodos

- **Descriptivos estratificados**: tasas y medianas por cliente × tipo × modalidad × edad × disciplina, con RR frente a la base del cliente y tamaños mínimos (n ≥ 50 por celda para titulaciones).
- **Análisis temporal**: meses desde el inicio de la matrícula hasta la baja (Portugal), mes del año de la baja (los tres), concentración por fecha exacta (lotes administrativos), hazard por año de permanencia.
- **Taxonomía administrativa**: clasificación de los motivos de anulación/baja registrados por la institución (Madrid, Portugal).
- **Correlación de rangos (Spearman)** entre % pagado y % de avance aprobado.
- **Grafos dirigidos de trayectoria**: nodos = titulaciones o disciplinas, aristas = alumnos que pasan de una a otra (cambio interno en Madrid; secuencia de matrículas por fecha de inicio en Portugal). Métricas: grado ponderado de entrada/salida, balance neto, PageRank.
- **Arquetipos deterministas**: seis celdas definidas por reglas (tipo × modalidad × edad), no por clustering, para que sean auditables y replicables en cualquier cliente.

### 1.5 Limitaciones que condicionan la lectura

1. **Madrid mide anulación pre-inicio, no abandono.** Sirve para composición, taxonomía, grafos e historial académico de reingresantes; sus variables de pago son inutilizables (el curso acababa de empezar: mediana de pago 0 %).
2. **UDIMA no tiene edad ni variables académicas/financieras para las bajas** (solo para los 7.477 activos de 2025). Cualquier cruce baja × edad o baja × pago excluye a UDIMA.
3. **Portugal está truncado a la izquierda**: las cohortes 2022-2023 casi no tienen filas de primer año (quien se fue en 2022 no aparece). Por eso las tasas usan el curso 2024 y el tiempo-hasta-baja usa entradas ≥ 2023.
4. **Semántica dudosa en dos variables de Portugal**: `q_pagos_vencidos` se comporta como "cuotas vencidas/emitidas" (más cuotas → menos baja), no como impagos; `asignaturas_convalidadas` llega vacía. Ninguna se usa.
5. La agrupación por disciplina es por palabras clave; es razonable, no perfecta (p. ej., "Gestión deportiva" se asignó a Negocios; "Ciencias del deporte" a Ciencias sociales/Deporte).

---

## 2. Quién es el alumno: composición y edad

### 2.1 Tres universidades, tres modelos

| | Europea Madrid | Europeia Portugal | UDIMA |
|---|---|---|---|
| % nuevo ingreso | 54 % | 62 % | 45 % |
| % grado / % posgrado | 69 % / 26 % | 31 % / 39 % (+ 23 % sin tipo en la fuente, inferido del nombre) | 37 % / 63 % |
| % online | 30 % | 35 % | 100 % |
| Edad mediana (p25-p75) | 22 (19-25) | 25 (21-33) | 32 (26-41) |

Madrid es una universidad de grado presencial joven con una pata online creciente; Portugal es mixta y muy fragmentada en posgraduaciones cortas (634 titulaciones); UDIMA es posgrado online de adulto profesional.

### 2.2 P1 · El alumno online no es el alumno presencial en digital

**Método**: edad mediana por cliente × tipo de título × modalidad (n ≥ 100). **Dónde**: los tres clientes; en Madrid y Portugal la comparación es *dentro de la misma universidad*.

| Tipo | Modalidad | Madrid | Portugal | UDIMA |
|---|---|---|---|---|
| Grado | presencial | **20** (3 % tiene 30+) | **21** (2 % tiene 30+) | — |
| Grado | online | **25** (28 % tiene 30+) | **31** (56 % tiene 30+) | **35** (65 % tiene 30+) |
| Posgrado | presencial | 25 (24 % tiene 30+) | 27 (38 % tiene 30+) | — |
| Posgrado | online | 27 (40 % tiene 30+) | 34 (65 % tiene 30+) | 31 (57 % tiene 30+) |

- En **grado**, la brecha online-presencial es de **+5 años en Madrid y +10 en Portugal**; UDIMA, sin presencial, se sitúa en 35. El grado online es un producto para el adulto que vuelve a estudiar, no una versión a distancia del grado de 18 años.
- En **posgrado**, la brecha es menor (+2 / +7) porque el posgrado presencial ya es de adulto joven.
- Consecuencia para el resto del análisis: cualquier comparación online vs presencial sin controlar por edad y tipo de título está confundida.
- Distribución por bandas (online): en las tres universidades el alumno online se distribuye casi uniformemente entre 25 y 50 años; el presencial se concentra en ≤ 24 (84 % Madrid, 67 % Portugal).

*Figura: `figs/01_edad_modalidad.png`*

### 2.3 Edad por disciplina (mediana)

| Disciplina | Madrid | Portugal | UDIMA |
|---|---|---|---|
| Educación / Profesorado | 25 | **47** | 32 |
| Salud clínica | 21 | 37 | 31,5 |
| Negocios / Gestión | 22 | 26 | 33 |
| Psicología | 22 | 26 | 34 |
| Ingeniería / Informática / Datos | 22 | 29 | 35 |
| Derecho / Fiscal | 23 | 22 | 29 |
| Marketing / Comunicación | 22 | 24 | 29 |
| Diseño / Creativas | 22 | 23 | 35 |

Educación es la disciplina "de segunda carrera" por excelencia (en Portugal, las microcredenciales para profesores en activo tienen mediana 47). Derecho y Marketing son las más jóvenes en los tres países.

### 2.4 Composición por sexo (solo UDIMA)

63 % mujeres entre los activos. Por disciplina: Psicología 82 % mujeres, Educación 67 %, Marketing 67 %, Negocios 59 %, Derecho 58 %, Ingeniería 23 %. El dato sexo no existe en Madrid ni en Portugal; no se puede validar transversalmente.

---

## 3. Cuándo se va: el primer año y el calendario

### 3.1 P2 · La baja es un fenómeno del primer año

**Método**: tasa de baja por tipo de estudiante en población cerrada; RR nuevo ingreso / reingreso. **Dónde**: los tres.

| Cliente | Nuevo ingreso | Reingreso | RR | % de las bajas que son nuevo ingreso |
|---|---|---|---|---|
| Europea Madrid (anulación pre-inicio) | 9,5 % (2.249 / 23.683) | 1,1 % (230 / 20.202) | **8,3×** | 91 % |
| Europeia Portugal (curso 2024) | 22,1 % (1.409 / 6.364) | 6,5 % (232 / 3.584) | **3,4×** | 86 % |
| UDIMA (2023-24) | 28,7 % (974 / 3.391) | 7,7 % (351 / 4.558) | **3,7×** | 74 % |

Por tipo de título el patrón se mantiene en las 9 celdas cliente × tipo:

| Tipo | Madrid NI / RE | Portugal NI / RE | UDIMA NI / RE |
|---|---|---|---|
| Grado | 13,9 % / 1,1 % | 30,3 % / 7,0 % | 32,4 % / 12,7 % |
| Posgrado | 4,7 % / 2,3 % | 10,9 % / 3,6 % | 26,9 % / 5,0 % |
| Ciclos / otro | 3,7 % / 1,2 % | 45,3 % / 11,3 % | 30,0 % / 10,0 % |

**Hazard por año de permanencia** (Portugal, cursos 2024 y 2025): año 0 → 22,1 % / 12,5 %; año 1 → 7,0 % / 3,9 %; año 2 → 5,2 % / 1,9 %. En Madrid, la anulación cae de 9,5 % en primer año a 1,3 % en segundo y ≈ 1 % después. Superar el primer año reduce el riesgo a un cuarto o menos, en las tres.

*Figura: `figs/02_nuevo_vs_reingreso.png`*

### 3.2 Meses desde el inicio hasta la baja (Portugal)

**Método**: `fecha_baja − fecha_inicio_matricula`, bajas con inicio ≥ 2023 (n = 2.970). **Dónde**: solo Portugal tiene ambas fechas para las bajas.

| Acumulado a… | 3 meses | 6 meses | 9 meses | 12 meses | 18 meses | 24 meses |
|---|---|---|---|---|---|---|
| % de las bajas | 18 % | 38 % | 57 % | **70 %** | 88 % | 96 % |

Mediana: **7,8 meses** (grado 9,1; posgrado 6,0). Excluyendo las bajas "não renovou" (que son un registro administrativo tardío, ver 3.4), la mediana baja a 6,6 meses y el 82 % ocurre antes del mes 12.

Es coherente con la lectura de UDIMA en el informe de riesgo (riesgo consolidado entre el 5.º y el 8.º mes): **la ventana de intervención útil es el primer semestre**.

*Figura: `figs/03_meses_hasta_baja.png`*

### 3.3 El calendario de la baja: tres relojes distintos

**Método**: distribución del mes del año de la fecha de baja. **Dónde**: los tres.

| Mes | Madrid | Portugal | UDIMA |
|---|---|---|---|
| Enero | 0 % | 10 % | 7 % |
| Febrero | 2 % | **26 %** | 8 % |
| Marzo | 2 % | 9 % | **12 %** |
| Abril | 4 % | 12 % | 9 % |
| Mayo | 11 % | 4 % | 7 % |
| Junio | 13 % | 10 % | 4 % |
| Julio | **22 %** | 3 % | 4 % |
| Agosto | **21 %** | 2 % | 6 % |
| Septiembre | **26 %** | 6 % | 10 % |
| Octubre | 0 % | 8 % | **15 %** |
| Noviembre | 0 % | 5 % | 11 % |
| Diciembre | 0 % | 5 % | 6 % |

- **Madrid**: reloj de admisión. El 69 % de las anulaciones ocurre en julio-septiembre, antes o al iniciar el curso. Es "summer melt": el alumno reserva plaza y la libera cuando consigue otra.
- **UDIMA**: reloj de semestres. Dos picos, **octubre (15 %) y marzo (12 %)**, 4-6 semanas después de cada inicio de cuatrimestre; el valle es junio-julio. El alumno online decide en el arranque de cada período.
- **Portugal**: reloj administrativo. Febrero concentra el 26 %, pero es un artefacto de registro (3.4).

*Figura: `figs/04_estacionalidad.png`*

### 3.4 La fecha de la baja es la del trámite, no la del abandono (Portugal)

**Método**: concentración de bajas por fecha exacta. **Dónde**: Portugal (3.878 bajas con fecha).

- **El 39 % de las bajas cae en solo 10 fechas.** La mayor: 19-02-2026, con 492 bajas en un día, todas "não renovou". Otras: 03-06-2024 (217), 13-04-2026 (184), 24-04-2026 (123).
- Por motivo: "não renovou" se registra casi íntegramente en febrero (490 de 560); "dívida" en marzo-abril y junio (lotes de cierre financiero); "desistência" y "early attrition" sí siguen el calendario real (picos en octubre y enero).
- En UDIMA la concentración es mucho menor (fecha más frecuente: 36 bajas), y en Madrid la anulación es individual.

**Implicación**: en muchas instituciones la baja "oficial" llega 3-8 meses después de que el alumno dejó de participar. Medir retención con la fecha administrativa subestima sistemáticamente la ventana de intervención. Es el argumento descriptivo más sólido para leer señales de comportamiento antes que el estado administrativo.

---

## 4. Por qué se va: taxonomía administrativa de la baja

**Método**: clasificación de los motivos registrados por la institución. **Dónde**: Madrid y Portugal (UDIMA no informa motivo).

### 4.1 Europea Madrid · anulaciones 2026-27 (n = 2.479)

| Motivo | n | % | Naturaleza |
|---|---|---|---|
| Abandono de los estudios | 1.345 | 55,8 % | Pérdida real (subcausa "motivos personales" 1.348) |
| Cambio de titulación dentro de la universidad | 857 | 35,5 % | **Movimiento interno** |
| Se ha matriculado en otro centro | 132 | 5,5 % | Pérdida competitiva |
| Cambio de universidad dentro del grupo | 43 | 1,8 % | Movimiento intra-grupo |
| Cambio de modalidad (F2F ↔ online) | 20 | 0,8 % | Movimiento interno |
| Requisitos / créditos mínimos / convocatoria | 12 | 0,5 % | Académico-normativo |

- **El 43 % de las anulaciones no son pérdidas para la institución** (cambio de titulación, modalidad o universidad del grupo). La propia institución lo reconoce con el flag `excluir_attrition = true` exactamente en esas categorías.
- Solo el 0,5 % es por causa académica declarada. En un snapshot de inicio de curso, la anulación es una decisión de elección, no de rendimiento.
- Por tipo: en grado, el 40 % de las anulaciones es cambio interno; en posgrado, el 18 % (el alumno de posgrado que se va, se va).

### 4.2 Europeia Portugal · bajas registradas (todas las cohortes, n = 4.392; curso 2024 entre paréntesis)

| Motivo | % total | % 2024 | Naturaleza |
|---|---|---|---|
| Desistência (renuncia voluntaria) | 42 % | 31 % | Pérdida voluntaria |
| Dívida (deuda) | 27 % | 17 % | Financiera |
| Não renovou (no renovó) | 13 % | 31 % | Abandono silencioso |
| Anulação de inscrição | 8 % | 7 % | Anulación pre-inicio |
| Early attrition (primeros 2 meses) | 5 % | 3 % | Pérdida temprana |
| Termination (visado, condiciones) | 1 % | 1 % | Administrativa / internacional |
| Sin motivo | 4 % | 10 % | — |

- Por tipo de estudiante: en nuevo ingreso pesan más deuda (29 % vs 20 %) y early attrition (6 % vs 1 %); en reingreso, desistência (52 %) y no renovación (22 %).
- Por título: en posgrado la deuda es el 38 % de las bajas (vs 22 % en grado); en grado la no renovación es el 20 % (vs 0 % en posgrado, que es anual).
- Por modalidad: online tiene más desistência (52 % vs 41 %) y más deuda (34 % vs 26 %); presencial concentra la no renovación (16 % vs 5 %).

*Figura: `figs/05_taxonomia_baja.png`*

### 4.3 Lectura transversal

Aunque las taxonomías no coinciden, en ambos clientes emerge la misma estructura de tres bloques: **(a) elección** (cambio interno, anulación pre-inicio, otro centro), **(b) desenganche** (abandono/desistência, no renovación, early attrition) y **(c) dinero** (dívida). El bloque (a) es entre el 8 % (Portugal) y el 43 % (Madrid) de las bajas registradas; el bloque (c), entre el 0 % declarado (Madrid, pre-inicio) y el 27 % (Portugal). Cualquier KPI de retención que no separe estos tres bloques mezcla fenómenos con dueños y remedios distintos.

---

## 5. Cómo rinde: patrones académicos

### 5.1 Un solo suspenso cambia el destino (Portugal, hipótesis a replicar)

**Método**: tasa de baja por número de asignaturas suspendidas y aprobadas en el año, nuevo ingreso, curso 2024. **Dónde**: Portugal (Madrid es pre-inicio; UDIMA no tiene notas para las bajas).

| Suspendidas en el año | n | % baja |
|---|---|---|
| 0 | 3.187 | **6,4 %** |
| 1 | 394 | **45,2 %** |
| 2 | 183 | 57,4 % |
| 3-4 | 127 | 40,9 % |

| Aprobadas en el año | n | % baja |
|---|---|---|
| 0 | 270 | **65,9 %** |
| 1-2 | 586 | 26,6 % |
| 3-5 | 1.572 | 9,4 % |
| 6-10 | 1.326 | 4,1 % |
| 11+ | 206 | 2,4 % |

- El salto no es gradual: **de 0 a 1 suspenso la baja se multiplica por 7**. A partir de 3 aprobadas la baja cae por debajo del 10 %.
- En reingreso el efecto es menor pero existe: 1,2 % sin suspensos → 12,9 % con uno → 32,7 % con 5+.
- Cautela: parte de los suspensos registrados en primer año pueden ser "no presentado" de alumnos que ya se habían desenganchado. El patrón describe una asociación, no una causa; su valor está en que **un solo evento observable en el expediente separa dos poblaciones con destinos muy distintos**.

*Figura: `figs/06_primer_suspenso.png`*

### 5.2 Los suspensos se concentran en pocos alumnos y se arrastran (Madrid, reingresantes)

**Método**: distribución de asignaturas suspendidas acumuladas y brecha entre % cursado y % aprobado por año de permanencia. **Dónde**: Madrid (n = 18.733 reingresantes con historial); Portugal como contraste.

- **El 20 % de los alumnos con más suspensos acumula el 72 % de todos los suspensos** de la universidad (Portugal: 94 %, con una tasa de suspenso mucho más baja en general: 77 % sin ningún suspenso).
- En grado presencial, la tasa de fracaso (suspensas / evaluadas) es del 27 % de media, frente al 15 % en grado online. Por disciplina, Salud clínica 33 %, Ingeniería 26 %, Psicología 20 %, Negocios 19 %, Marketing 12,5 %, Educación 12 %. En Portugal el orden es distinto (Ingeniería 18 %, Derecho 15 %, Negocios 10 %, Diseño 5,5 %), así que la dificultad relativa por disciplina **es institucional, no universal**.
- **La brecha cursado-aprobado se abre con los años.** Mediana de (`pct_avance` − `pct_avance_aprob`) en grado: 1 pp en 2.º año, 5 pp en 3.º, 7 pp en 4.º, 18 pp en 5.º, 25 pp en 6.º, 37 pp en 7.º. El alumno que permanece más allá del plan no está avanzando: está arrastrando.
- La mediana de avance aprobado se estanca en el 48 % a partir del 4.º año (0,11 → 0,30 → 0,48 → 0,48 → 0,45): una cohorte de "larga permanencia con bajo rendimiento" que no se da de baja pero tampoco se gradúa.

### 5.3 El que se va, se va con poco (Portugal)

**Método**: % del programa aprobado en el momento de la baja. **Dónde**: Portugal (1.020 bajas con dato).

| % aprobado al salir | ≤ 10 % | 10-25 % | 25-50 % | 50-75 % | > 75 % |
|---|---|---|---|---|---|
| % de las bajas | 36 % | 36 % | 21 % | 6 % | 1 % |

Mediana: **15 %** (nuevo ingreso 12 %, reingreso 37 %). Solo el 7 % de los que abandonan había superado la mitad del programa. El abandono "con el título a la vista" es marginal: la decisión se toma temprano y con poca inversión hundida.

---

## 6. Cómo paga: patrones financieros

### 6.1 P4 · Pagar y avanzar son dimensiones independientes

**Método**: correlación de Spearman entre `pct_pago_real` y `pct_avance_aprob`. **Dónde**: los tres.

| Población | n | ρ Spearman |
|---|---|---|
| Portugal, cursos 2024-25 | 15.769 | **0,006** (NI 0,05; RE −0,14) |
| UDIMA, activos 2025 | 6.239 | **0,09** (NI 0,11; RE 0,23) |
| Madrid, reingresantes | 20.202 | **−0,01** |

A nivel de alumno, saber cuánto ha pagado no dice casi nada de cuánto ha aprobado, y viceversa. Son dos ejes ortogonales de compromiso. Esto justifica empíricamente tratar lo financiero y lo académico como dimensiones separadas en cualquier perfilado (y es consistente con el perfil bidimensional "Académico + Financiero" que domina en los informes de riesgo).

### 6.2 El pago parcial anticipa la baja, incluso sin deuda declarada (Portugal)

**Método**: tasa de baja por banda de % pagado, curso 2024, excluyendo las bajas cuyo motivo es "dívida". **Dónde**: Portugal.

| % pagado sobre lo facturado | Nuevo ingreso · % baja (sin dívida) | Reingreso · % baja (sin dívida) |
|---|---|---|
| ≤ 25 % | **34 %** | **19 %** |
| 25-50 % | 17 % | 5 % |
| 50-75 % | 9 % | 5 % |
| 75-99 % | 7 % | 2 % |
| 100 % | 15 % (n = 108) | 0 % (n = 62) |

Quitando las bajas por deuda, el alumno que paga menos de un cuarto sigue dándose de baja 5 veces más que el que paga más de tres cuartos. El pago parcial funciona como **termómetro de compromiso**, no solo como síntoma de capacidad de pago. Mediana de % pagado por estado al cierre del año: finalizados 61 %, matriculados 41 %, nulos 26 %.

*Figura: `figs/11_pago_vs_baja.png`*

### 6.3 Perfil de pago de UDIMA (activos 2025)

Mediana de pago 100 % en reingreso y 83 % en nuevo ingreso; 10 % con al menos un impago acumulado; el importe mediano de posgrado (4.944 €) es un 6 % superior al de grado (4.652 €) y el alumno latinoamericano paga menos (88 % vs 100 %) con menos convalidaciones (1 vs 7).

---

## 7. De dónde viene: nacionalidad e internacionalización

### 7.1 P5 · El alumno internacional duplica la baja de nuevo ingreso

**Método**: tasa de baja por grupo de nacionalidad × tipo de estudiante en población cerrada; mezcla de motivos. **Dónde**: Portugal y UDIMA (Madrid no informa nacionalidad).

**Europeia Portugal · curso 2024**

| Nacionalidad | % matrícula | Nuevo ingreso · % baja | Reingreso · % baja | RR (NI) vs portugueses |
|---|---|---|---|---|
| Portugal | 80 % | 15,8 % | 5,8 % | 1,0 |
| Brasil | 5 % | 29,0 % | 6,8 % | 1,8 |
| PALOP (Angola, Cabo Verde, Guiné-Bissau, Moçambique…) | 10 % | **46,7 %** | 15,1 % | **3,0** |
| Otros | 5 % | **47,6 %** | 8,2 % | **3,0** |

Mezcla de motivos: los portugueses se van por desistência (46 %); PALOP y otros, por **deuda (32 %) y no renovación (42 %)**, frente al 12 % y 30 % de los locales. La baja internacional es financiero-administrativa; la local es de desenganche.

**UDIMA · matrículas 2023-24**

| Nacionalidad | % matrícula | Nuevo ingreso · % baja | Reingreso · % baja | RR (NI) vs españoles |
|---|---|---|---|---|
| España | 76 % | 23,5 % | 5,8 % | 1,0 |
| Latinoamérica (Colombia, R. Dominicana, Perú, Argentina, Venezuela, Ecuador…) | 20 % | **43,3 %** | 16,6 % | **1,8** |
| Otros | 4 % | 25,6 % | 10,3 % | 1,1 |

En UDIMA el efecto es todavía más marcado en grado (44 % vs 17 %) que en posgrado (28 % vs 10 %), y persiste en reingreso (×2,9). Entre los activos, el alumno latinoamericano paga un 12 % menos de lo facturado.

Dos universidades, dos países, dos poblaciones internacionales distintas, **misma estructura**: RR 1,8-3,0 en primer año y desplazamiento del motivo hacia lo financiero. Es el segmento con mayor brecha entre volumen (20-25 % de la matrícula) y atención específica.

---

## 8. Qué estudia: disciplinas y titulaciones

### 8.1 P6 · Disciplinas: una sobre la media en las tres, tres bajo la media en las tres

**Método**: RR de baja en nuevo ingreso por disciplina frente a la media del cliente. **Dónde**: los tres.

| Disciplina | Madrid | Portugal | UDIMA | Lectura |
|---|---|---|---|---|
| **Psicología** | **1,12** | **1,19** | **1,59** | Única > 1 en los tres |
| Ingeniería / Informática / Datos | 0,93 | 0,93 | 1,89 | Neutra presencial, alta online |
| Derecho / Fiscal | 0,68 | 1,31 | 0,81 | Depende del cliente |
| Negocios / Gestión / MBA | 0,75 | 1,20 | 0,99 | Depende del cliente |
| Salud clínica | 1,65 | 0,78 | 0,76 | Alta solo en Madrid (ver 8.2) |
| Diseño / Creativas | 0,62 | 0,95 | — | Baja / neutra |
| Marketing / Comunicación | **0,68** | **0,85** | **0,71** | < 1 en los tres |
| Educación / Profesorado | **0,48** | **0,19** | **0,92** | < 1 en los tres |
| Ciencias sociales / Deporte | **0,62** | **0,40** | **0,59** | < 1 en los tres |

- **Psicología** es la única disciplina que supera la media en las tres universidades, en grado (RR 0,98 / 1,02 / 1,25) y sobre todo en posgrado (1,01 / 1,33 / 2,20). Es la carrera de acceso masivo y exploratorio: se elige sin proyecto profesional definido y se abandona más.
- **Educación/Profesorado** es la más estable: máster de formación del profesorado, magisterio, microcredenciales docentes. El alumno llega con un objetivo laboral concreto (habilitación) y una edad mayor.
- Ingeniería online (UDIMA, RR 1,89; Portugal "engenharia informática EAD" RR 1,75) merece atención: la combinación de contenido exigente y modalidad a distancia produce la peor retención de la disciplina.

*Figura: `figs/07_disciplinas_heatmap.png`*

### 8.2 Titulaciones: el riesgo se concentra en pocos contextos

**Método**: RR por titulación × nuevo ingreso con n ≥ 50. **Dónde**: los tres.

| Cliente | Titulaciones (n ≥ 50) | Con RR ≥ 1,5 | Con RR ≤ 0,5 |
|---|---|---|---|
| Madrid | 120 | 31 (26 %) | 43 (36 %) |
| Portugal | 30 | 14 (47 %) | 3 (10 %) |
| UDIMA | 20 | 2 (10 %) | 2 (10 %) |

Casos extremos por cliente:

- **Madrid**: Enfermería (3 sedes) con 49-55 % de anulación pre-inicio (RR 5-6), seguida de Biomedicina y Medicina (25-28 %, RR 2,6-3,0). Es el patrón de **plaza de reserva**: el alumno se matricula en la privada mientras espera la pública y anula en septiembre. En el otro extremo, 43 titulaciones (mayoría posgrados online) no tienen ni una anulación.
- **Portugal**: Licenciatura em Marketing (75 %, RR 3,4), Informática de Gestão (49 %), Gestão Hoteleira (42 %), Design Global (41 %), Engenharia Informática EAD (39 %). Las posgraduaciones online cortas están en el otro extremo (Educação Digital 1,6 %).
- **UDIMA**: Máster en Energías Renovables (84 %, RR 2,9) y Prevención de Riesgos Laborales (54 %); las más estables, Asesoría Fiscal (12,5 %) y Marketing Digital (12,8 %).

En ninguna universidad la titulación más numerosa es la de mayor riesgo relativo: **el volumen de bajas viene de las grandes, la tasa de las medianas**. Es la misma lectura que en el informe de riesgo de UDIMA (Máster de Profesorado aporta por volumen; Logopedia por tasa).

---

## 9. Hacia dónde se mueve: grafos de trayectoria

### 9.1 P7 · Grafo de cambios internos de titulación (Madrid)

**Método**: grafo dirigido titulación origen → titulación destino, construido con los 533 alumnos que tienen una matrícula anulada por "cambio de titulación/plan/modalidad" y otra vigente en el mismo snapshot (557 aristas). Métricas de grado ponderado y PageRank. **Dónde**: Madrid.

Propiedades del grafo:

| Propiedad | Valor |
|---|---|
| Cambios dentro de la **misma disciplina** | **82 %** |
| Cambios dentro del **mismo tipo de título** | 96 % |
| Cambios que implican **cambio de modalidad** | 17 % |
| … de los cuales presencial → online | **76** (vs 21 online → presencial: **3,6 : 1**) |
| Cambios que implican cambio de sede | 7 % |

Flujos entre disciplinas más frecuentes (fuera de la diagonal): Marketing → Negocios (12), Negocios → Marketing (10), Negocios → Derecho (7), Negocios → Ingeniería (7). Derecho es el único receptor neto claro (+9); Negocios y Psicología son emisores netos (−10 cada una).

Titulaciones con mayor **entrada neta** (receptoras): Enfermería Sanitas (+24), Odontología (+19), Fisioterapia (+18), Psicología online (+16), Logopedia online (+10), Medicina (+7). Con mayor **salida neta** (emisoras): Psicología presencial (−24), Biomedicina (−18), foundation years de Salud (−13 / −11), ADE (−12).

Tres estructuras se leen en el grafo:

1. **Salas de espera**: Biomedicina → Medicina (15 alumnos) y los *foundation years* → Fisioterapia / Odontología / Enfermería (29). Son titulaciones cuya función real es puente hacia otra con numerus clausus.
2. **Válvula online**: Psicología presencial → Psicología online (17), Logopedia → Logopedia online (10), Derecho → Derecho online (6). El alumno que no encaja en presencial no se va: cambia de modalidad. El flujo inverso es residual.
3. **Cambio lateral de familia**: Marketing ↔ ADE, ADE → Derecho, ADE → Ingeniería. El alumno de Negocios que se mueve, se mueve dentro de la facultad.

PageRank (centralidad como destino, ponderado): Odontología y Odontología Sanitas encabezan; siguen Relaciones Internacionales, Psicología, ADE, Fisioterapia. Odontología es el "atractor" del grafo: recibe de foundation years, de Biomedicina y de otras titulaciones de Salud.

*Figura: `figs/08_grafo_transferencias_madrid.png` (nivel disciplina)*

### 9.2 Grafo de co-matrícula simultánea (Madrid)

1.353 pares de titulaciones cursadas a la vez por 3.119 alumnos. El 23 % son "complementos de formación" ligados a un máster. El resto es, casi íntegramente, **un curso universitario corto acoplado a un grado** (Astrofísica + Física 56; IoT + Ingeniería Informática 31; Bioingeniería deportiva + Ingeniería Biomédica 30; Gestión de empresas biotecnológicas + Biotecnología 27; Legaltech + Derecho 12). Combinaciones por tipo: posgrado+posgrado 669 alumnos, grado+grado 463, grado+posgrado 43. Es un patrón de **diseño de producto** (bundles de microcredenciales), más que de comportamiento espontáneo del alumno; se documenta porque muestra que la "matrícula única por alumno" no es un supuesto válido en universidades con catálogo amplio.

### 9.3 Grafo de trayectorias entre matrículas (Portugal)

**Método**: secuencia de matrículas por alumno ordenadas por fecha de inicio (910 alumnos, 944 transiciones). **Dónde**: Portugal.

| Transición | n | Observaciones |
|---|---|---|
| Grado (finalizado) → Posgrado | **268** | 77 % misma disciplina; brecha mediana 31 meses desde el inicio del grado. **El graduado propio es el principal canal de captación de posgrado.** |
| Baja → nueva matrícula | **191** (5,8 % de las bajas) | 73 % misma disciplina, 86 % mismo tipo; brecha mediana **3,2 meses**. |
| Posgrado → Posgrado | 372 | Mayoritariamente edición siguiente de la misma posgraduación (aplazamiento) o segunda posgraduación. |

Sobre el re-enganche tras baja: el motivo de la baja original fue desistência (46 %), anulación de inscripción (25 %) o deuda (21 %); la segunda matrícula termina en baja el 24 % de las veces (algo por encima de la media, pero tres de cada cuatro continúan o finalizan). Cuando cambia la modalidad en el re-enganche, va **presencial → online 26 veces y online → presencial 8 (3,3 : 1)**: la misma dirección y casi la misma proporción que en Madrid.

**Lectura transversal (P7)**: en dos universidades con datos independientes, el alumno que se mueve se queda en su disciplina (73-82 %) y, si cambia de modalidad, elige online 3 de cada 4 veces. Una parte de las bajas registradas son **aplazamientos de tres meses**, no abandonos; contarlas como pérdida sobreestima la deserción.

---

## 10. Arquetipos: seis celdas deterministas

**Método**: reglas sobre tipo de título × modalidad × edad de ingreso (25 como corte para grado presencial). Sin clustering, para que la asignación sea idéntica en cualquier cliente y auditable. **Dónde**: los tres (UDIMA solo en A3/A5/A6 por ser 100 % online; sin edad para las bajas).

| Arquetipo | Definición | Madrid: share · edad · baja NI (RR) | Portugal: share · edad · baja NI (RR) | UDIMA: share · baja NI (RR) |
|---|---|---|---|---|
| **A1 Grado presencial tradicional** | Grado, presencial, ≤ 24 | 53 % · 20 · 15,2 % (1,60) | 48 % · 21 · 27,9 % (1,26) | — |
| **A2 Grado presencial de edad atípica** | Grado, presencial, 25+ | 6 % · 27 · 12,7 % (1,34) | 6 % · 27 · **53,5 % (2,42)** | — |
| **A3 Grado online (adulto que vuelve)** | Grado, online | 10 % · 25 · 7,3 % (0,77) | 8 % · 31 · 27,4 % (1,24) | 34 % · 32,4 % (1,13) |
| **A4 Posgrado presencial** | Posgrado, presencial | 9 % · 25 · 6,9 % (0,73) | 18 % · 26 · 14,4 % (0,65) | — |
| **A5 Posgrado online (profesional)** | Posgrado, online | 17 % · 26 · **3,4 % (0,36)** | 17 % · 33 · **8,0 % (0,36)** | 65 % · 26,9 % (0,94) |
| **A6 Formación corta / ciclos** | Ciclos, cursos, microcredenciales | 5 % · 22 · 3,7 % (0,39) | 3 % · 22 · 45,3 % (2,05) | 1 % · 30 % (1,04) |

Patrones que se sostienen:

- **A5 (posgrado online profesional) es el arquetipo más estable en las tres universidades**: RR 0,36 en Madrid y Portugal; en UDIMA, la única universidad donde compite solo con grado online, también está por debajo (26,9 % vs 32,4 %). Alumno de 26-33 años, con título previo, que paga y avanza; se va menos y, cuando se va, es por deuda (Portugal: 38 % de sus bajas).
- **A2 (grado presencial de edad atípica) es el más frágil en cursada** (Portugal, RR 2,42). Dentro del grado presencial de nuevo ingreso, la baja crece de forma monótona con la edad de ingreso: **15 % a los ≤ 19, 28 % a los 20, 35 % a los 21, 39 % a los 22, 46 % a los 23-24, 46 % a los 25-29, 75 % a los 30-34**. Cada año de retraso respecto a la edad canónica añade riesgo; el adulto que entra a un formato diseñado para 18 años no encaja. En Madrid, que mide anulación pre-inicio, el gradiente es inverso (18 % a los 18, 12-13 % a los 25+): el joven anula porque elige; el adulto ya eligió.
- **A1** es el arquetipo mayoritario en las dos universidades con presencial (48-53 %) y tiene RR > 1 en ambas, pero por razones distintas (elección pre-inicio en Madrid; desenganche en cursada en Portugal).
- **A6** se comporta de forma opuesta según el diseño del producto: en Madrid, ciclos formativos presenciales (RR 0,39); en Portugal, CTeSP presenciales de acceso (RR 2,05). No es un arquetipo transversal.

*Figuras: `figs/09_arquetipos.png`, `figs/10_gradiente_edad.png`*

---

## 11. Otros hallazgos de un solo cliente

- **UDIMA · convalidaciones como marcador de segunda carrera.** El 30 % de los activos tiene asignaturas convalidadas (16 % en nuevo ingreso, 42 % en reingreso). En grado, quien convalida tiene 36-40 años frente a 31 quien no. La convalidación identifica al adulto con formación previa que vuelve; no se pudo cruzar con baja (sin dato en las bajas) ni replicar en Portugal (variable vacía).
- **UDIMA · reloj de decisión.** Bajas concentradas en las 4-6 semanas posteriores al inicio de cada cuatrimestre (octubre 15 %, marzo 12 %), en nuevo ingreso y reingreso por igual. La decisión se toma al arrancar el período, no al terminarlo.
- **Madrid · el reingresante que anula tiene expediente débil.** Los 230 reingresantes anulados tienen mediana de avance aprobado 12 % (vs 23 % del reingresante general), 5 aprobadas (vs 11) y una distribución de suspensos más larga (p75 = 8 vs 7).
- **Portugal · el precio no explica la baja de posgrado.** Por quintil de importe, la baja en posgrado nuevo ingreso oscila entre 8,5 % y 13 % sin tendencia; en grado la relación aparente (72 % en el quintil bajo → 19 % en el alto) está confundida con el tiempo de permanencia (el importe facturado crece con los meses cursados) y no debe leerse como efecto precio.

---

## 12. Síntesis: qué se repite y qué es local

| Dimensión | Universal (≥ 2 clientes, misma dirección) | Institucional (depende del cliente) |
|---|---|---|
| Quién | Online = adulto (+5 a +14 años en grado) | Composición por sexo, mix grado/posgrado |
| Cuándo | Primer año (RR 3,4-8,3×); ventana ≤ 6 meses; retención a la cuarta parte tras el primer año | Calendario de la baja (admisión / semestres / lotes administrativos) |
| Por qué | Tres bloques: elección, desenganche, dinero | Peso de cada bloque (43 % elección en Madrid; 27 % deuda en Portugal) |
| Cómo rinde | Pocos alumnos acumulan la mayoría de los suspensos (72-94 %) | Dificultad relativa por disciplina; efecto del primer suspenso (solo medible en Portugal) |
| Cómo paga | Pago y avance independientes (ρ ≈ 0); pago parcial anticipa la baja | Nivel absoluto de cumplimiento |
| De dónde | Internacional RR 1,8-3,0 en primer año, motivo financiero | Qué población es la internacional |
| Qué estudia | Psicología > media; Educación, Marketing, Cs. sociales < media | Titulaciones concretas de alto riesgo; efecto "plaza de reserva" en Salud |
| Hacia dónde | Se mueve dentro de la disciplina (73-82 %); modalidad → online 3:1; parte de las bajas son aplazamientos | Salas de espera y atractores concretos |
| Arquetipo | Posgrado online profesional = más estable (RR 0,36) | Formación corta / ciclos (opuesto según diseño) |

---

## 13. Anexo · inventario de entregables intermedios

Todo lo siguiente está en el contenedor de trabajo y puede exportarse como notebook o paquete de tablas:

- `01_standardize.py` · estandarización de los tres clientes al esquema común (sin PII).
- `disciplinas.py` · reglas de clasificación de titulaciones en 10 disciplinas (editable).
- `02_figs.py` · generación de las 11 figuras.
- `tables/` · 20 tablas CSV: composición (01, 02), primer año (03, 03b, 03c), tiempo hasta la baja (04), edad × baja (05, 05b), estacionalidad (06), disciplinas (07, 07b), titulaciones (08), aristas del grafo Madrid (09, 09b), aristas de trayectorias Portugal (10), arquetipos (11, 11b).
- `figs/` · 01 edad × modalidad, 02 nuevo vs reingreso, 03 meses hasta la baja, 04 estacionalidad, 05 taxonomía, 06 primer suspenso, 07 heatmap disciplinas, 08 grafo Madrid, 09 arquetipos, 10 gradiente de edad, 11 pago vs baja.

### Decisiones pendientes para pasar del crudo al informe

1. Confirmar el tratamiento de Madrid como "anulación pre-inicio" separado del abandono en cursada (este documento lo hace explícito en cada tabla).
2. Revisar el mapeo de disciplinas si se va a publicar (especialmente Gestión deportiva, Turismo y Salud no clínica).
3. Elegir qué hallazgos de un solo cliente se publican como hipótesis (candidatos: primer suspenso ×7, fecha administrativa vs abandono real, 43 % de anulaciones internas).
4. Para la landing: los mensajes con mayor respaldo transversal son P1, P2, P3, P5, P6 y P7. P4 (independencia pago-avance) es sólido pero requiere una frase de explicación.
