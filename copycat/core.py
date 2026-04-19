"""CopyCat core: configuration, argument parsing, main run_copycat orchestrator,
diff/merge/hook/watch operations."""

import argparse
import json
import logging
import shutil
import stat
import subprocess
import tempfile
import threading
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

from .exporters.ai import _generate_ai_summary
from .exporters.html import _write_html
from .exporters.json_export import _write_json
from .exporters.md import _write_md
from .exporters.pdf import _write_pdf
from .exporters.template import _write_template
from .exporters.timeline import build_timeline, _timeline_md, _timeline_ascii, _timeline_html
from .exporters.txt import _write_txt
from .utils.cache import _cleanup_cache, _hash_file, _load_cache, _save_cache
from .utils.files import (
    _collect_files,
    get_next_serial_number,
    get_plural,
    is_valid_serial_filename,
    move_to_archive,
)
from .utils.git import get_git_info
from .utils.plugins import TYPE_FILTERS, PLUGIN_RENDERERS, _loaded_plugins, load_plugins
from .utils.search import _build_search_results
from .utils.stats import _build_stats


def load_config(config_path=None):
    """Load copycat.conf and return a dict of raw string settings.

    Search order (first match wins):
    1. config_path  – if explicitly given
    2. CWD / copycat.conf
    3. Script-dir / copycat.conf

    Returns {} when no file is found or on read error.
    """
    if config_path is not None:
        candidates = [Path(config_path)]
    else:
        candidates = [
            Path.cwd() / "copycat.conf",
            Path(__file__).parent.parent / "copycat.conf",
        ]

    for path in candidates:
        if not path.is_file():
            continue
        cfg = {}
        try:
            for raw in path.read_text(encoding="utf-8").splitlines():
                line = raw.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" not in line:
                    continue
                key, _, val = line.partition("=")
                key = key.strip().lower().replace("-", "_")
                val = val.strip()
                if val:
                    cfg[key] = val
        except OSError:
            pass
        return cfg
    return {}


