# Patrones de comportamiento riesgoso a partir del Explicador de Riesgo

**Informe técnico · Retention Partner · Explicador de Riesgo**
Corrida analizada: predicción del 03-08-2026 · 7.477 matrículas activas con predicción
Notebook de referencia: `deteccion_patrones_riesgo.ipynb`

---

## Resumen ejecutivo

El Explicador de Riesgo produce, por cada matrícula de riesgo Alto o Medio, una base auditable (`full_facts`) con los tres hechos de mayor peso: qué variable, qué valor, qué tan atípico frente a sus pares y en qué dirección. Este trabajo construye sobre esa base un **algoritmo determinista de detección de patrones**: agrupa, mide concentración, busca combinaciones y valida contra datos crudos. No entrena ningún modelo ni usa clustering.

Sobre 748 matrículas de riesgo Alto y 1.495 de riesgo Medio, los resultados principales son:

1. **El riesgo Alto tiene cuatro causas.** El promedio de notas en el campus (26 %), el número de calificaciones (26 %), el porcentaje de pagos cobrados (19 %) y los días desde el primer bloqueo (14 %) explican el 85 % de las matrículas Alto. En el 81 % de los casos la causa dominante cae del lado que eleva el riesgo; no es contexto.

2. **El riesgo Alto es, sobre todo, de nuevo ingreso.** El 77 % de las matrículas Alto son de primer período. Un alumno de nuevo ingreso tiene 1,7 veces la tasa base de riesgo Alto; uno de reingreso, 0,4. En Grado, el 21,6 % de los nuevos ingresos está en Alto frente al 2,9 % de los reingresos.

3. **Nuevo ingreso y reingreso tienen riesgos de naturaleza distinta.** En nuevo ingreso el 64 % de las causas dominantes son académicas (campus sin actividad calificada, sin calificaciones formales). En reingreso el 48 % son financieras (pagos cobrados, impagos) y el 36 % administrativas (bloqueos, cambios de matrícula).

4. **Seis patrones concretos**, descritos en la sección 4: arranque sin tracción en Grado (P1), desconexión temprana en Máster (P2), segmentos con severidad no graduable que esconden un patrón real (P3), riesgo financiero de reingreso (P4), bloqueo reciente con pago parcial (P5) y un patrón menor de edad (P6).

5. **15 de los 23 contextos evaluables presentan un hallazgo sistémico**: al menos el 40 % de sus matrículas Alto comparten la misma causa dominante. El caso más claro es Grado en Psicología · Nuevo ingreso: 101 matrículas Alto (2,6 veces la tasa base), el 56 % con la misma causa.

6. **Los patrones discriminan.** El 60 % de las matrículas Alto no tiene ninguna calificación registrada, frente al 0,1 % de las Bajo. Los grupos con causa financiera pagan una mediana del 55 % de lo facturado, frente al 100 % de los Bajo.

7. **Dos hallazgos de calidad sobre los insumos** que conviene resolver antes de industrializar: (a) ocho variables tienen una dirección de riesgo distinta en el output y en el diccionario entregado; (b) para varios segmentos la referencia de severidad no tiene dispersión y el Explicador devuelve `medio` en hechos que, en los datos crudos, discriminan con fuerza.

---

## 1. Objetivo y alcance

**Objetivo.** Encontrar patrones compartidos entre los estudiantes de riesgo alto: qué causas se repiten, en qué contextos se concentran y qué combinaciones de hechos aparecen juntas. El resultado es un sistema reproducible (notebook) y este informe.

**Alcance.**

- Población de análisis: matrículas activas con nivel de riesgo **Alto o Medio** (2.243). El nivel **Alto** ordena y prioriza los hallazgos; el Medio aporta volumen y sirve de contraste.
- Contexto de agrupación: **titulación × tipo de estudiante** (nuevo ingreso / reingreso). Es la granularidad más fina disponible; el archivo no incluye el curso (1.º, 2.º año), por lo que "primer año" se aproxima con `nuevo ingreso`, que coincide uno a uno con "un solo período matriculado".
- Población de contraste: matrículas de riesgo **Bajo** (5.234), que no traen `full_facts` y se comparan por sus variables crudas.
- Fuera de alcance: las 10.750 matrículas sin predicción (bajas, inactivas o sin cursado) y cualquier dato personal (se eliminan en la carga).

---

## 2. Datos

| Concepto | Detalle |
|---|---|
| Matrículas en el archivo | 18.227 |
| Activas con predicción | 7.477 · Alto 748 (10,0 %) · Medio 1.495 (20,0 %) · Bajo 5.234 (70,0 %) |
| Hechos analizados | 6.729 (3 por matrícula de riesgo) sobre 28 variables distintas |
| Diccionario | `var_definitions.json`, 67 variables en 5 dimensiones |
| Contextos distintos en la población de riesgo | 96 (titulación × tipo de estudiante) |
| Variables crudas usadas en la validación | avance aprobado, % pagado sobre facturado, impagos, cambios de matrícula, edad, entregas LMS 90 d |

Cada hecho del `full_facts` trae: variable (`fuente`), etiqueta legible, valor formateado, severidad relativa a los pares del segmento (`muy bajo` … `muy alto`), macro-dimensión, peso SHAP y dirección de riesgo. El **hecho dominante** es el de mayor peso.

---

## 3. Método

