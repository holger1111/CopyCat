"""Internationalization (i18n) helpers for CopyCat report output.

Supported languages: ``de`` (German, default) and ``en`` (English).

Usage in exporters::

    from ..i18n import get_tr
    tr = get_tr(str(getattr(args, "lang", "de")))
    title = tr("overview")  # "Übersicht" or "Overview"
"""

from __future__ import annotations

from typing import Callable

# ---------------------------------------------------------------------------
# Translation table
# ---------------------------------------------------------------------------

_STRINGS: dict[str, dict[str, str]] = {
    # ── Mode labels ────────────────────────────────────────────────────────
    "mode_recursive":       {"de": "REKURSIV",         "en": "RECURSIVE"},
    "mode_flat":            {"de": "FLACH (Default)",   "en": "FLAT (Default)"},
    "mode_recursive_title": {"de": "Rekursiv",          "en": "Recursive"},
    "mode_flat_title":      {"de": "Flach",             "en": "Flat"},

    # ── Meta / header labels ───────────────────────────────────────────────
    "date":          {"de": "Datum",   "en": "Date"},
    "mode":          {"de": "Modus",   "en": "Mode"},
    "path":          {"de": "Pfad",    "en": "Path"},
    "total":         {"de": "Gesamt",  "en": "Total"},
    "search":        {"de": "Suche",   "en": "Search"},
    "search_prefix": {"de": "SUCHE:",  "en": "SEARCH:"},
    "pattern":       {"de": "Muster:", "en": "Pattern:"},

    # ── Column headers ────────────────────────────────────────────────────
    "type":              {"de": "Typ",          "en": "Type"},
    "count":             {"de": "Anzahl",        "en": "Count"},
    "file":              {"de": "Datei",         "en": "File"},
    "size":              {"de": "Größe",         "en": "Size"},
    "line":              {"de": "Zeile",         "en": "Line"},
    "lines":             {"de": "Zeilen",        "en": "Lines"},
    "matches":           {"de": "Treffer",       "en": "Matches"},
    "comment_short":     {"de": "Komm.",         "en": "Comm."},
    "comment":           {"de": "Kommentar",     "en": "Comment"},
    "blank":             {"de": "Leer",          "en": "Blank"},
    "complexity_short":  {"de": "Kompl.",        "en": "Compl."},
    "complexity":        {"de": "Komplexität",   "en": "Complexity"},
    "comment_ratio":     {"de": "Kommentaranteil", "en": "Comment ratio"},
    "lines_total":       {"de": "Zeilen gesamt", "en": "Lines total"},
    "code_lines":        {"de": "Code-Zeilen",   "en": "Code lines"},
    "files_total":       {"de": "Dateien gesamt","en": "Total files"},

    # ── Section headings ──────────────────────────────────────────────────
    "overview":             {"de": "Übersicht",           "en": "Overview"},
    "code_stats":           {"de": "Code-Statistiken",    "en": "Code Statistics"},
    "code_details":         {"de": "Code-Details",        "en": "Code Details"},
    "code_details_label":   {"de": "CODE-Details:",       "en": "CODE Details:"},
    "code_stats_upper":     {"de": "CODE-STATISTIKEN",    "en": "CODE STATISTICS"},
    "search_results":       {"de": "Suchergebnisse",      "en": "Search Results"},
    "search_results_upper": {"de": "SUCHERGEBNISSE",      "en": "SEARCH RESULTS"},
    "total_upper":          {"de": "GESAMT",              "en": "TOTAL"},

    # ── Inline markers ────────────────────────────────────────────────────
    "cache_hit_bracket": {"de": "[Cache-Treffer]",    "en": "[Cache hit]"},
    "cache_hit_md":      {"de": "*(Cache-Treffer)*",  "en": "*(Cache hit)*"},
    "cache_hit_html":    {"de": "Cache-Treffer",      "en": "Cache hit"},

    # ── Status / error messages ───────────────────────────────────────────
    "binary_skip": {
        "de": "(Binary oder ungültiges Encoding - übersprungen)",
        "en": "(Binary or invalid encoding - skipped)",
    },
    "read_error":      {"de": "(Fehler beim Lesen)",  "en": "(Read error)"},
    "pygments_missing": {
        "de": "Syntax-Highlighting nicht verfügbar (pip install pygments).",
        "en": "Syntax highlighting not available (pip install pygments).",
    },
    # Use .format(count=N) after calling tr():
    "lines_omitted": {
        "de": "... [{count} weitere Zeilen ausgelassen]",
        "en": "... [{count} more lines omitted]",
    },
    # Use .format(exc=...) after calling tr():
    "plugin_error": {
        "de": "[Plugin-Fehler: {exc}]",
        "en": "[Plugin error: {exc}]",
    },

    # ── Timeline ──────────────────────────────────────────────────────────
    "no_archive":     {"de": "Keine Archiv-Reports gefunden.\n", "en": "No archive reports found.\n"},
    "timeline_files": {"de": "Dateien",                          "en": "Files"},
}

_SUPPORTED: frozenset[str] = frozenset({"de", "en"})


def get_tr(lang: str = "de") -> Callable[[str], str]:
    """Return a translation callable for *lang* (``'de'`` or ``'en'``).

    The returned function accepts a translation key and returns the
    corresponding string.  Unknown keys are returned unchanged as a
    safe fallback.

    >>> tr = get_tr("en")
    >>> tr("overview")
    'Overview'
    >>> tr("total_upper")
    'TOTAL'
    """
    _lang: str = lang if lang in _SUPPORTED else "de"

    def _tr(key: str) -> str:
        entry = _STRINGS.get(key)
        if entry is None:
            return key
        return entry.get(_lang) or entry.get("de") or key

    return _tr
