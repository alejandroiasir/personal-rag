"""Genera la guía didáctica en Word (.docx) a partir de los diagramas en img/.

Requiere los PNG: primero ejecuta generar_diagramas.py.
    .venv/bin/python docs/guia-didactica/generar_guia.py
"""

from pathlib import Path

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

CARPETA = Path(__file__).parent
IMG = CARPETA / "img"
SALIDA = CARPETA / "guia-rag-personal.docx"
AZUL_TITULO = RGBColor(0x1D, 0x4F, 0x86)


# ---------- utilidades de formato ----------

def _sombrear(celda_xml, color: str) -> None:
    """Pone color de fondo a una celda (su elemento XML w:tc)."""
    propiedades = celda_xml.get_or_add_tcPr()
    sombra = OxmlElement("w:shd")
    sombra.set(qn("w:val"), "clear")
    sombra.set(qn("w:color"), "auto")
    sombra.set(qn("w:fill"), color)
    propiedades.append(sombra)


def _texto_con_negritas(parrafo, texto: str) -> None:
    """Escribe texto: lo que va entre ** ** queda en negrita y entre ` ` en monoespaciado."""
    for indice_codigo, trozo_codigo in enumerate(texto.split("`")):
        for indice_negrita, trozo in enumerate(trozo_codigo.split("**")):
            if trozo:
                ejecucion = parrafo.add_run(trozo)
                ejecucion.bold = indice_negrita % 2 == 1
                if indice_codigo % 2 == 1:
                    ejecucion.font.name = "Consolas"
                    ejecucion.font.size = Pt(10.5)


def titulo(doc, texto: str, nivel: int = 1) -> None:
    encabezado = doc.add_heading(texto, level=nivel)
    encabezado.paragraph_format.space_before = Pt(18 if nivel == 1 else 12)


def parrafo(doc, texto: str) -> None:
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(8)
    _texto_con_negritas(p, texto)


def lista(doc, elementos: list[str]) -> None:
    for elemento in elementos:
        p = doc.add_paragraph(style="List Bullet")
        p.paragraph_format.space_after = Pt(3)
        _texto_con_negritas(p, elemento)


def pasos(doc, elementos: list[str]) -> None:
    """Pasos numerados escritos a mano, para que cada lista empiece en 1."""
    for numero, elemento in enumerate(elementos, start=1):
        p = doc.add_paragraph()
        p.paragraph_format.left_indent = Cm(0.8)
        p.paragraph_format.first_line_indent = Cm(-0.6)
        p.paragraph_format.space_after = Pt(3)
        _texto_con_negritas(p, f"{numero}. {elemento}")


def codigo(doc, texto: str) -> None:
    """Bloque de comando o código con fondo gris y letra monoespaciada."""
    tabla_codigo = doc.add_table(rows=1, cols=1)
    tabla_codigo.style = "Table Grid"
    tabla_codigo.alignment = WD_TABLE_ALIGNMENT.CENTER
    celda = tabla_codigo.rows[0].cells[0]
    _sombrear(celda._tc, "F3F4F6")
    for indice, linea in enumerate(texto.strip("\n").split("\n")):
        p = celda.paragraphs[0] if indice == 0 else celda.add_paragraph()
        p.paragraph_format.space_after = Pt(0)
        ejecucion = p.add_run(linea)
        ejecucion.font.name = "Consolas"
        ejecucion.font.size = Pt(9.5)
    doc.add_paragraph().paragraph_format.space_after = Pt(2)


def caja(doc, etiqueta: str, texto: str, color: str) -> None:
    """Recuadro de color para ejercicios, consejos o avisos."""
    tabla = doc.add_table(rows=1, cols=1)
    tabla.style = "Table Grid"
    tabla.alignment = WD_TABLE_ALIGNMENT.CENTER
    celda = tabla.rows[0].cells[0]
    _sombrear(celda._tc, color)
    primer = celda.paragraphs[0]
    _texto_con_negritas(primer, f"**{etiqueta}** {texto}")
    doc.add_paragraph().paragraph_format.space_after = Pt(2)


def ejercicio(doc, texto: str) -> None:
    caja(doc, "Ejercicio:", texto, "FEF3C7")


def aviso(doc, texto: str) -> None:
    caja(doc, "Ojo:", texto, "FEE2E2")


def consejo(doc, texto: str) -> None:
    caja(doc, "Idea clave:", texto, "DCFCE7")