El sistema tiene tres niveles, todos deterministas y parametrizables.

### 3.1 Clasificación de cada hecho

La severidad describe una posición, no un juicio. Cruzándola con la dirección de riesgo, cada hecho se clasifica en:

- **eleva** — el valor cae del lado que eleva el riesgo (dirección `bajo` con severidad baja o muy baja; dirección `alto` con severidad alta o muy alta). Son los únicos hechos que describen un comportamiento riesgoso.
- **indeterminado** — severidad `medio` o dirección `neutro`. Es contexto.
- **favorable** — el valor cae del lado que reduce el riesgo. El modelo lo pesó, pero no describe riesgo.

Se marca además el caso `sin_dispersion_ref`: conteo con severidad `medio` y valor 0. Ocurre cuando la referencia de severidad del segmento (percentiles por titulación × mes) no tiene dispersión para esa variable, de modo que el Explicador no puede graduar la posición. Su lectura se resuelve en el nivel 3.

### 3.2 Nivel 1 · Arquetipos y hallazgos sistémicos

- **Riesgo relativo por contexto.** Tasa de riesgo Alto del contexto dividida por la tasa base (10,0 %). Marca dónde se concentra el riesgo antes de mirar causas.
- **Arquetipo** = `contexto × hecho dominante`, con el perfil de riesgo como atributo. La regla de referencia de la capa de acción incluye el perfil (`contexto × perfil_riesgo × hecho dominante`); en esta granularidad el perfil es homogéneo en el ~80 % de cada grupo y fragmenta las cohortes por debajo del tamaño reportable, por lo que se reporta como atributo. El parámetro `ARQUETIPO_CON_PERFIL` aplica la regla completa.
- **Hallazgo sistémico** = contexto donde una misma causa dominante explica ≥ 40 % de sus matrículas de riesgo. Se acompaña de `lift_vs_global` (concentración del contexto / share global de la causa): una concentración que solo replica la distribución general no es un hallazgo del contexto.

### 3.3 Nivel 2 · Co-ocurrencia

Con tres hechos por matrícula, todos los pares y tríos de `(variable, severidad)` se enumeran exhaustivamente. Para cada combinación: soporte en Alto, soporte en Medio y **lift Alto vs. Medio** (cociente de frecuencias, suavizado con +0,5 para evitar divisiones por cero). Las combinaciones que no aparecen ni una vez en Medio se marcan como exclusivas de Alto.

### 3.4 Nivel 3 · Validación con variables crudas

Cada grupo se compara con las matrículas de riesgo Bajo sobre las variables crudas disponibles: mediana, test de Mann-Whitney y tamaño del efecto como correlación rango-biserial `r` (|r| ≥ 0,3 moderado, ≥ 0,5 fuerte). Para los hechos académicos, la contraparte cruda es `sin_avance_registrado` (avance aprobado nulo = ninguna calificación registrada), comparada como proporción.

### 3.5 Parámetros

| Parámetro | Valor | Función |
|---|---|---|
| `MIN_GRUPO_CONTEXTO` | 15 | Matrículas Alto+Medio para evaluar un contexto |
| `MIN_FOCO_CONTEXTO` | 10 | Matrículas Alto para hallazgo con foco |
| `MIN_ARQUETIPO` | 10 | Tamaño mínimo de un arquetipo |
| `UMBRAL_CONCENTRACION` | 40 % | Concentración para declarar hallazgo sistémico |
| `MIN_COOCURRENCIA` | 15 | Soporte mínimo en Alto de un par o trío |
| `LIFT_MINIMO` | 1,3 | Lift mínimo para destacar una combinación |
| `RR_MINIMO` | 1,5 | Riesgo relativo para marcar un contexto sobre-representado |

---

## 4. Resultados

### 4.1 Panorama: cuatro causas explican el 85 % del riesgo Alto

![Figura 1](figuras/fig01_causa_dominante.png)

| Causa dominante | Variable | Alto | % Alto | % Medio |
|---|---|---|---|---|
| Promedio de notas en el campus | `lms_nota_media_acum` | 196 | 26,2 | 3,5 |
| Número de calificaciones | `n_calificaciones_acum` | 192 | 25,7 | 20,7 |
| Porcentaje de pagos cobrados | `ratio_cobrado_acum` | 143 | 19,1 | 11,6 |
| Días desde el primer bloqueo | `dias_desde_primer_bloqueo` | 102 | 13,6 | 2,1 |
| Otras (8 variables) | — | 115 | 15,4 | 62,1 |

Dos lecturas:

- **El promedio de notas en el campus y el bloqueo son marcadores de Alto, no de Medio** (26 % vs. 3,5 %; 14 % vs. 2 %). Lo que separa a un Alto de un Medio no es tener pocas calificaciones (eso también lo tienen los Medio), sino que lo poco que hay en el campus está calificado muy por debajo de los pares, o que existe un bloqueo reciente.
- **La causa dominante de un Alto casi siempre eleva el riesgo** (81 %); en Medio, solo en el 56 % de los casos. El riesgo Medio tiene más contexto y menos comportamiento.

![Figura 2](figuras/fig02_macro_dominante.png)

Por dimensión, el 52 % de las causas dominantes en Alto son académicas, el 23 % financieras y el 21 % contextuales. En esta salida, la dimensión "Contextual" agrupa sobre todo bloqueos y cambios de matrícula, es decir, hechos administrativos.

