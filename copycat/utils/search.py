"""Full-text search across project files."""

import concurrent.futures
import logging
import re
from pathlib import Path


def search_in_file(file_path: Path, pattern: str) -> list[tuple[int, str]]:
    """Search regex pattern in a text file. Returns list of (lineno, text) tuples.

    Sicherheit: Regex-Timeout gegen ReDoS (Catastrophic Backtracking).
    """
    try:
        # Limitiere Regex-Komplexität: max. 20 Alternatives, max. 5000 Zeichen
        if pattern.count("|") > 20 or len(pattern) > 5000:
            logging.warning("Regex-Pattern zu komplex, übersprungen: %s...", pattern[:50])
            return []
        compiled = re.compile(pattern, timeout=1)  # type: ignore[call-overload]  # 1 Sekunde Timeout
    except re.error:  # pragma: no cover
        return []  # pragma: no cover
    except (TypeError, AttributeError):
        # Fallback für Python < 3.11 ohne Timeout-Support
        try:
            compiled = re.compile(pattern)
        except re.error:
            return []
    matches = []
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            for lineno, line in enumerate(f, 1):
                try:
                    if compiled.search(line):
                        matches.append((lineno, line.rstrip()))
                except TimeoutError:  # pragma: no cover
                    logging.warning("Regex-Timeout in Datei: %s", file_path.name)  # pragma: no cover
                    break  # pragma: no cover
    except (UnicodeDecodeError, OSError):
        pass
    return matches


def _build_search_results(files: dict[str, list[Path]], pattern: str) -> dict[Path, list[tuple[int, str]]]:
    """Search pattern in all text-based files in parallel. Returns {Path: [(lineno, text)]}."""
    SEARCHABLE = {"code", "web", "db", "config", "docs", "deps"}
    candidates = [
        f for t, flist in files.items() if t in SEARCHABLE for f in flist
    ]
    if not candidates:
        return {}
    results = {}
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future_to_path = {executor.submit(search_in_file, f, pattern): f for f in candidates}
        for future in concurrent.futures.as_completed(future_to_path):
            f = future_to_path[future]
            hits = future.result()
            if hits:
                results[f] = hits
    return results
