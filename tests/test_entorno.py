"""Pruebas de entorno: Haystack 2.x fijado y núcleo de pipelines disponible (RS-001)."""

from importlib.metadata import version


def test_haystack_es_2x():
    # RS-001: el proyecto usa Haystack 2.x.
    assert version("haystack-ai").startswith("2.")


def test_pipeline_haystack_se_construye():
    # Comprueba que el núcleo de Haystack funciona antes de construir pipelines reales.
    from haystack import Pipeline
    from haystack.components.builders import PromptBuilder

    pipeline = Pipeline()
    pipeline.add_component("prompt", PromptBuilder(template="Hola {{ nombre }}"))
    assert "prompt" in pipeline.graph.nodes