def parse_arguments(config_path=None):
    parser = argparse.ArgumentParser(
        description="CopyCat v2.9 - Projekt-Dokumentierer"
    )
    parser.add_argument(
        "--input", "-i", default=None, help="Eingabeordner (default: Skriptordner)"
    )
    parser.add_argument(
        "--output", "-o", default=None, help="Ausgabeordner (default: Eingabeordner)"
    )
    parser.add_argument(
        "--types",
        "-t",
        nargs="*",
        default=["all"],
        help="Dateitypen: code, web, db, config, docs, deps, img, audio, diagram (oder 'all')",
    )
    parser.add_argument(
        "--recursive",
        "-r",
        action="store_true",
        help="Rekursive Suche in Unterordnern (default: nur Hauptordner)",
    )
    parser.add_argument(
        "--max-size",
        "-s",
        type=float,
        default=float("inf"),
        help="Max Dateigröße in MB (default: keine Grenze)",
    )
    parser.add_argument(
        "--format",
        "-f",
        choices=["txt", "json", "md", "html", "pdf"],
        default="txt",
        help="Ausgabeformat: txt (default), json, md, html, pdf",
    )
    parser.add_argument(
        "--search",
        "-S",
        default=None,
        help="Regex-Suchmuster für Inhaltssuche (z.B. 'TODO|FIXME', 'def ')",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Ausführliche Ausgabe (DEBUG-Level)",
    )
    parser.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        help="Nur Fehler anzeigen (WARNING-Level)",
    )
    parser.add_argument(
        "--diff",
        nargs=2,
        metavar=("REPORT_A", "REPORT_B"),
        help="Vergleiche zwei CopyCat-Reports und zeige Unterschiede (TXT oder JSON)",
    )
    parser.add_argument(
        "--merge",
        nargs="+",
        metavar="REPORT",
        help="Füge mehrere CopyCat-Reports zu einem Merge-Report zusammen",
    )
    parser.add_argument(
        "--install-hook",
        metavar="PROJECT_DIR",
        default=None,
        help="Installiere CopyCat als Git pre-commit Hook im angegebenen Projektordner",
    )
    parser.add_argument(
        "--template",
        metavar="TEMPLATE.j2",
        default=None,
        help="Jinja2-Template für benutzerdefinierte Ausgabe (erfordert: pip install jinja2)",
    )
    parser.add_argument(
        "--watch",
        "-w",
        action="store_true",
        help="Watch-Modus: bei Dateiänderungen Report automatisch neu erzeugen",
    )
    parser.add_argument(
        "--cooldown",
        type=float,
        default=2.0,
        metavar="SEKUNDEN",
        help="Watch: Wartezeit nach letzter Änderung in Sekunden (Standard: 2.0)",
    )
    parser.add_argument(
        "--plugin-dir",
        metavar="DIR",
        default=None,
        help="Verzeichnis mit Plugin-Dateien (.py); Standard: plugins/ neben CopyCat.py",
    )
    parser.add_argument(
        "--list-plugins",
        action="store_true",
        help="Geladene Plugins anzeigen und beenden",
    )
    parser.add_argument(
        "--exclude", "-E",
        nargs="*", default=[], metavar="PATTERN",
        help="Glob-Muster oder Ordner zum Ausschließen, z.B. '*.min.js' 'dist/' 'node_modules/'",
    )
    parser.add_argument(
        "--incremental", "-I",
        action="store_true",
        help="Inkrementeller Modus: nur geänderte Dateien neu scannen, Cache in .copycat_cache/",
    )
    parser.add_argument(
        "--stats",
        action="store_true",
        help="Code-Statistiken ausgeben (LOC, Kommentare, Leerzeilen, zyklomatische Komplexität)",
    )
    parser.add_argument(
        "--git-url",
        metavar="URL",
        default=None,
        help="Remote-Git-Repository klonen und scannen (z.B. https://github.com/user/repo)",
    )
    parser.add_argument(
        "--ai-summary",
        action="store_true",
        help="KI-Zusammenfassung am Ende des Reports anhängen (erfordert: pip install openai, Env-Var COPYCAT_AI_KEY)",
    )
    parser.add_argument(
        "--ai-model",
        default="gpt-4o-mini",
        metavar="MODEL",
        help="KI-Modell für --ai-summary (Standard: gpt-4o-mini; für Ollama z.B. 'llama3')",
    )
    parser.add_argument(
        "--ai-base-url",
        default=None,
        metavar="URL",
        help="Basis-URL für OpenAI-kompatible API (z.B. http://localhost:11434/v1 für Ollama)",
    )
    parser.add_argument(
        "--timeline",
        action="store_true",
        help="Report-Timeline aus dem Archiv ausgeben und beenden",
    )
    parser.add_argument(
        "--timeline-format",
        choices=["md", "ascii", "html"],
        default="md",
        metavar="FORMAT",
        help="Format für --timeline: md (default), ascii, html",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Trockenlauf: zeigt was gemacht würde, ohne Änderungen zu speichern",
    )
    parser.add_argument(
        "--cache-max-age",
        type=int,
        default=None,
        metavar="TAGE",
        help="Cache-Einträge älter als N Tage löschen (z.B. --cache-max-age 30)",
    )
    parser.add_argument(
        "--cache-clean",
        action="store_true",
        help="Gesamten Cache löschen und beenden",
    )

    # ── Config-Datei: Defaults aus copycat.conf (CLI überschreibt) ──────────
    cfg = load_config(config_path)

    _KNOWN_CONFIG_KEYS = {
        "types", "recursive", "max_size_mb", "format", "search",
        "input", "output", "exclude", "incremental", "stats",
        "git_url", "ai_model", "ai_base_url",
    }
    for _key in cfg:
        if _key not in _KNOWN_CONFIG_KEYS:
            logging.warning(
                "copycat.conf: unbekannter Schlüssel '%s' wird ignoriert "
                "(Tippfehler? Gültige Schlüssel: %s)",
                _key, ", ".join(sorted(_KNOWN_CONFIG_KEYS)),
            )

    overrides = {}
    if "types" in cfg:
        parts = [t.strip() for t in cfg["types"].replace(",", " ").split()]
        if parts:
            overrides["types"] = parts
    if "recursive" in cfg:
        overrides["recursive"] = cfg["recursive"].lower() in ("true", "yes", "1")
    if "max_size_mb" in cfg:
        try:
            overrides["max_size"] = float(cfg["max_size_mb"])
        except ValueError:
            logging.warning("copycat.conf: ungültiger max_size_mb-Wert wird ignoriert")
    if "format" in cfg:
        if cfg["format"] in ("txt", "json", "md", "html", "pdf"):
            overrides["format"] = cfg["format"]
        else:
            logging.warning("copycat.conf: ungültiger format-Wert wird ignoriert")
    if "search" in cfg:
        overrides["search"] = cfg["search"]
    if "input" in cfg:
        overrides["input"] = cfg["input"]
    if "output" in cfg:
        overrides["output"] = cfg["output"]
    if "exclude" in cfg:
        parts = [p.strip() for p in cfg["exclude"].replace(",", " ").split() if p.strip()]
        if parts:
            overrides["exclude"] = parts
    if "incremental" in cfg:
        overrides["incremental"] = cfg["incremental"].lower() in ("true", "yes", "1")
    if "stats" in cfg:
        overrides["stats"] = cfg["stats"].lower() in ("true", "yes", "1")
    if "git_url" in cfg:
        overrides["git_url"] = cfg["git_url"]
    if "ai_model" in cfg:
        overrides["ai_model"] = cfg["ai_model"]
    if "ai_base_url" in cfg:
        overrides["ai_base_url"] = cfg["ai_base_url"]
    if overrides:
        parser.set_defaults(**overrides)
    # ────────────────────────────────────────────────────────────────────────

    args = parser.parse_args()

    if args.types and len(args.types) == 1 and "," in args.types[0]:
        args.types = [t.strip() for t in args.types[0].split(",")]

    if args.exclude and len(args.exclude) == 1 and "," in args.exclude[0]:
        args.exclude = [p.strip() for p in args.exclude[0].split(",") if p.strip()]

    return args


