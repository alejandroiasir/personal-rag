# Especificación de Requisitos: Diagnóstico Normativo con RAG

| Campo | Valor |
|---|---|
| Proyecto | Diagnóstico normativo RAG con Haystack |
| Fase | 1 — Especificación de requisitos (Spec-Driven Development) |
| Versión | 1.0 |
| Fecha | 2026-10-27 |
| Estado | Borrador para revisión |
| Fuente base | Brief del proyecto (§1 Tipologías, §2 Formatos, §3 Criterios de calidad) |

---

## 1. Introducción

### 1.1 Propósito

Este documento define los requisitos del sistema de diagnóstico normativo. El sistema permite ingerir normas, categorizarlas, cruzarlas con planillas (Excel/CSV) y textos de la organización auditada, y generar diagnósticos con citas verificables a la fuente normativa. Este documento no contiene decisiones de diseño técnico. Esas decisiones se registran en el Design Doc/RFC (sección 11).

### 1.2 Alcance

**Incluido en la versión 1.0:**
- Ingesta y categorización de normas en formatos PDF con texto nativo, DOCX, HTML y TXT.
- Lectura de planillas XLSX y CSV con controles o requisitos a diagnosticar.
- Pipeline RAG (recuperación + generación) implementado con Haystack.
- Diagnóstico por ítem con estado y citas.
- Exportación de resultados a XLSX y PDF.
- Registro de auditoría de consultas.

**Excluido de la versión 1.0:**
- Asesoría jurídica o dictamen legal vinculante. El sistema es una herramienta de apoyo a la auditoría.
- OCR sobre PDF escaneados (se evalúa para la versión 1.1, ver DI-003).
- Acceso desde redes públicas o integraciones con sistemas de terceros fuera de la red privada.
- Edición de normas dentro del sistema.

### 1.3 Glosario

| Término | Definición |
|---|---|
| Norma | Documento normativo ingerido en el corpus (ley, reglamento, resolución, estándar). |
| Versión vigente | Versión de una norma aplicable a una fecha de análisis dada. |
| Categoría | Clasificación temática de una norma, tomada de un catálogo cerrado. |
| Fragmento (chunk) | Segmento de texto de una norma o documento, de hasta 512 tokens, indexado en la base vectorial. |
| Cita | Referencia verificable a un fragmento concreto: documento, versión, artículo o página y `chunk_id`. |
| Diagnóstico | Evaluación de un ítem de una planilla con estado (Cumple / No cumple / Sin evidencia) y citas. |
| Corpus dorado | Conjunto de preguntas y respuestas de referencia, validado por expertos, usado para medir calidad. |
| Sin evidencia | Estado de respuesta cuando el corpus recuperado no contiene información suficiente. |

### 1.4 Actores

| Actor | Descripción |
|---|---|
| Auditor normativo | Usuario principal. Consulta normas, carga planillas y revisa diagnósticos. |
| Auditor senior | Revisa y aprueba diagnósticos y corrige categorías. |
| Administrador de corpus | Ingesta normas, gestiona versiones y metadatos. |
| Responsable de seguridad | Verifica cifrado, control de acceso y registros de auditoría. |
| Sistema | Ejecuta los pipelines de ingesta, indexación, recuperación y generación. |

### 1.5 Convenciones