### 4.2 Dónde se concentra el riesgo: nuevo ingreso × titulación

| Tipo de estudiante | Activos | Alto | % Alto | RR Alto |
|---|---|---|---|---|
| Nuevo ingreso | 3.430 | 578 | 16,9 % | 1,68 |
| Reingreso | 4.047 | 170 | 4,2 % | 0,42 |

| Tipo de titulación × estudiante | % Alto |
|---|---|
| Grado · Nuevo ingreso | 21,6 % |
| Máster · Nuevo ingreso | 13,6 % |
| Máster · Reingreso | 5,5 % |
| Grado · Reingreso | 2,9 % |

Los nuevos ingresos de riesgo Alto tienen una mediana de 29 semanas desde la matrícula (rango 20–72): el riesgo aparece consolidado entre el quinto y el octavo mes.

![Figura 3](figuras/fig03_riesgo_relativo_contexto.png)

De los 69 contextos con al menos 30 matrículas activas, 16 están sobre-representados (RR ≥ 1,5 con al menos 10 Alto) y 29 sub-representados (RR ≤ 0,67). Todos los sobre-representados con más de 10 Alto, salvo uno, son de nuevo ingreso.

| Contexto | Activos | Alto | % Alto | RR Alto |
|---|---|---|---|---|
| Grado en Logopedia · Nuevo ingreso | 51 | 23 | 45,1 % | 4,5 |
| Máster en Dirección Financiera y Control de Gestión · Nuevo ingreso | 86 | 34 | 39,5 % | 4,0 |
| Máster en Dirección y Administración de Empresas (MBA) · Nuevo ingreso | 191 | 57 | 29,8 % | 3,0 |
| Máster en Marketing Digital y Redes Sociales · Nuevo ingreso | 79 | 21 | 26,6 % | 2,7 |
| Grado en Ingeniería de Organización Industrial · Nuevo ingreso | 62 | 16 | 25,8 % | 2,6 |
| Grado en Psicología · Nuevo ingreso | 393 | 101 | 25,7 % | 2,6 |
| Máster en Educación Inclusiva y Personalizada · Nuevo ingreso | 55 | 14 | 25,5 % | 2,5 |
| Grado en Derecho · Nuevo ingreso | 125 | 28 | 22,4 % | 2,2 |
| Máster en Energías Renovables y Eficiencia Energética · Reingreso | 60 | 13 | 21,7 % | 2,2 |

En el extremo opuesto, la titulación más numerosa (Máster en Formación del Profesorado · Nuevo ingreso, 394 activos) tiene un RR de 0,89: aporta 35 Alto por volumen, no por tasa. Grado en Psicología · Reingreso tiene un RR de 0,28 con 397 activos: la misma titulación pasa de 25,7 % de Alto en el primer período a 2,8 % después.

![Figura 3b](figuras/fig03b_macro_por_tipo.png)

La naturaleza del riesgo cambia con el tipo de estudiante:

| Causa dominante (riesgo Alto) | Nuevo ingreso | Reingreso | Grado | Máster |
|---|---|---|---|---|
| Promedio de notas en el campus | 33,0 % | 2,9 % | 40,5 % | 13,8 % |
| Número de calificaciones | 31,1 % | 7,1 % | 20,2 % | 30,2 % |
| Porcentaje de pagos cobrados | 12,6 % | 41,2 % | 12,4 % | 24,8 % |
| Días desde el primer bloqueo | 12,3 % | 18,2 % | 10,1 % | 16,9 % |
| Días desde el último cambio de matrícula | 1,4 % | 7,1 % | 1,2 % | 4,1 % |
| Número de impagos | 1,7 % | 5,3 % | 4,3 % | 1,0 % |
| Edad | 0,3 % | 5,3 % | 0,9 % | 2,0 % |

---

### 4.3 Los patrones detectados

Los seis patrones siguientes salen de cruzar los tres niveles. Cada uno indica dónde vive, qué lo compone, cuánto pesa y cómo se validó.

#### P1 · Arranque sin tracción (Grado · nuevo ingreso)

**Qué es.** Alumnos de primer período en Grado cuyo campus virtual muestra actividad calificada con notas muy por debajo de sus pares (promedio de notas en el campus `muy bajo`, valor mediano 0,5), sin calificaciones formales todavía. Es la lectura cuantitativa de "falta de adaptación en los primeros meses": el alumno está inscripto, entra, pero lo que entrega no prospera.

**Dónde vive.** Es el patrón más grande del archivo: 136 matrículas Alto en Grado · Nuevo ingreso (47 % de todas las Alto de ese grupo). Por titulación:

| Contexto | Alto en el contexto | Con esta causa | Concentración |
|---|---|---|---|
| Grado en Psicología · Nuevo ingreso | 101 | 57 | 56 % |
| Grado en Logopedia · Nuevo ingreso | 23 | 18 | 78 % |
| Grado en Ingeniería de Organización Industrial · Nuevo ingreso | 16 | 8 | 50 % |
| Grado en Criminología · Nuevo ingreso | 11 | 6 | 55 % |
| Grado en Relaciones Laborales y RR. HH. · Nuevo ingreso | 12 | 5 | 42 % |
| Grado en Ingeniería Informática · Nuevo ingreso | 10 | 4 | 40 % |

