"""
CopyCat v2.9 – thin wrapper around the copycat package.

All public symbols are imported here so that existing code and tests
that import directly from CopyCat continue to work unchanged.
"""

import logging
from pathlib import Path

# ── Public API (re-exported for backward compatibility) ──────────────────────
from copycat.core import (
    load_config,
    parse_arguments,
    run_copycat,
    diff_reports,
    merge_reports,
    install_hook,
    watch_and_run,
)
from copycat.exporters.ai import _generate_ai_summary
from copycat.exporters.html import _html_escape, _write_html
from copycat.exporters.json_export import _write_json
from copycat.exporters.md import _write_md
from copycat.exporters.pdf import _write_pdf
from copycat.exporters.template import _write_template
from copycat.exporters.timeline import (
    build_timeline,
    _timeline_ascii,
    _timeline_html,
    _timeline_md,
)
from copycat.exporters.txt import _write_txt
from copycat.extractors.binary import list_binary_file
from copycat.extractors.drawio import extract_drawio, _safe_xml_parse
from copycat.extractors.notebook import extract_notebook
from copycat.utils.cache import _cleanup_cache, _hash_file, _load_cache, _save_cache
from copycat.utils.files import (
    _collect_files,
    _should_exclude,
    get_next_serial_number,
    get_plural,
    is_valid_serial_filename,
    move_to_archive,
    size_filtered_glob,
)
from copycat.utils.git import get_git_info, should_skip_gitignore
from copycat.utils.plugins import (
    TYPE_FILTERS,
    PLUGIN_RENDERERS,
    _loaded_plugins,
    load_plugins,
)
from copycat.utils.search import _build_search_results, search_in_file
from copycat.utils.stats import _COMMENT_PREFIXES, _analyse_file, _build_stats

# ── Entry point ──────────────────────────────────────────────────────────────
if __name__ == "__main__":  # pragma: no cover
    _args = parse_arguments()
    if getattr(_args, "verbose", False):
        _log_level = logging.DEBUG
    elif getattr(_args, "quiet", False):
        _log_level = logging.WARNING
    else:
        _log_level = logging.INFO
    logging.basicConfig(level=_log_level, format="%(message)s")
    if getattr(_args, "list_plugins", False):
        _plugin_dir = getattr(_args, "plugin_dir", None) or str(Path(__file__).parent / "plugins")
        _loaded = load_plugins(_plugin_dir)
        if _loaded:
            print("Geladene Plugins:")
            for _t in _loaded:
                _pats = TYPE_FILTERS.get(_t, [])
                _rinfo = "benutzerdefinierter Renderer" if PLUGIN_RENDERERS.get(_t) else "Standard-Renderer"
                print(f"  {_t}: {', '.join(_pats)} ({_rinfo})")
        else:
            print(f"Keine Plugins in {_plugin_dir} gefunden.")
    elif getattr(_args, "install_hook", None):
        hook = install_hook(Path(_args.install_hook))
        print(f"Hook installiert: {hook}")
    elif getattr(_args, "merge", None):
        print(merge_reports([Path(p) for p in _args.merge]))
    elif getattr(_args, "diff", None):
        print(diff_reports(Path(_args.diff[0]), Path(_args.diff[1])))
    elif getattr(_args, "watch", False):
        watch_and_run(_args, cooldown=getattr(_args, "cooldown", 2.0))
    elif getattr(_args, "timeline", False):
        _tl_base = Path(_args.input or str(Path(__file__).parent))
        _tl_archive = _tl_base / "CopyCat_Archive"
        _tl_fmt = getattr(_args, "timeline_format", "md")
        print(build_timeline(_tl_archive, fmt=_tl_fmt))
    else:
        run_copycat(_args)