def tabla(doc, cabecera: list[str], filas: list[list[str]]) -> None:
    grid = doc.add_table(rows=1, cols=len(cabecera))
    grid.style = "Table Grid"
    grid.alignment = WD_TABLE_ALIGNMENT.CENTER
    for celda, texto in zip(grid.rows[0].cells, cabecera):
        celda.paragraphs[0].add_run(texto).bold = True
        _sombrear(celda._tc, "DBEAFE")
    for fila in filas:
        celdas = grid.add_row().cells
        for celda, texto in zip(celdas, fila):
            _texto_con_negritas(celda.paragraphs[0], texto)
    doc.add_paragraph().paragraph_format.space_after = Pt(2)


def figura(doc, nombre: str, pie: str) -> None:
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.keep_with_next = True
    p.add_run().add_picture(str(IMG / f"{nombre}.png"), width=Cm(15.5))
    descripcion = doc.add_paragraph()
    descripcion.alignment = WD_ALIGN_PARAGRAPH.CENTER
    marca = descripcion.add_run(pie)
    marca.italic = True
    marca.font.size = Pt(9)


CIERRES = {
    0: (
        ["Pensar que el modelo ya conoce tus documentos.",
         "Creer que una respuesta es correcta sin mirar la cita."],
        ["¿Por qué un RAG es más fiable que preguntar a un chat sin documentos?",
         "¿Qué pasaría si el sistema respondiera sin buscar antes?"],
    ),
    1: (
        ["Ejecutar `rag` sin el prefijo `.venv/bin/`.",
         "Instalar librerías fuera del entorno virtual."],
        ["¿Para qué sirve el entorno virtual?",
         "¿Qué carpeta contiene los programas del proyecto?"],
    ),
    2: (
        ["Esperar que dos frases distintas tengan similitud 1.",
         "Confundir la similitud (de 0 a 1) con un porcentaje de acierto."],
        ["¿Qué significa una similitud cercana a 0?",
         "¿Por qué dos frases con sinónimos pueden tener una similitud alta?"],
    ),
    3: (
        ["Fragmentos demasiado grandes: la búsqueda pierde precisión.",
         "Quitar el solape para ahorrar espacio: se pierden frases en las fronteras."],
        ["¿Por qué un fragmento de 180 palabras suele ser mejor que uno de 2.000?",
         "¿Qué problema evita el solape?"],
    ),
    4: (
        ["Creer que Qdrant es un servidor que hay que instalar.",
         "Abrir dos procesos sobre la misma carpeta `data/qdrant`."],
        ["¿Dónde se guarda el índice en modo local?",
         "¿Qué tiene que ver el número 1024 con el modelo de embeddings?"],
    ),
    5: (
        ["Olvidar reindexar cuando el documento cambia.",
         "Indexar un PDF escaneado y esperar que tenga texto."],
        ["¿Qué pasa si indexas dos veces el mismo archivo?",
         "¿Qué formatos admite el sistema?"],
    ),
    6: (
        ["Pensar que el modelo busca en internet.",
         "Confundir la búsqueda (Qdrant) con la redacción (el modelo)."],
        ["¿Qué pasos ocurren antes de que el modelo escriba la respuesta?",
         "¿Por qué la pregunta también se convierte en vector?"],
    ),
    7: (
        ["Creer que una cita [n] garantiza que la respuesta es correcta.",
         "Ignorar la abstención: «no lo sé» también es una respuesta válida."],
        ["¿Qué hace el sistema si el modelo no cita nada?",
         "¿Por qué el sistema debe abstenerse cuando no hay evidencia?"],
    ),
    8: (
        ["Confundir el navegador con el servidor.",
         "Olvidar que la web no tiene contraseña y solo escucha en 127.0.0.1."],
        ["¿Qué ruta se usa para hacer una pregunta?",
         "¿Por qué el servidor solo escucha en 127.0.0.1?"],
    ),
    9: (
        ["Medir con las mismas preguntas con las que se ajustó el sistema.",
         "Interpretar la evaluación como una validación jurídica."],
        ["¿Qué diferencia hay entre una pregunta respondible y una que no lo es?",
         "¿Qué significa que el documento correcto esté en primer lugar?"],
    ),
    10: (
        ["Subir documentos sensibles sin revisar dónde quedan las copias.",
         "Olvidar que la Papelera y las copias de seguridad conservan archivos."],
        ["¿Qué datos quedan guardados dentro de `data/`?",
         "¿Qué medidas reducen el riesgo de que alguien use la página sin permiso?"],
    ),
}


