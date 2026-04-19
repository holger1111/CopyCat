"""Jinja2 template-based report exporter."""

import argparse
from datetime import datetime
from pathlib import Path
from typing import Any


def _write_template(
    template_path: str | Path,
    files: dict[str, list[Path]],
    args: argparse.Namespace,
    input_dir: Path,
    git_info: str,
    serial: int,
    search_pattern: str | None = None,
    search_results: dict[Path, list[tuple[int, str]]] | None = None,
) -> str:
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
