"""Markdown report exporter."""

import argparse
from datetime import datetime
from pathlib import Path
from typing import IO, Any

from ..extractors.csv_extractor import extract_csv
from ..extractors.notebook import extract_notebook
from ..utils.files import get_plural
from ..utils.plugins import TYPE_FILTERS, PLUGIN_RENDERERS


def _write_md(
    writer: IO[str],
    files: dict[str, list[Path]],
    args: argparse.Namespace,
    input_dir: Path,
    git_info: str,
    serial: int,
    search_pattern: str | None = None,
    search_results: dict[Path, list[tuple[int, str]]] | None = None,
    cache: dict[Path, Any] | None = None,
    stats: dict[str, Any] | None = None,
) -> None:
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
                if bfile.suffix.lower() == ".csv":
                    writer.write(f"### {bfile.name}\n\n```\n")
                    extract_csv(writer, bfile)
                    writer.write("```\n\n")
                else:
                    writer.write(f"### {bfile.name}\n\n```\n")
                    extract_notebook(writer, bfile)
                    writer.write("```\n\n")
        elif t in PLUGIN_RENDERERS and PLUGIN_RENDERERS[t] is not None:
            for bfile in files[t]:
                writer.write(f"### {bfile.name}\n\n```\n")
                renderer = PLUGIN_RENDERERS[t]
                assert renderer is not None
                try:
                    renderer(bfile, writer, args)
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
