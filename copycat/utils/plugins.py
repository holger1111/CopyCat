"""Plugin system: type filters, renderers and plugin loader."""

import importlib.util
import logging
from pathlib import Path


TYPE_FILTERS: dict = {
    "code": ["*.java", "*.py", "*.spec", "*.cpp", "*.c"],
    "web": ["*.html", "*.css", "*.js", "*.ts", "*.jsx"],
    "db": ["*.sql", "*.db", "*.sqlite", "*.csv"],
    "config": ["*.json", "*.yaml", "*.xml", "*.properties", "*.env"],
    "docs": ["*.md", "*.txt", "*.log", "*.docx"],
    "deps": ["requirements.txt", "package.json", "pom.xml", "go.mod"],
    "img": ["*.png", "*.jpg", "*.gif", "*.bmp", "*.webp", "*.svg", "*.ico"],
    "audio": ["*.mp3", "*.wav", "*.ogg", "*.m4a", "*.flac"],
    "diagram": ["*.drawio", "*.dia", "*.puml"],
    "notebook": ["*.ipynb"],
}

PLUGIN_RENDERERS: dict = {}
_loaded_plugins: list = []


def load_plugins(plugin_dir=None):
    """Lade CopyCat-Plugins aus plugin_dir.

    Jede .py-Datei (außer _*.py) muss definieren::

        TYPE_NAME : str   – eindeutiger Typname
        PATTERNS  : list  – Glob-Muster (z.B. ["*.proto"])

    Optional::

        render_file(path, writer, args)
            Wird beim TXT/Markdown-Report für jede Datei aufgerufen.
            Fehlt diese Funktion, erfolgt Ausgabe via list_binary_file().

    Gibt eine Liste der erfolgreich geladenen Typnamen zurück.
    Fehlerhafte Plugins werden übersprungen (Warnung im Log).
    """
    if plugin_dir is None:
        plugin_dir = Path(__file__).parent.parent.parent / "plugins"
    plugin_dir = Path(plugin_dir)
    if not plugin_dir.is_dir():
        return []
    loaded = []
    for plugin_path in sorted(plugin_dir.glob("*.py")):
        if plugin_path.name.startswith("_"):
            continue
        module_name = plugin_path.stem
        try:
            spec = importlib.util.spec_from_file_location(module_name, plugin_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
        except Exception as exc:
            logging.warning("Plugin '%s' konnte nicht geladen werden: %s", module_name, exc)
            continue
        type_name = getattr(module, "TYPE_NAME", None)
        patterns = getattr(module, "PATTERNS", None)
        if not isinstance(type_name, str) or not type_name:
            logging.warning(
                "Plugin '%s': TYPE_NAME fehlt oder ungültig – übersprungen", module_name
            )
            continue
        if type_name in TYPE_FILTERS:
            logging.warning(
                "Plugin '%s': Typname '%s' ist bereits vergeben – übersprungen",
                module_name,
                type_name,
            )
            continue
        if (
            not isinstance(patterns, list)
            or not patterns
            or not all(isinstance(p, str) and p for p in patterns)
        ):
            logging.warning(
                "Plugin '%s': PATTERNS fehlt oder ungültig – übersprungen", module_name
            )
            continue
        TYPE_FILTERS[type_name] = patterns
        renderer = getattr(module, "render_file", None)
        PLUGIN_RENDERERS[type_name] = renderer if callable(renderer) else None
        _loaded_plugins.append(type_name)
        loaded.append(type_name)
        logging.info("Plugin geladen: %s (%s)", type_name, ", ".join(patterns))
    return loaded
