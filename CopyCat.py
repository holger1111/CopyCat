"""
CopyCat v2.7
"""

import argparse
import xml.etree.ElementTree as ET
import shutil
import re
import logging
import struct
import subprocess
import fnmatch
from pathlib import Path
from datetime import datetime


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="CopyCat v2.7 - Projekt-Dokumentierer"
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
    args = parser.parse_args()
    
    if args.types and len(args.types) == 1 and ',' in args.types[0]:
        args.types = [t.strip() for t in args.types[0].split(',')]
    
    return args


def is_valid_serial_filename(filename: str) -> bool:
    pattern = r"^combined_copycat_(\d+)\.txt$"
    return bool(re.match(pattern, filename))


def get_next_serial_number(base_path: Path) -> int:
    existing = list(base_path.glob("combined_copycat*.txt"))
    max_num = 0
    for p in existing:
        if is_valid_serial_filename(p.name):
            try:
                match = re.match(r"^combined_copycat_(\d+)\.txt$", p.name)
                num = int(match.group(1))
                max_num = max(max_num, num)
            except (ValueError, AttributeError):
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


def extract_drawio(writer, drawio_file):
    try:
        size = drawio_file.stat().st_size
        if size == 0:
            writer.write(f"[EMPTY: {drawio_file.name}] [SIZE: 0 bytes]\n")
            return

        with open(drawio_file, "r", encoding="utf-8") as f:
            xml_content = f.read()

        tree = ET.fromstring(xml_content)
        cells, texts = 0, 0

        for cell in tree.iter("mxCell"):
            cells += 1
            if "value" in cell.attrib and cell.attrib["value"].strip():
                texts += 1
                writer.write(
                    f"  [{cell.attrib.get('id','?')}] {cell.attrib['value'][:50]}...\n"
                )

        writer.write(f"DIAGRAM {drawio_file.name}: {cells} Cells, {texts} Texte\n")

    except ET.ParseError as e:
        writer.write(f"[XML PARSE ERROR: {drawio_file.name} - {str(e)}]\n")
    except UnicodeDecodeError:
        writer.write(f"[BINARY: {drawio_file.name} - Invalid Encoding]\n")


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
    gitignore_path = input_dir / ".gitignore"
    if not gitignore_path.exists():
        return False

    try:
        rel_path = file_path.relative_to(input_dir).as_posix()
        with open(gitignore_path, "r", encoding="utf-8") as f:
            for line in f:
                rule = line.strip()
                if rule.startswith("#") or not rule:
                    continue
                if "*" in rule:
                    if fnmatch.fnmatch(rel_path, rule):
                        return True
                elif rule.endswith("/"):
                    if rel_path.startswith(rule.rstrip("/")):
                        return True
                elif rel_path == rule:
                    return True
        return False
    except Exception:
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


def run_copycat(args):
    script_file = Path(__file__).resolve()
    script_dir = Path(__file__).parent
    input_dir = Path(args.input or str(script_dir))
    output_dir = Path(args.output or str(input_dir))
    output_dir.mkdir(exist_ok=True)

    if not input_dir.is_dir():
        print(f"Fehler: {input_dir} ist kein Ordner")
        return

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
                        if (
                            candidate.resolve() != script_file
                            and "combined_copycat" not in candidate.name
                        ):
                            files[t].append(candidate)

    serial = get_next_serial_number(output_dir)
    basename = "combined_copycat"
    new_file = output_dir / f"{basename}_{serial}.txt"

    existing = list(output_dir.glob("combined_copycat*.txt"))
    to_archive = [
        f for f in existing if f != new_file and is_valid_serial_filename(f.name)
    ]
    print(f"Archiviere {len(to_archive)} Datei(en)")

    for old_file in to_archive:
        move_to_archive(output_dir, old_file.name)

    mode_text = "REKURSIV" if args.recursive else "FLACH (Default)"
    with open(new_file, "w", encoding="utf-8") as writer:
        git_info = get_git_info(input_dir)
        writer.write(
            "=" * 60
            + f"\nCopyCat v2.7 | {datetime.now().strftime('%d.%m.%Y %H:%M')} | {mode_text}\n"
            + f"{input_dir}\n"
            + f"GIT: {git_info}\n\n"
        )
        total_files = sum(len(files[t]) for t in files)
        writer.write(
            f"Gesamt: {total_files} {get_plural(total_files)}\nSerial #{serial}\n"
            + "=" * 60
            + "\n"
        )

        for t, flist in files.items():
            if flist:
                count = len(flist)
                writer.write(f"{t.upper()}: {count} {get_plural(count)}\n")

        writer.write("\n")

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

    print(f"Erstellt: {new_file}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.ERROR, format="CopyCat ERROR: %(message)s")
    args = parse_arguments()
    run_copycat(args)
