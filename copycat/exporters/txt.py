"""Plain-text report exporter."""

import argparse
from datetime import datetime
from pathlib import Path
from typing import IO, Any

from ..extractors.binary import list_binary_file
from ..extractors.csv_extractor import extract_csv
from ..extractors.drawio import extract_drawio
from ..extractors.notebook import extract_notebook
from ..i18n import get_tr
from ..utils.files import get_plural
from ..utils.plugins import TYPE_FILTERS, PLUGIN_RENDERERS


def _write_txt(
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
    """Write TXT report."""
    _lang = str(getattr(args, "lang", "de"))
    tr = get_tr(_lang)
    mode_text = tr("mode_recursive") if args.recursive else tr("mode_flat")
    writer.write(
        "=" * 60
        + f"\nCopyCat v3.0 | {datetime.now().strftime('%d.%m.%Y %H:%M')} | {mode_text}\n"
        + f"{input_dir}\n"
        + f"GIT: {git_info}\n\n"
    )
    total_files = sum(len(files[t]) for t in files)
    search_results = search_results or {}
    search_line = ""
    if search_pattern:
        total_hits = sum(len(v) for v in search_results.values())
        search_line = f'{tr("search_prefix")} "{search_pattern}" \u2192 {total_hits} {tr("matches")} in {len(search_results)} {get_plural(len(search_results), _lang)}\n'
    writer.write(
        f"{tr('total')}: {total_files} {get_plural(total_files, _lang)}\nSerial #{serial}\n"
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
        writer.write(f"{'='*20} {tr('code_stats_upper')} {'='*20}\n")
        hdr = f"{tr('file'):<30} {'LOC':>5} {'Code':>5} {tr('comment_short'):>6} {tr('blank'):>5} {tr('complexity_short'):>7}\n"
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
        ratio_str = f"  ({tr('comment_ratio')}: {t['comment_ratio']}%)"
        writer.write(
            f"{tr('total_upper'):<30} {t['loc']:>5} {t['code']:>5} {t['comments']:>6} {t['blank']:>5} {compl_str:>7}\n"
        )
        writer.write(ratio_str + "\n\n")

    selected_types = args.types if args.types else ["all"]
    process_all = "all" in selected_types
    cache = cache or {}

    if process_all or "code" in selected_types:
        writer.write(f"{tr('code_details_label')}\n")
        for code_file in files["code"]:
            rel_path = code_file.relative_to(input_dir)
            folder = rel_path.parent.name if rel_path.parent.name != "." else ""
            bracket = f" [{folder}]" if folder else ""
            if code_file in cache:
                lines = cache[code_file].get("lines", 0)
                cached_marker = f" {tr('cache_hit_bracket')}" if cache[code_file].get("from_cache") else ""
                writer.write(f"  {code_file.name}: {lines} {tr('lines')}{bracket}{cached_marker}")
            else:
                try:
                    lines = sum(
                        1 for line in open(code_file, encoding="utf-8") if line.strip()
                    )
                    writer.write(f"  {code_file.name}: {lines} {tr('lines')}{bracket}")
                except UnicodeDecodeError:
                    writer.write(f"  {code_file.name}: 1 {tr('lines')}{bracket}")
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
                    writer.write(f"{tr('binary_skip')}\n")
                except Exception:
                    writer.write(f"{tr('read_error')}\n")
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
            elif t == "notebook" and bfile.suffix.lower() == ".csv":
                extract_csv(writer, bfile)
            elif t == "notebook":
                extract_notebook(writer, bfile)
            elif t in PLUGIN_RENDERERS and PLUGIN_RENDERERS[t] is not None:
                renderer = PLUGIN_RENDERERS[t]
                assert renderer is not None
                try:
                    renderer(bfile, writer, args)
                except Exception as exc:
                    writer.write(f"{tr('plugin_error').format(exc=exc)}\n")
            else:
                list_binary_file(writer, bfile)
                if args.recursive:
                    writer.write(f"  {tr('path')}: {bfile.parent.name}/{bfile.name}\n")

    if search_pattern and search_results:
        total_hits = sum(len(v) for v in search_results.values())
        writer.write(f"\n{'='*20} {tr('search_results_upper')} {'='*20}\n")
        writer.write(f'{tr("pattern")} "{search_pattern}" \u2192 {total_hits} {tr("matches")} in {len(search_results)} {get_plural(len(search_results), _lang)}\n\n')
        for f_path, hits in search_results.items():
            writer.write(f"  {f_path.name}:\n")
            for lineno, text in hits:
                writer.write(f"    L{lineno}: {text}\n")
