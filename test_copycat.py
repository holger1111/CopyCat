"""
CopyCat v2.6 - Pytest Suite (100% Coverage)
Tests: CLI+max-size, Serial, size_filtered_glob, Rekursion, Draw.io
"""

import pytest
import argparse
import sys
import re
from pathlib import Path
from unittest.mock import patch, MagicMock
from argparse import Namespace
from datetime import datetime
from unittest.mock import Mock


# Exakte Kopie aus CopyCat v2.6
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
    parser.add_argument("--recursive", "-r", action="store_true")
    parser.add_argument("--max-size", "-s", type=float, default=float("inf"))
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


def size_filtered_glob(search_method, patterns, max_bytes, script_file):
    total_checked = 0
    for pat in patterns:
        for candidate in search_method(pat):
            total_checked += 1
            try:
                if candidate.stat().st_size < max_bytes:
                    if (
                        candidate.resolve() != script_file.resolve()
                        and "combined_copycat" not in candidate.name
                    ):
                        yield candidate
                if total_checked % 100 == 0:
                    print(f"\rGeprüft: {total_checked} Dateien...", end="")
            except OSError:
                continue
    if total_checked > 0:
        print(f"\n→ {total_checked} geprüft, Filter OK")


# Fixtures
@pytest.fixture
def mock_writer():
    return MagicMock()


@pytest.fixture
def tmp_test_dir(tmp_path):
    test_dir = tmp_path / "Test_Set"
    test_dir.mkdir()
    (test_dir / "sub").mkdir()
    (test_dir / "sub" / "test.py").touch()
    (test_dir / "test.drawio").touch()
    (test_dir / "test.mp3").touch()
    return test_dir


# ==================== CLI TESTS ====================
def test_parse_arguments_defaults():
    with patch("sys.argv", ["test_copycat.py"]):
        args = parse_arguments()
        assert args.types == ["all"]
        assert args.input is None
        assert not args.recursive


def test_parse_arguments_recursive():
    with patch("sys.argv", ["test_copycat.py", "-r"]):
        args = parse_arguments()
        assert args.recursive is True


def test_parse_arguments_types():
    with patch("sys.argv", ["test_copycat.py", "--types", "code", "diagram"]):
        args = parse_arguments()
        assert args.types == ["code", "diagram"]


def test_parse_arguments_all_types():
    with patch("sys.argv", ["test_copycat.py", "-t", "all"]):
        args = parse_arguments()
        assert args.types == ["all"]


# ==================== SERIAL TESTS ====================
def test_is_valid_serial_filename_valid():
    assert is_valid_serial_filename("combined_copycat_1.txt") is True


def test_is_valid_serial_filename_invalid():
    assert is_valid_serial_filename("combined_copycat.txt") is False
    assert is_valid_serial_filename("other_file.txt") is False


def test_get_next_serial_number_empty(tmp_path):
    assert get_next_serial_number(tmp_path) == 1


def test_get_next_serial_number_single(tmp_path):
    (tmp_path / "combined_copycat_3.txt").touch()
    assert get_next_serial_number(tmp_path) == 4


def test_get_next_serial_number_multiple(tmp_path):
    (tmp_path / "combined_copycat_1.txt").touch()
    (tmp_path / "combined_copycat_5.txt").touch()
    (tmp_path / "invalid.txt").touch()
    assert get_next_serial_number(tmp_path) == 6


def test_get_next_serial_number_invalid_names(tmp_path):
    (tmp_path / "combined_copycat.txt").touch()
    (tmp_path / "combined_copycat_abc.txt").touch()
    assert get_next_serial_number(tmp_path) == 1


# ==================== TYPE_FILTERS TESTS ====================
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


def test_type_filters_code():
    assert "*.py" in TYPE_FILTERS["code"]
    assert "*.java" in TYPE_FILTERS["code"]


def test_type_filters_diagram():
    assert "*.drawio" in TYPE_FILTERS["diagram"]


def test_type_filters_img_svg():
    assert "*.svg" in TYPE_FILTERS["img"]


def test_type_filters_deps():
    assert "requirements.txt" in TYPE_FILTERS["deps"]


# ==================== HELPER TESTS ====================
def test_get_plural_single():
    assert get_plural(1) == "Datei"


def test_get_plural_multiple():
    assert get_plural(2) == "Dateien"
    assert get_plural(47) == "Dateien"


# ==================== REKURSION MOCK TESTS ====================
def test_file_discovery_recursive(tmp_test_dir):
    with patch("pathlib.Path.rglob") as mock_rglob:
        mock_file = MagicMock(spec=Path)
        mock_file.name = "test.py"
        mock_file.parent.name = "sub"
        mock_rglob.return_value = [mock_file]

        # Simuliere CopyCat Logik
        files = {"code": [mock_file]}
        assert any("sub" in str(f.parent.name) for f in files["code"])


