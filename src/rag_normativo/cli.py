"""Línea de comandos: indexar documentos, preguntar y evaluar."""

import argparse
import json
from pathlib import Path

from .evaluar import evaluar
from .motor import abrir_almacen, indexar, responder

CORPUS_DORADO = Path("corpus/dorado/preguntas.jsonl")
REPORTE = Path("data/evaluacion.json")


def _indexar(args: argparse.Namespace) -> None:
    total = indexar(args.rutas)
    print(f"Fragmentos indexados: {total}")


def _preguntar(args: argparse.Namespace) -> None:
    salida = responder(args.pregunta)
    print(salida["respuesta"])
    print("\nFuentes:")
    for fuente in salida["fuentes"]:
        marca = "citada" if fuente["citado"] else "recuperada"
        print(f"  [{fuente['n']}] {fuente['archivo']} (fragmento {fuente['fragmento']}) - {marca}")


def _evaluar(args: argparse.Namespace) -> None:
    resultados, resumen = evaluar(args.preguntas)
    for r in resultados:
        estado = "OK" if _caso_correcto(r) else "FALLO"
        print(f"{r['id']} {estado:5} {r['pregunta']}")
    print("\nResumen:")
    for metrica, valor in resumen.items():
        print(f"  {metrica}: {valor}")
    REPORTE.parent.mkdir(parents=True, exist_ok=True)
    REPORTE.write_text(json.dumps({"resumen": resumen, "casos": resultados}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nDetalle guardado en {REPORTE}")


def _caso_correcto(r: dict) -> bool:
    if r["respondible"]:
        return bool(r["respuesta_ok"])
    return bool(r["abstencion_ok"])


def _servir(args: argparse.Namespace) -> None:
    import uvicorn

    from .web import app

    print(f"Abre en el navegador: http://127.0.0.1:{args.puerto}")
    uvicorn.run(app, host="127.0.0.1", port=args.puerto, log_level="warning")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="rag", description="RAG sobre documentos locales")
    sub = parser.add_subparsers(dest="comando", required=True)

    indexar_p = sub.add_parser("indexar", help="Indexa archivos o carpetas")
    indexar_p.add_argument("rutas", nargs="+", type=Path)
    indexar_p.set_defaults(func=_indexar)

    preguntar_p = sub.add_parser("preguntar", help="Hace una pregunta a los documentos")
    preguntar_p.add_argument("pregunta")
    preguntar_p.set_defaults(func=_preguntar)

    evaluar_p = sub.add_parser("evaluar", help="Mide el sistema contra el corpus dorado")
    evaluar_p.add_argument("--preguntas", type=Path, default=CORPUS_DORADO)
    evaluar_p.set_defaults(func=_evaluar)

    servir_p = sub.add_parser("servir", help="Abre la página web en 127.0.0.1")
    servir_p.add_argument("--puerto", type=int, default=8000)
    servir_p.set_defaults(func=_servir)

    args = parser.parse_args(argv)
    if args.comando == "servir":
        args.func(args)
        return
    try:
        args.func(args)
    finally:
        abrir_almacen().close()