def cierre(doc, numero: int) -> None:
    """Cierra un bloque con errores frecuentes y preguntas de repaso."""
    errores, preguntas = CIERRES[numero]
    titulo(doc, "Errores frecuentes", nivel=2)
    lista(doc, errores)
    titulo(doc, "Preguntas de repaso", nivel=2)
    pasos(doc, preguntas)


def bloque(doc, numero: int, nombre: str, imagen: str, pie: str, introduccion: str) -> None:
    """Cabecera de cada mini bloque: título, visual al inicio y una frase de entrada."""
    if numero > 0:
        cierre(doc, numero - 1)
    encabezado = doc.add_heading(f"Bloque {numero}. {nombre}", level=1)
    encabezado.paragraph_format.page_break_before = True
    figura(doc, imagen, pie)
    parrafo(doc, introduccion)


# ---------- contenido ----------

def portada(doc) -> None:
    for _ in range(6):
        doc.add_paragraph()
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    marca = p.add_run("Cómo funciona un RAG personal")
    marca.bold = True
    marca.font.size = Pt(28)
    marca.font.color.rgb = AZUL_TITULO
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    subtitulo = p.add_run("Guía didáctica paso a paso para alumnos de nivel básico")
    subtitulo.font.size = Pt(14)
    doc.add_paragraph()
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.add_run("Octubre de 2026").font.size = Pt(11)


def introduccion(doc) -> None:
    doc.add_page_break()
    titulo(doc, "Cómo usar esta guía")
    parrafo(doc, "Esta guía explica, con un lenguaje sencillo, cómo funciona un sistema que responde preguntas "
                 "sobre tus propios documentos. Lo construiremos por partes, de lo más simple a lo más complejo.")
    parrafo(doc, "Cada bloque sigue el mismo orden: primero una **imagen** que resume la idea, después la "
                 "explicación, los pasos a seguir y, al final, un **ejercicio**. No hace falta saber programar "
                 "para seguirla: solo tienes que copiar los comandos en la terminal.")
    consejo(doc, "Lee un bloque entero antes de escribir ningún comando. Así sabrás qué estás haciendo y por qué.")
    titulo(doc, "Mapa de la guía", nivel=2)
    tabla(doc, ["Bloque", "Tema", "Qué aprendes"], [
        ["0", "Qué es un RAG", "La idea general en tres pasos"],
        ["1", "Lo básico", "Carpetas, Python y el entorno virtual"],
        ["2", "Texto a números", "Qué es un embedding y cómo se compara"],
        ["3", "Trocear documentos", "Por qué se parten en fragmentos"],
        ["4", "Guardar vectores", "La base de datos Qdrant"],
        ["5", "Indexar", "Cómo entra un documento al sistema"],
        ["6", "Buscar y responder", "El camino de una pregunta hasta la respuesta"],
        ["7", "Citas y 'no lo sé'", "Cómo se comprueba la respuesta"],
        ["8", "La web con FastAPI", "La página para subir documentos y preguntar"],
        ["9", "Medir la calidad", "Cómo saber si el sistema acierta"],
        ["10", "Privacidad", "Qué sale de tu equipo y qué no"],
        ["A-C", "Anexos", "Comandos, glosario y problemas comunes"],
    ])


