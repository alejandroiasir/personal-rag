"""Servidor web local: subir documentos, listarlos, borrarlos y hacer preguntas.

Escucha solo en 127.0.0.1. Los documentos no salen de esta máquina.
"""

from pathlib import Path

from fastapi import FastAPI, HTTPException, UploadFile
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from .motor import CONVERSORES, borrar_documento, indexar, listar_documentos, responder

DIRECTORIO_SUBIDOS = Path("data/subidos")

app = FastAPI(title="RAG personal", docs_url=None, redoc_url=None)


class Pregunta(BaseModel):
    pregunta: str


@app.get("/", response_class=HTMLResponse)
async def pagina() -> str:
    return PAGINA


@app.get("/api/documentos")
async def documentos() -> list[dict]:
    return listar_documentos()


@app.post("/api/documentos")
async def subir(archivos: list[UploadFile]) -> list[dict]:
    DIRECTORIO_SUBIDOS.mkdir(parents=True, exist_ok=True)
    resultados = []
    for archivo in archivos:
        nombre = Path(archivo.filename or "").name
        if Path(nombre).suffix.lower() not in CONVERSORES:
            resultados.append({"nombre": nombre, "ok": False, "error": "Formato no soportado"})
            continue
        destino = DIRECTORIO_SUBIDOS / nombre
        destino.write_bytes(await archivo.read())
        try:
            # Las llamadas al motor son síncronas: se ejecutan una a una, lo que evita
            # accesos concurrentes al almacén local de Qdrant.
            fragmentos = indexar([destino])
            resultados.append({"nombre": nombre, "ok": True, "fragmentos": fragmentos})
        except Exception as error:  # noqa: BLE001 - un archivo malo no debe tumbar el servidor
            resultados.append({"nombre": nombre, "ok": False, "error": str(error)})
    return resultados


@app.delete("/api/documentos/{nombre}")
async def eliminar(nombre: str) -> dict:
    nombre = Path(nombre).name
    eliminados = borrar_documento(nombre)
    copia = DIRECTORIO_SUBIDOS / nombre
    if copia.exists():
        copia.unlink()
    if eliminados == 0:
        raise HTTPException(status_code=404, detail="Documento no encontrado")
    return {"nombre": nombre, "fragmentos_eliminados": eliminados}


@app.post("/api/preguntar")
async def preguntar(entrada: Pregunta) -> dict:
    if not entrada.pregunta.strip():
        raise HTTPException(status_code=400, detail="La pregunta está vacía")
    try:
        return responder(entrada.pregunta)
    except Exception as error:
        raise HTTPException(
            status_code=503,
            detail=f"No se pudo consultar el modelo. ¿Está Ollama en marcha? ({error})",
        ) from error