**Cuadro completo.** En Psicología, el trío más frecuente es promedio de notas en el campus `muy bajo` + número de calificaciones `medio` (valor 0) + número de cursos accedidos `medio`: el alumno accede a los cursos, todavía no fue evaluado formalmente y su desempeño en las actividades del campus es el peor del segmento.

**Validación.** El 98 % de las matrículas Alto de Psicología con esta causa no tiene ninguna calificación registrada, frente al 1 % de las Bajo de la misma titulación (Logopedia: 100 % vs. 0 %). Además, las Alto de Psicología · Nuevo ingreso llevan 32 semanas matriculadas frente a 49 las Bajo: el riesgo se concentra en la cohorte de ingreso más reciente.

**Lectura.** Grado en Psicología · Nuevo ingreso concentra por sí sola el 13,5 % de todo el riesgo Alto de la institución con una causa homogénea. No es un problema individual: es de onboarding de la titulación.

#### P2 · Desconexión temprana (Máster · nuevo ingreso)

**Qué es.** Alumnos de primer período en Máster que no registran calificaciones (`muy bajo`, valor 0), acceden a muy pocos cursos (número de cursos accedidos `bajo`, mediana 3 frente a 10–16 en los demás) y, cuando hay actividad calificada, está muy por debajo de sus pares. Es un abandono silencioso: el alumno nunca llegó a engancharse.

**Dónde vive.**

| Contexto | Alto en el contexto | Causa dominante | Concentración |
|---|---|---|---|
| Máster en Dirección y Administración de Empresas (MBA) · Nuevo ingreso | 57 | Número de calificaciones `muy bajo` | 47 % |
| Máster en Formación del Profesorado · Nuevo ingreso | 35 | Número de calificaciones `muy bajo` | 60 % |
| Máster en Marketing Digital y Redes Sociales · Nuevo ingreso | 21 | Número de calificaciones `muy bajo` | 52 % |
| Grado en Magisterio de Educación Primaria · Nuevo ingreso | 21 | Número de calificaciones `muy bajo` | 48 % |

**Cuadro completo.** La combinación *número de calificaciones `muy bajo` + número de cursos accedidos `bajo` + promedio de notas en el campus `muy bajo`* aparece en 37 matrículas Alto y en **ninguna** Medio; el 65 % está en el MBA · Nuevo ingreso y el 22 % en Marketing Digital. Es la firma más específica del riesgo Alto que hay en el archivo.

**Validación.** El 96 % de las Alto del MBA con esta causa no tiene calificación registrada (Bajo del mismo contexto: 0 %). En Formación del Profesorado, 95 % vs. 0 %.

**Lectura.** P1 y P2 comparten la ausencia de calificaciones, pero difieren en el acceso: en P1 el alumno entra al campus y rinde mal; en P2 apenas entra. La intervención no es la misma.

#### P3 · Segmentos con severidad no graduable

**Qué es.** En tres contextos la causa dominante es número de calificaciones con severidad `medio` y valor 0. No es un hecho neutro: la referencia de severidad de esos segmentos no tiene dispersión para la variable, así que el Explicador no puede graduar la posición y devuelve `medio`. La clasificación por severidad lo dejaría como contexto; los datos crudos dicen otra cosa.

| Contexto | Matrículas con esta causa (A+M) | Alto | Sin avance registrado (grupo) | Sin avance registrado (Bajo del contexto) |
|---|---|---|---|---|
| Máster en Dirección Financiera y Control de Gestión · Nuevo ingreso | 32 | 27 | 84 % | 0 % |
| Grado en Psicología · Nuevo ingreso | 59 | 15 | 63 % | 1 % |
| Máster en Dirección y Gestión Pública · Nuevo ingreso | 19 | 0 | 0 % | 0 % |

**Lectura.** En Dirección Financiera (RR 4,0, el segundo contexto más sobre-representado) y en el subgrupo de Psicología, el valor 0 sí distingue a estos alumnos: los Bajo de la misma titulación tienen una mediana de avance aprobado de 0,85–1,00. El patrón es real y equivale a P1/P2; lo que falla es la referencia de severidad. En Gestión Pública el valor 0 no distingue a nadie y el hecho es efectivamente contexto. Ver la recomendación en la sección 5.

#### P4 · Riesgo financiero de reingreso

**Qué es.** Alumnos con historial que pagan una fracción baja de lo facturado (porcentaje de pagos cobrados `muy bajo`, mediana 50–60 %), acompañado en Grado de impagos formales (número de impagos `muy alto`, mediana 4).

**Dónde vive.** Es la causa dominante del 41 % de los reingresos en Alto (frente al 13 % de los nuevos ingresos), y del 25 % de los Alto de Máster.

| Contexto | Alto en el contexto | Con esta causa | Concentración |
|---|---|---|---|
| Máster en Energías Renovables y Eficiencia Energética · Reingreso | 13 | 7 | 54 % |
| Grado en Derecho · Reingreso | 12 | 6 | 50 % |
| Máster en Educación Inclusiva y Personalizada · Nuevo ingreso | 14 | 6 | 43 % |
| Máster en Dirección y Administración de Empresas (MBA) · Reingreso | 8 de 15 A+M | 7 | 47 % (A+M) |