def contenido(doc) -> None:
    bloque(doc, 0, "¿Qué es un RAG?", "00_idea", "Figura 0. Pregunta, búsqueda y respuesta.",
           "RAG son las siglas de **Retrieval-Augmented Generation**, que en español significa "
           "«generación aumentada con recuperación». Suena complicado, pero la idea es sencilla.")
    titulo(doc, "La idea con una comparación", nivel=2)
    parrafo(doc, "Imagina una biblioteca. Si alguien te pregunta algo concreto, un buen bibliotecario no responde "
                 "de memoria. Primero busca el libro adecuado, lee la página que contiene la respuesta y luego te "
                 "la explica, indicando de qué página la ha sacado.")
    parrafo(doc, "Un RAG hace exactamente eso con tus documentos: **busca** los fragmentos relevantes, "
                 "**lee** esos fragmentos y **responde** citando de dónde viene cada dato.")
    titulo(doc, "Los tres pasos", nivel=2)
    pasos(doc, [
        "**Buscar:** el sistema localiza los fragmentos de tus documentos que tienen relación con la pregunta.",
        "**Leer:** esos fragmentos se entregan a un modelo de lenguaje junto con la pregunta.",
        "**Responder:** el modelo redacta una respuesta basada solo en esos fragmentos, con citas.",
    ])
    titulo(doc, "¿Por qué no basta con un chat normal?", nivel=2)
    lista(doc, [
        "Un chat normal **no conoce tus documentos privados**: no los ha leído.",
        "Sin apoyo en fuentes, el modelo **puede inventar** una respuesta que suena bien.",
        "Con un RAG, cada respuesta **puede comprobarse** volviendo al fragmento original.",
        "Todo se ejecuta **en tu equipo**, así que tus documentos no se envían a internet.",
    ])
    ejercicio(doc, "Explica con tus palabras, en dos frases, qué hace cada uno de los tres pasos. "
                   "Compara tu explicación con la del bibliotecario.")

    bloque(doc, 1, "Lo básico: carpetas, Python y entorno virtual", "01_carpetas",
           "Figura 1. Las carpetas principales del proyecto.",
           "Antes de tocar el sistema conviene entender cómo está organizado el proyecto. Piensa en una caja "
           "de herramientas: cada cajón tiene una función.")
    titulo(doc, "Las carpetas del proyecto", nivel=2)
    lista(doc, [
        "**corpus/documentos/**: los archivos de ejemplo que usamos para probar el sistema.",
        "**src/rag_normativo/**: el código fuente, escrito en Python.",
        "**data/**: el índice y las copias de los documentos. Se crea sola al usar el sistema.",
        "**.venv/**: los programas que el proyecto necesita, guardados en un espacio aislado.",
    ])
    titulo(doc, "¿Qué es un entorno virtual?", nivel=2)
    parrafo(doc, "Un **entorno virtual** es como un cajón aislado para un proyecto. Así, las librerías de este "
                 "proyecto no se mezclan con las de otros proyectos de tu equipo. La carpeta se llama `.venv`.")
    titulo(doc, "Pasos de instalación", nivel=2)
    pasos(doc, [
        "Abre la terminal y sitúate en la carpeta del proyecto.",
        "Crea el entorno virtual:",
    ])
    codigo(doc, "python3 -m venv .venv")
    pasos(doc, ["Instala el proyecto dentro de ese entorno:"])
    codigo(doc, '.venv/bin/python -m pip install -e ".[dev]"')
    aviso(doc, "Tienes que usar `.venv/bin/...` para ejecutar los programas del proyecto. Si usas solo `python` "
               "o `rag`, puede que la terminal no encuentre el programa correcto.")
    ejercicio(doc, "Abre la carpeta del proyecto en el Finder y localiza las cuatro carpetas de la figura. "
                   "¿Qué archivos hay dentro de `corpus/documentos/`?")

    bloque(doc, 2, "Texto a números: los embeddings", "02_vectores",
           "Figura 2. Frases parecidas quedan cerca en el dibujo.",
           "Un ordenador no entiende el significado de las palabras. Para poder compararlas, las convierte en "
           "números. A esa lista de números se le llama **embedding** o **vector**.")
    titulo(doc, "¿Qué es un vector?", nivel=2)
    parrafo(doc, "Un vector es una lista de números. En este proyecto, cada fragmento de texto se convierte "
                 "en una lista de **1024 números** con el modelo `bge-m3`. Cada número aporta una pequeña pista "
                 "sobre el significado del texto.")
    titulo(doc, "¿Cómo se comparan dos vectores?", nivel=2)
    parrafo(doc, "Se usa la **similitud coseno**. Devuelve un número entre 0 y 1:")
    lista(doc, [
        "**Cerca de 1:** las frases tienen un sentido muy parecido.",
        "**Cerca de 0:** las frases no tienen relación.",
    ])
    parrafo(doc, "En nuestra prueba, «avisar del incidente» y «reportar la incidencia» dieron una similitud "
                 "alrededor de 0,74. En cambio, «receta de cocina» quedó cerca de 0,42 frente a ellas.")
    titulo(doc, "Pruébalo tú", nivel=2)
    codigo(doc, '.venv/bin/python scripts/demo_embeddings.py texto "avisar del incidente" '
                '"reportar la incidencia" "receta de cocina"')
    parrafo(doc, "La terminal muestra los primeros valores de cada vector, su longitud y una tabla de similitudes.")
    ejercicio(doc, "Ejecuta el comando con tres frases propias: dos parecidas y una distinta. "
                   "¿Qué similitud obtienes entre las parecidas?")

    bloque(doc, 3, "Trocear documentos en fragmentos", "03_trocear",
           "Figura 3. Un documento se parte en fragmentos que se solapan.",
           "Un documento de cien páginas es demasiado grande para buscar en él de una sola vez. Por eso se "
           "trocea en **fragmentos** más pequeños.")
    titulo(doc, "¿Por qué trocear?", nivel=2)
    lista(doc, [
        "Un fragmento pequeño habla de **una idea concreta**, así la búsqueda es más precisa.",
        "Solo se envían al modelo los fragmentos **relevantes**, no el documento entero.",
    ])
    titulo(doc, "Los dos parámetros", nivel=2)
    tabla(doc, ["Parámetro", "Valor", "Para qué sirve"], [
        ["Tamaño del fragmento", "180 palabras", "Cada fragmento tiene una idea completa y manejable."],
        ["Solape", "30 palabras", "Las palabras repetidas entre fragmentos evitan cortar una idea a la mitad."],
    ])
    parrafo(doc, "En el código, estos valores aparecen en `src/rag_normativo/motor.py` como `TAMANO_FRAGMENTO = 180` "
                 "y `SOLAPE_FRAGMENTO = 30`. Esto se traduce en la siguiente configuración:")
    codigo(doc, 'DocumentSplitter(split_by="word", split_length=180, split_overlap=30)')
    consejo(doc, "El solape es una red de seguridad: si una frase importante queda justo en la frontera, "
                 "aparece completa en algún fragmento.")
    ejercicio(doc, "Copia un párrafo de cualquier texto y cuenta sus palabras. ¿Cuántos fragmentos de 180 "
                   "palabras saldrían de un texto de 500 palabras?")

    bloque(doc, 4, "Guardar los vectores en Qdrant", "04_tabla",
           "Figura 4. Cada fragmento se guarda junto a su vector.",
           "Ya tenemos fragmentos y vectores. Ahora hay que guardarlos en un sitio donde se puedan buscar "
           "rápidamente por similitud. Ese sitio es una **base de datos vectorial**.")
    titulo(doc, "¿Qué es Qdrant?", nivel=2)
    parrafo(doc, "Qdrant es una base de datos especializada en vectores. Cuando haces una pregunta, busca "
                 "qué vectores guardados se parecen más al de la pregunta.")
    titulo(doc, "Modo local: sin servidor", nivel=2)
    parrafo(doc, "En este proyecto usamos Qdrant **en modo local**. Todo se guarda en la carpeta `data/qdrant`, "
                 "sin instalar ningún servidor ni contenedor.")
    codigo(doc, 'QdrantDocumentStore(path="data/qdrant", index="documentos", embedding_dim=1024)')
    aviso(doc, "El modo local solo admite **un proceso a la vez**. Si el servidor web está abierto, no ejecutes "
               "`evaluar` ni otros comandos sobre el mismo índice. Para la evaluación, para el servidor antes.")
    ejercicio(doc, "Ejecuta `ls data/` (en Mac o Linux) y busca la carpeta `qdrant`. Si todavía no existe, vuelve "
                   "a este ejercicio después del bloque 5.")

    bloque(doc, 5, "Indexar: de un archivo a vectores guardados", "05_indexar",
           "Figura 5. Los cuatro pasos de la indexación.",
           "**Indexar** significa preparar un documento para poder buscarlo. Es un proceso que se hace una vez "
           "por documento (y de nuevo si el documento cambia).")
    titulo(doc, "Los cuatro pasos", nivel=2)
    pasos(doc, [
        "**Convertir a texto.** Cada tipo de archivo tiene su lector: PDF, DOCX, TXT, MD o HTML.",
        "**Trocear.** El texto se parte en fragmentos de 180 palabras, como vimos en el bloque 3.",
        "**Crear vectores.** Cada fragmento se convierte en 1024 números con el modelo de embeddings.",
        "**Guardar.** Fragmento, vector y datos del archivo se escriben en Qdrant.",
    ])
    titulo(doc, "Ejecutarlo", nivel=2)
    codigo(doc, ".venv/bin/rag indexar corpus/documentos")
    parrafo(doc, "Si vuelves a indexar un archivo, **su versión anterior se reemplaza**. Así no quedan datos viejos "
                 "mezclados con los nuevos.")
    aviso(doc, "Un PDF escaneado (una foto de una página) no tiene texto que leer, y el sistema lo rechaza. "
               "Para estos casos haría falta un paso de reconocimiento de texto (OCR), que este proyecto no incluye.")
    ejercicio(doc, "Indexa la carpeta de ejemplo y revisa qué muestra el comando al terminar. Después, comprueba "
                   "que aparece la carpeta `data/qdrant`.")

    bloque(doc, 6, "Buscar y responder", "06_responder",
           "Figura 6. El camino de una pregunta hasta la respuesta.",
           "Ahora viene la parte que el usuario ve: escribes una pregunta y recibes una respuesta. Por dentro, "
           "el sistema sigue seis pasos.")
    titulo(doc, "Paso a paso", nivel=2)
    pasos(doc, [
        "**Pregunta:** escribes una frase en lenguaje natural.",
        "**Vector de la pregunta:** tu pregunta se convierte en vector con el mismo modelo que los fragmentos.",
        "**Buscar los 5 más parecidos:** Qdrant devuelve los cinco fragmentos más cercanos (en el código, `TOP_K = 5`).",
        "**Armar el prompt:** se escribe una instrucción para el modelo con esos fragmentos numerados.",
        "**El modelo escribe:** el modelo `qwen2.5:7b`, en modo local, redacta la respuesta.",
        "**Respuesta y fuentes:** recibes la respuesta junto con los fragmentos usados.",
    ])
    titulo(doc, "¿Qué es Haystack?", nivel=2)
    parrafo(doc, "**Haystack** es una biblioteca de Python que sirve para unir estos pasos como si fueran piezas "
                 "de un circuito. Cada pieza hace una tarea y pasa el resultado a la siguiente. Así el proyecto "
                 "queda ordenado y es fácil cambiar una pieza sin tocar las demás.")
    titulo(doc, "Lo que pide el prompt", nivel=2)
    parrafo(doc, "El prompt ordena al modelo que responda en **una o dos frases**, que use solo los fragmentos "
                 "y que cite con [n]. Además, le indica que diga «No encuentro esa información en los documentos» "
                 "si la respuesta no está. Como la temperatura del modelo está en 0, las respuestas son repetibles.")
    codigo(doc, '.venv/bin/rag preguntar "¿Cuántos días por semana puede aplicarse el teletrabajo?"')
    ejercicio(doc, "Haz una pregunta cuya respuesta esté en un documento de `corpus/documentos/`. Después haz la "
                   "misma pregunta con otras palabras. ¿La respuesta cambia?")

    bloque(doc, 7, "Citas y el «no lo sé»", "07_citas",
           "Figura 7. Una respuesta con cita, o una respuesta de abstención.",
           "Una respuesta sin fuentes es difícil de creer. Por eso el sistema intenta **citar** el fragmento en el "
           "que se basa y, si no encuentra nada, **se abstiene**.")
    titulo(doc, "Las citas [n]", nivel=2)
    parrafo(doc, "Cada fragmento lleva un número. Cuando el modelo usa uno, lo indica con su número, por ejemplo "
                 "[1]. Si el modelo no cita nada, el sistema usa un respaldo: elige el fragmento que más palabras "
                 "comparte con la respuesta. Las palabras de 4 letras o más se comparan por sus primeros cinco "
                 "caracteres, y los números se conservan.")
    titulo(doc, "Cuando no hay respuesta", nivel=2)
    parrafo(doc, "El sistema busca frases típicas de «no lo sé», como «no encuentro» o «no se menciona». Si las "
                 "encuentra, responde que no hay información en los documentos en lugar de inventar.")
    consejo(doc, "Estas comprobaciones son **heurísticas**: funcionan bien en la mayoría de casos, pero no son "
                 "una garantía. Siempre conviene leer el fragmento citado.")
    ejercicio(doc, "Pregunta algo que **no** esté en los documentos (por ejemplo, «¿Cuál es la capital de Francia?»). "
                   "¿El sistema se abstiene? Repítelo con una pregunta que sí tenga respuesta.")

    bloque(doc, 8, "La web con FastAPI", "08_web",
           "Figura 8. El navegador habla con un servidor local, que a su vez usa el motor RAG.",
           "Hasta ahora usábamos la terminal. Para que cualquiera pueda usar el sistema, hemos añadido una **página "
           "web**. Esa página se comunica con el código a través de una **API**, que se construye con **FastAPI**.")
    titulo(doc, "Conceptos básicos", nivel=2)
    lista(doc, [
        "**Servidor:** programa que espera peticiones y responde. Aquí es FastAPI.",
        "**Cliente:** quien hace la petición. Aquí es tu navegador.",
        "**API:** el conjunto de direcciones (rutas) por las que el cliente puede pedir cosas al servidor.",
        "**Ruta:** una dirección concreta, como `/api/preguntar`, que hace una tarea.",
    ])
    titulo(doc, "Las rutas del proyecto", nivel=2)
    tabla(doc, ["Método y ruta", "Qué hace"], [
        ["GET /", "Muestra la página web."],
        ["GET /api/documentos", "Lista los documentos indexados."],
        ["POST /api/documentos", "Sube y reindexa uno o varios archivos."],
        ["DELETE /api/documentos/{nombre}", "Quita un documento del índice."],
        ["POST /api/preguntar", "Recibe una pregunta y devuelve la respuesta con fuentes."],
    ])
    titulo(doc, "Ejemplo de ruta", nivel=2)
    parrafo(doc, "Así se declara la ruta de preguntas en `src/rag_normativo/web.py`, de forma simplificada:")
    codigo(doc, '@app.post("/api/preguntar")\nasync def preguntar(entrada: Pregunta) -> dict:\n'
                '    return responder(entrada.pregunta)')
    titulo(doc, "Arrancar el servidor", nivel=2)
    codigo(doc, ".venv/bin/rag servir")
    parrafo(doc, "Cuando aparezca el mensaje con la dirección, abre **http://localhost:8000** en el navegador. "
                 "Para parar el servidor, pulsa Ctrl+C en esa terminal.")
    aviso(doc, "El servidor escucha solo en 127.0.0.1, es decir, en tu propio equipo. Otros ordenadores de la red "
               "no pueden entrar. Además, la página **no tiene contraseña**: cualquiera con acceso a tu Mac podría "
               "usarla.")
    ejercicio(doc, "Arranca el servidor, sube un archivo de `corpus/documentos/` y haz una pregunta desde la página. "
                   "Compara la respuesta con la que obtuviste en el bloque 6.")

    bloque(doc, 9, "Medir la calidad", "09_medir",
           "Figura 9. Preguntas con respuesta conocida y las cuatro comprobaciones.",
           "Un sistema que responde no siempre responde bien. Para saberlo, hay que **medirlo** con preguntas cuya "
           "respuesta ya conocemos. Esa lista de preguntas se llama **corpus dorado**.")
    titulo(doc, "El corpus dorado", nivel=2)
    parrafo(doc, "El proyecto incluye 30 preguntas en `corpus/dorado/preguntas.jsonl`: 24 tienen respuesta en los "
                 "documentos y 6 no la tienen. Cada pregunta indica qué documento debería encontrarse y qué frase "
                 "debe aparecer en la respuesta.")
    titulo(doc, "Los distractores", nivel=2)
    parrafo(doc, "Los **distractores** son documentos parecidos que pueden confundir al sistema, como versiones "
                 "antiguas o borradores. Si el sistema acierta incluso con ellos, es más fiable. En nuestras pruebas, "
                 "el documento correcto quedó en primer lugar en 23 de 24 casos sin distractores, y en 13 de 24 con ellos.")
    titulo(doc, "Ejecutar la evaluación", nivel=2)
    pasos(doc, [
        "Para el servidor web si lo tienes abierto (Ctrl+C).",
        "Ejecuta:",
    ])
    codigo(doc, ".venv/bin/rag evaluar")
    parrafo(doc, "El resultado completo queda en `data/evaluacion.json`.")
    aviso(doc, "Las preguntas y los documentos son **ficticios** y las respuestas las preparamos nosotros. La evaluación "
               "mide que el sistema funciona, pero no que una respuesta jurídica o médica sea correcta.")
    ejercicio(doc, "Añade una pregunta nueva al archivo `corpus/dorado/preguntas.jsonl` con sus campos `id`, "
                   "`pregunta`, `respuesta_clave`, `documento` y `respondible`. Vuelve a evaluar.")

    bloque(doc, 10, "Privacidad: qué sale de tu equipo", "10_privacidad",
           "Figura 10. Todo ocurre dentro del equipo.",
           "Como los documentos pueden ser confidenciales, conviene saber con exactitud **dónde viven los datos** "
           "y qué riesgos tiene el sistema.")
    titulo(doc, "Lo que está bien", nivel=2)
    lista(doc, [
        "Los modelos (Ollama), el índice (Qdrant) y los documentos se quedan en tu equipo.",
        "El servidor solo escucha en 127.0.0.1, así que otros equipos de la red no llegan.",
        "La carpeta `data/` está excluida en `.gitignore`, así que git no la subiría por accidente.",
    ])
    titulo(doc, "Los riesgos a revisar", nivel=2)
    lista(doc, [
        "**Sin contraseña:** cualquier persona o programa con acceso a tu Mac puede usar la página.",
        "**Copias duplicadas:** los archivos subidos quedan en `data/subidos/` y el índice guarda el texto de los fragmentos.",
        "**Copias de seguridad:** la Papelera o Time Machine pueden conservar archivos que ya borraste.",
        "**Sincronización en la nube:** si la carpeta del proyecto está dentro de un directorio sincronizado con iCloud, `data/` podría subirse.",
    ])
    ejercicio(doc, "Haz una lista de tus documentos y decide cuáles son aptos para indexar. Anota también dónde "
                   "quieres guardar las copias y cuándo vas a borrar la carpeta `data/`.")
    cierre(doc, 10)


