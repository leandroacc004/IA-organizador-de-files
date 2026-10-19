"""Organizador de archivos con IA.

Patrón de orquestación: ROUTING.
Cada archivo pasa por un "router" que decide a qué categoría va:
  1. Ruta rápida: reglas por extensión (gratis, instantáneo).
  2. Ruta inteligente: si las reglas no alcanzan, Claude lee un fragmento del
     contenido y elige la categoría.
"""

import argparse
import shutil
import sys
from pathlib import Path

import anthropic

from llm import ErrorLLM, pedir_json

CATEGORIAS = ["facturas", "notas", "codigo", "recetas", "documentos_personales", "imagenes", "otros"]

REGLAS_POR_EXTENSION = {
    ".jpg": "imagenes", ".jpeg": "imagenes", ".png": "imagenes", ".gif": "imagenes", ".webp": "imagenes",
    ".py": "codigo", ".js": "codigo", ".ts": "codigo", ".java": "codigo", ".go": "codigo", ".sh": "codigo",
}

EXTENSIONES_TEXTO = {".txt", ".md", ".csv", ".json", ".html", ".xml", ".log", ".yaml", ".yml"}

MAX_CARACTERES = 1500

SYSTEM = (
    "Eres un clasificador de archivos. Recibes el nombre de un archivo y un fragmento de su "
    "contenido, y eliges la categoría que mejor describe su propósito. Si ninguna encaja bien, usa 'otros'."
)


def leer_fragmento(ruta: Path) -> str:
    """Lee solo el inicio del archivo: para clasificar no hace falta el documento entero."""
    if ruta.suffix.lower() not in EXTENSIONES_TEXTO:
        return "(archivo binario o no legible como texto)"
    try:
        return ruta.read_text(encoding="utf-8", errors="replace")[:MAX_CARACTERES]
    except OSError as e:
        return f"(no se pudo leer: {e})"


def clasificar_con_ia(ruta: Path) -> tuple[str, str]:
    schema = {
        "type": "object",
        "properties": {
            "categoria": {"type": "string", "enum": CATEGORIAS},
            "razon": {"type": "string"},
        },
        "required": ["categoria", "razon"],
        "additionalProperties": False,
    }
    prompt = (
        f"Nombre del archivo: {ruta.name}\n\n"
        f"<contenido>\n{leer_fragmento(ruta)}\n</contenido>\n\n"
        "Elige la categoría y explica la razón en una frase corta."
    )
    datos = pedir_json(prompt, schema, system=SYSTEM)
    return datos["categoria"], datos["razon"]


def router(ruta: Path) -> tuple[str, str, str]:
    """Devuelve (categoria, razon, ruta_usada)."""
    categoria = REGLAS_POR_EXTENSION.get(ruta.suffix.lower())
    if categoria:
        return categoria, f"regla por extensión {ruta.suffix}", "regla"
    categoria, razon = clasificar_con_ia(ruta)
    return categoria, razon, "IA"


def destino_libre(destino: Path) -> Path:
    """Evita sobrescribir: si ya existe, agrega _1, _2, ..."""
    if not destino.exists():
        return destino
    n = 1
    while True:
        candidato = destino.with_name(f"{destino.stem}_{n}{destino.suffix}")
        if not candidato.exists():
            return candidato
        n += 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Clasifica y organiza archivos usando reglas + Claude.")
    parser.add_argument("carpeta", type=Path, help="Carpeta con los archivos a organizar")
    parser.add_argument("--aplicar", action="store_true", help="Mover los archivos de verdad (por defecto solo muestra el plan)")
    args = parser.parse_args()

    carpeta: Path = args.carpeta
    if not carpeta.is_dir():
        print(f"No existe la carpeta: {carpeta}")
        return 1

    archivos = sorted(p for p in carpeta.iterdir() if p.is_file() and not p.name.startswith("."))
    if not archivos:
        print("No hay archivos para organizar.")
        return 0

    plan = []
    for ruta in archivos:
        try:
            categoria, razon, via = router(ruta)
        except ErrorLLM as e:
            categoria, razon, via = "otros", f"error al clasificar: {e}", "error"
        except anthropic.APIError as e:
            print(f"Error de la API de Claude: {e}")
            return 1
        plan.append((ruta, categoria))
        print(f"[{via:5}] {ruta.name:35} -> {categoria:22} ({razon})")

    if not args.aplicar:
        print("\nModo prueba: no se movió nada. Ejecuta con --aplicar para mover los archivos.")
        return 0

    for ruta, categoria in plan:
        carpeta_destino = carpeta / categoria
        carpeta_destino.mkdir(exist_ok=True)
        shutil.move(str(ruta), str(destino_libre(carpeta_destino / ruta.name)))
    print(f"\nListo: {len(plan)} archivos organizados en {carpeta}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
