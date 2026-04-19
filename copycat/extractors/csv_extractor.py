"""CSV file extractor: column analysis, statistics and data preview."""

import csv
import io
from pathlib import Path
from typing import IO, Any


# Maximum rows to include in the preview section
_PREVIEW_ROWS = 10
# Maximum column value width in the preview table
_COL_MAX_WIDTH = 20


def _detect_delimiter(sample: str) -> str:
    """Sniff the most likely delimiter from a sample of CSV text."""
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=",;\t|")
        return dialect.delimiter
    except csv.Error:
        return ","


def _col_stats(values: list[str]) -> dict[str, Any]:
    """Return basic statistics for a single column's string values."""
    non_empty = [v for v in values if v.strip()]
    empty_count = len(values) - len(non_empty)

    # Try numeric
    numeric: list[float] = []
    for v in non_empty:
        try:
            numeric.append(float(v.replace(",", ".")))
        except ValueError:
            pass

    stats: dict[str, Any] = {
        "count": len(values),
        "non_empty": len(non_empty),
        "empty": empty_count,
        "unique": len(set(non_empty)),
    }
    if numeric and len(numeric) == len(non_empty):
        stats["type"] = "numeric"
        stats["min"] = min(numeric)
        stats["max"] = max(numeric)
        stats["mean"] = round(sum(numeric) / len(numeric), 4)
    else:
        stats["type"] = "text"
        if non_empty:
            lengths = [len(v) for v in non_empty]
            stats["min_len"] = min(lengths)
            stats["max_len"] = max(lengths)
    return stats


def extract_csv(writer: IO[str], csv_file: Path) -> None:
    """Extract CSV structure, column statistics and a data preview.

    Writes a human-readable summary covering:
    - File metadata (size, encoding, delimiter, row/column count)
    - Per-column statistics (type, unique count, min/max or length range)
    - Preview table (first _PREVIEW_ROWS rows)
    """
    try:
        size = csv_file.stat().st_size
        if size == 0:
            writer.write(f"[EMPTY: {csv_file.name}]\n")
            return

        # Try encodings in order; fall back to latin-1 (never fails)
        raw_text: str | None = None
        detected_encoding = "utf-8"
        for enc in ("utf-8-sig", "utf-8", "latin-1"):
            try:
                raw_text = csv_file.read_text(encoding=enc)
                detected_encoding = enc.replace("utf-8-sig", "utf-8")
                break
            except (UnicodeDecodeError, OSError):
                continue

        if raw_text is None:
            writer.write(f"[CSV READ ERROR: {csv_file.name}]\n")
            return

        sample = raw_text[:4096]
        delimiter = _detect_delimiter(sample)
        delim_display = {"\\t": "TAB", "\t": "TAB"}.get(delimiter, repr(delimiter))

        reader = csv.reader(io.StringIO(raw_text), delimiter=delimiter)
        all_rows: list[list[str]] = list(reader)

        if not all_rows:
            writer.write(f"CSV {csv_file.name}: (leer)\n")
            return

        headers = all_rows[0]
        data_rows = all_rows[1:]
        n_cols = len(headers)
        n_rows = len(data_rows)

        writer.write(
            f"CSV {csv_file.name}: {n_rows} Zeilen × {n_cols} Spalten"
            f" | Trennzeichen: {delim_display}"
            f" | Encoding: {detected_encoding}"
            f" | Größe: {size:,} Bytes\n"
        )

        # ── Column statistics ────────────────────────────────────────────────
        writer.write("  Spalten:\n")
        col_data: list[list[str]] = [
            [row[i] if i < len(row) else "" for row in data_rows]
            for i in range(n_cols)
        ]
        for i, header in enumerate(headers):
            s = _col_stats(col_data[i])
            if s["type"] == "numeric":
                detail = (
                    f"numeric | min={s['min']} max={s['max']} mean={s['mean']}"
                    f" | {s['unique']} unique"
                )
            else:
                len_info = (
                    f"len {s['min_len']}–{s['max_len']}" if "min_len" in s else "–"
                )
                detail = f"text | {len_info} | {s['unique']} unique"
            empty_info = f" | {s['empty']} leer" if s["empty"] else ""
            writer.write(f"    [{i + 1:>2}] {header!r:<20} {detail}{empty_info}\n")

        # ── Preview table ────────────────────────────────────────────────────
        preview = data_rows[:_PREVIEW_ROWS]
        if not preview:
            return

        def _trunc(val: str) -> str:
            return val if len(val) <= _COL_MAX_WIDTH else val[:_COL_MAX_WIDTH - 1] + "…"

        col_widths = [
            max(len(_trunc(h)), *(len(_trunc(row[i] if i < len(row) else "")) for row in preview))
            for i, h in enumerate(headers)
        ]

        def _row_line(cells: list[str]) -> str:
            return "  | " + " | ".join(
                _trunc(cells[i] if i < len(cells) else "").ljust(col_widths[i])
                for i in range(n_cols)
            ) + " |\n"

        sep = "  +" + "+".join("-" * (w + 2) for w in col_widths) + "+\n"
        header_cells = [h.ljust(col_widths[i]) for i, h in enumerate(headers)]
        writer.write(f"\n  Vorschau ({min(n_rows, _PREVIEW_ROWS)} von {n_rows} Zeilen):\n")
        writer.write(sep)
        writer.write("  | " + " | ".join(header_cells) + " |\n")
        writer.write(sep)
        for row in preview:
            writer.write(_row_line(row))
        writer.write(sep)
        if n_rows > _PREVIEW_ROWS:
            writer.write(f"  … {n_rows - _PREVIEW_ROWS} weitere Zeilen\n")
        writer.write("\n")

    except OSError as exc:
        writer.write(f"[CSV READ ERROR: {csv_file.name} – {exc}]\n")
    except Exception as exc:
        writer.write(f"[CSV ERROR: {csv_file.name} – {exc}]\n")