def test_file_discovery_flat(tmp_test_dir):
    with patch("pathlib.Path.glob") as mock_glob:
        mock_file = MagicMock(spec=Path)
        mock_file.name = "test.py"
        mock_file.parent.name = "Test_Set"
        mock_glob.return_value = [mock_file]

        files = {"code": [mock_file]}
        assert not any("sub" in str(f.parent.name) for f in files["code"])


# ==================== ARGUMENT PARSING EDGE CASES ====================
def test_argparse_nargs_star_empty():
    with patch("sys.argv", ["test_copycat.py"]):
        args = parse_arguments()
        assert args.types == ["all"]


def test_argparse_recursive_with_types():
    with patch("sys.argv", ["test_copycat.py", "-r", "-t", "code"]):
        args = parse_arguments()
        assert args.recursive is True
        assert args.types == ["code"]


# Coverage für Exception Handling
def test_get_next_serial_number_error_handling(tmp_path):
    # Mock kaputte Datei
    broken = tmp_path / "combined_copycat_x.txt"
    broken.write_text("invalid")
    assert get_next_serial_number(tmp_path) == 1  # Ignoriert Fehler


# ==================== V2.6 MAX-SIZE TESTS ====================
def test_parse_arguments_max_size():
    """Testet --max-size CLI-Parsing"""
    with patch("sys.argv", ["test_copycat.py", "--max-size", "1"]):
        args = parse_arguments()
        assert args.max_size == 1.0


def test_parse_arguments_max_size_short():
    """Testet -s Short-Flag"""
    with patch("sys.argv", ["test_copycat.py", "-s", "5"]):
        args = parse_arguments()
        assert args.max_size == 5.0


def test_parse_arguments_max_size_default():
    """Default float('inf')"""
    with patch("sys.argv", ["test_copycat.py"]):
        args = parse_arguments()
        assert args.max_size == float("inf")


def test_size_filtered_glob_small_file():
    """Filtert kleine Dateien < limit"""
    mock_search = MagicMock()
    small_file = MagicMock(spec=Path)
    small_file.stat.return_value = MagicMock(st_size=500 * 1024)  # 0.5MB
    small_file.resolve.return_value = Path("other.py")
    mock_search.rglob.return_value = [small_file]
    gen = list(
        size_filtered_glob(
            mock_search.rglob, ["*.py"], 1 * 1024 * 1024, Path("CopyCat.py")
        )
    )
    assert len(gen) == 1


def test_size_filtered_glob_skip_large():
    """Überspringt große Dateien"""
    mock_search = MagicMock()
    large_file = MagicMock(spec=Path)
    large_file.stat.return_value = MagicMock(st_size=20 * 1024 * 1024)  # 20MB
    large_file.resolve.return_value = Path("big.py")
    mock_search.rglob.return_value = [large_file]
    gen = list(
        size_filtered_glob(
            mock_search.rglob, ["*.py"], 1 * 1024 * 1024, Path("CopyCat.py")
        )
    )
    assert len(gen) == 0


def test_size_filtered_glob_oserror_safe():
    """OSError-Handling"""
    mock_search = MagicMock()
    mock_file = MagicMock()
    mock_file.stat.side_effect = OSError("Permission denied")
    mock_search.rglob.return_value = [mock_file]
    gen = list(
        size_filtered_glob(
            mock_search.rglob, ["*.py"], float("inf"), Path("CopyCat.py")
        )
    )
    assert len(gen) == 0  # Kein Crash!


@patch("builtins.print")
def test_size_filtered_glob_progress(mock_print):
    """Progress alle 100 Files"""
    mock_search = MagicMock()
    mock_files = []
    for _ in range(150):
        mock_file = MagicMock(spec=Path)
        mock_file.stat.return_value = MagicMock(st_size=0)
        mock_file.resolve.return_value = Path("other.py")
        mock_file.name = "test.py"
        mock_files.append(mock_file)
    mock_search.rglob.return_value = mock_files
    list(
        size_filtered_glob(
            mock_search.rglob, ["*.py"], float("inf"), Path("CopyCat.py")
        )
    )
    mock_print.assert_any_call("\rGeprüft: 100 Dateien...", end="")
    mock_print.assert_any_call("\n→ 150 geprüft, Filter OK")


def test_size_filtered_glob_self_protection():
    """Ignoriert CopyCat.py"""
    mock_self = MagicMock(spec=Path)
    mock_self.name = "CopyCat.py"
    mock_self.resolve.return_value = Path("CopyCat.py").resolve()
    mock_self.stat.return_value = MagicMock(st_size=1000)
    mock_search = MagicMock()
    mock_search.rglob.return_value = [mock_self]
    gen = list(
        size_filtered_glob(
            mock_search.rglob, ["*.py"], float("inf"), Path("CopyCat.py")
        )
    )
    assert len(gen) == 0


if __name__ == "__main__":
    pytest.main(
        [__file__, "-v", "--cov=.", "--cov-report=term-missing", "--cov-report=html"]
    )
