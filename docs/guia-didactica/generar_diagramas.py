"""Genera los diagramas de la guía didáctica como PNG.

Dibuja cada diagrama como SVG y lo convierte a PNG con LibreOffice (sin dependencias de Python).
    .venv/bin/python docs/guia-didactica/generar_diagramas.py
"""

import subprocess
import tempfile
from pathlib import Path
from xml.sax.saxutils import escape

CARPETA_IMG = Path(__file__).parent / "img"
SOFFICE = "/opt/homebrew/bin/soffice"

AZUL = ("#dbeafe", "#2b6cb0")
VERDE = ("#dcfce7", "#15803d")
AMBAR = ("#fef3c7", "#b45309")
GRIS = ("#f3f4f6", "#6b7280")
ROJO = ("#fee2e2", "#b42318")
FUENTE = 'font-family="Helvetica, Arial, sans-serif"'


class Lienzo:
    def __init__(self, ancho: int, alto: int):
        self.ancho = ancho
        self.alto = alto
        self.partes: list[str] = []

    def caja(self, x, y, w, h, lineas, colores=AZUL, tam=17, punteada=False):
        fondo, borde = colores
        trazo = ' stroke-dasharray="8 6"' if punteada else ""
        self.partes.append(
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="12" fill="{fondo}" '
            f'stroke="{borde}" stroke-width="2"{trazo}/>'
        )
        n = len(lineas)
        for i, linea in enumerate(lineas):
            ty = y + h / 2 + (i - (n - 1) / 2) * (tam + 6) + tam / 3
            self.texto(x + w / 2, ty, linea, tam=tam, anclaje="middle")

    def texto(self, x, y, linea, tam=16, anclaje="start", color="#1c1f24", negrita=False):
        peso = ' font-weight="bold"' if negrita else ""
        self.partes.append(
            f'<text x="{x}" y="{y}" text-anchor="{anclaje}" {FUENTE} font-size="{tam}" '
            f'fill="{color}"{peso}>{escape(linea)}</text>'
        )

    def flecha(self, x1, y1, x2, y2, color="#6b7280"):
        self.partes.append(
            f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="3"/>'
        )
        dx, dy = x2 - x1, y2 - y1
        largo = (dx * dx + dy * dy) ** 0.5
        ux, uy = dx / largo, dy / largo
        bx, by = x2 - 14 * ux, y2 - 14 * uy
        px, py = -uy * 8, ux * 8
        self.partes.append(
            f'<polygon points="{x2},{y2} {bx + px},{by + py} {bx - px},{by - py}" fill="{color}"/>'
        )

    def linea(self, x1, y1, x2, y2, color="#6b7280", ancho=2):
        self.partes.append(
            f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="{ancho}"/>'
        )

    def punto(self, x, y, color="#2b6cb0", radio=9):
        self.partes.append(f'<circle cx="{x}" cy="{y}" r="{radio}" fill="{color}"/>')

    def svg(self) -> str:
        cuerpo = "".join(self.partes)
        return (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.ancho}" height="{self.alto}" '
            f'viewBox="0 0 {self.ancho} {self.alto}">'
            f'<rect width="100%" height="100%" fill="#ffffff"/>{cuerpo}</svg>'
        )


def flujo(lienzo, y, cajas, ancho_caja, separacion, altura=90, colores=None, tam=17):
    """Dibuja cajas en horizontal unidas por flechas."""
    x = 20
    for i, lineas in enumerate(cajas):
        color = colores[i] if colores else AZUL
        lienzo.caja(x, y, ancho_caja, altura, lineas, color, tam=tam)
        if i < len(cajas) - 1:
            lienzo.flecha(x + ancho_caja + 4, y + altura / 2, x + ancho_caja + separacion - 4, y + altura / 2)
        x += ancho_caja + separacion


