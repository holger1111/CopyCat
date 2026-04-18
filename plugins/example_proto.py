"""Beispiel-Plugin für CopyCat: Protobuf (.proto) Dateityp.

Kopiere diese Datei als Vorlage für eigene Typen.

Pflicht:
    TYPE_NAME : str  – eindeutiger Typname (darf kein eingebauter Typ sein)
    PATTERNS  : list – Glob-Muster (z.B. ["*.proto"])

Optional:
    render_file(path, writer, args) – benutzerdefinierter Renderer
        path   : pathlib.Path – die zu rendernde Datei
        writer : file-like     – Ausgabe-Writer
        args   : argparse.Namespace – CopyCat-Argumente
"""
TYPE_NAME = "proto"
PATTERNS = ["*.proto"]


def render_file(path, writer, args):
    """Protobuf-Datei als Text ausgeben."""
    writer.write(f"[PROTO: {path.name}]\n")
    try:
        writer.write(path.read_text(encoding="utf-8"))
        writer.write("\n")
    except UnicodeDecodeError:
        writer.write("[Binäre Datei – übersprungen]\n")
    except OSError as exc:
        writer.write(f"[Fehler: {exc}]\n")
