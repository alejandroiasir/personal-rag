"""Indexación y consulta RAG sobre documentos locales."""

import re
import unicodedata
from functools import lru_cache
from pathlib import Path

from haystack import Pipeline
from haystack.components.builders import PromptBuilder
from haystack.components.converters import (
    DOCXToDocument,
    HTMLToDocument,
    PyPDFToDocument,
    TextFileToDocument,
)
from haystack.components.preprocessors import DocumentSplitter
from haystack.components.writers import DocumentWriter
from haystack.document_stores.types import DuplicatePolicy
from haystack_integrations.components.embedders.ollama import (
    OllamaDocumentEmbedder,
    OllamaTextEmbedder,
)
from haystack_integrations.components.generators.ollama import OllamaGenerator
from haystack_integrations.components.retrievers.qdrant import QdrantEmbeddingRetriever
from haystack_integrations.document_stores.qdrant import QdrantDocumentStore

RUTA_INDICE = Path("data/qdrant")
NOMBRE_COLECCION = "documentos"
MODELO_EMBEDDINGS = "bge-m3"
DIMENSIONES_EMBEDDINGS = 1024
MODELO_LLM = "qwen2.5:7b"
URL_OLLAMA = "http://localhost:11434"
TAMANO_FRAGMENTO = 180  # palabras
SOLAPE_FRAGMENTO = 30  # palabras
TOP_K = 5
RESPUESTA_SIN_EVIDENCIA = "No encuentro esa información en los documentos."

CONVERSORES = {
    ".pdf": PyPDFToDocument,
    ".docx": DOCXToDocument,
    ".txt": TextFileToDocument,
    ".md": TextFileToDocument,
    ".html": HTMLToDocument,
}

SISTEMA = (
    "Eres un asistente que responde en español usando solo los fragmentos de documentos que recibes. "
    "Responde en una o dos frases. "
    "Si los fragmentos no contienen la respuesta, di: \"No encuentro esa información en los documentos.\" "
    "Termina cada dato con el número del fragmento entre corchetes, por ejemplo [1]."
)

PLANTILLA = """Fragmentos:
{% for doc in documents %}
[{{ loop.index }}] ({{ doc.meta.file_name }}) {{ doc.content }}
{% endfor %}
Pregunta: {{ pregunta }}
Respuesta:"""


PISTAS_SIN_EVIDENCIA = (
    "no encuentro",
    "no hay informacion",
    "no se proporciona",
    "no se menciona",
    "no menciona",
    "no contiene",
    "no incluye",
    "no aparece",
    "no se encuentra",
    "no puedo responder",
    "no tengo informacion",
    "ninguna informacion",
)


def normalizar(texto: str) -> str:
    """Minúsculas, sin tildes y con espacios simples, para comparar textos en español."""
    sin_tildes = "".join(
        c for c in unicodedata.normalize("NFKD", texto.lower()) if not unicodedata.combining(c)
    )
    return " ".join(sin_tildes.split())


def es_sin_evidencia(respuesta: str) -> bool:
    texto = normalizar(respuesta)
    return any(pista in texto for pista in PISTAS_SIN_EVIDENCIA)


def _palabras(texto: str) -> set[str]:
    # Cinco primeras letras: aproxima singular y plural (contraseña / contraseñas).
    # Los números se conservan: en normativa distinguen versiones (12 caracteres frente a 8).
    return {
        palabra[:5]
        for palabra in re.findall(r"[a-z0-9]+", normalizar(texto))
        if len(palabra) >= 4 or palabra.isdigit()
    }


def _fragmento_de_mayor_solapamiento(respuesta: str, documentos: list) -> int | None:
    """Índice (base 0) del fragmento que comparte más palabras con la respuesta."""
    palabras_respuesta = _palabras(respuesta)
    if not palabras_respuesta:
        return None
    puntuaciones = [len(palabras_respuesta & _palabras(doc.content)) for doc in documentos]
    mejor = max(range(len(documentos)), key=lambda i: puntuaciones[i])
    return mejor if puntuaciones[mejor] / len(palabras_respuesta) >= 0.5 else None


@lru_cache(maxsize=1)
def abrir_almacen() -> QdrantDocumentStore:
    """Qdrant en modo local admite un solo cliente abierto, así que se reutiliza."""
    return QdrantDocumentStore(
        path=str(RUTA_INDICE),
        index=NOMBRE_COLECCION,
        embedding_dim=DIMENSIONES_EMBEDDINGS,
        recreate_index=False,
    )


