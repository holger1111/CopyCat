"""
CopyCat v2.9
"""

import argparse
import json
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
        choices=["txt", "json", "md"],
        default="txt",
        help="Ausgabeformat: txt (default), json, md",
    )
    parser.add_argument(
        "--search",
        "-S",
        default=None,
        help="Regex-Suchmuster für Inhaltssuche (z.B. 'TODO|FIXME', 'def ')",
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
        if cfg["format"] in ("txt", "json", "md"):
            overrides["format"] = cfg["format"]
        else:
            logging.warning("copycat.conf: ungültiger format-Wert wird ignoriert")
    if "search" in cfg:
        overrides["search"] = cfg["search"]
    if "input" in cfg:
        overrides["input"] = cfg["input"]
    if "output" in cfg:
        overrides["output"] = cfg["output"]
    if overrides:
        parser.set_defaults(**overrides)
    # ────────────────────────────────────────────────────────────────────────

    args = parser.parse_args()

    if args.types and len(args.types) == 1 and ',' in args.types[0]:
        args.types = [t.strip() for t in args.types[0].split(',')]

    return args


def is_valid_serial_filename(filename: str) -> bool:
    pattern = r"^combined_copycat_(\d+)\.(txt|json|md)$"
    return bool(re.match(pattern, filename))


def get_next_serial_number(base_path: Path) -> int:
    existing = list(base_path.glob("combined_copycat*"))
    max_num = 0
    for p in existing:
        if is_valid_serial_filename(p.name):
            try:
                match = re.match(r"^combined_copycat_(\d+)\.(txt|json|md)$", p.name)
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
            print(f"Archiv-Fehler {filename}: {e}")


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


def size_filtered_glob(search_method, patterns, max_bytes, script_file, input_dir):
    total_checked = 0
    for pat in patterns:
        for candidate in search_method(pat):
            total_checked += 1
            try:
                if should_skip_gitignore(input_dir, candidate):
                    continue
                if candidate.stat().st_size < max_bytes:
                    if (
                        candidate.resolve() != script_file
                        and "combined_copycat" not in candidate.name
                    ):
                        yield candidate
                if total_checked % 100 == 0:
                    print(f"\rGeprüft: {total_checked} Dateien...", end="")
            except OSError:
                continue
    print(f"\n→ {total_checked} geprüft, Filter OK")


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
    """Search pattern in all text-based files. Returns {Path: [(lineno, text)]}."""
    SEARCHABLE = {"code", "web", "db", "config", "docs", "deps"}
    results = {}
    for t, flist in files.items():
        if t not in SEARCHABLE:
            continue
        for f in flist:
            hits = search_in_file(f, pattern)
            if hits:
                results[f] = hits
    return results


TYPE_FILTERS = {
    "code": ["*.java", "*.py", "*.spec", "*.cpp", "*.c"],
    "web": ["*.html", "*.css", "*.js", "*.ts", "*.jsx"],
    "db": ["*.sql", "*.db", "*.sqlite"],
    "config": ["*.json", "*.yaml", "*.xml", "*.properties", "*.env"],
    "docs": ["*.md", "*.txt", "*.log", "*.docx"],
    "deps": ["requirements.txt", "package.json", "pom.xml", "go.mod"],
    "img": ["*.png", "*.jpg", "*.gif", "*.bmp", "*.webp", "*.svg", "*.ico"],
    "audio": ["*.mp3", "*.wav", "*.ogg", "*.m4a", "*.flac"],
    "diagram": ["*.drawio", "*.dia", "*.puml"],
}


def _collect_files(args, input_dir, script_file):
    """Collect and return files dict based on args."""
    files = {k: [] for k in TYPE_FILTERS}
    selected_types = args.types if args.types else ["all"]
    process_all = "all" in selected_types
    search_method = input_dir.rglob if args.recursive else input_dir.glob
    use_filter = args.recursive or args.max_size != float("inf")
    limit_bytes = args.max_size * 1024 * 1024

    print(f"Suche {'rekursiv' if args.recursive else 'flach'} in {input_dir}")
    if use_filter:
        print(f"Limit: <{args.max_size}MB ({limit_bytes/1024/1024:.0f} Bytes)")

    for t, patterns in TYPE_FILTERS.items():
        if process_all or t in selected_types:
            if use_filter:
                for candidate in size_filtered_glob(
                    search_method, patterns, limit_bytes, script_file, input_dir
                ):
                    files[t].append(candidate)
            else:
                for pat in patterns:
                    for candidate in search_method(pat):
                        if should_skip_gitignore(input_dir, candidate):
                            continue
                        if (
                            candidate.resolve() != script_file
                            and "combined_copycat" not in candidate.name
                        ):
                            files[t].append(candidate)
    return files


def _write_txt(writer, files, args, input_dir, git_info, serial, search_pattern=None, search_results=None):
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

    selected_types = args.types if args.types else ["all"]
    process_all = "all" in selected_types

    if process_all or "code" in selected_types:
        writer.write("CODE-Details:\n")
        for code_file in files["code"]:
            rel_path = code_file.relative_to(input_dir)
            folder = rel_path.parent.name if rel_path.parent.name != "." else ""
            bracket = f" [{folder}]" if folder else ""
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

            try:
                with open(code_file, "r", encoding="utf-8") as f:
                    writer.writelines(f.readlines())
            except UnicodeDecodeError:
                writer.write("(Binary oder ungültiges Encoding - übersprungen)\n")
            except Exception:
                writer.write("(Fehler beim Lesen)\n")
            writer.write("\n\n")

    types_to_process = [
        t for t in (["all"] if process_all else selected_types) if t in TYPE_FILTERS
    ]
    for t in types_to_process:
        if t == "code" or not files[t]:
            continue
        writer.write(f"\n{'='*20} {t.upper()} {'='*20}\n")
        for bfile in files[t]:
            if t == "diagram" and bfile.suffix.lower() in [".drawio", ".dia"]:
                extract_drawio(writer, bfile)
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


def _write_json(path, files, args, input_dir, git_info, serial, search_pattern=None, search_results=None):
    """Write JSON report."""
    selected_types = args.types if args.types else ["all"]
    process_all = "all" in selected_types

    git_parts = git_info.split(" | ") if git_info != "No Git" else []
    branch = git_parts[0].replace("Branch: ", "") if len(git_parts) > 0 else None
    commit = git_parts[1].replace("Last Commit: ", "") if len(git_parts) > 1 else None

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
                try:
                    entry["lines"] = sum(
                        1 for line in open(f, encoding="utf-8") if line.strip()
                    )
                except Exception:
                    entry["lines"] = None
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
        "details": types_out,
    }

    with open(path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)


