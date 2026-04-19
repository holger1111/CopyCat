"""Incremental cache: hashing, loading, saving and cleanup."""

import hashlib
import json
import logging
import time
from pathlib import Path


def _hash_file(path: Path) -> str:
    """Return SHA-256 hex digest of a file's binary content. Returns '' on error."""
    h = hashlib.sha256()
    try:
        with open(path, "rb") as fh:
            for chunk in iter(lambda: fh.read(65536), b""):
                h.update(chunk)
    except OSError:
        return ""
    return h.hexdigest()


def _cleanup_cache(cache_dir: Path, max_age_days: int) -> int:
    """Löscht Cache-Einträge älter als max_age_days. Gibt Anzahl gelöschter Einträge zurück."""
    if not cache_dir.is_dir():
        return 0
    cache_file = cache_dir / "cache.json"
    if not cache_file.is_file():
        return 0
    try:
        current_time = time.time()
        with open(cache_file, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        entries = data.get("entries", {})
        deleted_count = 0
        for key in list(entries.keys()):
            entry = entries[key]
            file_time = entry.get("timestamp", 0)
            age_days = (current_time - file_time) / 86400
            if age_days > max_age_days:
                del entries[key]
                deleted_count += 1
        if deleted_count > 0:
            data["entries"] = entries
            with open(cache_file, "w", encoding="utf-8") as fh:
                json.dump(data, fh, ensure_ascii=False, indent=2)
            logging.info("Cache-Cleanup: %d alte Einträge gelöscht", deleted_count)
        return deleted_count
    except Exception:
        logging.exception("Cache-Cleanup fehlgeschlagen")
        return 0


def _load_cache(cache_file: Path) -> dict:
    """Load incremental cache from JSON. Returns {} on missing/invalid file."""
    if not cache_file.is_file():
        return {}
    try:
        with open(cache_file, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        if data.get("version") != "1":
            return {}
        return data.get("entries", {})
    except (OSError, json.JSONDecodeError, KeyError):
        return {}


def _save_cache(cache_file: Path, entries: dict) -> None:
    """Persist incremental cache entries to JSON with timestamps for cleanup."""
    try:
        cache_file.parent.mkdir(exist_ok=True)
        # Füge Timestamp hinzu falls nicht vorhanden (für Cache-Cleanup)
        current_time = time.time()
        for key in entries:
            if "timestamp" not in entries[key]:
                entries[key]["timestamp"] = current_time
        with open(cache_file, "w", encoding="utf-8") as fh:
            json.dump({"version": "1", "entries": entries}, fh, ensure_ascii=False, indent=2)
    except OSError:
        pass