def expandir_rutas(rutas: list[Path]) -> list[Path]:
    """Convierte carpetas en la lista de archivos soportados que contienen."""
    archivos = []
    for ruta in rutas:
        if ruta.is_dir():
            archivos.extend(sorted(p for p in ruta.rglob("*") if p.suffix.lower() in CONVERSORES))
        elif ruta.suffix.lower() in CONVERSORES:
            archivos.append(ruta)
        else:
            raise ValueError(f"Formato no soportado: {ruta}")
    return archivos


def _convertir(ruta: Path):
    conversor = CONVERSORES[ruta.suffix.lower()]()
    documentos = conversor.run(sources=[ruta])["documents"]
    documentos = [doc for doc in documentos if doc.content and doc.content.strip()]
    if not documentos:
        raise ValueError(f"{ruta.name} no tiene texto extraíble (¿PDF escaneado sin capa de texto?)")
    for documento in documentos:
        documento.meta["file_name"] = ruta.name
    return documentos


def listar_documentos() -> list[dict]:
    """Nombres de archivo indexados y número de fragmentos de cada uno."""
    conteo: dict[str, int] = {}
    for doc in abrir_almacen().filter_documents():
        nombre = doc.meta["file_name"]
        conteo[nombre] = conteo.get(nombre, 0) + 1
    return [{"nombre": n, "fragmentos": c} for n, c in sorted(conteo.items())]


def borrar_documento(nombre: str) -> int:
    """Elimina todos los fragmentos de un archivo. Devuelve cuántos había."""
    almacen = abrir_almacen()
    previos = almacen.filter_documents(
        filters={"field": "meta.file_name", "operator": "==", "value": nombre}
    )
    if previos:
        almacen.delete_documents(document_ids=[doc.id for doc in previos])
    return len(previos)


def indexar(rutas: list[Path]) -> int:
    """Indexa los archivos y reemplaza los fragmentos previos de cada archivo."""
    almacen = abrir_almacen()
    documentos = []
    for archivo in expandir_rutas(rutas):
        borrar_documento(archivo.name)
        documentos.extend(_convertir(archivo))

    partes = DocumentSplitter(
        split_by="word", split_length=TAMANO_FRAGMENTO, split_overlap=SOLAPE_FRAGMENTO
    ).run(documents=documentos)["documents"]
    embebidos = OllamaDocumentEmbedder(model=MODELO_EMBEDDINGS, url=URL_OLLAMA).run(
        documents=partes
    )["documents"]
    return DocumentWriter(document_store=almacen, policy=DuplicatePolicy.OVERWRITE).run(
        documents=embebidos
    )["documents_written"]


def _construir_consulta(almacen: QdrantDocumentStore) -> Pipeline:
    pipeline = Pipeline()
    pipeline.add_component("embedder", OllamaTextEmbedder(model=MODELO_EMBEDDINGS, url=URL_OLLAMA))
    pipeline.add_component("recuperador", QdrantEmbeddingRetriever(document_store=almacen, top_k=TOP_K))
    pipeline.add_component(
        "prompt", PromptBuilder(template=PLANTILLA, required_variables=["documents", "pregunta"])
    )
    pipeline.add_component(
        "llm",
        OllamaGenerator(
            model=MODELO_LLM,
            url=URL_OLLAMA,
            system_prompt=SISTEMA,
            generation_kwargs={"temperature": 0},
        ),
    )
    pipeline.connect("embedder.embedding", "recuperador.query_embedding")
    pipeline.connect("recuperador.documents", "prompt.documents")
    pipeline.connect("prompt.prompt", "llm.prompt")
    return pipeline


def responder(pregunta: str) -> dict:
    """Devuelve la respuesta, los fragmentos recuperados y cuáles se citaron."""
    pipeline = _construir_consulta(abrir_almacen())
    resultado = pipeline.run(
        {"embedder": {"text": pregunta}, "prompt": {"pregunta": pregunta}},
        include_outputs_from={"recuperador"},
    )
    documentos = resultado["recuperador"]["documents"]
    respuesta = resultado["llm"]["replies"][0]
    citados = {int(n) for n in re.findall(r"\[(\d+)\]", respuesta)}
    if not es_sin_evidencia(respuesta):
        mejor = _fragmento_de_mayor_solapamiento(respuesta, documentos)
        if mejor is not None:
            citados.add(mejor + 1)

    fuentes = [
        {
            "n": i,
            "archivo": doc.meta["file_name"],
            "fragmento": doc.meta.get("split_id"),
            "texto": doc.content,
            "citado": i in citados,
        }
        for i, doc in enumerate(documentos, start=1)
    ]
    return {"respuesta": respuesta, "fuentes": fuentes}