**Validación.** Es el patrón con la validación cruda más contundente: las 143 matrículas Alto con esta causa pagan una mediana del 55 % de lo facturado frente al 100 % de las Bajo (`r = −0,87`). En Energías Renovables · Reingreso, 44 % vs. 100 % (`r = −0,94`); en Educación Inclusiva, 45 % vs. 100 %. El grupo con causa "número de impagos" tiene una mediana de 4 impagos frente a 0 (`r = +0,95`).

**Lectura.** El porcentaje de pagos cobrados combina con hechos académicos en Grado (perfil `Academico + Financiero`) y con bloqueos en Máster: en reingreso, el problema financiero suele venir con un correlato académico o administrativo.

#### P5 · Bloqueo reciente con pago parcial

**Qué es.** Alumnos con un primer bloqueo reciente (días desde el primer bloqueo `bajo`, mediana ~150 días) que pagan de forma parcial pero, en su mayoría, sin impagos formales.

**Dónde vive.** 102 matrículas Alto (14 %), 71 de nuevo ingreso y 31 de reingreso, repartidas en muchos contextos sin llegar al umbral de concentración en ninguno; es un patrón transversal. La combinación *días desde el primer bloqueo `bajo` + días desde el último cambio de matrícula `medio`* aparece en 50 Alto y 8 Medio (lift 11,9); *bloqueo `bajo` + pagos cobrados `bajo`* aparece en 17 Alto y ningún Medio.

**Validación.** Las matrículas Alto con causa bloqueo pagan una mediana del 75 % de lo facturado (Bajo: 100 %, `r = −0,72`), pero el 64–83 % de ellas no tiene ningún impago formal (`r = +0,21`, débil). El grupo con causa "número de bloqueos" muestra lo mismo: 80 % pagado, sin diferencia en impagos.

**Lectura.** El bloqueo se asocia a pagos parciales (planes de pago, cuotas atrasadas) más que a impagos declarados, lo que apunta a un origen administrativo-financiero mixto y no a mora formal. Es evidencia útil para la pregunta abierta sobre la naturaleza de los bloqueos en cada institución; con estos datos, no se puede afirmar más que eso.

#### P6 · Edad (patrón menor, no accionable)

La edad es causa dominante de 11 matrículas Alto y 80 Medio, con valores de 55–59 años (mediana 57; Bajo: 32). Es un patrón demográfico real y estadísticamente nítido (`r = +0,95`), pero describe a quién le pasa, no qué hace: no es accionable a nivel individual. Se reporta para completar el mapa y porque puede orientar el diseño de acompañamiento a estudiantes mayores.

#### Un patrón de riesgo Medio que no llega a Alto

Días desde el último cambio de matrícula `bajo` (cambio reciente, mediana ~90–110 días) es la causa dominante del 12 % de los Medio pero solo del 3 % de los Alto. Concentra el 50 % de los Alto+Medio del MBA · Nuevo ingreso (147 matrículas) y el 71 % de Dirección Económico Financiera · Reingreso (78). Es el marcador típico de un riesgo Medio reciente y, en ausencia de los hechos académicos de P1/P2, no escala a Alto.

---

### 4.4 Arquetipos

Con `MIN_ARQUETIPO = 10` se identifican 33 arquetipos (`contexto × causa dominante`) que cubren el 40 % de las matrículas Alto y el 37 % de las Alto+Medio. La cobertura parcial es consecuencia directa de la granularidad elegida: con 96 contextos, el 60 % restante queda en grupos de menos de 10 que se recuperan en la vista agregada (`vista_agregada.csv`, por tipo de titulación × tipo de estudiante, cobertura 100 %).

| Id | Contexto | Causa dominante | Sev. típica | Total | Alto | Perfil típico (homog.) | Causas secundarias |
|---|---|---|---|---|---|---|---|
| A01 | Grado en Psicología · NI | Promedio de notas en el campus | muy bajo | 64 | 57 | Académico + Compromiso (80 %) | n.º calificaciones [medio] 48 % · cursos accedidos [medio] 22 % |
| A02 | MBA · NI | Número de calificaciones | muy bajo | 34 | 27 | Académico + Compromiso (88 %) | días últ. cambio matrícula [medio] 28 % |
| A03 | Máster Dirección Financiera · NI | Número de calificaciones | medio (no graduable) | 32 | 27 | Académico + Compromiso (97 %) | ítems calificados [bajo] 38 % |
| A04 | MBA · NI | Promedio de notas en el campus | muy bajo | 23 | 23 | Académico + Compromiso (100 %) | n.º calificaciones [muy bajo] 50 % · cursos accedidos [bajo] 48 % |
| A05 | Máster Formación del Profesorado · NI | Número de calificaciones | muy bajo | 25 | 21 | Académico + Compromiso (80 %) | ítems calificados [muy bajo] 30 % |
| A06 | Grado en Logopedia · NI | Promedio de notas en el campus | muy bajo | 18 | 18 | Académico + Compromiso (56 %) | n.º calificaciones [medio] 50 % · ítems calificados [bajo] 25 % |
| A07 | Grado en Psicología · NI | Número de calificaciones | medio (no graduable) | 61 | 17 | Académico + Compromiso (80 %) | días últ. cambio matrícula [muy alto] 20 % |
| A08 | Máster Marketing Digital · NI | Número de calificaciones | muy bajo | 20 | 11 | Académico + Compromiso (100 %) | días últ. cambio matrícula [medio] 28 % |
| A09 | Grado Magisterio Ed. Primaria · NI | Número de calificaciones | muy bajo | 63 | 10 | Académico + Compromiso (95 %) | ítems calificados [bajo] 37 % |
| A10 | Grado en Psicología · NI | Porcentaje de pagos cobrados | bajo | 18 | 9 | Académico + Financiero (56 %) | promedio notas campus [bajo] 17 % |
| A11 | Grado en Psicología · NI | Días desde el primer bloqueo | medio | 10 | 9 | Contextual + Financiero (40 %) | pagos cobrados [bajo] 30 % |
| A12 | Grado Ing. Organización Industrial · NI | Promedio de notas en el campus | bajo | 12 | 8 | Académico + Compromiso (75 %) | n.º calificaciones [muy bajo] 42 % |