def diff_reports(path_a: Path, path_b: Path) -> str:
    """Compare two CopyCat reports (TXT or JSON) and return a formatted diff summary."""

    def _parse_txt(text: str) -> dict:
        import re
        m = re.search(r"CopyCat v[\d.]+ \| (.+?) \|", text)
        date_str = m.group(1) if m else "unbekannt"
        type_counts = {
            mo.group(1).lower(): int(mo.group(2))
            for mo in re.finditer(r"^(\w+): (\d+) Datei", text, re.MULTILINE)
        }
        files = {fm.group(1) for fm in re.finditer(r"^----- (.+?) -----$", text, re.MULTILINE)}
        return {"date": date_str, "types": type_counts, "files": files}

    def _parse_json_report(text: str) -> dict:
        data = json.loads(text)
        date_str = data.get("generated", "unbekannt")
        type_counts = data.get("types", {})
        files = {
            e["name"]
            for entries in data.get("details", {}).values()
            for e in entries
        }
        return {"date": date_str, "types": type_counts, "files": files}

    def _parse_report(path: Path) -> dict:
        text = path.read_text(encoding="utf-8")
        return _parse_json_report(text) if path.suffix.lower() == ".json" else _parse_txt(text)

    info_a = _parse_report(path_a)
    info_b = _parse_report(path_b)
    added = info_b["files"] - info_a["files"]
    removed = info_a["files"] - info_b["files"]
    unchanged = info_a["files"] & info_b["files"]

    lines = [
        "CopyCat Diff-Report",
        "=" * 60,
        f"A: {path_a.name}  ({info_a['date']})",
        f"B: {path_b.name}  ({info_b['date']})",
        "",
    ]

    all_types = sorted(set(info_a["types"]) | set(info_b["types"]))
    change_lines = []
    for t in all_types:
        cnt_a = info_a["types"].get(t, 0)
        cnt_b = info_b["types"].get(t, 0)
        if cnt_a != cnt_b:
            delta = cnt_b - cnt_a
            sign = "+" if delta > 0 else ""
            change_lines.append(f"  {t.upper():<12} {cnt_a} \u2192 {cnt_b}  ({sign}{delta})")
    if change_lines:
        lines.append("Typ-\u00c4nderungen:")
        lines += change_lines
        lines.append("")

    if added:
        lines.append(f"Neu (+{len(added)}):")
        for f in sorted(added):
            lines.append(f"  + {f}")
        lines.append("")

    if removed:
        lines.append(f"Entfernt (-{len(removed)}):")
        for f in sorted(removed):
            lines.append(f"  - {f}")
        lines.append("")

    if not added and not removed and not change_lines:
        lines.append("Keine \u00c4nderungen.")
    else:
        lines.append(f"Unver\u00e4ndert: {len(unchanged)} {get_plural(len(unchanged))}")

    return "\n".join(lines) + "\n"


