# ADR-001: Diseño minimalista para uso personal

- **Estado:** Aceptado
- **Fecha:** 2026-10-27
- **Requisitos afectados:** RS-001, RS-002, RS-005, RS-007 (nuevo), RF-001, RF-004, RF-005, RF-006, RF-007, RF-008

## Contexto

El proyecto es personal. El objetivo es indexar cualquier documento que el usuario quiera (normas, contratos, procedimientos, apuntes) y obtener respuestas con citas correctas. La especificación original (`docs/requirements.md`) describe un sistema empresarial con autenticación, registro de auditoría, despliegue privado multiusuario y exportación. Esa escala no aplica aquí.

## Decisión

| Aspecto | Decisión | Requisito original |
|---|---|---|
| Framework | Haystack 2.31.0, pipelines de indexación y consulta | RS-001 (se mantiene) |
| Almacén vectorial | Qdrant en modo local embebido (`data/qdrant/`), sin servidor ni Docker | RS-002 (cumple: autoalojado) |
| Embeddings | Ollama con `bge-m3` (multilingüe, 1024 dimensiones) | RS-005 (cumple: local) |
| LLM | Ollama con `qwen2.5:7b` (el 3B se contradecía en 2 de 30 casos) | RS-005 (cumple: local) |
| Formatos | PDF, DOCX, TXT, MD, HTML | DI-003 (ampliado a todos los textos) |
| Fragmentación | 180 palabras con 30 de solape | RF-004 (se usa palabras en lugar de tokens) |
| Recuperación | Top-5 por similitud coseno | RF-006 (k=5 en lugar de k=8) |
| Respuesta sin evidencia | Se detecta por expresiones de negativa ("no hay información", "no se menciona", etc.) | RF-007 (heurística, no comparación con una frase fija) |
| Citas | Archivo y fragmento. Se marca como citado el fragmento que el modelo referencia con `[n]` o, si no lo hace, el que más palabras comparte con la respuesta | DI-006 (versión y artículo se omiten) |
| Interfaz | Línea de comandos: `indexar`, `preguntar`, `evaluar` | HU-004 a HU-010 (se omiten UI, exportación y auditoría) |
| Versiones de normas | No se gestionan | RF-012 (fuera de alcance) |
| Autenticación, roles, registro de auditoría | No se implementan | RF-011, RNF-003 multiusuario, HU-009 (fuera de alcance) |

## Por qué

- **Un solo runtime local (Ollama) para generar y para embeber** reduce la instalación a un programa y dos modelos.
- **Qdrant embebido** no necesita contenedor y guarda el índice en una carpeta. Conserva filtros por metadatos si más adelante hacen falta.
- **Haystack** se mantiene porque es un requisito del proyecto y ofrece componentes de conversión y división ya probados.

## Consecuencias

- Todo se ejecuta en el equipo del usuario. Ningún documento sale de la máquina (RNF-007 se cumple por diseño).
- La calidad de las respuestas depende del modelo. El cambio de modelo es una línea de configuración (`MODELO_LLM` en `motor.py`).
- El modelo 7B tarda más por respuesta. En una consulta medida de extremo a extremo tardó unos 7,5 s, dentro del umbral de RNF-002.
- La detección de "Sin evidencia" y la cita por solapamiento son heurísticas. Son transparentes y comprobables, pero no equivalen a una verificación semántica.
- `deploy/docker-compose.yml` ya no es necesario. Queda como opción si más adelante se quiere un servidor.
- El corpus dorado (`corpus/dorado/`) lo preparó el equipo técnico con documentos ficticios. Mide que el pipeline funciona, no la exactitud jurídica de una norma real.

## Alternativas descartadas

- **pgvector:** requiere PostgreSQL en ejecución. Más piezas para el mismo resultado en uso personal.
- **Un LLM en la nube:** rompe RNF-007 y el objetivo de mantener los documentos en local.
- **Haystack 3.x:** la especificación fija 2.x (RS-001).
