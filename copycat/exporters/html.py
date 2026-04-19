"""HTML report exporter and shared _html_escape helper."""

import logging
from datetime import datetime

from ..utils.files import get_plural
from ..utils.plugins import TYPE_FILTERS, PLUGIN_RENDERERS


def _html_escape(s: str) -> str:
    """Escape special HTML characters."""
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


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