NI = nuevo ingreso. Tabla completa en `arquetipos.csv`.

Un detalle operativo: los arquetipos A01, A07, A10 y A11 son cuatro cohortes distintas dentro de la misma titulación. Grado en Psicología · Nuevo ingreso no es un problema, son al menos tres (académico, financiero, bloqueo) con volúmenes muy distintos.

### 4.5 Hallazgos sistémicos

![Figura 4](figuras/fig04_heatmap_contexto_causa.png)

Sobre la población Alto, 15 de los 23 contextos con al menos 10 matrículas Alto superan el 40 % de concentración en una misma causa. Sobre Alto+Medio, 19 de 49.

| Contexto (riesgo Alto) | n | Causa dominante | Concentración | Lift vs. global | Tipo |
|---|---|---|---|---|---|
| Grado en Psicología · NI | 101 | Promedio de notas en el campus [muy bajo] | 56 % | 2,2 | comportamiento |
| MBA · NI | 57 | Número de calificaciones [muy bajo] | 47 % | 1,9 | comportamiento |
| Máster Dirección Financiera · NI | 34 | Número de calificaciones [medio] | 79 % | 3,1 | severidad no graduable |
| Máster Formación del Profesorado · NI | 35 | Número de calificaciones [muy bajo] | 60 % | 2,3 | comportamiento |
| Grado en Logopedia · NI | 23 | Promedio de notas en el campus [muy bajo] | 78 % | 3,0 | comportamiento |
| Máster Marketing Digital · NI | 21 | Número de calificaciones [muy bajo] | 52 % | 2,0 | comportamiento |
| Grado Magisterio Ed. Primaria · NI | 21 | Número de calificaciones [muy bajo] | 48 % | 1,9 | comportamiento |
| Grado Ing. Organización Industrial · NI | 16 | Promedio de notas en el campus [bajo] | 50 % | 1,9 | comportamiento |
| Máster Dirección y Gestión Pública · NI | 11 | Promedio de notas en el campus [bajo] | 73 % | 2,8 | comportamiento |
| Máster Energías Renovables · Reingreso | 13 | Porcentaje de pagos cobrados [muy bajo] | 54 % | 2,8 | comportamiento |
| Grado en Criminología · NI | 11 | Promedio de notas en el campus [bajo] | 55 % | 2,1 | comportamiento |
| Grado en Derecho · Reingreso | 12 | Porcentaje de pagos cobrados [muy bajo] | 50 % | 2,6 | comportamiento |
| Máster Educación Inclusiva · NI | 14 | Porcentaje de pagos cobrados [muy bajo] | 43 % | 2,2 | comportamiento |
| Grado Relaciones Laborales y RR. HH. · NI | 12 | Promedio de notas en el campus [muy bajo] | 42 % | 1,6 | comportamiento |
| Grado Ingeniería Informática · NI | 10 | Promedio de notas en el campus [bajo] | 40 % | 1,5 | comportamiento |

En todos los casos el lift vs. global es mayor que 1,5: la concentración no replica la distribución general, es propia del contexto. Los 8 contextos que no superan el umbral (Derecho · NI, ADE · NI, Economía · NI, Psicología · Reingreso, entre otros) tienen el riesgo repartido en dos o tres causas: son contextos con riesgo heterogéneo donde el tratamiento tiene que segmentarse.

### 4.6 Co-ocurrencia: qué acompaña a la causa dominante

![Figura 5](figuras/fig05_coocurrencia_lift.png)

De 41 combinaciones con soporte ≥ 15 en Alto, 38 tienen lift ≥ 1,3 y 4 no aparecen ni una vez en Medio.