def diagrama_0_idea():
    d = Lienzo(900, 260)
    d.texto(450, 40, "La idea en una imagen", tam=20, anclaje="middle", negrita=True)
    flujo(
        d, 90,
        [["Tu pregunta"], ["Busca en tus", "documentos"], ["Respuesta con", "fuentes citadas"]],
        ancho_caja=230, separacion=105, altura=100,
        colores=[AMBAR, AZUL, VERDE], tam=18,
    )
    return d.svg()


def diagrama_1_carpetas():
    d = Lienzo(900, 380)
    d.texto(450, 40, "Carpetas del proyecto", tam=20, anclaje="middle", negrita=True)
    filas = [
        ("corpus/documentos/", "Tus archivos de ejemplo (PDF, DOCX, TXT, MD)", AZUL),
        ("src/rag_normativo/", "El código: motor, web y comandos", VERDE),
        ("data/", "Índice y copias. Se genera solo", AMBAR),
        (".venv/", "Programas de Python instalados para el proyecto", GRIS),
    ]
    y = 80
    for carpeta, descripcion, color in filas:
        d.caja(40, y, 260, 56, [carpeta], color, tam=17)
        d.texto(330, y + 35, descripcion, tam=17)
        y += 74
    return d.svg()


def diagrama_2_vectores():
    d = Lienzo(900, 480)
    d.texto(450, 36, "Frases como puntos: las parecidas quedan cerca", tam=20, anclaje="middle", negrita=True)
    ox, oy = 90, 430
    d.linea(ox, oy, 840, oy, color="#9ca3af")
    d.linea(ox, oy, ox, 80, color="#9ca3af")
    d.texto(830, oy + 28, "dimensión 1", tam=14, anclaje="end", color="#6b7280")
    d.texto(ox - 10, 90, "dimensión 2", tam=14, anclaje="end", color="#6b7280")

    puntos = [
        ("avisar del incidente", 280, 200, "#2b6cb0"),
        ("reportar la incidencia", 330, 240, "#2b6cb0"),
        ("fecha de la reunión", 520, 330, "#b45309"),
        ("receta de cocina", 720, 150, "#b42318"),
    ]
    for etiqueta, x, y, color in puntos:
        d.punto(x, y, color)
        d.texto(x + 14, y - 12, etiqueta, tam=16)
    d.linea(280, 200, 330, 240, color="#15803d", ancho=3)
    d.texto(195, 300, "muy parecidas", tam=16, color="#15803d", negrita=True)
    d.texto(450, 460, "Cada frase es un vector: una lista de números (aquí, 2 para dibujarlo; en el proyecto, 1024).",
            tam=14, anclaje="middle", color="#6b7280")
    return d.svg()


def diagrama_3_trocear():
    d = Lienzo(900, 420)
    d.texto(450, 36, "Un documento se parte en fragmentos que se solapan", tam=20, anclaje="middle", negrita=True)
    d.caja(60, 70, 780, 50, ["Documento completo (muchas palabras)"], GRIS, tam=16)
    filas = [
        (150, 60, 360, "Fragmento 1: 180 palabras"),
        (230, 300, 360, "Fragmento 2: 180 palabras"),
        (310, 540, 300, "Fragmento 3: ..."),
    ]
    for y, x, ancho, etiqueta in filas:
        d.caja(x, y, ancho, 52, [etiqueta], AZUL, tam=16)
    # zonas de solape
    d.caja(300, 230, 60, 52, [""], ROJO, tam=12)
    d.caja(540, 310, 60, 52, [""], ROJO, tam=12)
    d.texto(330, 395, "zona roja = solape de 30 palabras", tam=16, anclaje="middle", color="#b42318", negrita=True)
    d.texto(450, 130, "▼ se parte en fragmentos ▼", tam=15, anclaje="middle", color="#6b7280")
    return d.svg()


