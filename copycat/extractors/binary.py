"""Binary file metadata extractor."""

import logging
import struct


def list_binary_file(writer, bin_file):
    try:
        size = bin_file.stat().st_size
        if size == 0:
            writer.write(f"[EMPTY: {bin_file.name}]\n")
            return

        with open(bin_file, "rb") as f:
            data = f.read(1024)
        suffix = bin_file.suffix.lower()
        mime_types = {
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".gif": "image/gif",
            ".bmp": "image/bmp",
            ".webp": "image/webp",
            ".wav": "audio/wav",
            ".mp3": "audio/mpeg",
            ".ogg": "audio/ogg",
            ".m4a": "audio/mp4",
            ".flac": "audio/flac",
            ".json": "application/json",
            ".sql": "text/sql",
            ".yaml": "text/yaml",
            ".xml": "text/xml",
            ".html": "text/html",
            ".css": "text/css",
            ".md": "text/markdown",
            ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            ".csv": "text/csv",
        }
        mime = mime_types.get(suffix, "application/octet-stream")
        duration = "N/A"
        if suffix == ".wav" and size > 44:
            frames = struct.unpack("<I", data[4:8])[0]
            rate = struct.unpack("<I", data[24:28])[0]
            duration = f"{frames / rate:.2f}s"

        dur_info = f" [DUR: {duration}]" if "audio" in mime else ""
        writer.write(f"[BINARY: {bin_file.name}] [MIME: {mime}] [SIZE: {size} bytes]{dur_info}\n")
    except UnicodeDecodeError:
        writer.write(f"[BINARY SKIPPED: {bin_file.name} - Ungültiges Text-Encoding]\n")
    except (struct.error, OSError) as e:
        writer.write(f"[BINARY ERROR: {bin_file.name} - {str(e)}]\n")
    except Exception:
        logging.exception(f"Unexpected error in list_binary_file {bin_file.name}")
        writer.write(f"[ERROR: {bin_file.name}]\n")
