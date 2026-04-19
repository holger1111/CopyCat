"""File collection, serial numbering, archiving and exclusion helpers."""

import argparse
import fnmatch
import logging
import re
import shutil
from collections.abc import Callable, Iterator
from pathlib import Path

from .git import should_skip_gitignore
from .plugins import TYPE_FILTERS


def is_valid_serial_filename(filename: str) -> bool:
    pattern = r"^combined_copycat_(\d+)\.(txt|json|md|html|pdf)$"
    return bool(re.match(pattern, filename))


def get_next_serial_number(base_path: Path) -> int:
    existing = list(base_path.glob("combined_copycat*"))
    max_num = 0
    for p in existing:
        match = re.match(r"^combined_copycat_(\d+)\.(txt|json|md|html|pdf)$", p.name)
        if match is not None:
            try:
                num = int(match.group(1))
                max_num = max(max_num, num)
            except (ValueError, AttributeError):  # pragma: no cover
                continue
    return max_num + 1


def move_to_archive(base_path: Path, filename: str) -> None:
    archive_path = base_path / "CopyCat_Archive"
    archive_path.mkdir(exist_ok=True)

    old_file = base_path / filename
    if old_file.exists() and is_valid_serial_filename(filename):
        try:
            shutil.move(old_file, archive_path / filename)
        except (shutil.Error, PermissionError, OSError) as e:
            logging.warning("Archiv-Fehler %s: %s", filename, e)


def get_plural(count: int, lang: str = "de") -> str:
    if lang == "en":
        return "file" if count == 1 else "files"
    return "Datei" if count == 1 else "Dateien"


def _should_exclude(candidate: Path, input_dir: Path, exclude_patterns: list[str]) -> bool:
    """Prüft ob candidate auf ein Exclude-Glob-Muster passt."""
    if not exclude_patterns:
        return False
    try:
        rel = str(candidate.relative_to(input_dir)).replace("\\", "/")
    except ValueError:
        rel = candidate.name
    name = candidate.name
    for pattern in exclude_patterns:
        p = pattern.rstrip("/")
        if pattern.endswith("/"):
            if rel.startswith(p + "/") or rel == p:
                return True
        if fnmatch.fnmatch(name, p):
            return True
        if fnmatch.fnmatch(rel, p):
            return True
    return False


def size_filtered_glob(
    search_method: Callable[[str], Iterator[Path]],
    patterns: list[str],
    max_bytes: float,
    script_file: Path,
    input_dir: Path,
    exclude_patterns: list[str] | None = None,
) -> Iterator[Path]:
    total_checked = 0
    for pat in patterns:
        for candidate in search_method(pat):
            total_checked += 1
            try:
                if should_skip_gitignore(input_dir, candidate):
                    continue
                if _should_exclude(candidate, input_dir, exclude_patterns or []):
                    continue
                if candidate.stat().st_size < max_bytes:
                    if (
                        candidate.resolve() != script_file
                        and "combined_copycat" not in candidate.name
                    ):
                        yield candidate
                if total_checked % 100 == 0:
                    logging.debug("Geprüft: %d Dateien...", total_checked)
            except OSError:
                continue
    logging.info("→ %d geprüft, Filter OK", total_checked)


def _collect_files(args: argparse.Namespace, input_dir: Path, script_file: Path) -> dict[str, list[Path]]:
    """Collect and return files dict based on args."""
    files: dict[str, list[Path]] = {k: [] for k in TYPE_FILTERS}
    selected_types = args.types if args.types else ["all"]
    process_all = "all" in selected_types
    search_method = input_dir.rglob if args.recursive else input_dir.glob
    use_filter = args.recursive or args.max_size != float("inf")
    limit_bytes = args.max_size * 1024 * 1024
    exclude_patterns = getattr(args, "exclude", None) or []

    logging.info("Suche %s in %s", "rekursiv" if args.recursive else "flach", input_dir)
    if use_filter:
        logging.info("Limit: <%sMB (%.0f Bytes)", args.max_size, limit_bytes)

    for t, patterns in TYPE_FILTERS.items():
        if process_all or t in selected_types:
            if use_filter:
                for candidate in size_filtered_glob(
                    search_method, patterns, limit_bytes, script_file, input_dir, exclude_patterns
                ):
                    files[t].append(candidate)
            else:
                for pat in patterns:
                    for candidate in search_method(pat):
                        if should_skip_gitignore(input_dir, candidate):
                            continue
                        if _should_exclude(candidate, input_dir, exclude_patterns):
                            continue
                        if (
                            candidate.resolve() != script_file
                            and "combined_copycat" not in candidate.name
                        ):
                            files[t].append(candidate)
    return files
