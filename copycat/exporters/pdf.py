"""PDF report exporter (requires reportlab)."""

import argparse
from datetime import datetime
from pathlib import Path
from typing import Any

from ..i18n import get_tr
from ..utils.files import get_plural
from .html import _html_escape


def _write_pdf(
    path: Path,
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
    """Write PDF report using reportlab.

    Requires: pip install reportlab
    """
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.platypus import (
            SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Preformatted,
        )
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import mm
        from reportlab.lib import colors as rl_colors
    except ImportError as exc:
        raise ImportError(
            "reportlab ist nicht installiert. Bitte: pip install reportlab"
        ) from exc

    doc = SimpleDocTemplate(
        str(path), pagesize=A4,
        rightMargin=20 * mm, leftMargin=20 * mm,
        topMargin=25 * mm, bottomMargin=20 * mm,
        title=f"CopyCat Report #{serial}",
        author="CopyCat v3.0",
    )
    styles = getSampleStyleSheet()
    h2_style = styles["Heading2"]
    h3_style = styles["Heading3"]
    normal_style = styles["Normal"]
    code_style = ParagraphStyle(
        "CCCode", parent=normal_style,
        fontName="Courier", fontSize=7,
        leftIndent=8, spaceAfter=4, leading=10,
    )
    title_style = ParagraphStyle(
        "CCTitle", parent=styles["Title"],
        fontSize=16, spaceAfter=6,
    )

    story = []
    _lang = str(getattr(args, "lang", "de"))
    tr = get_tr(_lang)
    now = datetime.now().strftime("%d.%m.%Y %H:%M")
    mode_text = tr("mode_recursive_title") if args.recursive else tr("mode_flat_title")
    total_files = sum(len(v) for v in files.values())
    cache = cache or {}
    sr = search_results or {}
    _hdr_bg = rl_colors.HexColor("#e3f2fd")
    _grid_c = rl_colors.HexColor("#90caf9")

    # Header
    story.append(Paragraph(f"CopyCat v3.0 Report #{serial}", title_style))
    story.append(Spacer(1, 4 * mm))

    # Meta table
    meta_data = [
        [tr("date"), now],
        [tr("mode"), mode_text],
        [tr("path"), str(input_dir)],
        ["Git", git_info],
        [tr("total"), f"{total_files} {get_plural(total_files, _lang)}"],
    ]
    if search_pattern:
        total_hits = sum(len(v) for v in sr.values())
        meta_data.append([
            tr("search"),
            f'"{search_pattern}" \u2192 {total_hits} {tr("matches")} in {len(sr)} {get_plural(len(sr), _lang)}',
        ])
    meta_table = Table(meta_data, colWidths=[35 * mm, None])
    meta_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), _hdr_bg),
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("GRID", (0, 0), (-1, -1), 0.4, _grid_c),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 6 * mm))

    # Overview
    story.append(Paragraph(tr("overview"), h2_style))
    ov_rows = [[tr("type"), tr("count")]] + [
        [t.upper(), str(len(flist))] for t, flist in files.items() if flist
    ]
    ov_table = Table(ov_rows, colWidths=[55 * mm, 30 * mm])
    ov_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), _hdr_bg),
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("GRID", (0, 0), (-1, -1), 0.4, _grid_c),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    story.append(ov_table)
    story.append(Spacer(1, 5 * mm))

    # Stats
    if stats and stats.get("per_file"):
        story.append(Paragraph(tr("code_stats"), h2_style))
        tot = stats["total"]
        avg_str = (
            f"\u00d8 {tot['avg_complexity']}"
            if tot["avg_complexity"] is not None else "\u2013"
        )
        s_rows = [[tr("file"), "LOC", "Code", tr("comment_short"), tr("blank"), tr("complexity_short")]]
        for fpath, s in stats["per_file"].items():
            c = str(s["complexity"]) if s["complexity"] is not None else "\u2013"
            s_rows.append([fpath.name, str(s["loc"]), str(s["code"]),
                           str(s["comments"]), str(s["blank"]), c])
        s_rows.append([tr("total_upper"), str(tot["loc"]), str(tot["code"]),
                       str(tot["comments"]), str(tot["blank"]), avg_str])
        s_table = Table(s_rows)
        s_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), _hdr_bg),
            ("BACKGROUND", (0, -1), (-1, -1), rl_colors.HexColor("#fff9c4")),
            ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("GRID", (0, 0), (-1, -1), 0.4, _grid_c),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ]))
        story.append(s_table)
        story.append(Paragraph(f"{tr('comment_ratio')}: {tot['comment_ratio']}%", normal_style))
        story.append(Spacer(1, 4 * mm))

    # Code details
    selected_types = args.types if args.types else ["all"]
    process_all = "all" in selected_types
    _MAX_LINES_PDF = 150
    if process_all or "code" in selected_types:
        story.append(Paragraph(tr("code_details"), h2_style))
        for code_file in files.get("code", []):
            rel_path = code_file.relative_to(input_dir)
            if code_file in cache:
                code_text = cache[code_file].get("content", "")
                lines_count = cache[code_file].get("lines", 0)
            else:
                try:
                    code_text = code_file.read_text(encoding="utf-8")
                    lines_count = sum(1 for ln in code_text.splitlines() if ln.strip())
                except (UnicodeDecodeError, OSError):
                    code_text = tr("binary_skip")
                    lines_count = 0
            story.append(Paragraph(f"{rel_path.as_posix()} ({lines_count} {tr('lines')})", h3_style))
            code_lines = code_text.splitlines()
            if len(code_lines) > _MAX_LINES_PDF:
                code_text = "\n".join(code_lines[:_MAX_LINES_PDF]) + (
                    "\n" + tr("lines_omitted").format(count=len(code_lines) - _MAX_LINES_PDF)
                )
            safe_code = _html_escape(code_text)
            story.append(Preformatted(safe_code, code_style))
            story.append(Spacer(1, 2 * mm))

    # Search results
    if search_pattern and sr:
        total_hits = sum(len(v) for v in sr.values())
        story.append(Paragraph(
            f'{tr("search_results")}: "{search_pattern}" ({total_hits} {tr("matches")})', h2_style
        ))
        sr_rows = [[tr("file"), tr("line"), tr("matches")]]
        for f_path, hits in sr.items():
            for lineno, text in hits:
                sr_rows.append([f_path.name, str(lineno), text.strip()[:80]])
        sr_table = Table(sr_rows, colWidths=[50 * mm, 15 * mm, None])
        sr_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), _hdr_bg),
            ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("GRID", (0, 0), (-1, -1), 0.4, _grid_c),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ]))
        story.append(sr_table)

    doc.build(story)
