# IA organizador de files

CLI que revisa una carpeta, decide la categoría de cada archivo (factura, notas, código, receta…) y los mueve a subcarpetas. Es un proyecto chico para aprender el patrón de orquestación más simple: **routing**.

## Qué se aprende aquí

**Routing** es mandar cada entrada por el camino que le corresponde. En este proyecto el router tiene dos caminos:

```
archivo ──► ¿la extensión ya lo dice? ──sí──► categoría por regla (gratis, instantáneo)
                       │
                       no
                       ▼
            Claude lee un fragmento ──► categoría + razón (JSON validado)
```

- **Reglas primero, IA después.** Un `.png` no necesita un modelo para saber que es una imagen. Usar la IA solo donde hace falta ahorra dinero y tiempo, y es un principio que se repite en cualquier sistema de automatización.
- **Leer un fragmento, no todo.** Para clasificar basta con los primeros 1500 caracteres (`MAX_CARACTERES`). Es la idea básica detrás del *chunking*: al modelo se le pasa solo la parte del texto que necesita.
- **Structured outputs.** La respuesta de Claude se restringe con un JSON Schema (`output_config.format`) cuya categoría es un `enum`. El modelo no puede inventar categorías y el programa no tiene que interpretar texto libre.
- **Modo prueba por defecto.** Primero muestra el plan; solo mueve archivos con `--aplicar`. Es una buena práctica para cualquier automatización que modifique cosas.

## Estructura

| Archivo | Para qué sirve |
|---|---|
| `organizer.py` | CLI y router: reglas por extensión, clasificación con IA, movimiento de archivos |
| `llm.py` | Cliente de Claude: helper para pedir JSON validado y manejo de rechazos |
| `ejemplos/` | Archivos de prueba para ver el router en acción |

## Requisitos

- Python 3.10 o superior
- Una API key de Anthropic ([console.anthropic.com](https://console.anthropic.com))

## Instalación

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
export ANTHROPIC_API_KEY="tu-api-key"   # Windows: set ANTHROPIC_API_KEY=tu-api-key
```

## Uso

```bash
# 1. Ver el plan sin mover nada
python organizer.py ejemplos

# 2. Mover los archivos de verdad
python organizer.py ejemplos --aplicar
```

Salida de ejemplo:

```
[IA   ] datos_varios.csv                    -> otros                  (Datos tabulares de mediciones climáticas)
[IA   ] documento_sin_nombre.txt            -> documentos_personales  (Es un currículum vitae)
[IA   ] factura_marzo.txt                   -> facturas               (Factura con proveedor, IVA y total a pagar)
[regla] limpiar_logs.sh                     -> codigo                 (regla por extensión .sh)
[IA   ] pan_de_banano.txt                   -> recetas                (Lista de ingredientes y preparación)
[IA   ] reunion_lunes.md                    -> notas                  (Notas de una reunión de equipo)
```

> El archivo `documento_sin_nombre.txt` muestra por qué hace falta la IA: el nombre no dice nada, pero el contenido es un CV.

## Configuración

| Variable | Valor por defecto | Descripción |
|---|---|---|
| `ANTHROPIC_API_KEY` | — | Tu API key (obligatoria) |
| `CLAUDE_MODEL` | `claude-opus-5-5` | Modelo a usar. Para clasificar, uno más barato como `claude-haiku-5-5` suele alcanzar |

Las categorías y las reglas se editan al inicio de `organizer.py` (`CATEGORIAS` y `REGLAS_POR_EXTENSION`).

## Ideas para seguir aprendiendo

1. Agregar una caché (por ejemplo, un JSON con el hash de cada archivo) para no reclasificar lo que ya se clasificó.
2. Clasificar en paralelo con `concurrent.futures.ThreadPoolExecutor` para carpetas grandes.
3. Agregar un tercer camino al router: si la IA devuelve "otros", pedirle que proponga una categoría nueva.
4. Leer PDFs con `pypdf` y clasificarlos por su primera página.
