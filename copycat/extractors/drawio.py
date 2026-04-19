"""draw.io diagram extractor: compressed and plain XML."""

import base64
import logging
import xml.etree.ElementTree as ET
import zipfile
import zlib
from urllib.parse import unquote


def _decode_drawio_compressed(data: str) -> str:
    """Decode Base64/zlib (raw deflate)/URL-encoded draw.io diagram content."""
    raw = base64.b64decode(data)
    xml_bytes = zlib.decompress(raw, wbits=-15)
    return unquote(xml_bytes.decode("utf-8"))


def _safe_xml_parse(xml_bytes_or_str):
    """Parse XML with protection against entity expansion bombs (billion laughs)."""
    try:
        import defusedxml.ElementTree as SafeET
        return SafeET.fromstring(xml_bytes_or_str if isinstance(xml_bytes_or_str, str)
                                  else xml_bytes_or_str.decode("utf-8"))
    except ImportError:
        pass
    if hasattr(ET, "XMLParser"):
        parser = ET.XMLParser()
        parser.feed(xml_bytes_or_str if isinstance(xml_bytes_or_str, str)
                    else xml_bytes_or_str.decode("utf-8"))
        return parser.close()
    return ET.fromstring(xml_bytes_or_str)  # pragma: no cover


def _collect_cells(tree) -> list:
    """Collect mxCell elements from tree, decompressing diagram content if needed."""
    cells = list(tree.iter("mxCell"))
    if cells:
        return cells
    for diagram in tree.iter("diagram"):
        text = (diagram.text or "").strip()
        if not text:
            continue
        try:
            inner_xml = _decode_drawio_compressed(text)
            inner_tree = _safe_xml_parse(inner_xml)
            cells.extend(inner_tree.iter("mxCell"))
        except Exception:
            pass
    return cells


def _write_cells(writer, drawio_file, tree):
    """Count and write mxCell entries from tree (compressed or plain)."""
    cells_list = _collect_cells(tree)
    cells, texts = 0, 0
    unique_values = set()
    for cell in cells_list:
        cells += 1
        value = cell.attrib.get("value", "").strip()
        if value:
            texts += 1
            unique_values.add(value)
            geo = cell.find("mxGeometry")
            pos = ""
            if geo is not None:
                x = geo.attrib.get("x")
                y = geo.attrib.get("y")
                if x is not None and y is not None:
                    pos = f" (x={x}, y={y})"
            writer.write(f"  [{cell.attrib.get('id','?')}] {value[:50]}...{pos}\n")
    unique = len(unique_values)
    writer.write(f"DIAGRAM {drawio_file.name}: {cells} Cells, {texts} Texte, {unique} Unique\n")


def extract_drawio(writer, drawio_file):
    try:
        size = drawio_file.stat().st_size
        if size == 0:
            writer.write(f"[EMPTY: {drawio_file.name}] [SIZE: 0 bytes]\n")
            return

        LIMIT_BYTES = 1_048_576  # 1MB
        if size > LIMIT_BYTES:
            writer.write(f"[SKIPPED: {drawio_file.name} - exceeds 1MB limit]\n")
            return

        with open(drawio_file, "r", encoding="utf-8") as f:
            xml_content = f.read()

        tree = _safe_xml_parse(xml_content)
        _write_cells(writer, drawio_file, tree)

    except ET.ParseError as e:
        writer.write(f"[XML PARSE ERROR: {drawio_file.name} - {str(e)}]\n")
    except UnicodeDecodeError:
        try:
            with zipfile.ZipFile(drawio_file, "r") as zf:
                xml_names = [n for n in zf.namelist() if n.endswith(".xml") or n.endswith(".drawio")]
                if not xml_names:
                    xml_names = zf.namelist()
                if not xml_names:
                    writer.write(f"[ZIP EMPTY: {drawio_file.name}]\n")
                    return
                with zf.open(xml_names[0]) as xf:
                    xml_content = xf.read().decode("utf-8")
            tree = _safe_xml_parse(xml_content)
            _write_cells(writer, drawio_file, tree)
        except zipfile.BadZipFile:
            writer.write(f"[BINARY: {drawio_file.name} - Invalid Encoding]\n")
        except ET.ParseError as e:
            writer.write(f"[XML PARSE ERROR: {drawio_file.name} - {str(e)}]\n")