- **Prioridad:** MoSCoW (**Must**, **Should**, **Could**, **Won't** para esta versión).
- **Identificadores:** RF (funcional), RNF (no funcional), RS (restricción), DI (datos e integraciones), NG (negocio), HU (historia de usuario).
- **Números:** los decimales usan coma en el texto de negocio y punto en los valores de configuración, siguiendo la convención del brief.
- **Plazos y umbrales:** todos los valores se expresan con unidad, condición de medición y método de verificación.

---

## 2. Requisitos Funcionales

### RF-001 — Ingesta de normas

- **Descripción:** El sistema debe aceptar normas en PDF con texto nativo, DOCX, HTML y TXT, y registrarlas en el corpus con sus metadatos obligatorios (ver DI-001). Una norma se acepta solo si supera la validación de formato y de metadatos.
- **Prioridad (MoSCoW):** Must
- **Criterio de verificación:**
  - Sobre un corpus de prueba de 200 normas (40 por formato), al menos 196 (98 %) se ingieren sin error.
  - Las 4 normas rechazadas restantes generan un registro de error con motivo explícito (formato no soportado, metadato faltante o archivo corrupto).
  - El 100 % de las normas aceptadas tiene los campos obligatorios de DI-001 completos.
- **Fuente:** Brief §1 (Ingesta/categorización de normas).

### RF-002 — Categorización de normas

- **Descripción:** Al ingerir una norma, el sistema propone una categoría de un catálogo cerrado definido por el área de cumplimiento. Un Administrador de corpus puede confirmarla o corregirla. La categoría final queda registrada con su origen (automática o manual).
- **Prioridad (MoSCoW):** Must
- **Criterio de verificación:**
  - Sobre un conjunto etiquetado manualmente de 200 normas, la categoría propuesta coincide con la etiqueta de referencia en al menos el 90 % de los casos (precisión).
  - El 100 % de las categorías asignadas pertenece al catálogo cerrado. Ningún valor fuera de catálogo se persiste.
  - El 100 % de los registros indica si la categoría es `automatica` o `manual`.
- **Fuente:** Brief §1 (Ingesta/categorización de normas); §1 (Datos: metadatos para filtrado, categoría).

### RF-003 — Lectura de planillas Excel y CSV

- **Descripción:** El sistema debe leer planillas XLSX y CSV que contengan requisitos o controles a diagnosticar. Debe validar que existan las columnas obligatorias definidas en DI-002, detectar filas inválidas y generar un informe de errores por número de fila.
- **Prioridad (MoSCoW):** Must
- **Criterio de verificación:**
  - Una planilla de hasta 50.000 filas y 100 columnas se procesa en 30 segundos o menos, medido sobre la infraestructura de referencia.
  - Sobre un conjunto de 30 planillas de prueba con errores sembrados (celdas vacías, columnas faltantes, codificación incorrecta), el sistema detecta el 100 % de los errores sembrados y los informa con número de fila y columna.
  - Ninguna fila válida se descarta: el número de filas procesadas válidas es igual al número de filas válidas del archivo de prueba.
- **Fuente:** Brief §1 (Lectura de planillas Excel/CSV); §1 (Datos: conectores Excel/CSV).

### RF-004 — Ingesta y fragmentación de textos a auditar

- **Descripción:** El sistema debe ingerir textos de la organización auditada (procedimientos, políticas, contratos) en los mismos formatos de RF-001, y dividirlos en fragmentos de hasta 512 tokens con solape de 64 tokens. Cada fragmento conserva la referencia a su sección de origen.
- **Prioridad (MoSCoW):** Must
- **Criterio de verificación:**
  - El 100 % de los fragmentos generados tiene una longitud de 512 tokens o menos, medido con el tokenizador del modelo de embeddings configurado.
  - Dos fragmentos consecutivos de un mismo documento comparten exactamente 64 tokens de solape (verificado en 100 documentos de prueba).
  - El 100 % de los fragmentos tiene `seccion_origen` no vacío cuando el documento contiene encabezados.
- **Fuente:** Brief §1 (Ingesta de textos); §2 (Requisitos de pipeline).

### RF-005 — Indexación vectorial

- **Descripción:** El sistema debe generar embeddings de cada fragmento y almacenarlos en la base vectorial junto con los metadatos de DI-001 y DI-005. Un documento nuevo o actualizado debe quedar disponible para consulta en un plazo máximo de 15 minutos desde su ingesta.
- **Prioridad (MoSCoW):** Must
- **Criterio de verificación:**
  - Tras la ingesta de 100 documentos de prueba, el 100 % de sus fragmentos aparece en la búsqueda vectorial dentro de 15 minutos (medido con marca de tiempo de ingesta y de disponibilidad).
  - El número de vectores almacenados por documento coincide con el número de fragmentos generados (diferencia = 0).
- **Fuente:** Brief §1 (Pipeline RAG, Retrieval); §2 (Restricciones: Vector Database).

### RF-006 — Recuperación con filtros por metadatos

- **Descripción:** El sistema debe recuperar los fragmentos más relevantes para una consulta (top-k configurable, valor por defecto `k = 8`), permitiendo filtrar por categoría, fecha de publicación y versión. Los filtros se aplican antes de devolver resultados.
- **Prioridad (MoSCoW):** Must
- **Criterio de verificación:**
  - Con un filtro activo, el 100 % de los fragmentos devueltos cumple el filtro (ningún resultado fuera del filtro).
  - Sobre el corpus dorado (200 preguntas), la recuperación contiene al menos un fragmento de la fuente correcta en el top-8 para el 90 % de las preguntas (Recall@8 ≥ 0,90).
  - El número de resultados devueltos es igual a `k` cuando el corpus filtrado tiene al menos `k` fragmentos.
- **Fuente:** Brief §1 (Retrieval con Haystack); §1 (Datos: metadatos para filtrado).

### RF-007 — Generación de respuestas fundamentadas

- **Descripción:** El sistema debe generar respuestas utilizando únicamente los fragmentos recuperados como evidencia. Cuando los fragmentos no contienen información suficiente para responder, el sistema debe responder con el estado `Sin evidencia` y no generar contenido.
- **Prioridad (MoSCoW):** Must
- **Criterio de verificación:**
  - En un subconjunto de 50 preguntas sin respuesta en el corpus, el 100 % de las respuestas devuelve el estado `Sin evidencia`.
  - Ninguna respuesta contiene información que no esté presente en los fragmentos recuperados (verificado según RNF-001).
- **Fuente:** Brief §1 (Generation con Haystack); §3 (RNF: respuestas fieles sin alucinaciones).

### RF-008 — Citas verificables

- **Descripción:** Cada afirmación de una respuesta o diagnóstico debe incluir al menos una cita con el formato definido en DI-006 (documento, versión, artículo o página y `chunk_id`). El sistema debe verificar que la cita exista en el corpus antes de mostrarla.
- **Prioridad (MoSCoW):** Must
- **Criterio de verificación:**
  - El 100 % de las respuestas con estado distinto de `Sin evidencia` incluye al menos una cita.
  - El 100 % de las citas mostradas resuelve a un `chunk_id` existente en el corpus (prueba automática sobre 500 respuestas).
  - El 0 % de citas apunta a una versión no vigente cuando la consulta especifica fecha de análisis (ver RF-012).
- **Fuente:** Brief §1 (Exportación de diagnósticos con citas); §3 (Verificabilidad).

### RF-009 — Diagnóstico por ítem de planilla

- **Descripción:** Para cada fila válida de una planilla cargada (RF-003), el sistema debe generar un diagnóstico con estado `Cumple`, `No cumple` o `Sin evidencia`, acompañado de justificación y citas (RF-008).
- **Prioridad (MoSCoW):** Must
- **Criterio de verificación:**
  - El número de diagnósticos generados es igual al número de filas válidas de la planilla (diferencia = 0).
  - El estado asignado coincide con la etiqueta del auditor senior en al menos el 85 % de los ítems de un conjunto de 100 ítems etiquetados.
  - Una planilla de 500 ítems se diagnostica en 20 minutos o menos sobre la infraestructura de referencia (RNF-002 aplica por consulta individual).
- **Fuente:** Brief §1 (Pipeline RAG); §1 (Negocio: reducción del tiempo de auditoría).

### RF-010 — Exportación de diagnósticos con citas

- **Descripción:** El sistema debe exportar los diagnósticos a XLSX y PDF. Cada fila o sección incluye ítem, estado, justificación, citas (DI-006) y fecha de generación. El archivo indica las versiones de normas usadas.
- **Prioridad (MoSCoW):** Must
- **Criterio de verificación:**
  - Un diagnóstico de 500 ítems se exporta en 20 segundos o menos.
  - El 100 % de los ítems exportados contiene estado y al menos una cita, o el estado `Sin evidencia` sin cita.
  - Un auditor externo puede localizar la cita en la norma original en 60 segundos o menos en el 90 % de las muestras (prueba de usabilidad con 10 ítems tomados al azar y 5 participantes).
- **Fuente:** Brief §1 (Exportación de diagnósticos con citas).

### RF-011 — Registro de auditoría de consultas

- **Descripción:** El sistema debe registrar cada consulta y diagnóstico con: usuario, marca de tiempo, texto de la consulta, `chunk_id` recuperados, versión del modelo y del índice, y respuesta generada. Los registros se conservan 365 días.
- **Prioridad (MoSCoW):** Must
- **Criterio de verificación:**
  - El 100 % de las consultas ejecutadas en una prueba de 200 consultas tiene su registro completo (7 campos).
  - Un registro puede reconstruirse para reproducir la respuesta (RNF-009) con el mismo índice y modelo.
  - La eliminación de registros con más de 365 días se ejecuta automáticamente, con verificación diaria de cero registros vencidos.
- **Fuente:** Brief §3 (Criterios de calidad: trazable); RNF-006.

### RF-012 — Gestión de versiones normativas

- **Descripción:** Al ingerir una nueva versión de una norma, el sistema debe conservar la versión anterior, marcar la nueva como vigente desde su fecha de entrada en vigor y permitir consultar cualquier versión por fecha de análisis.
- **Prioridad (MoSCoW):** Should
- **Criterio de verificación:**
  - Dada una norma con dos versiones (V1 vigente hasta 2026-06-30, V2 desde 2026-07-01), una consulta con fecha de análisis 2026-06-15 recupera solo fragmentos de V1, y una con 2026-07-15 recupera solo V2. Se verifica en 20 casos de prueba con 100 % de aciertos.
  - Ninguna versión se elimina del índice al ingerir una nueva.
- **Fuente:** Brief §1 (Datos: metadatos de versión y fecha).

---

## 3. Requisitos No Funcionales

### RNF-001 — Fidelidad sin alucinaciones

- **Descripción:** Las respuestas y diagnósticos deben estar soportados por los fragmentos citados. Una afirmación no soportada se considera alucinación.
- **Prioridad (MoSCoW):** Must
- **Criterio de verificación:**
  - Sobre el corpus dorado de 200 preguntas, al menos el 95 % de las afirmaciones se califican como "soportadas" por la cita, según revisión de dos expertos con acuerdo entre evaluadores κ ≥ 0,7.
  - El 0 % de las citas apunta a un `chunk_id` inexistente o a un texto que no contiene la afirmación citada (prueba automática y muestra manual de 50 citas).
- **Fuente:** Brief §3 (RNF: respuestas fieles sin alucinaciones).

### RNF-002 — Latencia

- **Descripción:** El tiempo total desde que el usuario envía una consulta hasta que recibe la respuesta completa (recuperación + generación + citas) debe ser inferior a 10 segundos en el percentil 95.
- **Prioridad (MoSCoW):** Must
- **Criterio de verificación:**
  - Sobre 500 consultas del corpus dorado, con 10 usuarios concurrentes en la infraestructura de referencia (definida en el Design Doc), el percentil 95 de latencia es menor a 10,0 s.
  - La medición incluye todo el tiempo desde la recepción de la petición HTTP hasta el último byte de la respuesta.
- **Fuente:** Brief §3 (RNF: latencia p95 < 10 s).

### RNF-003 — Cifrado en tránsito y en reposo

- **Descripción:** Todo dato en tránsito debe usar TLS 1.2 o superior, con TLS 1.3 preferido. Todo dato en reposo (documentos, índice vectorial, registros de auditoría, copias de seguridad) debe cifrarse con AES-256.
- **Prioridad (MoSCoW):** Must
- **Criterio de verificación:**
  - Un escaneo con herramienta de análisis TLS (por ejemplo, testssl.sh) sobre todos los endpoints internos da como resultado 0 protocolos inferiores a TLS 1.2 y 0 suites de cifrado débiles.
  - La configuración de cifrado en reposo se verifica en 100 % de los almacenes (base vectorial, almacenamiento de documentos, base de registros y backups) mediante revisión de configuración firmada por el Responsable de seguridad.
- **Fuente:** Brief §3 (RNF: cifrado en tránsito/reposo).

### RNF-004 — Disponibilidad

- **Descripción:** El servicio debe estar disponible para consultas durante el horario hábil definido por la organización.
- **Prioridad (MoSCoW):** Should
- **Criterio de verificación:**
  - Disponibilidad medida mensualmente con monitorización sintética (una consulta cada 60 segundos): mayor o igual a 99,5 % sobre el horario hábil.
- **Fuente:** Supuesto de operación (pendiente de confirmación por el cliente, ver sección 12).

### RNF-005 — Escalabilidad del corpus

- **Descripción:** El sistema debe mantener los umbrales de RNF-002 y RF-006 con un corpus de hasta 1.000.000 de fragmentos indexados.
- **Prioridad (MoSCoW):** Should
- **Criterio de verificación:**
  - Con un corpus de prueba de 1.000.000 de fragmentos, el percentil 95 de latencia (RNF-002) se mantiene por debajo de 10,0 s, y el Recall@8 (RF-006) no baja de 0,90.
- **Fuente:** Supuesto de dimensionamiento (pendiente de confirmación, ver sección 12).

### RNF-006 — Trazabilidad

- **Descripción:** Toda respuesta debe poder vincularse con la versión de las normas, el modelo de lenguaje, el modelo de embeddings y el índice que la generaron.
- **Prioridad (MoSCoW):** Must
- **Criterio de verificación:**
  - El 100 % de los registros generados en la prueba de 200 consultas contiene los identificadores de versión de estos cuatro componentes (verificable por consulta de auditoría).
- **Fuente:** Brief §3 (Criterios de calidad: trazable).

### RNF-007 — Privacidad y despliegue privado

- **Descripción:** Ningún contenido de normas, planillas, textos o consultas puede salir de la red privada de la organización. Esto incluye los modelos de lenguaje y de embeddings.
- **Prioridad (MoSCoW):** Must
- **Criterio de verificación:**
  - Una prueba de egreso de red durante 200 consultas registra 0 conexiones salientes hacia dominios o direcciones públicas no autorizadas.
  - El 100 % de los componentes de inferencia (LLM y embeddings) se despliega dentro de la red privada, verificado en la revisión de arquitectura.
- **Fuente:** Brief §2 (Restricciones: despliegue privado).

### RNF-008 — Rendimiento de ingesta

- **Descripción:** La ingesta de documentos debe completarse dentro de un tiempo acotado para permitir actualizaciones diarias del corpus.
- **Prioridad (MoSCoW):** Should
- **Criterio de verificación:**
  - Un PDF de 100 páginas con texto nativo se ingiere, fragmenta, indexa y queda disponible en 60 segundos o menos, medido en la infraestructura de referencia.
- **Fuente:** Supuesto de operación (pendiente de confirmación, ver sección 12).

### RNF-009 — Reproducibilidad

- **Descripción:** Una misma consulta, ejecutada con el mismo índice, la misma versión de modelos y la misma configuración, debe devolver los mismos fragmentos recuperados y la misma respuesta.
- **Prioridad (MoSCoW):** Should
- **Criterio de verificación:**
  - Sobre 50 consultas repetidas 10 veces cada una, el 100 % de las ejecuciones devuelve el mismo conjunto ordenado de `chunk_id` y la misma respuesta textual.
- **Fuente:** Brief §3 (Criterios de calidad: verificable).

### RNF-010 — Accesibilidad de la interfaz

- **Descripción:** La interfaz de usuario debe cumplir el nivel AA de WCAG 2.1 en las pantallas de consulta, carga de planillas y visualización de diagnósticos.
- **Prioridad (MoSCoW):** Could
- **Criterio de verificación:**
  - Un análisis automático con herramienta de accesibilidad (por ejemplo, axe) en las 3 pantallas da 0 violaciones de nivel crítico o serio.
- **Fuente:** Supuesto de calidad de interfaz (pendiente de confirmación, ver sección 12).

---

## 4. Restricciones

### RS-001 — Framework Haystack

- **Descripción:** El pipeline de ingesta, recuperación y generación debe implementarse con Haystack 2.x. La versión exacta se fija en el archivo de dependencias.
- **Prioridad (MoSCoW):** Must
- **Criterio de verificación:** El archivo de dependencias fija una versión 2.x exacta. Los pipelines de recuperación y generación se definen como componentes de Haystack, verificado en revisión de código.
- **Fuente:** Brief §2 (Restricciones: uso de Haystack).

### RS-002 — Base de datos vectorial

- **Descripción:** La base vectorial debe ser Qdrant o pgvector, autoalojada en la red privada. La elección final se registra en el Design Doc.
- **Prioridad (MoSCoW):** Must
- **Criterio de verificación:** La base vectorial seleccionada aparece en el Design Doc aprobado y está desplegada dentro de la red privada (verificado según RNF-007).
- **Fuente:** Brief §2 (Restricciones: Vector Database, ej. Qdrant/pgvector).

### RS-003 — Despliegue privado

- **Descripción:** Todos los componentes (aplicación, pipelines, base vectorial, base de registros, modelos) se despliegan en infraestructura privada de la organización, sin exposición pública de los endpoints de datos.
- **Prioridad (MoSCoW):** Must
- **Criterio de verificación:** Un escaneo desde una red externa a los puertos de servicio devuelve 0 puertos de datos accesibles. La revisión de arquitectura confirma el despliegue privado.
- **Fuente:** Brief §2 (Restricciones: despliegue privado).

### RS-004 — Idioma

- **Descripción:** El corpus, las consultas, las respuestas y los diagnósticos deben estar en español. El sistema debe procesar documentos con marcas de idioma `es`.
- **Prioridad (MoSCoW):** Must
- **Criterio de verificación:** El 100 % de las respuestas y diagnósticos en la prueba de aceptación está redactado en español, verificado por revisión de un hablante nativo sobre una muestra de 50 respuestas.
- **Fuente:** Supuesto de negocio (confirmar con el cliente, ver sección 12).

### RS-005 — Modelos de lenguaje y embeddings privados

- **Descripción:** Los modelos de lenguaje y de embeddings deben estar alojados dentro de la red privada o detrás de un endpoint privado controlado por la organización.
- **Prioridad (MoSCoW):** Must
- **Criterio de verificación:** Revisión de configuración confirma que la URL del modelo apunta a un endpoint interno, y la prueba de egreso de RNF-007 no registra tráfico a proveedores externos.
- **Fuente:** Brief §2 (Restricciones: despliegue privado); RNF-007.

### RS-006 — Catálogo cerrado de categorías

- **Descripción:** Las categorías normativas se definen en un catálogo controlado por el área de cumplimiento. Solo el Administrador de corpus puede modificarlo.
- **Prioridad (MoSCoW):** Should
- **Criterio de verificación:** El catálogo tiene un identificador de versión y un registro de cambios. Un intento de asignar una categoría fuera del catálogo es rechazado (prueba de 20 casos).
- **Fuente:** Brief §1 (Ingesta/categorización de normas).

---

## 5. Datos e Integraciones

### DI-001 — Metadatos obligatorios de normas

| Campo | Tipo | Obligatorio | Formato o valores | Uso |
|---|---|---|---|---|
| `doc_id` | texto | Sí | Identificador único, sin espacios | Trazabilidad |
| `titulo` | texto | Sí | 1 a 300 caracteres | Visualización |
| `categoria` | enumeración | Sí | Valor del catálogo (RS-006) | Filtro (RF-006) |
| `origen_categoria` | enumeración | Sí | `automatica` o `manual` | Auditoría (RF-002) |
| `fecha_publicacion` | fecha | Sí | ISO 8601 (`AAAA-MM-DD`) | Filtro (RF-006) |
| `fecha_vigencia_inicio` | fecha | Sí | ISO 8601 | Filtro por versión (RF-012) |
| `version` | texto | Sí | `V` seguido de número entero (`V1`, `V2`) | Filtro (RF-006, RF-012) |
| `fuente_url` | texto | No | URL o ruta interna | Referencia |
| `idioma` | enumeración | Sí | `es` | RS-004 |

- **Prioridad (MoSCoW):** Must
- **Criterio de verificación:** Una norma sin alguno de los campos obligatorios es rechazada en RF-001. El 100 % de los registros aceptados valida el esquema en la prueba automática.
- **Fuente:** Brief §1 (Datos e integraciones: metadatos para filtrado — categoría, fecha, versión).

### DI-002 — Conector de planillas Excel y CSV

- **Descripción:** El conector debe leer XLSX (primera hoja o hoja indicada) y CSV. Debe detectar codificación (UTF-8 o Windows-1252) y separador (`,` o `;`). La primera fila debe contener los encabezados.
- **Columnas obligatorias de entrada:** `id_item`, `requisito` (texto de 1 a 2.000 caracteres), `area` (texto).
- **Columnas opcionales:** `categoria_sugerida` (valor de catálogo), `fecha_referencia` (ISO 8601).
- **Prioridad (MoSCoW):** Must
- **Criterio de verificación:**
  - Un archivo sin alguna columna obligatoria se rechaza con mensaje que nombra la columna faltante (prueba de 10 archivos).
  - Un CSV con codificación Windows-1252 y separador `;` se lee con 0 caracteres corruptos en 10 muestras.
  - Los campos de longitud superior a 2.000 caracteres se marcan como fila inválida con número de fila.
- **Fuente:** Brief §1 (Lectura de planillas Excel/CSV); §1 (Datos: conectores Excel/CSV).

### DI-003 — Conector de textos normativos y de la organización

- **Descripción:** Formatos soportados en la versión 1.0: PDF con texto nativo, DOCX, HTML y TXT. Los PDF escaneados sin capa de texto se rechazan. El soporte de OCR se evalúa para la versión 1.1.
- **Prioridad (MoSCoW):** Must (formatos soportados); Won't para OCR en 1.0; Could para OCR en 1.1
- **Criterio de verificación:**
  - El 98 % de los documentos de prueba en formatos soportados se convierte a texto con cobertura de caracteres de al menos 99 % frente a la referencia.
  - Un PDF sin capa de texto se rechaza con motivo explícito en el 100 % de los casos de prueba.
- **Fuente:** Brief §1 (Ingesta de textos).

### DI-004 — Esquema de exportación de diagnósticos

- **Descripción:** La exportación en XLSX y PDF incluye las columnas: `id_item`, `requisito`, `estado` (`Cumple`, `No cumple`, `Sin evidencia`), `justificacion`, `citas` (lista en formato DI-006), `version_norma`, `fecha_generacion`.
- **Prioridad (MoSCoW):** Must
- **Criterio de verificación:** Un archivo exportado de prueba contiene las 8 columnas en el orden indicado, y el 100 % de las filas tiene los valores de `estado` del conjunto permitido.
- **Fuente:** Brief §1 (Exportación de diagnósticos con citas).

### DI-005 — Campos indexados en la base vectorial

- **Descripción:** Los campos `categoria`, `fecha_publicacion`, `fecha_vigencia_inicio`, `version` y `doc_id` deben estar indexados como filtros en la base vectorial.
- **Prioridad (MoSCoW):** Must
- **Criterio de verificación:** Una consulta filtrada por cualquiera de estos campos responde en 1 segundo o menos sobre un índice de 1.000.000 de fragmentos (medido en 100 consultas, percentil 95).
- **Fuente:** Brief §1 (Datos: metadatos para filtrado).

### DI-006 — Formato de cita

- **Descripción:** Cada cita sigue la estructura: `doc_id`, `version`, referencia de localización (artículo, sección o página), `chunk_id`. Ejemplo de estructura: `doc_id=RES-2024-15 | version=V2 | art=7.3 | chunk_id=c-004821`.
- **Prioridad (MoSCoW):** Must
- **Criterio de verificación:** El 100 % de las citas generadas en la prueba de 500 respuestas contiene los 4 componentes y resuelve a un `chunk_id` existente (RF-008).
- **Fuente:** Brief §1 (Exportación de diagnósticos con citas).

---

## 6. Objetivos de Negocio

### NG-001 — Reducción del tiempo de auditoría normativa

- **Descripción:** El sistema debe reducir el tiempo medio que un auditor dedica a un ciclo de auditoría normativa.
- **Prioridad (MoSCoW):** Must
- **Criterio de verificación:** Tiempo medio por auditoría reducido en al menos 40 % frente a la línea base medida en 10 auditorías de referencia realizadas antes del piloto, con medición de 10 auditorías durante el piloto.
- **Fuente:** Brief §1 (Negocio: reducción del tiempo de auditoría normativa).

### NG-002 — Adopción por los auditores

- **Descripción:** Los auditores deben usar el sistema como herramienta principal para consultas normativas y diagnósticos.
- **Prioridad (MoSCoW):** Should
- **Criterio de verificación:** A los 3 meses de puesta en producción, al menos el 80 % de los auditores activos registrados ejecutó al menos 4 consultas por semana, según registros de RF-011.
- **Fuente:** Supuesto de negocio (confirmar con el cliente, ver sección 12).

### NG-003 — Confianza en el diagnóstico

- **Descripción:** Los auditores deben confiar en la trazabilidad de las respuestas, lo que se refleja en la proporción de citas verificadas.
- **Prioridad (MoSCoW):** Should
- **Criterio de verificación:** En el piloto, al menos el 90 % de los diagnósticos revisados por un auditor senior se aprueba sin cambios en el estado asignado.
- **Fuente:** Brief §3 (Criterios de calidad: verificable, trazable).

---

## 7. Historias de Usuario

### HU-001 — Ingestar una norma nueva

**Historia:** Como Administrador de corpus, quiero cargar una norma en formato PDF, DOCX, HTML o TXT para que esté disponible en el corpus con sus metadatos completos.

- **Requisitos relacionados:** RF-001, RF-005, DI-001
- **Criterios de aceptación:**
  - **Given** el Administrador de corpus tiene sesión iniciada y una norma en PDF con texto nativo con todos los metadatos obligatorios,
    **When** carga el archivo y confirma la ingesta,
    **Then** el sistema muestra el estado `Ingerida` en menos de 60 segundos para un documento de 100 páginas y la norma aparece en la búsqueda al cabo de 15 minutos como máximo.
  - **Given** el Administrador de corpus carga un archivo sin el campo `fecha_publicacion`,
    **When** el sistema valida el archivo,
    **Then** rechaza la ingesta y muestra el mensaje "Falta el campo obligatorio: fecha_publicacion" sin crear ningún registro.
  - **Given** el Administrador de corpus carga un PDF escaneado sin capa de texto,
    **When** el sistema lo procesa,
    **Then** muestra el motivo "PDF sin texto nativo; OCR no disponible en esta versión" y no crea fragmentos.

### HU-002 — Revisar la categoría propuesta

**Historia:** Como Administrador de corpus, quiero revisar la categoría que el sistema propone para cada norma para asegurar que la clasificación es correcta.

- **Requisitos relacionados:** RF-002, RS-006
- **Criterios de aceptación:**
  - **Given** una norma ingerida con categoría propuesta `Seguridad de la información`,
    **When** el Administrador de corpus cambia la categoría a `Protección de datos` desde el catálogo,
    **Then** el sistema guarda el cambio, registra `origen_categoria = manual` y el cambio queda en el registro de auditoría.
  - **Given** el Administrador de corpus intenta escribir un valor que no está en el catálogo,
    **When** confirma el cambio,
    **Then** el sistema rechaza el valor y muestra solo las opciones del catálogo vigente.

### HU-003 — Cargar una planilla de controles

**Historia:** Como Auditor normativo, quiero cargar una planilla Excel o CSV con los controles a revisar para que el sistema los procese sin que yo deba copiarlos manualmente.

- **Requisitos relacionados:** RF-003, DI-002
- **Criterios de aceptación:**
  - **Given** el Auditor normativo tiene un archivo XLSX con 500 filas válidas y las columnas obligatorias,
    **When** lo carga,
    **Then** el sistema muestra "500 filas válidas" en 30 segundos o menos y habilita el botón de diagnóstico.
  - **Given** un archivo CSV con la columna `requisito` ausente,
    **When** el Auditor normativo lo carga,
    **Then** el sistema rechaza el archivo y muestra el mensaje "Falta la columna obligatoria: requisito".
  - **Given** un archivo con 20 filas en las que el campo `requisito` supera los 2.000 caracteres,
    **When** el sistema lo procesa,
    **Then** excluye esas 20 filas, muestra el número de cada fila excluida y procesa el resto.

### HU-004 — Consultar una norma con respuesta citada

**Historia:** Como Auditor normativo, quiero hacer una pregunta en lenguaje natural sobre la normativa para obtener una respuesta con citas que pueda verificar en la fuente.

- **Requisitos relacionados:** RF-006, RF-007, RF-008, RNF-001, RNF-002
- **Criterios de aceptación:**
  - **Given** el corpus contiene la norma RES-2024-15 con la versión V2 vigente,
    **When** el Auditor normativo pregunta "¿Qué plazo establece la norma para notificar un incidente?" con fecha de análisis 2026-10-27,
    **Then** el sistema devuelve la respuesta en menos de 10 segundos (percentil 95 sobre el corpus dorado) con al menos una cita en formato DI-006 que apunta a la versión V2.
  - **Given** la respuesta contiene una cita,
    **When** el Auditor normativo selecciona la cita,
    **Then** el sistema muestra el fragmento original de la norma con el texto resaltado.

### HU-005 — Recibir "Sin evidencia" cuando no existe respuesta en el corpus

**Historia:** Como Auditor normativo, quiero saber cuándo el corpus no contiene la respuesta para no basarme en información inventada.

- **Requisitos relacionados:** RF-007, RNF-001
- **Criterios de aceptación:**
  - **Given** el corpus no contiene ninguna norma sobre "requisitos de certificación de drones",
    **When** el Auditor normativo formula esa pregunta,
    **Then** el sistema responde con el estado `Sin evidencia` y el texto "No se encontró evidencia suficiente en el corpus vigente", sin citas y sin contenido generado.

### HU-006 — Diagnosticar una planilla completa

**Historia:** Como Auditor normativo, quiero obtener el diagnóstico de cada control de mi planilla para identificar los incumplimientos sin revisarlos uno a uno.

- **Requisitos relacionados:** RF-009, RF-008, DI-004
- **Criterios de aceptación:**
  - **Given** una planilla válida de 500 ítems cargada,
    **When** el Auditor normativo ejecuta el diagnóstico,
    **Then** el sistema genera 500 diagnósticos en 20 minutos o menos, cada uno con estado `Cumple`, `No cumple` o `Sin evidencia`, y con justificación y citas.
  - **Given** un ítem recibe el estado `No cumple`,
    **When** el Auditor normativo abre el detalle,
    **Then** ve la justificación y, al menos, una cita que identifica el artículo o página de la norma.

### HU-007 — Exportar el diagnóstico con citas

**Historia:** Como Auditor senior, quiero exportar el diagnóstico en XLSX o PDF con las citas incluidas para compartirlo con el comité de cumplimiento.

- **Requisitos relacionados:** RF-010, DI-004
- **Criterios de aceptación:**
  - **Given** un diagnóstico de 500 ítems completado,
    **When** el Auditor senior elige exportar a XLSX,
    **Then** el archivo se descarga en 20 segundos o menos y contiene las 8 columnas de DI-004 para los 500 ítems.
  - **Given** el Auditor senior elige exportar a PDF,
    **When** el sistema genera el archivo,
    **Then** el PDF incluye, en cada ítem, las citas y la versión de norma usada, y su primera página indica la fecha de generación.

### HU-008 — Consultar la versión vigente a una fecha

**Historia:** Como Auditor normativo, quiero consultar la norma tal como estaba vigente en una fecha concreta para auditar hechos pasados.

- **Requisitos relacionados:** RF-012, RF-006, RF-008
- **Criterios de aceptación:**
  - **Given** la norma tiene V1 vigente hasta 2026-06-30 y V2 desde 2026-07-01,
    **When** el Auditor normativo consulta con fecha de análisis 2026-06-15,
    **Then** todas las citas de la respuesta apuntan a V1.
  - **Given** la misma norma,
    **When** el Auditor normativo consulta con fecha de análisis 2026-07-15,
    **Then** todas las citas apuntan a V2.

### HU-009 — Revisar el registro de auditoría

**Historia:** Como Responsable de seguridad, quiero consultar qué usuario ejecutó qué consulta y con qué fuentes para verificar el uso del sistema y responder a auditorías internas.

- **Requisitos relacionados:** RF-011, RNF-006
- **Criterios de aceptación:**
  - **Given** existe un registro de consulta realizada el 2026-10-20 por un usuario,
    **When** el Responsable de seguridad filtra por usuario y fecha,
    **Then** el sistema muestra el registro con los 7 campos definidos en RF-011 en 3 segundos o menos.
  - **Given** un registro tiene más de 365 días,
    **When** se ejecuta la purga diaria,
    **Then** el registro se elimina y deja de aparecer en las consultas.

### HU-010 — Corregir una planilla con errores

**Historia:** Como Auditor normativo, quiero ver qué filas de mi planilla tienen errores para corregirlas y volver a cargar el archivo sin perder las filas válidas.

- **Requisitos relacionados:** RF-003, DI-002
- **Criterios de aceptación:**
  - **Given** una planilla con 10 filas inválidas de 510,
    **When** el Auditor normativo carga la planilla,
    **Then** el sistema muestra el informe con las 10 filas, su número y la columna con error, y permite continuar con las 500 filas válidas.
  - **Given** el Auditor normativo corrige las 10 filas y vuelve a cargar el archivo,
    **When** el sistema lo procesa,
    **Then** muestra "510 filas válidas" y no duplica ninguna fila.

---

## 8. Matriz de Trazabilidad

| Objetivo de negocio | Historias de usuario | Requisitos funcionales | Requisitos no funcionales | Restricciones y datos |
|---|---|---|---|---|
| NG-001 Reducir tiempo de auditoría | HU-003, HU-004, HU-006, HU-007 | RF-003, RF-006, RF-007, RF-009, RF-010 | RNF-002 | DI-002, DI-004 |
| NG-002 Adopción | HU-004, HU-006 | RF-006, RF-009 | RNF-002, RNF-004 | — |
| NG-003 Confianza | HU-004, HU-005, HU-007 | RF-007, RF-008 | RNF-001, RNF-006 | DI-006 |
| Gestión del corpus | HU-001, HU-002, HU-008 | RF-001, RF-002, RF-005, RF-012 | RNF-005, RNF-008 | DI-001, DI-003, DI-005, RS-006 |
| Seguridad y auditoría | HU-009 | RF-011 | RNF-003, RNF-007 | RS-003, RS-005 |
| Robustez de entrada | HU-010 | RF-003, RF-004 | — | DI-002 |

---

## 9. Criterios de Calidad de la Especificación

Cada requisito de este documento cumple los siguientes criterios. Antes de aprobar cambios, el revisor debe verificarlos.

- **Claridad:** no contiene términos subjetivos sin definición. Están prohibidos términos como "rápido", "fácil", "intuitivo", "adecuado", "robusto", "eficiente", "amigable", "suficiente" sin umbral medible, y "etc.".
- **Medibilidad:** cada requisito incluye al menos una cifra, una condición o un estado observable.
- **Verificabilidad:** cada requisito tiene un criterio de verificación con método (prueba automática, muestra manual, revisión de configuración, prueba de usabilidad).
- **Trazabilidad:** cada requisito tiene un identificador único, una fuente y, cuando aplica, relación con historias de usuario (sección 8).
- **Atomicidad:** un requisito describe una sola capacidad o restricción. Si aparece "y" entre dos capacidades independientes, se divide.
- **Ausencia de diseño:** el requisito describe el qué y el criterio, no la tecnología interna. Las decisiones de implementación se documentan en el Design Doc (sección 11).

---

## 10. Supuestos y Dependencias

- **Corpus dorado:** el área de cumplimiento entrega 200 preguntas con respuesta y fuente validadas antes de la fase de diseño. Dependencia de RNF-001, RF-006 y RNF-002.
- **Etiquetado de categorías:** el área de cumplimiento etiqueta 200 normas con el catálogo de RS-006. Dependencia de RF-002.
- **Línea base:** se miden 10 auditorías de referencia antes del piloto. Dependencia de NG-001.
- **Infraestructura de referencia:** se define en el Design Doc y debe incluir CPU, memoria, almacenamiento y GPU si el modelo lo requiere. Dependencia de RNF-002, RNF-005 y RNF-008.
- **Modelos privados:** existen modelos de lenguaje y de embeddings aprobados para uso en la red privada. Dependencia de RS-005.

---

## 11. Plantilla de Design Doc / RFC

Esta plantilla se usa en la Fase 1. Cada sección debe completarse antes de aprobar el diseño.

**Título:** `[Nombre de la decisión o componente]`
**Autor:** `[Nombre]`
**Estado:** `Borrador | En revisión | Aprobado | Reemplazado`
**Fecha:** `[AAAA-MM-DD]`
**Requisitos de referencia:** `[lista de IDs, por ejemplo RF-006, RNF-002]`

### 11.1 Contexto

Describir el problema, el estado actual y las restricciones que lo condicionan. Citar los requisitos de la sección 2 a 5 que motivan el diseño.

### 11.2 Objetivos

Lista numerada de resultados medibles. Cada objetivo debe referenciar al menos un requisito.

1. `[Objetivo medible con referencia a RF/RNF]`

### 11.3 No objetivos

Lista de lo que el diseño no resuelve de forma explícita, para evitar expansión de alcance.

1. `[No objetivo]`

### 11.4 Alternativas consideradas

Para cada alternativa, documentar ventajas, desventajas y motivo de descarte o selección.

| Opción | Ventajas | Desventajas | Decisión |
|---|---|---|---|
| `[Opción A, por ejemplo Qdrant autoalojado]` | `[ventajas]` | `[desventajas]` | `[seleccionada o descartada, con motivo]` |
| `[Opción B, por ejemplo pgvector]` | `[ventajas]` | `[desventajas]` | `[seleccionada o descartada, con motivo]` |

### 11.5 Diseño propuesto

#### 11.5.1 Componentes

| Componente | Responsabilidad | Tecnología | Requisitos que satisface |
|---|---|---|---|
| Ingesta | Conversión, validación de metadatos y fragmentación | `[Haystack converters, componentes propios]` | RF-001, RF-004, DI-001 |
| Indexación | Generación de embeddings y escritura en la base vectorial | `[Haystack embedders, Qdrant o pgvector]` | RF-005, DI-005 |
| Recuperación | Búsqueda con filtros y top-k | `[Haystack retrievers]` | RF-006, RNF-002 |
| Generación | Respuesta fundamentada y estado Sin evidencia | `[Haystack generators, LLM privado]` | RF-007, RNF-001 |
| Citas | Validación y formato de citas | `[componente propio]` | RF-008, DI-006 |
| Exportación | Generación de XLSX y PDF | `[librería a definir]` | RF-010, DI-004 |
| Registro | Escritura de registros de auditoría | `[base de datos a definir]` | RF-011, RNF-006 |

#### 11.5.2 Flujo de datos

Describir el recorrido de una consulta y de una ingesta, indicando cada componente y el dato que transmite. Incluir, para cada salto, el protocolo de transporte (TLS 1.2 o superior, RNF-003).

#### 11.5.3 Modelo de datos

Describir las entidades, sus campos y sus relaciones. Referenciar DI-001, DI-004, DI-005 y RF-011.

#### 11.5.4 Infraestructura de referencia

Especificar hardware, versiones de software y configuración de cifrado para la medición de RNF-002, RNF-005 y RNF-008.

### 11.6 Riesgos

| ID | Riesgo | Probabilidad | Impacto | Mitigación | Requisito afectado |
|---|---|---|---|---|---|
| R-01 | `[Por ejemplo: alucinaciones por evidencia recuperada insuficiente]` | `[Alta/Media/Baja]` | `[Alto/Medio/Bajo]` | `[acción concreta y medible]` | RNF-001 |
| R-02 | `[Por ejemplo: latencia p95 superior a 10 s con corpus grande]` | `[Alta/Media/Baja]` | `[Alto/Medio/Bajo]` | `[acción concreta y medible]` | RNF-002, RNF-005 |

### 11.7 Plan de verificación

Indicar cómo se medirá cada criterio de verificación de los requisitos referenciados, con el responsable y la fecha prevista.

### 11.8 Preguntas abiertas

1. `[Pregunta, con responsable y fecha de resolución]`

---

## 12. Preguntas Abiertas para Validación

Las siguientes decisiones requieren confirmación del cliente antes de cerrar la Fase 1.

1. **RNF-004:** ¿cuál es el horario hábil y la ventana de mantenimiento aceptada?
2. **RNF-005 y RNF-008:** ¿cuál es el volumen esperado de normas y de documentos por mes?
3. **RNF-010:** ¿es obligatorio el cumplimiento de WCAG 2.1 AA para la interfaz?
4. **NG-001 y NG-002:** ¿quién entrega la línea base y las métricas de adopción?
5. **RS-004:** ¿existen documentos en otros idiomas que deban incluirse en el corpus?
6. **DI-003:** ¿se requiere OCR en la versión 1.0 o se aprueba para la versión 1.1?