| Combinación | Alto | Medio | Lift | Dónde (Alto) |
|---|---|---|---|---|
| N.º calificaciones [muy bajo] + cursos accedidos [bajo] | 42 | 0 | exclusiva | MBA · NI 57 % · Marketing Digital · NI 19 % |
| Cursos accedidos [bajo] + promedio notas campus [muy bajo] | 37 | 0 | exclusiva | MBA · NI 65 % · Marketing Digital · NI 22 % |
| N.º calificaciones [muy bajo] + cursos accedidos [bajo] + promedio notas campus [muy bajo] | 37 | 0 | exclusiva | MBA · NI 65 % · Marketing Digital · NI 22 % |
| Días desde primer bloqueo [bajo] + pagos cobrados [bajo] | 17 | 0 | exclusiva | Energías Renovables (NI y Reingreso) 36 % · Psicología · Reingreso 12 % |
| N.º calificaciones [medio] + cursos accedidos [medio] | 37 | 2 | ≥ 20 | Psicología · NI 76 % · Logopedia · NI 24 % |
| N.º calificaciones [medio] + promedio notas campus [bajo] + ítems calificados [bajo] | 21 | 1 | ≥ 20 | Dirección Financiera · NI 52 % · Psicología · NI 48 % |
| Días desde primer bloqueo [medio] + pagos cobrados [muy bajo] | 20 | 2 | 16,4 | repartida (Máster · NI) |
| Días desde primer bloqueo [bajo] + días últ. cambio matrícula [medio] | 50 | 8 | 11,9 | transversal |
| N.º calificaciones [muy bajo] + promedio notas campus [muy bajo] | 112 | 28 | 7,9 | transversal (la más frecuente) |
| N.º calificaciones [muy bajo] + ítems calificados [muy bajo] | 86 | 48 | 3,6 | transversal |

La combinación más frecuente en Alto (n.º calificaciones `muy bajo` + promedio de notas en el campus `muy bajo`, 15 % de los Alto) es también 8 veces más frecuente que en Medio: sin calificaciones formales y con lo poco calificado en el campus muy por debajo. Las cuatro combinaciones exclusivas de Alto son la firma de P2 (desconexión) y de P5 (bloqueo + pago parcial).

### 4.7 Validación con variables crudas

![Figura 6](figuras/fig06_crudos_por_nivel.png)

| Variable cruda (mediana salvo indicación) | Alto | Medio | Bajo |
|---|---|---|---|
| Semanas desde la matrícula | 36 | 59 | 88 |
| Avance aprobado | 0,40 | 0,63 | 0,88 |
| % pagado sobre lo facturado | 0,67 | 0,91 | 1,00 |
| Períodos matriculados | 1 | 1 | 2 |
| **% sin ninguna calificación registrada** | **59,9 %** | 10,9 % | 0,1 % |
| % con algún impago | 20,2 % | 14,4 % | 7,9 % |
| % sin entregas en el LMS en 90 días | 84,1 % | 86,4 % | 88,4 % |

Por causa dominante (grupo = Alto con esa causa; control = todas las Bajo):

| Causa dominante | n | Variable cruda | Grupo | Control | Efecto |
|---|---|---|---|---|---|
| Promedio de notas en el campus | 196 | sin avance registrado | 97 % | 0 % | +97 pp |
| Número de calificaciones | 192 | sin avance registrado | 86 % | 0 % | +86 pp |
| Porcentaje de pagos cobrados | 143 | % pagado | 0,55 | 1,00 | r = −0,87 |
| Días desde el primer bloqueo | 102 | % pagado | 0,75 | 1,00 | r = −0,72 |
| Días desde el primer bloqueo | 102 | impagos | 0 | 0 | r = +0,21 |
| Número de bloqueos | 21 | % pagado | 0,80 | 1,00 | r = −0,70 |
| Número de impagos | 19 | impagos | 4 | 0 | r = +0,95 |
| Edad | 11 | edad | 56 | 32 | r = +0,95 |
| Días desde el último cambio de matrícula | 20 | cambios de matrícula | 6 | 5 | r = +0,13 (n.s.) |

Los patrones académicos (P1, P2, P3) y financieros (P4) se confirman con efectos fuertes. El patrón de bloqueo (P5) se confirma por el lado del pago y no por el de los impagos. El único hecho que no se sostiene en crudo es el de cambios de matrícula, que en Alto es una causa marginal (3 %).

La ventana de 90 días de entregas en el LMS no discrimina niveles (84–88 % sin entregas en todos): la corrida cae sobre el receso académico. No se usó en la validación por causa.

---

## 5. Calidad de los insumos

Dos hallazgos que afectan la explicación que llega al cliente y conviene resolver antes de industrializar la detección de patrones.

### 5.1 Dirección de riesgo distinta entre el output y el diccionario

En 8 de las 28 variables presentes en `full_facts`, la `direccion_riesgo` embebida en el output (la que el Explicador aplicó) difiere de la del `var_definitions.json` entregado. El output se generó con otro diccionario (el artefacto de entrenamiento).

| Variable | En el output | En el diccionario |
|---|---|---|
| `n_bloqueos_acum` | alto | bajo |
| `lms_n_cursos_accedidos_acum` | bajo | alto |
| `lms_dias_desde_ultima_entrega` | bajo | alto |
| `lms_nota_media_90d` | bajo | alto |
| `nota_media_365d` | bajo | alto |
| `n_nodos_completados_acum` | bajo | alto |
| `n_periodos_matriculado` | bajo | alto |
| `plan_pct_tiempo_transcurrido` | bajo | alto |

La dirección decide si un hecho "eleva el riesgo" o es "contextual" en el texto final; con dos diccionarios, la misma matrícula recibe dos explicaciones distintas. El análisis usó la dirección del output. Recomendación: una única fuente de verdad para el diccionario, versionada junto al modelo.

### 5.2 Referencia de severidad sin dispersión