def diagrama_4_tabla():
    d = Lienzo(900, 330)
    d.texto(450, 36, "Qdrant guarda cada fragmento junto a su vector", tam=20, anclaje="middle", negrita=True)
    columnas = [(40, 90, "id"), (130, 380, "fragmento (texto)"), (510, 350, "vector (1024 números)")]
    for x, ancho, titulo in columnas:
        d.caja(x, 70, ancho, 50, [titulo], AZUL, tam=17)
    filas = [
        ("1", "Las contraseñas tienen 12 caracteres...", "[0.021, -0.113, 0.054, ...]"),
        ("2", "Las copias de seguridad se hacen a las 02:00...", "[-0.007, 0.089, 0.031, ...]"),
        ("3", "El teletrabajo es de 3 días por semana...", "[0.047, 0.012, -0.095, ...]"),
    ]
    y = 130
    for id_, texto, vector in filas:
        d.caja(40, y, 90, 50, [id_], VERDE, tam=17)
        d.caja(130, y, 380, 50, [texto], GRIS, tam=14)
        d.caja(510, y, 350, 50, [vector], AMBAR, tam=14)
        y += 60
    d.texto(450, 318, "Los números son ejemplos: el vector real tiene 1024 valores.", tam=14, anclaje="middle",
            color="#6b7280")
    return d.svg()


def diagrama_5_indexar():
    d = Lienzo(900, 260)
    d.texto(450, 40, "Indexar: un archivo entra y sale guardado como vectores", tam=20, anclaje="middle", negrita=True)
    flujo(
        d, 90,
        [["1. Convertir", "a texto"], ["2. Trocear", "en fragmentos"], ["3. Crear", "vectores"], ["4. Guardar", "en Qdrant"]],
        ancho_caja=170, separacion=50, altura=100, colores=[AZUL, AZUL, VERDE, AMBAR], tam=17,
    )
    return d.svg()


def diagrama_6_responder():
    d = Lienzo(900, 300)
    d.texto(450, 40, "Responder: de la pregunta a la respuesta", tam=20, anclaje="middle", negrita=True)
    pasos = [
        ["Pregunta"], ["Vector de", "la pregunta"], ["Buscar los 5", "más parecidos"],
        ["Armar el", "prompt"], ["El modelo", "escribe"], ["Respuesta", "+ fuentes"],
    ]
    colores = [AMBAR, AZUL, AZUL, AZUL, VERDE, VERDE]
    x = 15
    for i, lineas in enumerate(pasos):
        d.caja(x, 110, 124, 100, lineas, colores[i], tam=15)
        if i < len(pasos) - 1:
            d.flecha(x + 128, 160, x + 146, 160)
        x += 146
    d.texto(450, 260, "Haystack conecta estos pasos como piezas de una cadena.", tam=15, anclaje="middle",
            color="#6b7280")
    return d.svg()


def diagrama_7_citas():
    d = Lienzo(900, 400)
    d.texto(450, 36, "Respuesta con citas, o 'no lo sé'", tam=20, anclaje="middle", negrita=True)
    d.caja(40, 70, 380, 100, ["Pregunta: ¿Cuánto", "duran las copias?"], AMBAR, tam=17)
    d.flecha(425, 120, 470, 120)
    d.caja(480, 70, 380, 100, ["Las copias se conservan", "30 días [1]."], VERDE, tam=17)
    d.caja(40, 210, 380, 80, ["Fragmento [1]: politica_seguridad.md"], AZUL, tam=16)
    d.texto(60, 345, "La cita [1] apunta al fragmento de origen.", tam=15, color="#15803d")
    d.caja(480, 210, 380, 80, ["Si no hay evidencia:", "'No encuentro esa información'"], ROJO, tam=16)
    d.texto(60, 380, "Sin evidencia, el sistema se abstiene en vez de inventar.", tam=15, color="#b42318")
    return d.svg()


