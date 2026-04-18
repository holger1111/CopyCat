"""
CopyCat v2.9
"""

import argparse
import concurrent.futures
import hashlib
import importlib.util
import json
import stat
import tempfile
import threading
import time
import xml.etree.ElementTree as ET
import shutil
import re
import logging
import struct
import subprocess
import fnmatch
import zipfile
import base64
import zlib
from urllib.parse import unquote
from pathlib import Path
from datetime import datetime


def load_config(config_path=None):
    """Load copycat.conf and return a dict of raw string settings.

    Search order (first match wins):
    1. config_path  – if explicitly given
    2. CWD / copycat.conf
    3. Script-dir / copycat.conf

    Returns {} when no file is found or on read error.
    Supported keys: types, recursive, max_size_mb, format, search, input, output
    """
    if config_path is not None:
        candidates = [Path(config_path)]
    else:
        candidates = [
            Path.cwd() / "copycat.conf",
            Path(__file__).parent / "copycat.conf",
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
        choices=["txt", "json", "md", "html"],
        default="txt",
        help="Ausgabeformat: txt (default), json, md, html",
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
        help="Jinja2-Template f\u00fcr benutzerdefinierte Ausgabe (erfordert: pip install jinja2)",
    )
    parser.add_argument(
        "--watch",
        "-w",
        action="store_true",
        help="Watch-Modus: bei Datei\u00e4nderungen Report automatisch neu erzeugen",
    )
    parser.add_argument(
        "--cooldown",
        type=float,
        default=2.0,
        metavar="SEKUNDEN",
        help="Watch: Wartezeit nach letzter \u00c4nderung in Sekunden (Standard: 2.0)",
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

    # ── Config-Datei: Defaults aus copycat.conf (CLI überschreibt) ──────────
    cfg = load_config(config_path)
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
        if cfg["format"] in ("txt", "json", "md", "html"):
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
    if overrides:
        parser.set_defaults(**overrides)
    # ────────────────────────────────────────────────────────────────────────

    args = parser.parse_args()

    if args.types and len(args.types) == 1 and ',' in args.types[0]:
        args.types = [t.strip() for t in args.types[0].split(',')]

    if args.exclude and len(args.exclude) == 1 and ',' in args.exclude[0]:
        args.exclude = [p.strip() for p in args.exclude[0].split(',') if p.strip()]

    return args


def is_valid_serial_filename(filename: str) -> bool:
    pattern = r"^combined_copycat_(\d+)\.(txt|json|md|html)$"
    return bool(re.match(pattern, filename))


def get_next_serial_number(base_path: Path) -> int:
    existing = list(base_path.glob("combined_copycat*"))
    max_num = 0
    for p in existing:
        if is_valid_serial_filename(p.name):
            try:
                match = re.match(r"^combined_copycat_(\d+)\.(txt|json|md|html)$", p.name)
                num = int(match.group(1))
                max_num = max(max_num, num)
            except (ValueError, AttributeError):  # pragma: no cover
                continue
    return max_num + 1


def move_to_archive(base_path: Path, filename: str):
    archive_path = base_path / "CopyCat_Archive"
    archive_path.mkdir(exist_ok=True)

    old_file = base_path / filename
    if old_file.exists() and is_valid_serial_filename(filename):
        try:
            shutil.move(old_file, archive_path / filename)
        except (shutil.Error, PermissionError, OSError) as e:
            logging.warning("Archiv-Fehler %s: %s", filename, e)


def list_binary_file(writer, bin_file):
    try:
        size = bin_file.stat().st_size
        if size == 0:
            writer.write(f"[EMPTY: {bin_file.name}]\n")
            return

        with open(bin_file, "rb") as f:
            data = f.read(1024)
        suffix = bin_file.suffix.lower()
        mime_types = {
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".gif": "image/gif",
            ".bmp": "image/bmp",
            ".webp": "image/webp",
            ".wav": "audio/wav",
            ".mp3": "audio/mpeg",
            ".ogg": "audio/ogg",
            ".m4a": "audio/mp4",
            ".flac": "audio/flac",
            ".json": "application/json",
            ".sql": "text/sql",
            ".yaml": "text/yaml",
            ".xml": "text/xml",
            ".html": "text/html",
            ".css": "text/css",
            ".md": "text/markdown",
            ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            ".csv": "text/csv",
        }
        mime = mime_types.get(suffix, "application/octet-stream")
        duration = "N/A"
        if suffix == ".wav" and size > 44:
            frames = struct.unpack("<I", data[4:8])[0]
            rate = struct.unpack("<I", data[24:28])[0]
            duration = f"{frames / rate:.2f}s"

        dur_info = f" [DUR: {duration}]" if "audio" in mime else ""
        writer.write(f"[BINARY: {bin_file.name}] [MIME: {mime}] [SIZE: {size} bytes]{dur_info}\n")
    except UnicodeDecodeError:
        writer.write(f"[BINARY SKIPPED: {bin_file.name} - Ungültiges Text-Encoding]\n")
    except (struct.error, OSError) as e:
        writer.write(f"[BINARY ERROR: {bin_file.name} - {str(e)}]\n")
    except Exception as e:
        logging.error(f"Unexpected error in list_binary_file {bin_file.name}: {e}")
        writer.write(f"[ERROR: {bin_file.name}]\n")


def _decode_drawio_compressed(data: str) -> str:
    """Decode Base64/zlib (raw deflate)/URL-encoded draw.io diagram content."""
    raw = base64.b64decode(data)
    xml_bytes = zlib.decompress(raw, wbits=-15)
    return unquote(xml_bytes.decode("utf-8"))


def _collect_cells(tree) -> list:
    """Collect mxCell elements from tree, decompressing diagram content if needed."""
    cells = list(tree.iter("mxCell"))
    if cells:
        return cells
    for diagram in tree.iter("diagram"):
        text = (diagram.text or "").strip()
        if not text:
            continue
        try:
            inner_xml = _decode_drawio_compressed(text)
            inner_tree = ET.fromstring(inner_xml)
            cells.extend(inner_tree.iter("mxCell"))
        except Exception:
            pass
    return cells


def _write_cells(writer, drawio_file, tree):
    """Count and write mxCell entries from tree (compressed or plain)."""
    cells_list = _collect_cells(tree)
    cells, texts = 0, 0
    unique_values = set()
    for cell in cells_list:
        cells += 1
        value = cell.attrib.get("value", "").strip()
        if value:
            texts += 1
            unique_values.add(value)
            geo = cell.find("mxGeometry")
            pos = ""
            if geo is not None:
                x = geo.attrib.get("x")
                y = geo.attrib.get("y")
                if x is not None and y is not None:
                    pos = f" (x={x}, y={y})"
            writer.write(f"  [{cell.attrib.get('id','?')}] {value[:50]}...{pos}\n")
    unique = len(unique_values)
    writer.write(f"DIAGRAM {drawio_file.name}: {cells} Cells, {texts} Texte, {unique} Unique\n")


def extract_drawio(writer, drawio_file):
    try:
        size = drawio_file.stat().st_size
        if size == 0:
            writer.write(f"[EMPTY: {drawio_file.name}] [SIZE: 0 bytes]\n")
            return

        LIMIT_BYTES = 1_048_576  # 1MB
        if size > LIMIT_BYTES:
            writer.write(f"[SKIPPED: {drawio_file.name} - exceeds 1MB limit]\n")
            return

        with open(drawio_file, "r", encoding="utf-8") as f:
            xml_content = f.read()

        tree = ET.fromstring(xml_content)
        _write_cells(writer, drawio_file, tree)

    except ET.ParseError as e:
        writer.write(f"[XML PARSE ERROR: {drawio_file.name} - {str(e)}]\n")
    except UnicodeDecodeError:
        try:
            with zipfile.ZipFile(drawio_file, "r") as zf:
                xml_names = [n for n in zf.namelist() if n.endswith(".xml") or n.endswith(".drawio")]
                if not xml_names:
                    xml_names = zf.namelist()
                if not xml_names:
                    writer.write(f"[ZIP EMPTY: {drawio_file.name}]\n")
                    return
                with zf.open(xml_names[0]) as xf:
                    xml_content = xf.read().decode("utf-8")
            tree = ET.fromstring(xml_content)
            _write_cells(writer, drawio_file, tree)
        except zipfile.BadZipFile:
            writer.write(f"[BINARY: {drawio_file.name} - Invalid Encoding]\n")
        except ET.ParseError as e:
            writer.write(f"[XML PARSE ERROR: {drawio_file.name} - {str(e)}]\n")


def extract_notebook(writer, nb_file):
    """Extract code and markdown cells from a Jupyter Notebook (.ipynb)."""
    try:
        with open(nb_file, "r", encoding="utf-8") as f:
            nb = json.load(f)
        cells = nb.get("cells", [])
        code_cells = [c for c in cells if c.get("cell_type") == "code"]
        md_cells = [c for c in cells if c.get("cell_type") == "markdown"]
        writer.write(
            f"NOTEBOOK {nb_file.name}: {len(cells)} Cells "
            f"({len(code_cells)} Code, {len(md_cells)} Markdown)\n"
        )
        for i, cell in enumerate(cells, 1):
            ctype = cell.get("cell_type", "unknown")
            source = "".join(cell.get("source", []))
            if source.strip():
                writer.write(f"  [Cell {i} \u2013 {ctype}]\n")
                for line in source.splitlines():
                    writer.write(f"  {line}\n")
                writer.write("\n")
    except (json.JSONDecodeError, KeyError) as e:
        writer.write(f"[NOTEBOOK ERROR: {nb_file.name} - {e}]\n")
    except OSError as e:
        writer.write(f"[NOTEBOOK READ ERROR: {nb_file.name} - {e}]\n")


def get_git_info(input_dir: Path) -> str:
    if not (input_dir / ".git").exists():
        return "No Git"
    try:
        branch = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=input_dir,
            capture_output=True,
            text=True,
            timeout=5,
        )
        branch_name = branch.stdout.strip() if branch.returncode == 0 else "N/A"

        commit = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=input_dir,
            capture_output=True,
            text=True,
            timeout=5,
        )
        commit_hash = commit.stdout.strip() if commit.returncode == 0 else "N/A"

        return f"Branch: {branch_name} | Last Commit: {commit_hash}"
    except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
        return "No Git"


