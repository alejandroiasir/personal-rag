"""Muestra los embeddings: vectores numéricos que representan el significado de un texto.

Modo texto: convierte frases en vectores y compara su similitud.
    .venv/bin/python scripts/demo_embeddings.py texto "frase 1" "frase 2" "frase 3"

Modo almacén: muestra los vectores guardados para un documento indexado.
    Requiere parar antes el servidor web (Qdrant local admite un solo proceso).
    .venv/bin/python scripts/demo_embeddings.py almacen politica_seguridad.md
"""

import argparse
import math

from haystack_integrations.components.embedders.ollama import OllamaTextEmbedder
from haystack_integrations.document_stores.qdrant import QdrantDocumentStore

from rag_normativo.motor import (
    DIMENSIONES_EMBEDDINGS,
    MODELO_EMBEDDINGS,
    NOMBRE_COLECCION,
    RUTA_INDICE,
    URL_OLLAMA,
)

VALORES_MOSTRADOS = 8


def norma(vector: list[float]) -> float:
    return math.sqrt(sum(x * x for x in vector))


def similitud_coseno(a: list[float], b: list[float]) -> float:
    """1 significa mismo sentido, 0 significa sin relación."""
    return sum(x * y for x, y in zip(a, b)) / (norma(a) * norma(b))


def redondear(vector: list[float]) -> list[float]:
    return [round(x, 4) for x in vector[:VALORES_MOSTRADOS]]


def modo_texto(textos: list[str]) -> None:
    embedder = OllamaTextEmbedder(model=MODELO_EMBEDDINGS, url=URL_OLLAMA)
    vectores = [embedder.run(text=texto)["embedding"] for texto in textos]

    print(f"Cada texto se convierte en un vector de {len(vectores[0])} números.\n")
    for texto, vector in zip(textos, vectores):
        print(f'"{texto}"')
        print(f"  primeros {VALORES_MOSTRADOS} valores: {redondear(vector)}")
        print(f"  longitud del vector: {norma(vector):.4f}\n")

    print("Similitud coseno entre frases (1 = mismo sentido, 0 = sin relación):")
    ancho = max(len(str(i + 1)) for i in range(len(textos)))
    print(" " * (ancho + 3) + "  ".join(f"{i + 1:>5}" for i in range(len(textos))))
    for i, va in enumerate(vectores):
        fila = "  ".join(f"{similitud_coseno(va, vb):>5.2f}" for vb in vectores)
        print(f"{i + 1:>{ancho}} : {fila}")
    print("\nFrases:")
    for i, texto in enumerate(textos):
        print(f"  {i + 1}. {texto}")


def modo_almacen(nombre_archivo: str) -> None:
    almacen = QdrantDocumentStore(
        path=str(RUTA_INDICE),
        index=NOMBRE_COLECCION,
        embedding_dim=DIMENSIONES_EMBEDDINGS,
        recreate_index=False,
        return_embedding=True,
    )
    try:
        fragmentos = almacen.filter_documents(
            filters={"field": "meta.file_name", "operator": "==", "value": nombre_archivo}
        )
        if not fragmentos:
            print(f"No hay fragmentos indexados para {nombre_archivo}.")
            return
        for fragmento in fragmentos:
            vector = fragmento.embedding
            print(f"Fragmento {fragmento.meta.get('split_id', 0)} de {nombre_archivo}")
            print(f"  texto: {fragmento.content[:120]}...")
            print(f"  vector: {len(vector)} números, primeros {VALORES_MOSTRADOS}: {redondear(vector)}")
            print(f"  longitud del vector: {norma(vector):.4f}\n")
    finally:
        almacen.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Muestra embeddings como vectores numéricos")
    sub = parser.add_subparsers(dest="modo", required=True)

    texto_p = sub.add_parser("texto", help="Convierte frases en vectores y las compara")
    texto_p.add_argument("textos", nargs="+")

    almacen_p = sub.add_parser("almacen", help="Muestra los vectores guardados de un archivo")
    almacen_p.add_argument("archivo")

    args = parser.parse_args()
    if args.modo == "texto":
        modo_texto(args.textos)
    else:
        modo_almacen(args.archivo)


if __name__ == "__main__":
    main()
