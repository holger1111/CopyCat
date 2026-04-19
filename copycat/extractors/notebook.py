"""Jupyter Notebook (.ipynb) cell extractor."""

import json
from pathlib import Path
from typing import IO


def extract_notebook(writer: IO[str], nb_file: Path) -> None:
    """Extract code and markdown cells from a Jupyter Notebook (.ipynb)."""
    try:
        with open(nb_file, "r", encoding="utf-8") as f:
            nb = json.load(f)
        cells = nb.get("cells", [])
        code_cells = [c for c in cells if c.get("cell_type") == "code"]
        md_cells = [c for c in cells if c.get("cell_type") == "markdown"]
        writer.write(
            f"NOTEBOOK {nb_file.name}: {len(cells)} Cells "
            f"({len(code_cells)} Code, {len(md_cells)} Markdown)\n"
        )
        for i, cell in enumerate(cells, 1):
            ctype = cell.get("cell_type", "unknown")
            source = "".join(cell.get("source", []))
            if source.strip():
                writer.write(f"  [Cell {i} \u2013 {ctype}]\n")
                for line in source.splitlines():
                    writer.write(f"  {line}\n")
                writer.write("\n")
    except (json.JSONDecodeError, KeyError) as e:
        writer.write(f"[NOTEBOOK ERROR: {nb_file.name} - {e}]\n")
    except OSError as e:
        writer.write(f"[NOTEBOOK READ ERROR: {nb_file.name} - {e}]\n")
