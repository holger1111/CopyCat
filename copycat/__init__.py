"""CopyCat package – public API."""

from .core import (
    load_config,
    parse_arguments,
    run_copycat,
    diff_reports,
    merge_reports,
    install_hook,
    watch_and_run,
)
from .exporters.timeline import build_timeline, _timeline_md, _timeline_ascii, _timeline_html
from .exporters.html import _html_escape, _write_html
from .exporters.txt import _write_txt
from .exporters.json_export import _write_json
from .exporters.md import _write_md
from .exporters.pdf import _write_pdf
from .exporters.template import _write_template
from .exporters.ai import _generate_ai_summary
from .extractors.binary import list_binary_file
from .extractors.drawio import extract_drawio
from .extractors.notebook import extract_notebook
from .utils.cache import _hash_file, _load_cache, _save_cache
from .utils.files import (
    get_next_serial_number,
    get_plural,
    is_valid_serial_filename,
    move_to_archive,
    size_filtered_glob,
)
from .utils.git import get_git_info, should_skip_gitignore
from .utils.plugins import TYPE_FILTERS, PLUGIN_RENDERERS, _loaded_plugins, load_plugins
from .utils.search import search_in_file, _build_search_results
from .utils.stats import _analyse_file, _build_stats, _COMMENT_PREFIXES

__all__ = [
    "load_config", "parse_arguments", "run_copycat",
    "diff_reports", "merge_reports", "install_hook", "watch_and_run",
    "build_timeline", "_timeline_md", "_timeline_ascii", "_timeline_html",
    "_html_escape", "_write_html", "_write_txt", "_write_json", "_write_md",
    "_write_pdf", "_write_template", "_generate_ai_summary",
    "list_binary_file", "extract_drawio", "extract_notebook",
    "_hash_file", "_load_cache", "_save_cache",
    "get_next_serial_number", "get_plural", "is_valid_serial_filename",
    "move_to_archive", "size_filtered_glob",
    "get_git_info", "should_skip_gitignore",
    "TYPE_FILTERS", "PLUGIN_RENDERERS", "_loaded_plugins", "load_plugins",
    "search_in_file", "_build_search_results",
    "_analyse_file", "_build_stats", "_COMMENT_PREFIXES",
]
