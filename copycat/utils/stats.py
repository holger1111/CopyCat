"""Per-file code statistics: LOC, blank, comment lines and cyclomatic complexity."""

import re
from pathlib import Path


# Mapping Dateiendung → Tuple von Zeilenpräfixen, die als Kommentar gewertet werden
_COMMENT_PREFIXES: dict = {
    ".py": ("#", '"""', "'''"),
    ".rb": ("#",), ".sh": ("#",), ".bash": ("#",), ".r": ("#",),
    ".yml": ("#",), ".yaml": ("#",), ".toml": ("#",),
    ".java": ("//", "/*", "*/", "*"), ".c": ("//", "/*", "*/", "*"),
    ".cpp": ("//", "/*", "*/", "*"), ".h": ("//", "/*", "*/", "*"),
    ".cs": ("//", "/*", "*/", "*"), ".js": ("//", "/*", "*/", "*"),
    ".ts": ("//", "/*", "*/", "*"), ".jsx": ("//", "/*", "*/", "*"),
    ".tsx": ("//", "/*", "*/", "*"), ".go": ("//", "/*", "*/", "*"),
    ".swift": ("//", "/*", "*/", "*"), ".kt": ("//", "/*", "*/", "*"),
    ".scala": ("//", "/*", "*/", "*"), ".groovy": ("//", "/*", "*/", "*"),
    ".sql": ("--", "/*", "*/"),
    ".html": ("<!--",), ".xml": ("<!--",), ".svg": ("<!--",),
    ".css": ("/*", "*/", "*"), ".less": ("/*", "*/", "*"), ".scss": ("/*", "*/", "*"),
}


def _analyse_file(path: Path) -> dict:
    """Analyse a source file: count LOC, blank, comment, code lines + cyclomatic complexity."""
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return {"loc": 0, "code": 0, "comments": 0, "blank": 0, "complexity": None}
    lines = text.splitlines()
    suffix = path.suffix.lower()
    comment_prefixes = _COMMENT_PREFIXES.get(suffix, ("#",))
    blank = sum(1 for ln in lines if not ln.strip())
    comments = sum(
        1 for ln in lines
        if ln.strip() and any(ln.strip().startswith(p) for p in comment_prefixes)
    )
    code = max(len(lines) - blank - comments, 0)
    complexity = None
    if suffix == ".py":
        try:
            import ast as _ast
            tree = _ast.parse(text)
            _DECISION = (
                _ast.If, _ast.For, _ast.While, _ast.ExceptHandler,
                _ast.With, _ast.Assert, _ast.ListComp, _ast.DictComp,
                _ast.SetComp, _ast.GeneratorExp,
            )
            complexity = 1 + sum(1 for n in _ast.walk(tree) if isinstance(n, _DECISION))
        except SyntaxError:
            complexity = None
    else:
        m = re.findall(r'\b(?:if|else|elif|for|while|switch|case|catch|except)\b|&&|\|\|', text)
        complexity = 1 + len(m) if m else 1
    return {"loc": len(lines), "code": code, "comments": comments, "blank": blank, "complexity": complexity}


def _build_stats(files: dict, cache: dict = None) -> dict:
    """Build per-file and aggregate stats for all code files."""
    cache = cache or {}
    per_file: dict = {}
    for f in files.get("code", []):
        if f in cache and cache[f].get("stats"):
            per_file[f] = cache[f]["stats"]
        else:
            per_file[f] = _analyse_file(f)
    if per_file:
        total_loc = sum(v["loc"] for v in per_file.values())
        total_code = sum(v["code"] for v in per_file.values())
        total_comments = sum(v["comments"] for v in per_file.values())
        total_blank = sum(v["blank"] for v in per_file.values())
        complexities = [v["complexity"] for v in per_file.values() if v["complexity"] is not None]
        avg_c = round(sum(complexities) / len(complexities), 1) if complexities else None
        max_c = max(complexities) if complexities else None
        comment_ratio = round(total_comments / total_loc * 100, 1) if total_loc else 0.0
    else:
        total_loc = total_code = total_comments = total_blank = 0
        avg_c = max_c = None
        comment_ratio = 0.0
    return {
        "per_file": per_file,
        "total": {
            "loc": total_loc,
            "code": total_code,
            "comments": total_comments,
            "blank": total_blank,
            "avg_complexity": avg_c,
            "max_complexity": max_c,
            "comment_ratio": comment_ratio,
        },
    }