def diagrama_8_web():
    d = Lienzo(900, 300)
    d.texto(450, 36, "La web: tu navegador habla con un servidor local", tam=20, anclaje="middle", negrita=True)
    d.caja(30, 110, 230, 100, ["Navegador", "(tu pantalla)"], AMBAR, tam=17)
    d.caja(335, 110, 230, 100, ["FastAPI", "127.0.0.1:8000"], AZUL, tam=17)
    d.caja(640, 110, 230, 100, ["Motor RAG", "Qdrant + Ollama"], VERDE, tam=17)
    d.flecha(262, 150, 332, 150)
    d.flecha(568, 150, 638, 150)
    d.texto(297, 140, "petición", tam=13, anclaje="middle", color="#6b7280")
    d.texto(603, 140, "consulta", tam=13, anclaje="middle", color="#6b7280")
    d.texto(450, 260, "GET /api/documentos · POST /api/documentos · POST /api/preguntar · DELETE ...",
            tam=14, anclaje="middle", color="#6b7280")
    return d.svg()


def diagrama_9_medir():
    d = Lienzo(900, 420)
    d.texto(450, 36, "Medir: preguntas con respuesta conocida", tam=20, anclaje="middle", negrita=True)
    d.caja(330, 60, 240, 60, ["30 preguntas"], AZUL, tam=18)
    d.flecha(420, 122, 220, 170)
    d.flecha(480, 122, 680, 170)
    d.caja(90, 172, 260, 60, ["24 con respuesta"], VERDE, tam=17)
    d.caja(550, 172, 260, 60, ["6 sin respuesta"], ROJO, tam=17)
    metricas = [
        "¿El documento correcto sale entre los 5 primeros?",
        "¿La respuesta contiene la frase clave?",
        "¿La cita [n] apunta al documento correcto?",
        "¿Se abstiene cuando no hay respuesta?",
    ]
    y = 275
    for m in metricas:
        d.texto(90, y, "• " + m, tam=16)
        y += 34
    return d.svg()


def diagrama_10_privacidad():
    d = Lienzo(900, 400)
    d.texto(450, 36, "Qué sale de tu equipo y qué no", tam=20, anclaje="middle", negrita=True)
    d.caja(40, 70, 520, 260, [""], AZUL, tam=16)
    d.texto(60, 100, "Tu Mac (todo ocurre aquí)", tam=18, negrita=True, color="#1d4f86")
    d.caja(70, 130, 180, 80, ["Documentos"], VERDE, tam=16)
    d.caja(280, 130, 180, 80, ["Índice Qdrant"], VERDE, tam=16)
    d.caja(70, 230, 390, 70, ["Ollama: modelos de IA"], VERDE, tam=16)
    d.caja(620, 70, 240, 260, ["Internet", "", "Sin envío", "de tus datos"], ROJO, tam=18, punteada=True)
    d.texto(450, 375, "Nada de lo que subes o preguntas cruza al exterior.", tam=15,
            anclaje="middle", color="#6b7280")
    return d.svg()


DIAGRAMAS = {
    "00_idea": diagrama_0_idea,
    "01_carpetas": diagrama_1_carpetas,
    "02_vectores": diagrama_2_vectores,
    "03_trocear": diagrama_3_trocear,
    "04_tabla": diagrama_4_tabla,
    "05_indexar": diagrama_5_indexar,
    "06_responder": diagrama_6_responder,
    "07_citas": diagrama_7_citas,
    "08_web": diagrama_8_web,
    "09_medir": diagrama_9_medir,
    "10_privacidad": diagrama_10_privacidad,
}


def main() -> None:
    CARPETA_IMG.mkdir(parents=True, exist_ok=True)
    temporal = Path(tempfile.mkdtemp(prefix="diagramas_"))
    for nombre, generar in DIAGRAMAS.items():
        svg = temporal / f"{nombre}.svg"
        svg.write_text(generar(), encoding="utf-8")
        subprocess.run(
            [SOFFICE, "--headless", "--convert-to", "png", "--outdir", str(CARPETA_IMG), str(svg)],
            check=True,
            capture_output=True,
        )
        print(f"generado {CARPETA_IMG / (nombre + '.png')}")


if __name__ == "__main__":
    main()