def should_skip_gitignore(input_dir: Path, file_path: Path) -> bool:
    try:
        rel = file_path.relative_to(input_dir)
    except ValueError:
        return False

    parts = rel.parts
    current_dir = input_dir

    for i in range(len(parts)):
        gitignore_path = current_dir / ".gitignore"
        if gitignore_path.exists():
            sub_rel = "/".join(parts[i:])
            try:
                skip = False
                with open(gitignore_path, "r", encoding="utf-8") as f:
                    for line in f:
                        rule = line.strip()
                        if rule.startswith("#") or not rule:
                            continue
                        negate = rule.startswith("!")
                        effective_rule = rule[1:] if negate else rule
                        if "*" in effective_rule:
                            matched = fnmatch.fnmatch(sub_rel, effective_rule)
                        elif effective_rule.endswith("/"):
                            base = effective_rule.rstrip("/")
                            matched = sub_rel == base or sub_rel.startswith(base + "/")
                        else:
                            matched = sub_rel == effective_rule
                        if matched:
                            skip = not negate
                if skip:
                    return True
            except Exception:
                pass
        if i < len(parts) - 1:
            current_dir = current_dir / parts[i]

    return False


def get_plural(count):
    return "Datei" if count == 1 else "Dateien"


def size_filtered_glob(search_method, patterns, max_bytes, script_file, input_dir, exclude_patterns=None):
    total_checked = 0
    for pat in patterns:
        for candidate in search_method(pat):
            total_checked += 1
            try:
                if should_skip_gitignore(input_dir, candidate):
                    continue
                if _should_exclude(candidate, input_dir, exclude_patterns or []):
                    continue
                if candidate.stat().st_size < max_bytes:
                    if (
                        candidate.resolve() != script_file
                        and "combined_copycat" not in candidate.name
                    ):
                        yield candidate
                if total_checked % 100 == 0:
                    logging.debug("Geprüft: %d Dateien...", total_checked)
            except OSError:
                continue
    logging.info("→ %d geprüft, Filter OK", total_checked)


def search_in_file(file_path, pattern):
    """Search regex pattern in a text file. Returns list of (lineno, text) tuples."""
    try:
        compiled = re.compile(pattern)
    except re.error:
        return []
    matches = []
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            for lineno, line in enumerate(f, 1):
                if compiled.search(line):
                    matches.append((lineno, line.rstrip()))
    except (UnicodeDecodeError, OSError):
        pass
    return matches