Para número de calificaciones en al menos tres segmentos (Psicología · NI, Dirección Financiera · NI, Gestión Pública · NI), la referencia de severidad devuelve `medio` a un valor 0 porque los percentiles p10–p90 del segmento × mes son todos 0. En dos de esos segmentos el valor 0 discrimina con fuerza en los datos crudos (63–84 % sin calificación registrada frente a 0–1 % en los Bajo). El Explicador está describiendo como "contextual" un hecho que es la causa principal del riesgo. Recomendación: revisar la construcción de la referencia para segmentos con baja dispersión (caída a `__global__` cuando `p10 == p90`, o referencia por semanas desde la matrícula en lugar de mes calendario para nuevo ingreso).

### 5.3 Otras limitaciones

- **Top-3.** `full_facts` conserva los tres hechos de mayor peso. Comportamientos con peso menor (p. ej. entregas no presentadas) no aparecen aunque existan; el patrón "no presenta tareas" solo se observa indirectamente, a través de ítems calificados y promedio de notas en el campus.
- **Sin campo de curso.** "Primer año" se aproxima con nuevo ingreso. Si el archivo incluyera el curso, P1 y P2 podrían separarse por año.
- **Snapshot único.** Todo es una foto del 03-08-2026. La evolución de los patrones (si el arranque sin tracción de una cohorte se resuelve o se convierte en baja) requiere series de corridas.
- **Variables crudas exportadas.** La salida trae pocas variables crudas de campus (solo entregas 90 d). Incluir en el output las acumuladas de LMS y el número de calificaciones permitiría validar P1/P2 directamente y no por la vía indirecta del avance nulo.

---

## 6. Lectura para la acción

Sin entrar en el diseño de intervenciones, los patrones se ordenan naturalmente por quién puede actuar:

| Patrón | Quién puede actuar | Señal a mover | Volumen Alto |
|---|---|---|---|
| P1 Arranque sin tracción | Coordinación de titulación / tutoría (onboarding) | Actividad calificada en el campus en los primeros meses | 136 (Grado NI) |
| P2 Desconexión temprana | Tutoría / seguimiento de nuevo ingreso | Acceso a los cursos y primera entrega | 110 (Máster NI) |
| P3 Severidad no graduable | Equipo de datos (corrección de la referencia) | — | 27 + 15 |
| P4 Financiero de reingreso | Cobranzas / becas | Porcentaje pagado, plan de pago | 143 |
| P5 Bloqueo reciente | Administración académica + cobranzas | Resolución del bloqueo | 102 |
| P6 Edad | Institución (diseño de acompañamiento) | — (no accionable individualmente) | 11 |

Grado en Psicología · Nuevo ingreso merece un tratamiento propio: una titulación, 101 matrículas Alto, cuatro cohortes distintas y un hallazgo sistémico de onboarding que explica más de la mitad.

---

## 7. Reproducibilidad

El notebook `deteccion_patrones_riesgo.ipynb` corre de punta a punta sobre cualquier salida del Explicador en modo `pro` (con `full_facts`) y su `var_definitions.json`. Configuración en la primera celda: rutas, mapa de columnas, columnas PII a eliminar, población, umbrales. Salidas en `outputs/`:

| Archivo | Contenido |
|---|---|
| `tablas/panorama_causas_dominantes.csv` | Distribución de causas dominantes Alto vs. Medio |
| `tablas/mapa_causas_por_tipo.csv` | Causas dominantes por tipo de estudiante y titulación |
| `tablas/riesgo_por_contexto.csv` | Activos, Alto, Medio, RR por contexto |
| `tablas/arquetipos.csv` | Arquetipos `contexto × causa` con perfil y causas secundarias |
| `tablas/vista_agregada.csv` | Vista por tipo de titulación × tipo de estudiante (cobertura 100 %) |
| `tablas/hallazgos_sistemicos.csv` | Concentración por contexto, Alto y Alto+Medio |
| `tablas/coocurrencias.csv` · `coocurrencias_donde.csv` | Pares y tríos con soporte, lift y contextos |
| `tablas/validacion_crudos_global.csv` · `validacion_crudos_hallazgos.csv` | Contraste con la población Bajo |
| `tablas/control_diccionario.csv` | Direcciones output vs. diccionario |
| `figuras/fig01` … `fig06` | Las figuras de este informe |
| `resumen_automatico.md` | Borrador con los números clave, para comparar corridas |

Ningún archivo de salida contiene identificadores individuales ni datos personales.

---

## Anexo · Variables citadas

| Etiqueta en el texto | Variable | Dimensión | Dirección (output) |
|---|---|---|---|
| Promedio de notas en el campus | `lms_nota_media_acum` | Rendimiento Académico | bajo |
| Número de calificaciones | `n_calificaciones_acum` | Rendimiento Académico | bajo |
| Ítems calificados en el campus | `lms_n_items_calificados_acum` | Interacción en Plataforma | bajo |
| Número de cursos accedidos | `lms_n_cursos_accedidos_acum` | Interacción en Plataforma | bajo |
| Porcentaje de pagos cobrados | `ratio_cobrado_acum` | Situación Financiera | bajo |
| Número de impagos | `n_impagos_acum` | Situación Financiera | alto |
| Días desde el primer bloqueo | `dias_desde_primer_bloqueo` | Perfil Institucional | bajo |
| Número de bloqueos | `n_bloqueos_acum` | Perfil Institucional | alto |
| Días desde el último cambio de matrícula | `dias_desde_ultimo_cambio_mat` | Perfil Institucional | bajo |
| Edad | `edad_en_observacion` | Perfil Demográfico | alto |
