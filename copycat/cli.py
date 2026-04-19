"""CopyCat CLI entry point.

This module provides the ``main()`` function that is registered as a
console-script entry point in ``pyproject.toml``::

    copycat = "copycat.cli:main"

The legacy ``python CopyCat.py`` workflow continues to work unchanged –
``CopyCat.py`` now delegates here.
"""

import logging
from pathlib import Path

from . import __version__
from .core import (
    diff_reports,
    install_hook,
    merge_reports,
    parse_arguments,
    run_copycat,
    watch_and_run,
)
from .exporters.timeline import build_timeline
from .utils.plugins import PLUGIN_RENDERERS, TYPE_FILTERS, load_plugins


def main() -> None:
    """Parse arguments and dispatch to the appropriate CopyCat operation."""
    args = parse_arguments()

    if getattr(args, "verbose", False):
        log_level = logging.DEBUG
    elif getattr(args, "quiet", False):
        log_level = logging.WARNING
    else:
        log_level = logging.INFO
    logging.basicConfig(level=log_level, format="%(message)s")

    if getattr(args, "list_plugins", False):
        plugin_dir = getattr(args, "plugin_dir", None) or str(
            Path(__file__).parent.parent / "plugins"
        )
        loaded = load_plugins(plugin_dir)
        if loaded:
            print("Geladene Plugins:")
            for t in loaded:
                pats = TYPE_FILTERS.get(t, [])
                rinfo = (
                    "benutzerdefinierter Renderer"
                    if PLUGIN_RENDERERS.get(t)
                    else "Standard-Renderer"
                )
                print(f"  {t}: {', '.join(pats)} ({rinfo})")
        else:
            print(f"Keine Plugins in {plugin_dir} gefunden.")

    elif getattr(args, "install_hook", None):
        hook = install_hook(Path(args.install_hook))
        print(f"Hook installiert: {hook}")

    elif getattr(args, "merge", None):
        print(merge_reports([Path(p) for p in args.merge]))

    elif getattr(args, "diff", None):
        print(diff_reports(Path(args.diff[0]), Path(args.diff[1])))

    elif getattr(args, "watch", False):
        watch_and_run(args, cooldown=getattr(args, "cooldown", 2.0))

    elif getattr(args, "timeline", False):
        tl_base = Path(args.input or str(Path(__file__).parent.parent))
        tl_archive = tl_base / "CopyCat_Archive"
        tl_fmt = getattr(args, "timeline_format", "md")
        print(build_timeline(tl_archive, fmt=tl_fmt, lang=getattr(args, "lang", "de")))

    else:
        run_copycat(args)


if __name__ == "__main__":  # pragma: no cover
    main()