def _build_search_results(files, pattern):
    """Search pattern in all text-based files in parallel. Returns {Path: [(lineno, text)]}."""
    SEARCHABLE = {"code", "web", "db", "config", "docs", "deps"}
    candidates = [
        f for t, flist in files.items() if t in SEARCHABLE for f in flist
    ]
    if not candidates:
        return {}
    results = {}
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future_to_path = {executor.submit(search_in_file, f, pattern): f for f in candidates}
        for future in concurrent.futures.as_completed(future_to_path):
            f = future_to_path[future]
            hits = future.result()
            if hits:
                results[f] = hits
    return results


def diff_reports(path_a: Path, path_b: Path) -> str:
    """Compare two CopyCat reports (TXT or JSON) and return a formatted diff summary."""

    def _parse_txt(text: str) -> dict:
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
    script_path = Path(__file__).resolve()
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
    """Merge multiple CopyCat TXT/JSON reports into one combined report string.

    Each report is included as a labelled section.  If *output* is given, the
    merged text is also written to that file.
    """
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


def _write_template(
    template_path, files, args, input_dir, git_info, serial,
    search_pattern=None, search_results=None,
):
    """Render a Jinja2 template with CopyCat report context.

    Requires: pip install jinja2
    Raises ImportError when jinja2 is not installed.
    Raises ValueError on template I/O or rendering errors.
    """
    try:
        from jinja2 import Template, TemplateError
    except ImportError as exc:
        raise ImportError(
            "jinja2 ist nicht installiert. Bitte: pip install jinja2"
        ) from exc

    try:
        source = Path(template_path).read_text(encoding="utf-8")
    except OSError as exc:
        raise ValueError(f"Template-Datei nicht lesbar: {exc}") from exc
    try:
        tmpl = Template(source)
    except TemplateError as exc:
        raise ValueError(f"Template-Syntaxfehler: {exc}") from exc

    type_data = {
        t: [
            {
                "name": f.name,
                "path": f.relative_to(input_dir).as_posix(),
                "size": f.stat().st_size,
            }
            for f in flist
        ]
        for t, flist in files.items()
        if flist
    }
    sr = search_results or {}
    context = {
        "input_dir": str(input_dir),
        "date": datetime.now().strftime("%d.%m.%Y %H:%M"),
        "git": git_info,
        "serial": serial,
        "mode": "recursive" if args.recursive else "flat",
        "total_files": sum(len(flist) for flist in files.values()),
        "types": type_data,
        "search_pattern": search_pattern,
        "search_results": {
            f.name: [{"line": ln, "text": txt} for ln, txt in hits]
            for f, hits in sr.items()
        },
    }
    try:
        return tmpl.render(**context)
    except TemplateError as exc:
        raise ValueError(f"Template-Renderfehler: {exc}") from exc


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

    input_dir = Path(args.input or str(Path(__file__).parent))
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
                except Exception as exc:
                    logging.error("Watch-Fehler beim Re-Run: %s", exc)
    finally:
        observer.stop()
        observer.join()


