"""Evalúa el pipeline contra el corpus dorado (preguntas con fuente conocida)."""

import json
from pathlib import Path

from .motor import es_sin_evidencia, normalizar, responder


def cargar_casos(ruta: Path) -> list[dict]:
    lineas = ruta.read_text(encoding="utf-8").splitlines()
    return [json.loads(linea) for linea in lineas if linea.strip()]


def evaluar_caso(caso: dict) -> dict:
    salida = responder(caso["pregunta"])
    respuesta = normalizar(salida["respuesta"])
    fuentes = salida["fuentes"]
    claves = [normalizar(c) for c in caso["respuesta_clave"]]

    if caso["respondible"]:
        texto_recuperado = normalizar(
            " ".join(f["texto"] for f in fuentes if f["archivo"] == caso["documento"])
        )
        recuperacion_ok = all(c in texto_recuperado for c in claves)
        respuesta_ok = all(c in respuesta for c in claves)
        cita_ok = any(f["citado"] and f["archivo"] == caso["documento"] for f in fuentes)
        posiciones = [f["n"] for f in fuentes if f["archivo"] == caso["documento"]]
        posicion = min(posiciones) if posiciones else None
        abstencion_ok = None
    else:
        recuperacion_ok = None
        respuesta_ok = None
        cita_ok = None
        abstencion_ok = es_sin_evidencia(salida["respuesta"])

    return {
        "id": caso["id"],
        "pregunta": caso["pregunta"],
        "respondible": caso["respondible"],
        "recuperacion_ok": recuperacion_ok,
        "respuesta_ok": respuesta_ok,
        "cita_ok": cita_ok,
        "posicion_documento_correcto": posicion if caso["respondible"] else None,
        "abstencion_ok": abstencion_ok,
        "respuesta": salida["respuesta"],
    }


def resumir(resultados: list[dict]) -> dict:
    respondibles = [r for r in resultados if r["respondible"]]
    sin_respuesta = [r for r in resultados if not r["respondible"]]
    correctas = [r for r in respondibles if r["respuesta_ok"]]
    return {
        "recuperacion_en_top_k": f"{sum(r['recuperacion_ok'] for r in respondibles)}/{len(respondibles)}",
        "respuestas_correctas": f"{len(correctas)}/{len(respondibles)}",
        "citas_correctas_en_respuestas_correctas": f"{sum(r['cita_ok'] for r in correctas)}/{len(correctas)}",
        "sin_evidencia_correcto": f"{sum(r['abstencion_ok'] for r in sin_respuesta)}/{len(sin_respuesta)}",
        "documento_correcto_en_primer_lugar": f"{sum(r['posicion_documento_correcto'] == 1 for r in respondibles)}/{len(respondibles)}",
        "posicion_media_documento_correcto": f"{sum(r['posicion_documento_correcto'] for r in respondibles if r['posicion_documento_correcto']) / max(1, sum(bool(r['posicion_documento_correcto']) for r in respondibles)):.2f}",
    }


def evaluar(ruta_casos: Path) -> tuple[list[dict], dict]:
    resultados = [evaluar_caso(caso) for caso in cargar_casos(ruta_casos)]
    return resultados, resumir(resultados)