def install_hook(project_dir: Path) -> Path:
    """Install a CopyCat pre-commit Git hook in project_dir/.git/hooks/pre-commit.

    The hook runs CopyCat (--quiet) before every commit and stages the
    generated report automatically.

    Raises FileNotFoundError when no .git/hooks directory is found.
    """
    hook_dir = project_dir / ".git" / "hooks"
    if not hook_dir.is_dir():
        raise FileNotFoundError(
            f"Kein Git-Repository in '{project_dir}' (.git/hooks fehlt)"
        )
    script_path = Path(__file__).resolve().parent.parent / "CopyCat.py"
    hook_path = hook_dir / "pre-commit"
    hook_content = (
        "#!/bin/sh\n"
        "# CopyCat pre-commit hook – automatisch installiert\n"
        f'python "{script_path}" --quiet\n'
        "git add combined_copycat_*.txt combined_copycat_*.json "
        "combined_copycat_*.md combined_copycat_*.html 2>/dev/null || true\n"
    )
    hook_path.write_text(hook_content, encoding="utf-8")
    try:
        hook_path.chmod(
            hook_path.stat().st_mode
            | stat.S_IXUSR
            | stat.S_IXGRP
            | stat.S_IXOTH
        )
    except OSError:
        pass
    return hook_path


def merge_reports(paths: list, output: Path = None) -> str:
    """Merge multiple CopyCat TXT/JSON reports into one combined report string."""
    sections = []
    for path in paths:
        text = path.read_text(encoding="utf-8")
        if path.suffix.lower() == ".json":
            try:
                data = json.loads(text)
                header = f"=== {path.name}  ({data.get('generated', '?')}) ==="
                sub_lines = [header]
                for t, entries in data.get("details", {}).items():
                    if entries:
                        sub_lines.append(
                            f"{t.upper()}: {len(entries)} {get_plural(len(entries))}"
                        )
                        for e in entries:
                            sub_lines.append(f"  {e.get('path', e.get('name', '?'))}")
                sections.append("\n".join(sub_lines))
            except (json.JSONDecodeError, KeyError) as exc:
                sections.append(f"=== {path.name} [FEHLER: {exc}] ===")
        else:
            sections.append(f"=== {path.name} ===\n{text.strip()}")

    separator = "\n\n" + "\u2500" * 60 + "\n\n"
    merged = (
        "=" * 60 + "\n"
        f"CopyCat Merge-Report | {datetime.now().strftime('%d.%m.%Y %H:%M')}\n"
        f"{len(paths)} {get_plural(len(paths))} zusammengef\u00fchrt\n"
        + "=" * 60 + "\n\n"
        + separator.join(sections)
        + "\n"
    )
    if output is not None:
        output.write_text(merged, encoding="utf-8")
    return merged