PAGINA = """<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>RAG personal</title>
<style>
  :root {
    --fondo: #f6f7f9; --tarjeta: #ffffff; --texto: #1c1f24; --suave: #6b7280;
    --borde: #e3e6eb; --acento: #2b6cb0; --acento-texto: #ffffff; --peligro: #b42318;
    --badge: #e6f0fb; --badge-texto: #1d4f86;
  }
  @media (prefers-color-scheme: dark) {
    :root:not([data-theme="light"]) {
      --fondo: #15171a; --tarjeta: #1d2024; --texto: #e7e9ec; --suave: #9aa1ab;
      --borde: #2c3036; --acento: #5b9bd5; --acento-texto: #0b1420; --peligro: #f97066;
      --badge: #1f2f42; --badge-texto: #9cc7f0;
    }
  }
  :root[data-theme="dark"] {
    --fondo: #15171a; --tarjeta: #1d2024; --texto: #e7e9ec; --suave: #9aa1ab;
    --borde: #2c3036; --acento: #5b9bd5; --acento-texto: #0b1420; --peligro: #f97066;
    --badge: #1f2f42; --badge-texto: #9cc7f0;
  }
  * { box-sizing: border-box; }
  body {
    margin: 0; background: var(--fondo); color: var(--texto);
    font: 15px/1.5 system-ui, -apple-system, "Segoe UI", sans-serif;
  }
  header { padding: 20px 24px; border-bottom: 1px solid var(--borde); background: var(--tarjeta); }
  header h1 { margin: 0; font-size: 18px; font-weight: 600; }
  header p { margin: 2px 0 0; color: var(--suave); font-size: 13px; }
  main {
    display: grid; grid-template-columns: minmax(280px, 380px) 1fr; gap: 20px;
    padding: 20px 24px; max-width: 1200px; margin: 0 auto;
  }
  @media (max-width: 760px) { main { grid-template-columns: 1fr; padding: 16px; } }
  .tarjeta {
    background: var(--tarjeta); border: 1px solid var(--borde); border-radius: 10px; padding: 16px;
  }
  h2 { margin: 0 0 12px; font-size: 15px; font-weight: 600; }
  button {
    font: inherit; cursor: pointer; border: 0; border-radius: 8px;
    padding: 8px 14px; background: var(--acento); color: var(--acento-texto);
  }
  button:disabled { opacity: .5; cursor: default; }
  button.secundario { background: transparent; color: var(--peligro); border: 1px solid var(--borde); padding: 4px 10px; }
  input[type="file"] { width: 100%; margin-bottom: 10px; }
  textarea {
    width: 100%; min-height: 84px; resize: vertical; font: inherit; padding: 10px;
    border: 1px solid var(--borde); border-radius: 8px; background: var(--fondo); color: var(--texto);
  }
  .estado { color: var(--suave); font-size: 13px; margin: 8px 0 0; min-height: 1.2em; }
  .error { color: var(--peligro); }
  ul.lista { list-style: none; padding: 0; margin: 12px 0 0; max-height: 52vh; overflow: auto; }
  ul.lista li {
    display: flex; justify-content: space-between; align-items: center; gap: 8px;
    padding: 8px 0; border-top: 1px solid var(--borde); font-size: 14px;
  }
  ul.lista li span.nombre { overflow-wrap: anywhere; }
  ul.lista li small { color: var(--suave); white-space: nowrap; }
  .vacio { color: var(--suave); font-size: 14px; }
  .respuesta { white-space: pre-wrap; font-size: 15px; margin: 0 0 16px; }
  .fuentes { border-top: 1px solid var(--borde); padding-top: 12px; }
  .fuente { margin: 0 0 10px; }
  .fuente .cabecera { display: flex; flex-wrap: wrap; gap: 8px; align-items: center; font-size: 14px; }
  .badge {
    font-size: 12px; padding: 2px 8px; border-radius: 999px;
    background: var(--badge); color: var(--badge-texto);
  }
  .badge.suave { background: transparent; color: var(--suave); border: 1px solid var(--borde); }
  details summary { cursor: pointer; color: var(--suave); font-size: 13px; margin-top: 4px; }
  details p { white-space: pre-wrap; font-size: 13px; color: var(--suave); margin: 6px 0 0; }
</style>
</head>
<body>
<header>
  <h1>RAG personal</h1>
  <p>Documentos y modelo en esta máquina. Servidor en 127.0.0.1.</p>
</header>
<main>
  <section class="tarjeta">
    <h2>Documentos</h2>
    <input id="archivos" type="file" multiple
           accept=".pdf,.docx,.txt,.md,.html">
    <button id="subir">Subir e indexar</button>
    <p id="estado-subida" class="estado"></p>
    <ul id="lista" class="lista"></ul>
  </section>

  <section class="tarjeta">
    <h2>Pregunta</h2>
    <textarea id="pregunta" placeholder="Escribe una pregunta sobre tus documentos"></textarea>
    <p><button id="preguntar">Preguntar</button></p>
    <p id="estado-pregunta" class="estado"></p>
    <div id="resultado"></div>
  </section>
</main>

<script>
const $ = (id) => document.getElementById(id);

function elemento(tag, texto, clase) {
  const el = document.createElement(tag);
  if (texto !== undefined && texto !== null) el.textContent = texto;
  if (clase) el.className = clase;
  return el;
}

async function cargarLista() {
  const lista = $("lista");
  lista.replaceChildren();
  const docs = await (await fetch("/api/documentos")).json();
  if (docs.length === 0) {
    lista.append(elemento("li", "Aún no hay documentos indexados.", "vacio"));
    return;
  }
  for (const doc of docs) {
    const fila = elemento("li");
    fila.append(elemento("span", doc.nombre, "nombre"));
    const derecha = elemento("span");
    derecha.append(elemento("small", doc.fragmentos + " fragm."));
    const borrar = elemento("button", "Quitar", "secundario");
    borrar.onclick = async () => {
      if (!confirm("¿Quitar «" + doc.nombre + "» del índice?")) return;
      await fetch("/api/documentos/" + encodeURIComponent(doc.nombre), { method: "DELETE" });
      cargarLista();
    };
    derecha.append(borrar);
    fila.append(derecha);
    lista.append(fila);
  }
}

$("subir").onclick = async () => {
  const archivos = $("archivos").files;
  if (archivos.length === 0) return;
  const boton = $("subir");
  boton.disabled = true;
  $("estado-subida").textContent = "Indexando " + archivos.length + " archivo(s)…";
  $("estado-subida").className = "estado";
  const datos = new FormData();
  for (const f of archivos) datos.append("archivos", f);
  try {
    const respuesta = await fetch("/api/documentos", { method: "POST", body: datos });
    const resultados = await respuesta.json();
    const fallos = resultados.filter((r) => !r.ok);
    $("estado-subida").textContent = fallos.length === 0
      ? "Listo: " + resultados.length + " archivo(s) indexados."
      : fallos.map((r) => r.nombre + ": " + r.error).join(" · ");
    $("estado-subida").className = fallos.length ? "estado error" : "estado";
    $("archivos").value = "";
    await cargarLista();
  } catch (error) {
    $("estado-subida").textContent = "No se pudo subir: " + error;
    $("estado-subida").className = "estado error";
  } finally {
    boton.disabled = false;
  }
};

function pintarRespuesta(datos) {
  const cont = $("resultado");
  cont.replaceChildren();
  cont.append(elemento("p", datos.respuesta, "respuesta"));
  const fuentes = elemento("div", null, "fuentes");
  fuentes.append(elemento("h2", "Fuentes recuperadas"));
  for (const f of datos.fuentes) {
    const bloque = elemento("div", null, "fuente");
    const cab = elemento("div", null, "cabecera");
    cab.append(elemento("strong", "[" + f.n + "] " + f.archivo));
    cab.append(elemento("span", "fragmento " + f.fragmento, "badge suave"));
    if (f.citado) cab.append(elemento("span", "citada", "badge"));
    bloque.append(cab);
    const detalle = document.createElement("details");
    detalle.append(elemento("summary", "Ver texto del fragmento"));
    detalle.append(elemento("p", f.texto));
    bloque.append(detalle);
    fuentes.append(bloque);
  }
  cont.append(fuentes);
}

$("preguntar").onclick = async () => {
  const texto = $("pregunta").value.trim();
  if (!texto) return;
  const boton = $("preguntar");
  boton.disabled = true;
  $("estado-pregunta").textContent = "Consultando el modelo… puede tardar unos segundos.";
  $("estado-pregunta").className = "estado";
  try {
    const respuesta = await fetch("/api/preguntar", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ pregunta: texto }),
    });
    const datos = await respuesta.json();
    if (!respuesta.ok) throw new Error(datos.detail || "Error desconocido");
    $("estado-pregunta").textContent = "";
    pintarRespuesta(datos);
  } catch (error) {
    $("estado-pregunta").textContent = String(error.message || error);
    $("estado-pregunta").className = "estado error";
  } finally {
    boton.disabled = false;
  }
};

$("pregunta").addEventListener("keydown", (e) => {
  if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) $("preguntar").click();
});

cargarLista();
</script>
</body>
</html>
"""
