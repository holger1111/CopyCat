"""Report timeline: build and render from CopyCat_Archive."""

import json
import re
from pathlib import Path
from typing import Any

from ..utils.files import is_valid_serial_filename
from .html import _html_escape


def build_timeline(archive_dir: Path | None = None, fmt: str = "md") -> str:
    """Build a timeline from CopyCat archive reports.

    Reads all ``combined_copycat_N.*`` files from *archive_dir*
    (default: ``CopyCat_Archive/`` next to the package root), extracts metadata
    and returns a formatted timeline string.

    fmt: ``'md'`` (Markdown table), ``'ascii'`` (ASCII bar chart), ``'html'`` (Chart.js HTML)
    """
    if archive_dir is None:
        archive_dir = Path(__file__).parent.parent.parent / "CopyCat_Archive"
    archive_dir = Path(archive_dir)

    entries = []
    for report_file in sorted(archive_dir.glob("combined_copycat_*.*")):
        if not is_valid_serial_filename(report_file.name):
            continue
        m = re.match(r"^combined_copycat_(\d+)\.(txt|json|md|html|pdf)$", report_file.name)
        if not m:  # pragma: no cover
            continue
        serial_num = int(m.group(1))
        ext = m.group(2)
        if ext == "pdf":
            continue  # PDF nicht als Text lesbar

        try:
            text = report_file.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        entry: dict[str, Any] = {"serial": serial_num, "date": "?", "total": 0, "types": {}}
        if ext == "json":
            try:
                data = json.loads(text)
                entry["date"] = data.get("generated", "?")
                entry["total"] = int(data.get("files", 0))
                entry["types"] = {t: int(c) for t, c in data.get("types", {}).items()}
            except (json.JSONDecodeError, KeyError, ValueError):
                pass
        else:
            m_date = re.search(r"CopyCat v[\d.]+ \| (.+?) \|", text)
            if m_date:
                entry["date"] = m_date.group(1).strip()
            m_total = re.search(r"Gesamt: (\d+)", text)
            if m_total:
                entry["total"] = int(m_total.group(1))
            for tm in re.finditer(r"^(\w+): (\d+) Datei", text, re.MULTILINE):
                entry["types"][tm.group(1).lower()] = int(tm.group(2))
        entries.append(entry)

    if not entries:
        return "Keine Archiv-Reports gefunden.\n"

    entries.sort(key=lambda e: e["serial"])

    if fmt == "ascii":
        return _timeline_ascii(entries)
    if fmt == "html":
        return _timeline_html(entries)
    return _timeline_md(entries)


def _timeline_md(entries: list[dict[str, Any]]) -> str:
    all_types = sorted({t for e in entries for t in e["types"]})
    header = "| Serial | Datum | Gesamt |" + "".join(f" {t.upper()} |" for t in all_types)
    sep = "|---|---|---|" + "|---|" * len(all_types)
    rows = []
    for e in entries:
        row = f"| #{e['serial']} | {e['date']} | {e['total']} |"
        row += "".join(f" {e['types'].get(t, 0)} |" for t in all_types)
        rows.append(row)
    return "# CopyCat Report-Timeline\n\n" + header + "\n" + sep + "\n" + "\n".join(rows) + "\n"


def _timeline_ascii(entries: list[dict[str, Any]]) -> str:
    max_total = max((e["total"] for e in entries), default=1) or 1
    _w = 40
    lines = ["CopyCat Report-Timeline (ASCII)", "=" * 56]
    for e in entries:
        bar = "\u2588" * int(e["total"] / max_total * _w)
        lines.append(f"  #{e['serial']:>3} [{e['date']:>16}]  {bar} {e['total']}")
    lines.append("=" * 56)
    return "\n".join(lines) + "\n"


def _timeline_html(entries: list[dict[str, Any]]) -> str:
    labels = json.dumps([f"#{e['serial']}" for e in entries])
    data_pts = json.dumps([e["total"] for e in entries])
    rows = "".join(
        f"<tr><td>#{e['serial']}</td><td>{_html_escape(e['date'])}</td>"
        f"<td>{e['total']}</td></tr>"
        for e in entries
    )
    return (
        '<!DOCTYPE html>\n<html lang="de">\n<head>\n<meta charset="UTF-8">\n'
        '<title>CopyCat Timeline</title>\n'
        '<script src="https://cdn.jsdelivr.net/npm/chart.js@4/dist/chart.umd.min.js">'
        '</script>\n'
        '<style>'
        'body{font-family:"Segoe UI",Arial,sans-serif;max-width:900px;'
        'margin:0 auto;padding:24px;background:#f5f5f5}'
        'h1,h2{color:#1565c0}'
        'canvas{background:#fff;border-radius:8px;padding:12px;'
        'box-shadow:0 1px 3px rgba(0,0,0,.1);margin-bottom:24px}'
        'table{border-collapse:collapse;width:100%;background:#fff;border-radius:8px;'
        'box-shadow:0 1px 3px rgba(0,0,0,.1)}'
        'th,td{padding:9px 16px;border:1px solid #e0e0e0;text-align:left}'
        'th{background:#e3f2fd;font-weight:600}'
        '</style>\n</head>\n<body>\n'
        '<h1>&#128008; CopyCat Report-Timeline</h1>\n'
        '<canvas id="cc-chart" height="80"></canvas>\n'
        '<script>\nnew Chart(document.getElementById("cc-chart"), {\n'
        '  type: "bar",\n'
        f'  data: {{ labels: {labels},\n'
        f'    datasets: [{{ label: "Dateien gesamt", data: {data_pts},\n'
        '      backgroundColor: "#1565c0", borderRadius: 4 }] },\n'
        '  options: { responsive: true,\n'
        '    plugins: { legend: { display: false } },\n'
        '    scales: { y: { beginAtZero: true } } }\n'
        '});\n</script>\n'
        '<h2>Details</h2>\n'
        '<table>\n<tr><th>Serial</th><th>Datum</th><th>Dateien</th></tr>\n'
        f'{rows}\n</table>\n</body>\n</html>\n'
    )