def watch_and_run(args, cooldown: float = 2.0, stop_event=None):
    """Watch the input directory for changes and re-run CopyCat.

    Requires: pip install watchdog
    Blocks until stop_event is set (or KeyboardInterrupt in CLI mode).
    Raises ImportError when watchdog is not installed.
    """
    try:
        from watchdog.observers import Observer
        from watchdog.events import FileSystemEventHandler
    except ImportError as exc:
        raise ImportError(
            "watchdog ist nicht installiert. Bitte: pip install watchdog"
        ) from exc

    input_dir = Path(args.input or str(Path(__file__).parent.parent))
    if stop_event is None:
        stop_event = threading.Event()

    last_event_time = [0.0]

    class _Handler(FileSystemEventHandler):
        def on_any_event(self, event):
            if not event.is_directory:
                last_event_time[0] = time.monotonic()

    observer = Observer()
    observer.schedule(
        _Handler(), str(input_dir), recursive=getattr(args, "recursive", False)
    )
    observer.start()
    logging.info(
        "Watch: %s | Cooldown: %.1fs | stop_event.set() zum Beenden",
        input_dir, cooldown,
    )

    try:
        while not stop_event.is_set():
            time.sleep(0.25)
            t = last_event_time[0]
            if t > 0.0 and (time.monotonic() - t) >= cooldown:
                last_event_time[0] = 0.0
                logging.info("Änderung erkannt – erzeuge Report...")
                try:
                    run_copycat(args)
                except Exception:
                    logging.exception("Watch-Fehler beim Re-Run")
    finally:
        observer.stop()
        observer.join()


