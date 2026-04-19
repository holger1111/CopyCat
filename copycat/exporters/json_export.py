"""JSON report exporter."""

import argparse
import csv
import io
import json
from datetime import datetime
from pathlib import Path
from typing import Any


def _write_json(
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
            if t == "notebook" and f.suffix.lower() == ".csv":
                try:
                    raw = f.read_text(encoding="utf-8-sig", errors="replace")
                    sample = raw[:4096]
                    try:
                        dialect = csv.Sniffer().sniff(sample, delimiters=",;\t|")
                        delim = dialect.delimiter
                    except csv.Error:
                        delim = ","
                    reader = csv.reader(io.StringIO(raw), delimiter=delim)
                    all_rows = list(reader)
                    headers = all_rows[0] if all_rows else []
                    entry["csv"] = {
                        "rows": max(0, len(all_rows) - 1),
                        "columns": len(headers),
                        "headers": headers,
                        "delimiter": delim,
                    }
                except Exception:
                    entry["csv"] = None
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

    with open(path, "w", encoding="utf-8") as out_f:
        json.dump(report, out_f, ensure_ascii=False, indent=2)