def anexos(doc) -> None:
    doc.add_page_break()
    titulo(doc, "Anexo A. Comandos resumidos")
    tabla(doc, ["Acción", "Comando"], [
        ["Crear el entorno virtual", "python3 -m venv .venv"],
        ["Instalar el proyecto", '.venv/bin/python -m pip install -e ".[dev]"'],
        ["Indexar una carpeta", ".venv/bin/rag indexar corpus/documentos"],
        ["Hacer una pregunta", '.venv/bin/rag preguntar "tu pregunta"'],
        ["Evaluar con el corpus dorado", ".venv/bin/rag evaluar"],
        ["Arrancar la web", ".venv/bin/rag servir"],
        ["Ver embeddings", '.venv/bin/python scripts/demo_embeddings.py texto "frase 1" "frase 2"'],
        ["Ejecutar las pruebas", ".venv/bin/python -m pytest -q"],
    ])
    parrafo(doc, "Antes de usarlo, hay que descargar los modelos en Ollama:")
    codigo(doc, "ollama pull qwen2.5:7b\nollama pull bge-m3")

    titulo(doc, "Anexo B. Glosario")
    tabla(doc, ["Término", "Significado sencillo"], [
        ["RAG", "Buscar en tus documentos y responder con lo encontrado."],
        ["Embedding o vector", "Lista de números que representa el significado de un texto."],
        ["Similitud coseno", "Medida de cuánto se parecen dos vectores (de 0 a 1)."],
        ["Fragmento (chunk)", "Trozo de un documento, de unas 180 palabras."],
        ["Solape", "Palabras repetidas entre dos fragmentos seguidos."],
        ["Base vectorial", "Base de datos que busca por similitud de vectores."],
        ["Pipeline", "Cadena de pasos en la que la salida de uno es la entrada del siguiente."],
        ["Prompt", "Instrucción escrita que recibe el modelo, junto con los datos."],
        ["API", "Conjunto de rutas por las que un programa pide cosas a otro."],
        ["Entorno virtual", "Espacio aislado con las librerías de un único proyecto."],
        ["Corpus dorado", "Preguntas con respuesta conocida para medir el sistema."],
        ["Distractor", "Documento parecido que puede confundir al sistema."],
    ])

    titulo(doc, "Anexo C. Problemas comunes")
    tabla(doc, ["Síntoma", "Causa probable y solución"], [
        ["'rag: command not found' o no existe .venv/bin/rag",
         "Falta instalar el proyecto en el entorno virtual: ejecuta de nuevo `pip install -e \".[dev]\"`."],
        ["Error 503 al preguntar", "Ollama no está en marcha. Abre la app de Ollama y vuelve a intentarlo."],
        ["Error de bloqueo al evaluar o indexar", "El servidor web está abierto y usa el índice. Páralo con Ctrl+C."],
        ["Mensaje de archivo sin texto al indexar", "Suele ser un PDF escaneado. Usa una versión con texto seleccionable."],
        ["Formato no soportado", "Solo se admiten PDF, DOCX, TXT, MD y HTML."],
        ["La respuesta cita un fragmento que no encaja", "Es una heurística: revisa siempre el fragmento y reformula la pregunta."],
    ])


def main() -> None:
    doc = Document()
    doc.core_properties.author = "Proyecto RAG personal"
    doc.core_properties.title = "Cómo funciona un RAG personal"
    estilo = doc.styles["Normal"]
    estilo.font.name = "Calibri"
    estilo.font.size = Pt(12)
    estilo.paragraph_format.line_spacing = 1.25
    for seccion in doc.sections:
        seccion.page_height = Cm(29.7)
        seccion.page_width = Cm(21.0)
        seccion.left_margin = seccion.right_margin = Cm(2.2)
        seccion.top_margin = seccion.bottom_margin = Cm(2.2)
        seccion.footer.paragraphs[0].text = "Guía didáctica · RAG personal"
        seccion.footer.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER

    portada(doc)
    introduccion(doc)
    contenido(doc)
    anexos(doc)
    doc.save(SALIDA)
    print(f"guardado {SALIDA}")


if __name__ == "__main__":
    main()
