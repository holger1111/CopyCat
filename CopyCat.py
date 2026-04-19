"""
CopyCat v3.0 – thin wrapper around the copycat package.

All public symbols are imported here so that existing code and tests
that import directly from CopyCat continue to work unchanged.
"""

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
from copycat.extractors.csv_extractor import extract_csv
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
    from copycat.cli import main as _main
    _main()
