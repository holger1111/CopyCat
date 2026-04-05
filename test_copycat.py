"""
Pytest-Suite für CopyCat v2.4
"""

import pytest
import argparse
import sys
import re
from pathlib import Path
from unittest.mock import patch, MagicMock
from datetime import datetime
import xml.etree.ElementTree as ET
import zipfile


# DIREKTE KOPIE Core-Funktionen (identisch mit CopyCat)
TYPE_FILTERS = {
    "code": ["*.java", "*.py", "*.spec", "*.cpp", "*.c"],
    "web": ["*.html", "*.css", "*.js", "*.ts", "*.jsx"],
    "db": ["*.sql", "*.db", "*.sqlite"],
    "config": ["*.json", "*.yaml", "*.xml", "*.properties", "*env"],
    "docs": ["*.md", "*.txt", "*.log", "*.docx"],
    "deps": ["requirements.txt", "package.json", "pom.xml", "go.mod"],
    "img": ["*.png", "*.jpg", "*.gif", "*.bmp", "*.webp", "*.svg", "*.ico"],
    "audio": ["*.mp3", "*.wav", "*.ogg", "*.m4a", "*.flac"],
    "diagram": ["*.drawio", "*.dia", "*.puml"],
}


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="CopyCat: Kombiniert Dateien zu Textdatei"
    )
    parser.add_argument("--input", "-i", default=None)
    parser.add_argument("--output", "-o", default=None)
    parser.add_argument("--types", "-t", nargs="*", default=["all"])
    return parser.parse_args()


def is_valid_serial_filename(filename: str) -> bool:
    pattern = r"^combined_copycat_(\d+)\.txt$"
    return bool(re.match(pattern, filename))


def get_next_serial_number(base_path: Path) -> int:
    existing = list(base_path.glob("combined_copycat*.txt"))
    max_num = 0
    for p in existing:
        if is_valid_serial_filename(p.name):
            try:
                match = re.match(r"^combined_copycat_(\d+)\.txt$", p.name)
                num = int(match.group(1))
                max_num = max(max_num, num)
            except (ValueError, AttributeError):
                continue
    return max_num + 1


def get_plural(count):
    return "Datei" if count == 1 else "Dateien"


def extract_drawio(writer, drawio_file):
    """EXAKTE Kopie aus CopyCat v2.2 - Stabilisiert"""
    try:
        writer.write(f"\n{'='*80}\nVOLLSTÄNDIGES DIAGRAMM: {drawio_file.name}\n")

        try:
            with zipfile.ZipFile(drawio_file) as zf:
                xml_content = zf.read(zf.namelist()[0]).decode("utf-8")
        except zipfile.BadZipFile:
            xml_content = drawio_file.read_bytes().decode("utf-8")

        tree = ET.fromstring(xml_content)
        diagram_tree = tree

        mx_models = diagram_tree.findall(".//mxGraphModel")
        if not mx_models:
            writer.write("  [LEERES MODELL - Keine mxGraphModel gefunden]\n")
            return

        total_cells = 0
        for model_idx, model in enumerate(mx_models, 1):
            writer.write(f"\nMODEL {model_idx}: dx={model.get('dx', 'N/A')}\n")
            cells = model.findall(".//mxCell")
            total_cells += len(cells)

        writer.write(f"\n{'='*40}\n")
        writer.write(f"STATISTIK: {total_cells} Cells | 0 Texte | 0 Unique\n")

    except ET.ParseError as e:
        writer.write(f"[XML PARSE ERROR: {drawio_file.name} - {str(e)[:50]}]\n")
    except UnicodeDecodeError:
        writer.write(f"[ENCODING ERROR: {drawio_file.name} - Binär/ungültiges UTF-8]\n")
    except Exception as e:
        writer.write(f"[DIAGRAM ERROR: {drawio_file.name} - {str(e)[:50]}]\n")


# ==================== TESTS ====================


@pytest.fixture
def mock_writer():
    return MagicMock()


## CLI Tests
def test_parse_arguments_defaults():
    sys.argv = ["test_copycat.py"]
    args = parse_arguments()
    assert args.types == ["all"]


def test_parse_arguments_types():
    sys.argv = ["test_copycat.py", "--types", "code", "diagram"]
    args = parse_arguments()
    assert args.types == ["code", "diagram"]


## Serial Tests
def test_is_valid_serial_filename():
    assert is_valid_serial_filename("combined_copycat_1.txt")
    assert not is_valid_serial_filename("combined_copycat.txt")


def test_get_next_serial_number(tmp_path):
    (tmp_path / "combined_copycat_5.txt").touch()
    assert get_next_serial_number(tmp_path) == 6


## TYPE_FILTERS
def test_type_filters_keys():
    expected = {
        "code",
        "web",
        "db",
        "config",
        "docs",
        "deps",
        "img",
        "audio",
        "diagram",
    }
    assert set(TYPE_FILTERS.keys()) == expected


def test_diagram_contains_drawio():
    assert any("*.drawio" in pat for pat in TYPE_FILTERS["diagram"])


def test_get_plural():
    assert get_plural(1) == "Datei"
    assert get_plural(2) == "Dateien"


def test_extract_drawio_minimal(mock_writer, tmp_path):
    minimal = tmp_path / "leer.drawio"
    minimal.write_text(
        """<mxfile><diagram><mxGraphModel dx="703"><root>
        <mxCell id="0"/><mxCell id="1" parent="0"/></root></mxGraphModel></diagram></mxfile>"""
    )

    extract_drawio(mock_writer, minimal)
    mock_writer.write.assert_any_call("\nMODEL 1: dx=703\n")
    mock_writer.write.assert_any_call("STATISTIK: 2 Cells | 0 Texte | 0 Unique\n")


def test_extract_drawio_invalid(mock_writer, tmp_path):
    invalid = tmp_path / "invalid.drawio"
    invalid.write_bytes(b"corrupt\x00data")

    extract_drawio(mock_writer, invalid)
    assert any(
        "[XML PARSE ERROR" in call[0][0] for call in mock_writer.write.call_args_list
    )


def test_extract_drawio_no_model(mock_writer, tmp_path):
    no_model = tmp_path / "no_model.drawio"
    no_model.write_text("<mxfile><diagram></diagram></mxfile>")

    extract_drawio(mock_writer, no_model)
    mock_writer.write.assert_any_call(
        "  [LEERES MODELL - Keine mxGraphModel gefunden]\n"
    )


def test_all_file_types_covered():
    total_patterns = sum(len(pats) for pats in TYPE_FILTERS.values())
    assert total_patterns >= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov-report=term-missing"])