def run_copycat(args):
    git_url = getattr(args, "git_url", None)
    _tmp_dir_obj = None

    plugin_dir = getattr(args, "plugin_dir", None)
    if plugin_dir:
        load_plugins(plugin_dir)
    script_file = Path(__file__).resolve()
    script_dir = Path(__file__).parent.parent  # workspace root

    # ── Git-URL: Remote-Repository klonen ───────────────────────────────────
    if git_url:
        try:
            parsed = urlparse(git_url)
            scheme = parsed.scheme.lower()
            if scheme not in ("https", "git", "ssh") and not git_url.startswith("git@"):
                logging.error("Ungültiges Git-URL-Schema: %s", scheme)
                return None
            dangerous_chars = [";", "&", "|", "`", "$", "(", ")", "\n", "\r"]
            if any(char in git_url for char in dangerous_chars):
                logging.error("Git-URL enthält verdächtige Zeichen")
                return None
        except Exception:  # pragma: no cover
            logging.exception("Git-URL Validierung fehlgeschlagen")  # pragma: no cover
            return None  # pragma: no cover
        _tmp_dir_obj = tempfile.TemporaryDirectory()
        tmp_clone = Path(_tmp_dir_obj.name) / "repo"
        logging.info("Klone Repository (mit Sicherheitsprüfung): %s", git_url)
        try:
            result = subprocess.run(
                ["git", "clone", "--depth", "1", "--", git_url, str(tmp_clone)],
                capture_output=True, text=True, timeout=120,
            )
        except FileNotFoundError:
            logging.error("git ist nicht installiert oder nicht im PATH")
            _tmp_dir_obj.cleanup()
            return None
        except subprocess.TimeoutExpired:
            logging.error("git clone Timeout nach 120 Sekunden: %s", git_url)
            _tmp_dir_obj.cleanup()
            return None
        if result.returncode != 0:
            logging.error("git clone fehlgeschlagen: %s", result.stderr.strip())
            _tmp_dir_obj.cleanup()
            return None
        input_dir = tmp_clone
        output_dir = Path(args.output or str(script_dir))
    else:
        input_dir = Path(args.input or str(script_dir))
        output_dir = Path(args.output or str(input_dir))
    # ────────────────────────────────────────────────────────────────────────

    output_dir.mkdir(exist_ok=True)

    if not input_dir.is_dir():
        logging.error("Fehler: %s ist kein Ordner", input_dir)
        if _tmp_dir_obj is not None:
            _tmp_dir_obj.cleanup()
        return None

    # ── Cache-Clean: Gesamten Cache löschen und beenden ─────────────────────
    if getattr(args, "cache_clean", False):
        cache_dir = output_dir / ".copycat_cache"
        cache_file = cache_dir / "cache.json"
        if cache_file.is_file():
            try:
                cache_file.unlink()
                logging.info("Cache vollständig gelöscht: %s", cache_file)
                print(f"\n✓ Cache gelöscht: {cache_file}")
            except OSError:
                logging.exception("Cache-Datei konnte nicht gelöscht werden")
        else:
            logging.info("Kein Cache vorhanden: %s", cache_file)
            print(f"\nKein Cache vorhanden: {cache_file}")
        if _tmp_dir_obj:
            _tmp_dir_obj.cleanup()
        return None

    fmt = getattr(args, "format", "txt")
    files = _collect_files(args, input_dir, script_file)

    serial = get_next_serial_number(output_dir)
    new_file = output_dir / f"combined_copycat_{serial}.{fmt}"

    existing = list(output_dir.glob("combined_copycat*"))
    to_archive = [
        f for f in existing if f != new_file and is_valid_serial_filename(f.name)
    ]
    logging.info("Archiviere %d Datei(en)", len(to_archive))
    for old_file in to_archive:
        move_to_archive(output_dir, old_file.name)

    git_info = get_git_info(input_dir)

    search_pattern = getattr(args, "search", None)
    if search_pattern:
        logging.info('Suche nach Muster: "%s"', search_pattern)
    search_results = _build_search_results(files, search_pattern) if search_pattern else {}

    # ── Inkrementeller Cache ─────────────────────────────────────────────────
    cache_map: dict = {}
    if getattr(args, "incremental", False):
        cache_dir = output_dir / ".copycat_cache"
        cache_file = cache_dir / "cache.json"

        cache_max_age = getattr(args, "cache_max_age", None)
        if cache_max_age and cache_max_age > 0:
            _cleanup_cache(cache_dir, cache_max_age)

        raw_cache = _load_cache(cache_file)
        new_entries: dict = {}
        for code_file in files.get("code", []):
            rel_key = code_file.relative_to(input_dir).as_posix()
            current_hash = _hash_file(code_file)
            cached = raw_cache.get(rel_key, {})
            if current_hash and current_hash == cached.get("hash"):
                cache_map[code_file] = {
                    "lines": cached.get("lines", 0),
                    "content": cached.get("content", ""),
                    "from_cache": True,
                }
                new_entries[rel_key] = cached
                logging.debug("Cache-Treffer: %s", rel_key)
            else:
                try:
                    content = code_file.read_text(encoding="utf-8")
                    lines = sum(1 for line in content.splitlines() if line.strip())
                except UnicodeDecodeError:
                    content = "(Binary oder ung\u00fcltiges Encoding - \u00fcbersprungen)"
                    lines = 1
                except Exception:
                    content = "(Fehler beim Lesen)"
                    lines = 0
                new_entries[rel_key] = {"hash": current_hash, "lines": lines, "content": content}
                cache_map[code_file] = {"lines": lines, "content": content, "from_cache": False}
        _save_cache(cache_file, new_entries)
        n_cached = sum(1 for f in files.get("code", []) if f in cache_map and
                       new_entries.get(f.relative_to(input_dir).as_posix(), {}).get("hash")
                       == raw_cache.get(f.relative_to(input_dir).as_posix(), {}).get("hash"))
        n_changed = len(files.get("code", [])) - n_cached
        logging.info("Inkrementell: %d aus Cache, %d neu/ge\u00e4ndert", n_cached, n_changed)

    # ── Code-Statistiken ─────────────────────────────────────────────────────
    stats_map = None
    if getattr(args, "stats", False):
        stats_map = _build_stats(files, cache_map)
        t = stats_map["total"]
        logging.info(
            "Code-Statistiken: %d Dateien | %d LOC | %d Code | %d Kommentar | %d Leer | Ø Kompl. %s",
            len(stats_map["per_file"]), t["loc"], t["code"], t["comments"], t["blank"],
            t["avg_complexity"] if t["avg_complexity"] is not None else "–",
        )

    template_path = getattr(args, "template", None)

    # ── DRY-RUN ──────────────────────────────────────────────────────────────
    if getattr(args, "dry_run", False):
        total_files = sum(len(flist) for flist in files.values())
        logging.info("*** DRY-RUN MODE ***")
        logging.info("Würde scannen: %d Dateien | Würde erstellen: 1 Report (%s)", total_files, fmt)
        if getattr(args, "archive_move", False):
            logging.info("Würde verschieben: Dateien ins Archiv")
        print(f"\n✓ DRY-RUN: Würde {total_files} Dateien scannen und Report als {fmt} erstellen")
        if _tmp_dir_obj:
            _tmp_dir_obj.cleanup()
        return None

    if template_path:
        content = _write_template(
            template_path, files, args, input_dir, git_info, serial,
            search_pattern, search_results,
        )
        with open(new_file, "w", encoding="utf-8") as writer:
            writer.write(content)
    elif fmt == "json":
        _write_json(new_file, files, args, input_dir, git_info, serial,
                    search_pattern, search_results, cache_map, stats_map)
    elif fmt == "md":
        with open(new_file, "w", encoding="utf-8") as writer:
            _write_md(writer, files, args, input_dir, git_info, serial,
                      search_pattern, search_results, cache_map, stats_map)
    elif fmt == "html":
        _write_html(new_file, files, args, input_dir, git_info, serial,
                    search_pattern, search_results, cache_map, stats_map)
    elif fmt == "pdf":
        _write_pdf(new_file, files, args, input_dir, git_info, serial,
                   search_pattern, search_results, cache_map, stats_map)
    else:
        with open(new_file, "w", encoding="utf-8") as writer:
            _write_txt(writer, files, args, input_dir, git_info, serial,
                       search_pattern, search_results, cache_map, stats_map)

    # ── KI-Zusammenfassung ───────────────────────────────────────────────────
    if getattr(args, "ai_summary", False):
        logging.info("Generiere KI-Zusammenfassung...")
        try:
            ai_text = _generate_ai_summary(
                files, input_dir, git_info, stats_map,
                model=getattr(args, "ai_model", "gpt-4o-mini"),
                base_url=getattr(args, "ai_base_url", None),
            )
            if fmt == "json":
                with open(new_file, "r", encoding="utf-8") as fh:
                    _report_data = json.load(fh)
                _report_data["ai_summary"] = ai_text
                with open(new_file, "w", encoding="utf-8") as fh:
                    json.dump(_report_data, fh, ensure_ascii=False, indent=2)
            elif fmt == "html":
                from .exporters.html import _html_escape
                _html_content = new_file.read_text(encoding="utf-8")
                _ai_section = (
                    f'<section style="margin-top:24px">\n'
                    f'<h2>\U0001f916 KI-Zusammenfassung</h2>\n'
                    f'<p style="background:#fff;padding:16px;border-radius:8px;'
                    f'box-shadow:0 1px 3px rgba(0,0,0,.1);white-space:pre-wrap">'
                    f'{_html_escape(ai_text)}</p>\n</section>\n'
                )
                new_file.write_text(
                    _html_content.replace("</body>", _ai_section + "</body>"),
                    encoding="utf-8",
                )
            elif fmt == "pdf":
                logging.warning(
                    "KI-Zusammenfassung im PDF-Format nur als Log-Ausgabe verfügbar."
                )
                logging.info("KI-Zusammenfassung:\n%s", ai_text)
            else:  # txt, md
                with open(new_file, "a", encoding="utf-8") as fh:
                    if fmt == "md":
                        fh.write(f"\n## \U0001f916 KI-Zusammenfassung\n\n{ai_text}\n")
                    else:
                        fh.write(
                            f"\n{'=' * 20} KI-ZUSAMMENFASSUNG {'=' * 20}\n{ai_text}\n"
                        )
            logging.info("KI-Zusammenfassung erfolgreich hinzugefügt.")
        except (ImportError, ValueError) as exc:
            logging.warning("KI-Zusammenfassung fehlgeschlagen: %s", exc)

    logging.info("Erstellt: %s", new_file)
    if _tmp_dir_obj is not None:
        _tmp_dir_obj.cleanup()
    return str(new_file)