def _write_md(writer, files, args, input_dir, git_info, serial, search_pattern=None, search_results=None):
    """Write Markdown report."""
    mode_text = "Rekursiv" if args.recursive else "Flach"
    total_files = sum(len(files[t]) for t in files)
    selected_types = args.types if args.types else ["all"]
    process_all = "all" in selected_types

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

    if process_all or "code" in selected_types:
        writer.write("## Code-Details\n\n")
        for code_file in files["code"]:
            rel_path = code_file.relative_to(input_dir)
            try:
                lines = sum(
                    1 for line in open(code_file, encoding="utf-8") if line.strip()
                )
            except Exception:
                lines = "?"
            writer.write(f"### `{rel_path.as_posix()}` ({lines} Zeilen)\n\n")
            writer.write(f"```\n")
            try:
                with open(code_file, "r", encoding="utf-8") as f:
                    writer.write(f.read())
            except UnicodeDecodeError:
                writer.write("(Binary oder ungültiges Encoding - übersprungen)\n")
            except Exception:
                writer.write("(Fehler beim Lesen)\n")
            writer.write(f"```\n\n")

    types_to_process = [
        t for t in (["all"] if process_all else selected_types) if t in TYPE_FILTERS
    ]
    for t in types_to_process:
        if t == "code" or not files[t]:
            continue
        writer.write(f"## {t.upper()}\n\n")
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


def run_copycat(args):
    script_file = Path(__file__).resolve()
    script_dir = Path(__file__).parent
    input_dir = Path(args.input or str(script_dir))
    output_dir = Path(args.output or str(input_dir))
    output_dir.mkdir(exist_ok=True)

    if not input_dir.is_dir():
        print(f"Fehler: {input_dir} ist kein Ordner")
        return

    fmt = getattr(args, "format", "txt")
    files = _collect_files(args, input_dir, script_file)

    serial = get_next_serial_number(output_dir)
    new_file = output_dir / f"combined_copycat_{serial}.{fmt}"

    existing = list(output_dir.glob("combined_copycat*"))
    to_archive = [
        f for f in existing if f != new_file and is_valid_serial_filename(f.name)
    ]
    print(f"Archiviere {len(to_archive)} Datei(en)")
    for old_file in to_archive:
        move_to_archive(output_dir, old_file.name)

    git_info = get_git_info(input_dir)

    search_pattern = getattr(args, "search", None)
    if search_pattern:
        print(f'Suche nach Muster: "{search_pattern}"')
    search_results = _build_search_results(files, search_pattern) if search_pattern else {}

    if fmt == "json":
        _write_json(new_file, files, args, input_dir, git_info, serial, search_pattern, search_results)
    elif fmt == "md":
        with open(new_file, "w", encoding="utf-8") as writer:
            _write_md(writer, files, args, input_dir, git_info, serial, search_pattern, search_results)
    else:
        with open(new_file, "w", encoding="utf-8") as writer:
            _write_txt(writer, files, args, input_dir, git_info, serial, search_pattern, search_results)

    print(f"Erstellt: {new_file}")


if __name__ == "__main__":  # pragma: no cover
    logging.basicConfig(level=logging.ERROR, format="CopyCat ERROR: %(message)s")
    args = parse_arguments()
    run_copycat(args)
