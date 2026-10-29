"""Pruebas de las funciones deterministas del motor (sin llamar a Ollama)."""

from types import SimpleNamespace

from rag_normativo.motor import (
    _fragmento_de_mayor_solapamiento,
    es_sin_evidencia,
    expandir_rutas,
    normalizar,
)


def test_normalizar_quita_tildes_y_mayusculas():
    assert normalizar("  Plazo  DE   Notificación ") == "plazo de notificacion"


def test_es_sin_evidencia_reconoce_negativas_habituales():
    assert es_sin_evidencia("No hay información sobre el salario en los documentos.")
    assert es_sin_evidencia("No encuentro esa información en los documentos.")


def test_es_sin_evidencia_no_marca_respuestas_con_datos():
    assert not es_sin_evidencia("El plazo es de 24 horas desde la detección.")


def test_fragmento_de_mayor_solapamiento_elige_el_que_contiene_la_respuesta():
    fragmentos = [
        SimpleNamespace(content="El horario de oficina es de nueve a dieciocho."),
        SimpleNamespace(content="Las contraseñas deben tener un mínimo de 12 caracteres."),
    ]
    respuesta = "La longitud mínima de una contraseña es de 12 caracteres."
    assert _fragmento_de_mayor_solapamiento(respuesta, fragmentos) == 1


def test_fragmento_de_mayor_solapamiento_sin_coincidencia_devuelve_none():
    fragmentos = [SimpleNamespace(content="Texto completamente distinto sobre otro asunto.")]
    assert _fragmento_de_mayor_solapamiento("Respuesta sobre cifrado AES.", fragmentos) is None


def test_expandir_rutas_ignora_formatos_no_soportados_en_carpetas(tmp_path):
    (tmp_path / "a.txt").write_text("hola", encoding="utf-8")
    (tmp_path / "b.png").write_bytes(b"\x89PNG")
    archivos = expandir_rutas([tmp_path])
    assert [a.name for a in archivos] == ["a.txt"]