TYPE_FILTERS = {
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
        plugin_dir = Path(__file__).parent / "plugins"
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


def _should_exclude(candidate, input_dir, exclude_patterns):
    """Prüft ob candidate auf ein Exclude-Glob-Muster passt."""
    if not exclude_patterns:
        return False
    try:
        rel = str(candidate.relative_to(input_dir)).replace("\\", "/")
    except ValueError:
        rel = candidate.name
    name = candidate.name
    for pattern in exclude_patterns:
        p = pattern.rstrip("/")
        if pattern.endswith("/"):
            if rel.startswith(p + "/") or rel == p:
                return True
        if fnmatch.fnmatch(name, p):
            return True
        if fnmatch.fnmatch(rel, p):
            return True
    return False


# ── Code-Statistiken (Idee 5) ─────────────────────────────────────────────────

# Mapping Dateiendung → Tuple von Zeilenpräfixen, die als Kommentar gewertet werden
_COMMENT_PREFIXES: dict = {
    ".py": ("#", '"""', "'''"),
    ".rb": ("#",), ".sh": ("#",), ".bash": ("#",), ".r": ("#",),
    ".yml": ("#",), ".yaml": ("#",), ".toml": ("#",),
    ".java": ("//", "/*", "*/", "*"), ".c": ("//", "/*", "*/", "*"),
    ".cpp": ("//", "/*", "*/", "*"), ".h": ("//", "/*", "*/", "*"),
    ".cs": ("//", "/*", "*/", "*"), ".js": ("//", "/*", "*/", "*"),
    ".ts": ("//", "/*", "*/", "*"), ".jsx": ("//", "/*", "*/", "*"),
    ".tsx": ("//", "/*", "*/", "*"), ".go": ("//", "/*", "*/", "*"),
    ".swift": ("//", "/*", "*/", "*"), ".kt": ("//", "/*", "*/", "*"),
    ".scala": ("//", "/*", "*/", "*"), ".groovy": ("//", "/*", "*/", "*"),
    ".sql": ("--", "/*", "*/"),
    ".html": ("<!--",), ".xml": ("<!--",), ".svg": ("<!--",),
    ".css": ("/*", "*/", "*"), ".less": ("/*", "*/", "*"), ".scss": ("/*", "*/", "*"),
}


def _analyse_file(path: Path) -> dict:
    """Analyse a source file: count LOC, blank, comment, code lines + cyclomatic complexity."""
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return {"loc": 0, "code": 0, "comments": 0, "blank": 0, "complexity": None}
    lines = text.splitlines()
    suffix = path.suffix.lower()
    comment_prefixes = _COMMENT_PREFIXES.get(suffix, ("#",))
    blank = sum(1 for ln in lines if not ln.strip())
    comments = sum(
        1 for ln in lines
        if ln.strip() and any(ln.strip().startswith(p) for p in comment_prefixes)
    )
    code = max(len(lines) - blank - comments, 0)
    complexity = None
    if suffix == ".py":
        try:
            import ast as _ast
            tree = _ast.parse(text)
            _DECISION = (
                _ast.If, _ast.For, _ast.While, _ast.ExceptHandler,
                _ast.With, _ast.Assert, _ast.ListComp, _ast.DictComp,
                _ast.SetComp, _ast.GeneratorExp,
            )
            complexity = 1 + sum(1 for n in _ast.walk(tree) if isinstance(n, _DECISION))
        except SyntaxError:
            complexity = None
    else:
        m = re.findall(r'\b(?:if|else|elif|for|while|switch|case|catch|except)\b|&&|\|\|', text)
        complexity = 1 + len(m) if m else 1
    return {"loc": len(lines), "code": code, "comments": comments, "blank": blank, "complexity": complexity}


def _build_stats(files: dict, cache: dict = None) -> dict:
    """Build per-file and aggregate stats for all code files."""
    cache = cache or {}
    per_file: dict = {}
    for f in files.get("code", []):
        if f in cache and cache[f].get("stats"):
            per_file[f] = cache[f]["stats"]
        else:
            per_file[f] = _analyse_file(f)
    if per_file:
        total_loc = sum(v["loc"] for v in per_file.values())
        total_code = sum(v["code"] for v in per_file.values())
        total_comments = sum(v["comments"] for v in per_file.values())
        total_blank = sum(v["blank"] for v in per_file.values())
        complexities = [v["complexity"] for v in per_file.values() if v["complexity"] is not None]
        avg_c = round(sum(complexities) / len(complexities), 1) if complexities else None
        max_c = max(complexities) if complexities else None
        comment_ratio = round(total_comments / total_loc * 100, 1) if total_loc else 0.0
    else:
        total_loc = total_code = total_comments = total_blank = 0
        avg_c = max_c = None
        comment_ratio = 0.0
    return {
        "per_file": per_file,
        "total": {
            "loc": total_loc,
            "code": total_code,
            "comments": total_comments,
            "blank": total_blank,
            "avg_complexity": avg_c,
            "max_complexity": max_c,
            "comment_ratio": comment_ratio,
        },
    }


def _collect_files(args, input_dir, script_file):
    """Collect and return files dict based on args."""
    files = {k: [] for k in TYPE_FILTERS}
    selected_types = args.types if args.types else ["all"]
    process_all = "all" in selected_types
    search_method = input_dir.rglob if args.recursive else input_dir.glob
    use_filter = args.recursive or args.max_size != float("inf")
    limit_bytes = args.max_size * 1024 * 1024
    exclude_patterns = getattr(args, 'exclude', None) or []

    logging.info("Suche %s in %s", "rekursiv" if args.recursive else "flach", input_dir)
    if use_filter:
        logging.info("Limit: <%sMB (%.0f Bytes)", args.max_size, limit_bytes)

    for t, patterns in TYPE_FILTERS.items():
        if process_all or t in selected_types:
            if use_filter:
                for candidate in size_filtered_glob(
                    search_method, patterns, limit_bytes, script_file, input_dir, exclude_patterns
                ):
                    files[t].append(candidate)
            else:
                for pat in patterns:
                    for candidate in search_method(pat):
                        if should_skip_gitignore(input_dir, candidate):
                            continue
                        if _should_exclude(candidate, input_dir, exclude_patterns):
                            continue
                        if (
                            candidate.resolve() != script_file
                            and "combined_copycat" not in candidate.name
                        ):
                            files[t].append(candidate)
    return files


def _write_txt(writer, files, args, input_dir, git_info, serial, search_pattern=None, search_results=None, cache=None, stats=None):
    """Write TXT report."""
    mode_text = "REKURSIV" if args.recursive else "FLACH (Default)"
    writer.write(
        "=" * 60
        + f"\nCopyCat v2.9 | {datetime.now().strftime('%d.%m.%Y %H:%M')} | {mode_text}\n"
        + f"{input_dir}\n"
        + f"GIT: {git_info}\n\n"
    )
    total_files = sum(len(files[t]) for t in files)
    search_results = search_results or {}
    search_line = ""
    if search_pattern:
        total_hits = sum(len(v) for v in search_results.values())
        search_line = f'SUCHE: "{search_pattern}" \u2192 {total_hits} Treffer in {len(search_results)} {get_plural(len(search_results))}\n'
    writer.write(
        f"Gesamt: {total_files} {get_plural(total_files)}\nSerial #{serial}\n"
        + search_line
        + "=" * 60
        + "\n"
    )

    for t, flist in files.items():
        if flist:
            count = len(flist)
            writer.write(f"{t.upper()}: {count} {get_plural(count)}\n")

    writer.write("\n")

    if stats and stats["per_file"]:
        writer.write(f"{'='*20} CODE-STATISTIKEN {'='*20}\n")
        hdr = f"{'Datei':<30} {'LOC':>5} {'Code':>5} {'Komm.':>6} {'Leer':>5} {'Kompl.':>7}\n"
        sep = "-" * len(hdr.rstrip()) + "\n"
        writer.write(hdr)
        writer.write(sep)
        for fpath, s in stats["per_file"].items():
            c = f"{s['complexity']}" if s["complexity"] is not None else "–"
            writer.write(
                f"{fpath.name:<30} {s['loc']:>5} {s['code']:>5} {s['comments']:>6} {s['blank']:>5} {c:>7}\n"
            )
        writer.write(sep)
        t = stats["total"]
        avg_str = f"Ø {t['avg_complexity']}" if t["avg_complexity"] is not None else "–"
        max_str = f"Max {t['max_complexity']}" if t["max_complexity"] is not None else ""
        compl_str = f"{avg_str} / {max_str}" if max_str else avg_str
        ratio_str = f"  (Kommentaranteil: {t['comment_ratio']}%)"
        writer.write(
            f"{'GESAMT':<30} {t['loc']:>5} {t['code']:>5} {t['comments']:>6} {t['blank']:>5} {compl_str:>7}\n"
        )
        writer.write(ratio_str + "\n\n")

    selected_types = args.types if args.types else ["all"]
    process_all = "all" in selected_types
    cache = cache or {}

    if process_all or "code" in selected_types:
        writer.write("CODE-Details:\n")
        for code_file in files["code"]:
            rel_path = code_file.relative_to(input_dir)
            folder = rel_path.parent.name if rel_path.parent.name != "." else ""
            bracket = f" [{folder}]" if folder else ""
            if code_file in cache:
                lines = cache[code_file].get("lines", 0)
                cached_marker = " [Cache-Treffer]" if cache[code_file].get("from_cache") else ""
                writer.write(f"  {code_file.name}: {lines} Zeilen{bracket}{cached_marker}")
            else:
                try:
                    lines = sum(
                        1 for line in open(code_file, encoding="utf-8") if line.strip()
                    )
                    writer.write(f"  {code_file.name}: {lines} Zeilen{bracket}")
                except UnicodeDecodeError:
                    writer.write(f"  {code_file.name}: 1 Zeilen{bracket}")
                except Exception:
                    writer.write(f"  {code_file.name}: [FEHLER]")

            writer.write("\n")
            writer.write(f"----- {code_file.name} -----\n")

            if code_file in cache:
                writer.write(cache[code_file].get("content", ""))
            else:
                try:
                    with open(code_file, "r", encoding="utf-8") as f:
                        writer.writelines(f.readlines())
                except UnicodeDecodeError:
                    writer.write("(Binary oder ung\u00fcltiges Encoding - \u00fcbersprungen)\n")
                except Exception:
                    writer.write("(Fehler beim Lesen)\n")
            writer.write("\n\n")

    types_to_process = [
        t for t in (list(TYPE_FILTERS) if process_all else selected_types) if t in TYPE_FILTERS
    ]
    for t in types_to_process:
        if t == "code" or not files[t]:
            continue
        writer.write(f"\n{'='*20} {t.upper()} {'='*20}\n")
        for bfile in files[t]:
            if t == "diagram" and bfile.suffix.lower() in [".drawio", ".dia"]:
                extract_drawio(writer, bfile)
            elif t == "notebook":
                extract_notebook(writer, bfile)
            elif t in PLUGIN_RENDERERS and PLUGIN_RENDERERS[t] is not None:
                try:
                    PLUGIN_RENDERERS[t](bfile, writer, args)
                except Exception as exc:
                    writer.write(f"[Plugin-Fehler: {exc}]\n")
            else:
                list_binary_file(writer, bfile)
                if args.recursive:
                    writer.write(f"  Pfad: {bfile.parent.name}/{bfile.name}\n")

    if search_pattern and search_results:
        total_hits = sum(len(v) for v in search_results.values())
        writer.write(f"\n{'='*20} SUCHERGEBNISSE {'='*20}\n")
        writer.write(f'Muster: "{search_pattern}" \u2192 {total_hits} Treffer in {len(search_results)} {get_plural(len(search_results))}\n\n')
        for f_path, hits in search_results.items():
            writer.write(f"  {f_path.name}:\n")
            for lineno, text in hits:
                writer.write(f"    L{lineno}: {text}\n")


def _write_json(path, files, args, input_dir, git_info, serial, search_pattern=None, search_results=None, cache=None, stats=None):
    """Write JSON report."""
    selected_types = args.types if args.types else ["all"]
    process_all = "all" in selected_types

    git_parts = git_info.split(" | ") if git_info != "No Git" else []
    branch = git_parts[0].replace("Branch: ", "") if len(git_parts) > 0 else None
    commit = git_parts[1].replace("Last Commit: ", "") if len(git_parts) > 1 else None
    cache = cache or {}

    types_out = {}
    for t, flist in files.items():
        if not flist:
            continue
        file_entries = []
        for f in flist:
            entry = {
                "name": f.name,
                "path": f.relative_to(input_dir).as_posix(),
                "size": f.stat().st_size,
            }
            if t == "code":
                if f in cache:
                    entry["lines"] = cache[f].get("lines")
                else:
                    try:
                        entry["lines"] = sum(
                            1 for line in open(f, encoding="utf-8") if line.strip()
                        )
                    except Exception:
                        entry["lines"] = None
                if stats and f in stats.get("per_file", {}):
                    entry["stats"] = stats["per_file"][f]
            if search_pattern is not None:
                hits = (search_results or {}).get(f, [])
                entry["matches"] = [{"line": ln, "text": txt} for ln, txt in hits]
            file_entries.append(entry)
        types_out[t] = file_entries

    sr = search_results or {}
    search_out = (
        {
            "pattern": search_pattern,
            "total_matches": sum(len(v) for v in sr.values()),
            "files_matched": len(sr),
        }
        if search_pattern is not None
        else None
    )
    report = {
        "version": "2.9",
        "generated": datetime.now().strftime("%d.%m.%Y %H:%M"),
        "mode": "recursive" if args.recursive else "flat",
        "input": str(input_dir),
        "serial": serial,
        "git": {"branch": branch, "commit": commit} if branch else None,
        "files": sum(len(v) for v in types_out.values()),
        "types": {t: len(v) for t, v in types_out.items()},
        "search": search_out,
        "code_stats": stats["total"] if stats else None,
        "details": types_out,
    }

    with open(path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)


def _write_md(writer, files, args, input_dir, git_info, serial, search_pattern=None, search_results=None, cache=None, stats=None):
    """Write Markdown report."""
    mode_text = "Rekursiv" if args.recursive else "Flach"
    total_files = sum(len(files[t]) for t in files)
    selected_types = args.types if args.types else ["all"]
    process_all = "all" in selected_types
    cache = cache or {}

    writer.write(f"# CopyCat v2.9 Report\n\n")
    writer.write(f"| | |\n|---|---|\n")
    writer.write(f"| **Datum** | {datetime.now().strftime('%d.%m.%Y %H:%M')} |\n")
    writer.write(f"| **Modus** | {mode_text} |\n")
    writer.write(f"| **Pfad** | `{input_dir}` |\n")
    writer.write(f"| **Git** | {git_info} |\n")
    writer.write(f"| **Gesamt** | {total_files} {get_plural(total_files)} |\n")
    writer.write(f"| **Serial** | #{serial} |\n")
    if search_pattern:
        sr = search_results or {}
        total_hits = sum(len(v) for v in sr.values())
        writer.write(f'| **Suche** | `{search_pattern}` \u2192 {total_hits} Treffer in {len(sr)} {get_plural(len(sr))} |\n')
    writer.write("\n")

    writer.write("## Übersicht\n\n")
    writer.write("| Typ | Anzahl |\n|---|---|\n")
    for t, flist in files.items():
        if flist:
            writer.write(f"| {t.upper()} | {len(flist)} |\n")
    writer.write("\n")

    if stats and stats["per_file"]:
        writer.write("## Code-Statistiken\n\n")
        writer.write("| Datei | LOC | Code | Kommentar | Leer | Komplexität |\n|---|---|---|---|---|---|\n")
        for fpath, s in stats["per_file"].items():
            c = str(s["complexity"]) if s["complexity"] is not None else "–"
            writer.write(f"| `{fpath.name}` | {s['loc']} | {s['code']} | {s['comments']} | {s['blank']} | {c} |\n")
        tot = stats["total"]
        avg_str = f"Ø {tot['avg_complexity']}" if tot["avg_complexity"] is not None else "–"
        max_str = f" / Max {tot['max_complexity']}" if tot["max_complexity"] is not None else ""
        writer.write(
            f"| **GESAMT** | **{tot['loc']}** | **{tot['code']}** | **{tot['comments']}** |"
            f" **{tot['blank']}** | **{avg_str}{max_str}** |\n"
        )
        writer.write(f"\n> Kommentaranteil: {tot['comment_ratio']}%\n\n")

    if process_all or "code" in selected_types:
        writer.write("## Code-Details\n\n")
        for code_file in files["code"]:
            rel_path = code_file.relative_to(input_dir)
            if code_file in cache:
                lines = cache[code_file].get("lines", 0)
                cached_badge = " *(Cache-Treffer)*" if cache[code_file].get("from_cache") else ""
            else:
                try:
                    lines = sum(
                        1 for line in open(code_file, encoding="utf-8") if line.strip()
                    )
                except Exception:
                    lines = "?"
                cached_badge = ""
            writer.write(f"### `{rel_path.as_posix()}` ({lines} Zeilen){cached_badge}\n\n")
            writer.write(f"```\n")
            if code_file in cache:
                writer.write(cache[code_file].get("content", ""))
            else:
                try:
                    with open(code_file, "r", encoding="utf-8") as f:
                        writer.write(f.read())
                except UnicodeDecodeError:
                    writer.write("(Binary oder ung\u00fcltiges Encoding - \u00fcbersprungen)\n")
                except Exception:
                    writer.write("(Fehler beim Lesen)\n")
            writer.write(f"```\n\n")

    types_to_process = [
        t for t in (list(TYPE_FILTERS) if process_all else selected_types) if t in TYPE_FILTERS
    ]
    for t in types_to_process:
        if t == "code" or not files[t]:
            continue
        writer.write(f"## {t.upper()}\n\n")
        if t == "notebook":
            for bfile in files[t]:
                writer.write(f"### {bfile.name}\n\n```\n")
                extract_notebook(writer, bfile)
                writer.write("```\n\n")
        elif t in PLUGIN_RENDERERS and PLUGIN_RENDERERS[t] is not None:
            for bfile in files[t]:
                writer.write(f"### {bfile.name}\n\n```\n")
                try:
                    PLUGIN_RENDERERS[t](bfile, writer, args)
                except Exception as exc:
                    writer.write(f"[Plugin-Fehler: {exc}]\n")
                writer.write("```\n\n")
        else:
            writer.write("| Datei | Größe |\n|---|---|\n")
            for bfile in files[t]:
                size = bfile.stat().st_size
                writer.write(f"| `{bfile.name}` | {size} bytes |\n")
            writer.write("\n")

    if search_pattern and search_results:
        writer.write(f'## Suchergebnisse: `{search_pattern}`\n\n')
        writer.write("| Datei | Zeile | Treffer |\n|---|---|---|\n")
        for f_path, hits in search_results.items():
            for lineno, text in hits:
                safe_text = text.replace("|", "\\|").strip()
                writer.write(f"| `{f_path.name}` | {lineno} | `{safe_text}` |\n")
        writer.write("\n")


# ── Cache-Hilfsfunktionen (Idee 4: Inkrementelle Reports) ────────────────────

def _html_escape(s: str) -> str:
    """Escape special HTML characters."""
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def _hash_file(path: Path) -> str:
    """Return SHA-256 hex digest of a file's binary content. Returns '' on error."""
    h = hashlib.sha256()
    try:
        with open(path, "rb") as fh:
            for chunk in iter(lambda: fh.read(65536), b""):
                h.update(chunk)
    except OSError:
        return ""
    return h.hexdigest()


def _load_cache(cache_file: Path) -> dict:
    """Load incremental cache from JSON. Returns {} on missing/invalid file."""
    if not cache_file.is_file():
        return {}
    try:
        with open(cache_file, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        if data.get("version") != "1":
            return {}
        return data.get("entries", {})
    except (OSError, json.JSONDecodeError, KeyError):
        return {}


def _save_cache(cache_file: Path, entries: dict) -> None:
    """Persist incremental cache entries to JSON."""
    try:
        cache_file.parent.mkdir(exist_ok=True)
        with open(cache_file, "w", encoding="utf-8") as fh:
            json.dump({"version": "1", "entries": entries}, fh, ensure_ascii=False, indent=2)
    except OSError:
        pass


# ── HTML-Report (Idee 3) ──────────────────────────────────────────────────────

def _write_html(path, files, args, input_dir, git_info, serial,
                search_pattern=None, search_results=None, cache=None, stats=None):
    """Write a self-contained HTML report with optional Pygments syntax highlighting."""
    try:
        from pygments import highlight
        from pygments.lexers import get_lexer_for_filename
        from pygments.formatters import HtmlFormatter
        from pygments.util import ClassNotFound
        from pygments.lexers import TextLexer
        _formatter = HtmlFormatter(style="friendly", inline_styles=True, nowrap=True)
        _has_pygments = True
    except ImportError:
        _has_pygments = False
        _formatter = None

    def _highlight_code(text: str, filename: str) -> str:
        if not _has_pygments:
            return f"<pre><code>{_html_escape(text)}</code></pre>"
        try:
            lexer = get_lexer_for_filename(filename, stripall=True)
        except ClassNotFound:
            lexer = TextLexer()
        return f"<pre>{highlight(text, lexer, _formatter)}</pre>"

    mode_text = "Rekursiv" if args.recursive else "Flach"
    total_files = sum(len(files[t]) for t in files)
    selected_types = args.types if args.types else ["all"]
    process_all = "all" in selected_types
    cache = cache or {}
    sr = search_results or {}
    now = datetime.now().strftime("%d.%m.%Y %H:%M")

    # Build overview rows
    overview_rows = "".join(
        f"<tr><td>{_html_escape(t.upper())}</td><td>{len(flist)}</td></tr>"
        for t, flist in files.items() if flist
    )

    # Search summary row
    search_meta = ""
    if search_pattern:
        total_hits = sum(len(v) for v in sr.values())
        search_meta = (
            f"<tr><th>Suche</th><td><code>{_html_escape(search_pattern)}</code>"
            f" \u2192 {total_hits} Treffer in {len(sr)} {get_plural(len(sr))}</td></tr>"
        )

    # Code sections
    code_html_parts = []
    if process_all or "code" in selected_types:
        for code_file in files["code"]:
            rel_path = code_file.relative_to(input_dir)
            if code_file in cache:
                lines_count = cache[code_file].get("lines", 0)
                code_text = cache[code_file].get("content", "")
                badge = (' <span style="background:#e8f5e9;border:1px solid #a5d6a7;'
                         'border-radius:3px;padding:1px 5px;font-size:.8em;color:#2e7d32">'
                         'Cache-Treffer</span>') if cache[code_file].get("from_cache") else ""
            else:
                try:
                    code_text = code_file.read_text(encoding="utf-8")
                    lines_count = sum(1 for line in code_text.splitlines() if line.strip())
                except UnicodeDecodeError:
                    code_text = "(Binary oder ung\u00fcltiges Encoding - \u00fcbersprungen)"
                    lines_count = 1
                except Exception:
                    code_text = "(Fehler beim Lesen)"
                    lines_count = 0
                badge = ""
            folder = rel_path.parent.name if rel_path.parent.name != "." else ""
            folder_str = (f' <span style="color:#666;font-size:.9em">[{_html_escape(folder)}]</span>'
                          if folder else "")
            highlighted = _highlight_code(code_text, code_file.name)
            code_html_parts.append(
                f'<details open>\n'
                f'<summary><strong>{_html_escape(code_file.name)}</strong>{folder_str} '
                f'<em style="color:#555">{lines_count} Zeilen</em>{badge}</summary>\n'
                f'<div style="overflow-x:auto">{highlighted}</div>\n'
                f'</details>\n'
            )

    # Other type sections
    other_sections = []
    types_to_process = [
        t for t in (list(TYPE_FILTERS) if process_all else selected_types) if t in TYPE_FILTERS
    ]
    for t in types_to_process:
        if t == "code" or not files[t]:
            continue
        rows = "".join(
            f'<tr><td>{_html_escape(bfile.name)}</td><td>{bfile.stat().st_size} bytes</td></tr>'
            for bfile in files[t]
        )
        other_sections.append(
            f'<h2>{_html_escape(t.upper())}</h2>\n'
            f'<table><tr><th>Datei</th><th>Gr\u00f6\u00dfe</th></tr>{rows}</table>\n'
        )

    # Search results section
    search_section = ""
    if search_pattern and sr:
        total_hits = sum(len(v) for v in sr.values())
        rows = ""
        for f_path, hits in sr.items():
            for lineno, text in hits:
                rows += (f'<tr><td>{_html_escape(f_path.name)}</td>'
                         f'<td>{lineno}</td>'
                         f'<td><code>{_html_escape(text.strip())}</code></td></tr>\n')
        search_section = (
            f'<h2>Suchergebnisse: <code>{_html_escape(search_pattern)}</code>'
            f' ({total_hits} Treffer)</h2>\n'
            f'<table><tr><th>Datei</th><th>Zeile</th><th>Treffer</th></tr>\n'
            f'{rows}</table>\n'
        )

    pygments_note = "" if _has_pygments else (
        '<p style="color:#888;font-size:.85em">'
        'Syntax-Highlighting nicht verf\u00fcgbar (pip install pygments).</p>'
    )

    # Stats section HTML
    stats_section = ""
    if stats and stats["per_file"]:
        tot = stats["total"]
        avg_str = f"Ø {tot['avg_complexity']}" if tot["avg_complexity"] is not None else "–"
        max_str = f"Max {tot['max_complexity']}" if tot["max_complexity"] is not None else ""
        compl_summary = f"{avg_str} / {max_str}" if max_str else avg_str
        cards = (
            f'<div class="stat-card"><div class="stat-val">{tot["loc"]}</div>'
            f'<div class="stat-label">Zeilen gesamt</div></div>'
            f'<div class="stat-card"><div class="stat-val">{tot["code"]}</div>'
            f'<div class="stat-label">Code-Zeilen</div></div>'
            f'<div class="stat-card"><div class="stat-val">{tot["comment_ratio"]}%</div>'
            f'<div class="stat-label">Kommentaranteil</div></div>'
            f'<div class="stat-card"><div class="stat-val">{compl_summary}</div>'
            f'<div class="stat-label">Komplexität</div></div>'
        )
        rows_html = ""
        for fpath, s in stats["per_file"].items():
            c = str(s["complexity"]) if s["complexity"] is not None else "–"
            rows_html += (
                f'<tr><td>{_html_escape(fpath.name)}</td>'
                f'<td>{s["loc"]}</td><td>{s["code"]}</td>'
                f'<td>{s["comments"]}</td><td>{s["blank"]}</td><td>{c}</td></tr>\n'
            )
        stats_section = (
            f'<section>\n<h2>Code-Statistiken</h2>\n'
            f'<div class="stat-cards">{cards}</div>\n'
            f'<table><tr><th>Datei</th><th>LOC</th><th>Code</th>'
            f'<th>Kommentar</th><th>Leer</th><th>Komplexität</th></tr>\n'
            f'{rows_html}</table>\n</section>\n'
        )

    html = (
        f'<!DOCTYPE html>\n<html lang="de">\n<head>\n'
        f'<meta charset="UTF-8">\n'
        f'<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        f'<title>CopyCat Report #{serial}</title>\n'
        f'<style>\n'
        f'body{{font-family:"Segoe UI",Arial,sans-serif;max-width:1200px;margin:0 auto;padding:20px;background:#f5f5f5;color:#212121}}\n'
        f'header{{background:#1565c0;color:#fff;padding:16px 24px;border-radius:8px;margin-bottom:20px}}\n'
        f'header h1{{margin:0 0 4px 0;font-size:1.5em}}\n'
        f'table{{border-collapse:collapse;margin-bottom:16px;background:#fff;border-radius:4px;box-shadow:0 1px 3px rgba(0,0,0,.1)}}\n'
        f'th,td{{padding:7px 14px;border:1px solid #e0e0e0;text-align:left}}\n'
        f'th{{background:#e3f2fd;font-weight:600}}\n'
        f'details{{background:#fff;border:1px solid #e0e0e0;border-radius:6px;margin:6px 0;box-shadow:0 1px 2px rgba(0,0,0,.06)}}\n'
        f'summary{{padding:10px 16px;cursor:pointer;font-size:1em;background:#f8f9fa;border-radius:6px;user-select:none}}\n'
        f'summary:hover{{background:#e8eaf6}}\n'
        f'pre{{margin:0;padding:14px 16px;overflow-x:auto;font-size:.88em;line-height:1.5;border-top:1px solid #e0e0e0}}\n'
        f'h2{{color:#1565c0;border-bottom:2px solid #e3f2fd;padding-bottom:4px;margin-top:28px}}\n'
        f'code{{background:#f5f5f5;padding:1px 4px;border-radius:3px;font-size:.92em}}\n'
        f'.stat-cards{{display:flex;gap:12px;flex-wrap:wrap;margin-bottom:16px}}\n'
        f'.stat-card{{background:#fff;border:1px solid #e0e0e0;border-radius:8px;padding:14px 20px;min-width:130px;box-shadow:0 1px 3px rgba(0,0,0,.08);text-align:center}}\n'
        f'.stat-val{{font-size:1.6em;font-weight:700;color:#1565c0}}\n'
        f'.stat-label{{font-size:.78em;color:#666;margin-top:4px}}\n'
        f'</style>\n</head>\n<body>\n'
        f'<header><h1>&#128008; CopyCat v2.9 Report</h1></header>\n'
        f'<section>\n'
        f'<table>\n'
        f'<tr><th>Datum</th><td>{now}</td></tr>\n'
        f'<tr><th>Modus</th><td>{mode_text}</td></tr>\n'
        f'<tr><th>Pfad</th><td><code>{_html_escape(str(input_dir))}</code></td></tr>\n'
        f'<tr><th>Git</th><td>{_html_escape(git_info)}</td></tr>\n'
        f'<tr><th>Gesamt</th><td>{total_files} {get_plural(total_files)}</td></tr>\n'
        f'<tr><th>Serial</th><td>#{serial}</td></tr>\n'
        f'{search_meta}\n'
        f'</table>\n</section>\n'
        f'<section>\n<h2>\u00dcbersicht</h2>\n'
        f'<table><tr><th>Typ</th><th>Anzahl</th></tr>\n{overview_rows}</table>\n</section>\n'
        + stats_section
        + f'<section>\n<h2>Code-Details</h2>\n{pygments_note}\n'
        + "".join(code_html_parts)
        + f'</section>\n'
        + "".join(other_sections)
        + search_section
        + f'</body>\n</html>\n'
    )

    with open(path, "w", encoding="utf-8") as fh:
        fh.write(html)


def run_copycat(args):
    git_url = getattr(args, "git_url", None)
    _tmp_dir_obj = None

    plugin_dir = getattr(args, "plugin_dir", None)
    if plugin_dir:
        load_plugins(plugin_dir)
    script_file = Path(__file__).resolve()
    script_dir = Path(__file__).parent

    # ── Git-URL: Remote-Repository klonen ───────────────────────────────────
    if git_url:
        if not re.match(r'^(https?://\S+|git@\S+:\S+|git://\S+|ssh://\S+)$', git_url):
            logging.error("Ung\u00fcltige Git-URL: %s", git_url)
            return None
        _tmp_dir_obj = tempfile.TemporaryDirectory()
        tmp_clone = Path(_tmp_dir_obj.name) / "repo"
        logging.info("Klone Repository: %s", git_url)
        result = subprocess.run(
            ["git", "clone", "--depth", "1", "--", git_url, str(tmp_clone)],
            capture_output=True, text=True, timeout=120,
        )
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

    # ── Inkrementeller Cache (Idee 4) ────────────────────────────────────────
    cache_map: dict = {}  # Path → {"lines": int, "content": str}
    if getattr(args, "incremental", False):
        cache_dir = output_dir / ".copycat_cache"
        cache_file = cache_dir / "cache.json"
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

    # ── Code-Statistiken (Idee 5) ─────────────────────────────────────────────
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
    if template_path:
        content = _write_template(
            template_path, files, args, input_dir, git_info, serial,
            search_pattern, search_results,
        )
        with open(new_file, "w", encoding="utf-8") as writer:
            writer.write(content)
    elif fmt == "json":
        _write_json(new_file, files, args, input_dir, git_info, serial, search_pattern, search_results, cache_map, stats_map)
    elif fmt == "md":
        with open(new_file, "w", encoding="utf-8") as writer:
            _write_md(writer, files, args, input_dir, git_info, serial, search_pattern, search_results, cache_map, stats_map)
    elif fmt == "html":
        _write_html(new_file, files, args, input_dir, git_info, serial, search_pattern, search_results, cache_map, stats_map)
    else:
        with open(new_file, "w", encoding="utf-8") as writer:
            _write_txt(writer, files, args, input_dir, git_info, serial, search_pattern, search_results, cache_map, stats_map)

    logging.info("Erstellt: %s", new_file)
    if _tmp_dir_obj is not None:
        _tmp_dir_obj.cleanup()
    return str(new_file)


if __name__ == "__main__":  # pragma: no cover
    _args = parse_arguments()
    if getattr(_args, "verbose", False):
        _log_level = logging.DEBUG
    elif getattr(_args, "quiet", False):
        _log_level = logging.WARNING
    else:
        _log_level = logging.INFO
    logging.basicConfig(level=_log_level, format="%(message)s")
    if getattr(_args, "list_plugins", False):
        _plugin_dir = getattr(_args, "plugin_dir", None) or str(Path(__file__).parent / "plugins")
        _loaded = load_plugins(_plugin_dir)
        if _loaded:
            print("Geladene Plugins:")
            for _t in _loaded:
                _pats = TYPE_FILTERS.get(_t, [])
                _rinfo = "benutzerdefinierter Renderer" if PLUGIN_RENDERERS.get(_t) else "Standard-Renderer"
                print(f"  {_t}: {', '.join(_pats)} ({_rinfo})")
        else:
            print(f"Keine Plugins in {_plugin_dir} gefunden.")
    elif getattr(_args, "install_hook", None):
        hook = install_hook(Path(_args.install_hook))
        print(f"Hook installiert: {hook}")
    elif getattr(_args, "merge", None):
        print(merge_reports([Path(p) for p in _args.merge]))
    elif getattr(_args, "diff", None):
        print(diff_reports(Path(_args.diff[0]), Path(_args.diff[1])))
    elif getattr(_args, "watch", False):
        watch_and_run(_args, cooldown=getattr(_args, "cooldown", 2.0))
    else:
        run_copycat(_args)
