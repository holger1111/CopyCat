"""CopyCat v2.9 - Pytest Suite (Refactored & Optimized)"""

import subprocess
import struct
import json
import re
from io import StringIO
from pathlib import Path
from unittest.mock import patch, MagicMock, Mock
from argparse import Namespace

import pytest

from CopyCat import (
    parse_arguments,
    get_next_serial_number,
    is_valid_serial_filename,
    move_to_archive,
    list_binary_file,
    extract_drawio,
    get_git_info,
    should_skip_gitignore,
    get_plural,
    size_filtered_glob,
    run_copycat,
    search_in_file,
    _build_search_results,
    _write_json,
    _write_md,
    _write_txt,
    TYPE_FILTERS,
)


# ==================== FIXTURES ====================

@pytest.fixture
def mock_writer():
    """Mock file writer for testing."""
    mock = MagicMock()
    mock.write = MagicMock()
    return mock


@pytest.fixture
def run_args(tmp_path):
    """Factory fixture for Namespace args."""
    def _make_args(types=None, recursive=False, max_size=None, input_path=None, output_path=None, fmt="txt", search=None):
        return Namespace(
            input=str(input_path or tmp_path),
            output=str(output_path or tmp_path),
            types=types or ["code"],
            recursive=recursive,
            max_size=max_size or float("inf"),
            format=fmt,
            search=search,
        )
    return _make_args


@pytest.fixture
def tmp_test_dir(tmp_path):
    """Create a test directory structure."""
    test_dir = tmp_path / "Test_Set"
    test_dir.mkdir()
    (test_dir / "sub").mkdir()
    (test_dir / "sub" / "test.py").touch()
    (test_dir / "test.drawio").touch()
    (test_dir / "test.mp3").touch()
    return test_dir


# ==================== ARGUMENT PARSING TESTS ====================

@pytest.mark.parametrize("argv,expected", [
    (["test_copycat.py"], {"types": ["all"], "recursive": False, "max_size": float("inf"), "format": "txt"}),
    (["test_copycat.py", "-r"], {"types": ["all"], "recursive": True}),
    (["test_copycat.py", "-t", "code", "diagram"], {"types": ["code", "diagram"]}),
    (["test_copycat.py", "-t", "code,diagram"], {"types": ["code", "diagram"]}),
    (["test_copycat.py", "-s", "5"], {"max_size": 5.0}),
    (["test_copycat.py", "-r", "-t", "code"], {"recursive": True, "types": ["code"]}),
    (["test_copycat.py", "-f", "json"], {"format": "json"}),
    (["test_copycat.py", "-f", "md"], {"format": "md"}),
    (["test_copycat.py", "--format", "txt"], {"format": "txt"}),
])
def test_parse_arguments(argv, expected):
    """Test argument parsing with various combinations."""
    with patch("sys.argv", argv):
        args = parse_arguments()
        for key, val in expected.items():
            assert getattr(args, key) == val


# ==================== SERIAL NUMBER TESTS ====================

@pytest.mark.parametrize("files,expected", [
    ([], 1),
    (["combined_copycat_3.txt"], 4),
    (["combined_copycat_1.txt", "combined_copycat_5.txt", "invalid.txt"], 6),
    (["combined_copycat.txt", "combined_copycat_abc.txt"], 1),
    (["combined_copycat_2.json"], 3),
    (["combined_copycat_4.md"], 5),
    (["combined_copycat_3.txt", "combined_copycat_7.json", "combined_copycat_2.md"], 8),
])
def test_get_next_serial_number(tmp_path, files, expected):
    """Test serial number generation."""
    for fname in files:
        (tmp_path / fname).touch()
    assert get_next_serial_number(tmp_path) == expected


def test_is_valid_serial_filename():
    """Test serial filename validation (imported from CopyCat)."""
    assert is_valid_serial_filename("combined_copycat_1.txt") is True
    assert is_valid_serial_filename("combined_copycat_5.json") is True
    assert is_valid_serial_filename("combined_copycat_3.md") is True
    assert is_valid_serial_filename("combined_copycat.txt") is False
    assert is_valid_serial_filename("other_file.txt") is False
    assert is_valid_serial_filename("combined_copycat_1.csv") is False


# ==================== PLURAL TESTS ====================

@pytest.mark.parametrize("count,expected", [
    (0, "Dateien"),
    (1, "Datei"),
    (2, "Dateien"),
    (47, "Dateien"),
    (999, "Dateien"),
])
def test_get_plural(count, expected):
    """Test plural form handling."""
    assert get_plural(count) == expected


# ==================== TYPE FILTERS TESTS ====================

@pytest.mark.parametrize("type_key,expected_patterns", [
    ("code", ["*.py", "*.java"]),
    ("diagram", ["*.drawio"]),
    ("img", ["*.svg"]),
    ("deps", ["requirements.txt"]),
])
def test_type_filters(type_key, expected_patterns):
    """Test type filter availability and patterns."""
    assert type_key in TYPE_FILTERS.keys()
    for pattern in expected_patterns:
        assert pattern in TYPE_FILTERS[type_key]


def test_type_filters_all_present():
    """Test all required type filters exist."""
    expected = {"code", "web", "db", "config", "docs", "deps", "img", "audio", "diagram"}
    assert set(TYPE_FILTERS.keys()) == expected


def test_type_filters_runtime():
    """Test type filters at runtime."""
    selected_types = ["code", "diagram"]
    for t in selected_types:
        assert t in TYPE_FILTERS.keys()
        assert len(TYPE_FILTERS[t]) > 0


# ==================== GIT INFO TESTS ====================

def test_get_git_info_no_repo(tmp_path):
    """Test git info when repo doesn't exist."""
    assert get_git_info(tmp_path) == "No Git"


def test_get_git_info_mock(tmp_path):
    """Test git info with mocked git commands."""
    with patch("subprocess.run") as mock_run:
        mock_run.return_value.stdout = "main\n"
        mock_run.return_value.returncode = 0
        (tmp_path / ".git").mkdir()
        result = get_git_info(tmp_path)
        assert "Branch: main" in result


def test_get_git_info_timeout(tmp_path):
    """Test git info with timeout."""
    (tmp_path / ".git").mkdir()
    with patch("subprocess.run", side_effect=subprocess.TimeoutExpired("git", 1)):
        assert "No Git" in get_git_info(tmp_path)


def test_get_git_info_edge_cases(tmp_path, run_args):
    """Test git info with edge cases in copycat integration."""
    with patch("subprocess.check_output") as mock_subprocess:
        mock_subprocess.side_effect = FileNotFoundError
        run_copycat(run_args())
        report = next(tmp_path.glob("combined_copycat_*.txt"))
        assert "GIT: No Git" in report.read_text()


# ==================== GITIGNORE TESTS ====================

@pytest.mark.parametrize("gitignore_content,file_name,should_skip", [
    (None, "test.py", False),
    ("*.pyc\n", "dummy.pyc", True),
    ("*.pyc\n*.tmp\n", "file.tmp", True),
    ("*.py\n!important.py\n", "important.py", False),
    ("*.py\n!important.py\n", "test.py", True),
])
def test_should_skip_gitignore(tmp_path, gitignore_content, file_name, should_skip):
    """Test gitignore handling."""
    if gitignore_content:
        (tmp_path / ".gitignore").write_text(gitignore_content)
    
    test_file = tmp_path / file_name
    test_file.touch()
    
    result = should_skip_gitignore(tmp_path, test_file)
    assert result == should_skip


def test_gitignore_pattern_matching(tmp_path, run_args):
    """Test complex gitignore pattern matching including negation."""
    (tmp_path / ".gitignore").write_text("*.py\nbuild/\n!important.py\n")

    (tmp_path / "build").mkdir()
    (tmp_path / "build" / "generated.py").touch()
    (tmp_path / "important.py").touch()
    (tmp_path / "test.py").touch()

    run_copycat(run_args(types=["code"], recursive=True))

    report = next(tmp_path.glob("combined_copycat_*.txt"))
    report_text = report.read_text()
    assert "test.py" not in report_text        # blocked by *.py
    assert "important.py" in report_text       # negation un-ignores it


def test_gitignore_recursive(tmp_path, run_args):
    """Test that subdirectory .gitignore files are respected."""
    (tmp_path / "sub").mkdir()
    (tmp_path / "sub" / ".gitignore").write_text("*.py\n")
    (tmp_path / "sub" / "ignored.py").touch()
    (tmp_path / "visible.py").touch()

    run_copycat(run_args(types=["code"], recursive=True))

    report = next(tmp_path.glob("combined_copycat_*.txt"))
    report_text = report.read_text()
    assert "visible.py" in report_text
    assert "ignored.py" not in report_text


def test_gitignore_flat_mode(tmp_path, run_args):
    """Test that gitignore is applied in non-recursive flat mode."""
    (tmp_path / ".gitignore").write_text("ignored.py\n")
    (tmp_path / "visible.py").touch()
    (tmp_path / "ignored.py").touch()

    run_copycat(run_args(types=["code"]))

    report = next(tmp_path.glob("combined_copycat_*.txt"))
    report_text = report.read_text()
    assert "visible.py" in report_text
    assert "ignored.py" not in report_text


def test_should_skip_gitignore_outside_dir(tmp_path):
    """Test should_skip_gitignore when file is outside input_dir (ValueError)."""
    outside = tmp_path.parent / "outside.py"
    outside.touch()
    assert should_skip_gitignore(tmp_path, outside) is False


def test_should_skip_gitignore_read_error(tmp_path):
    """Test should_skip_gitignore when .gitignore cannot be read."""
    gi = tmp_path / ".gitignore"
    gi.write_text("*.py")
    test_file = tmp_path / "test.py"
    test_file.touch()
    with patch("builtins.open", side_effect=OSError("permission denied")):
        result = should_skip_gitignore(tmp_path, test_file)
    assert result is False


# ==================== SIZE FILTERED GLOB TESTS ====================

@pytest.mark.parametrize("file_size,max_size,should_include", [
    (500 * 1024, 1 * 1024 * 1024, True),
    (20 * 1024 * 1024, 1 * 1024 * 1024, False),
])
def test_size_filtered_glob(tmp_path, file_size, max_size, should_include):
    """Test size filtering."""
    mock_search = MagicMock()
    mock_file = MagicMock(spec=Path)
    mock_file.stat.return_value = MagicMock(st_size=file_size)
    mock_file.resolve.return_value = Path("other.py")
    mock_file.name = "test.py"
    mock_file.relative_to = MagicMock(return_value=Path("other.py"))
    mock_search.rglob.return_value = [mock_file]
    
    gen = list(size_filtered_glob(
        mock_search.rglob, ["*.py"], max_size, Path("CopyCat.py"), tmp_path
    ))
    assert (len(gen) == 1) == should_include


@patch("builtins.print")
def test_size_filtered_glob_progress(mock_print):
    """Test progress reporting in size_filtered_glob."""
    mock_search = MagicMock()
    mock_files = [
        MagicMock(
            spec=Path,
            stat=Mock(return_value=Mock(st_size=0)),
            resolve=Mock(return_value=Path("other.py")),
            name="test.py",
            relative_to=Mock(return_value=Path("test.py")),
        )
        for _ in range(101)
    ]
    mock_search.rglob.return_value = mock_files
    
    list(size_filtered_glob(
        mock_search.rglob, ["*.py"], float("inf"), Path("CopyCat.py"), Path(".")
    ))
    
    mock_print.assert_any_call("\rGeprüft: 100 Dateien...", end="")
    mock_print.assert_any_call("\n→ 101 geprüft, Filter OK")


def test_size_filtered_glob_oserror_safe(tmp_path):
    """Test OSError handling in size_filtered_glob."""
    mock_search = MagicMock()
    mock_file = MagicMock()
    mock_file.stat.side_effect = OSError("Permission denied")
    mock_search.rglob.return_value = [mock_file]
    
    gen = list(size_filtered_glob(
        mock_search.rglob, ["*.py", "*.pyc"], 1024, Path("CopyCat.py"), tmp_path
    ))
    assert len(gen) == 0


def test_size_filtered_glob_self_protection():
    """Test that CopyCat.py is not included in its own output."""
    script_path = Path("CopyCat.py").resolve()
    mock_self = MagicMock(spec=Path)
    mock_self.name = "CopyCat.py"
    mock_self.resolve.return_value = script_path
    mock_self.stat.return_value = MagicMock(st_size=1000)
    mock_search = MagicMock()
    mock_search.rglob.return_value = [mock_self]

    gen = list(size_filtered_glob(
        mock_search.rglob, ["*.py"], float("inf"), script_path, Path(".")
    ))
    assert len(gen) == 0


def test_size_filtered_glob_total_checked(tmp_path, monkeypatch):
    """Test total checked counter."""
    def mock_gitignore(*args):
        raise OSError()

    with monkeypatch.context() as m:
        m.setattr("CopyCat.should_skip_gitignore", mock_gitignore)
        files = list(size_filtered_glob(lambda p: [], ["*.py"], 0, Path(), tmp_path))
    assert files == []


# ==================== FILE PROCESSING TESTS ====================

def test_list_binary_file(tmp_path, mock_writer):
    """Test binary file listing."""
    binary = tmp_path / "test.wav"
    binary.write_bytes(b"RIFF....WAVEfmt ")
    list_binary_file(mock_writer, binary)
    assert mock_writer.write.called


def test_list_binary_file_unicode_error(tmp_path, mock_writer):
    """Test binary file with unicode decode error."""
    binary = tmp_path / "binary.dat"
    binary.write_bytes(b"\xff\x00\xab")
    
    with patch(
        "builtins.open", 
        side_effect=UnicodeDecodeError("utf-8", b"", 0, 1, "invalid")
    ):
        list_binary_file(mock_writer, binary)
    
    mock_writer.write.assert_called_with(
        "[BINARY SKIPPED: binary.dat - Ungültiges Text-Encoding]\n"
    )


def test_list_binary_file_struct_error(tmp_path, mock_writer):
    """Test list_binary_file with OSError on file read (struct.error/OSError handler)."""
    f = tmp_path / "test.bin"
    f.write_bytes(b"\x00" * 50)  # size > 0, stat() works
    with patch("builtins.open", side_effect=OSError("permission denied")):
        list_binary_file(mock_writer, f)
    assert "[BINARY ERROR: test.bin" in mock_writer.write.call_args[0][0]


def test_list_binary_file_wav_duration(tmp_path, mock_writer):
    """Test WAV duration calculation branch (size > 44 bytes)."""
    # Bytes 4-7: frames=44100, bytes 24-27: rate=44100 → duration=1.00s
    data = bytearray(52)
    data[4:8] = b"\x44\xAC\x00\x00"   # frames = 44100
    data[24:28] = b"\x44\xAC\x00\x00"  # rate  = 44100
    wav = tmp_path / "audio.wav"
    wav.write_bytes(bytes(data))
    list_binary_file(mock_writer, wav)
    written = mock_writer.write.call_args[0][0]
    assert "[BINARY: audio.wav]" in written
    assert "[DUR: 1.00s]" in written


def test_list_binary_file_generic_error(mock_writer):
    """Test list_binary_file with unexpected exception (not OSError/struct.error)."""
    bad_file = MagicMock()
    bad_file.name = "surprise.bin"
    bad_file.stat.side_effect = RuntimeError("unexpected")
    list_binary_file(mock_writer, bad_file)
    written = mock_writer.write.call_args[0][0]
    assert "[ERROR: surprise.bin]" in written


# ==================== EXTRACT DRAWIO TESTS ====================

@pytest.mark.parametrize("content,has_cells", [
    (b"", False),
    (b'<mxGraphModel><root><mxCell id="1"/></root></mxGraphModel>', True),
    (b"<root></root>", False),
])
def test_extract_drawio(tmp_path, mock_writer, content, has_cells):
    """Test drawio extraction."""
    drawio = tmp_path / "test.drawio"
    drawio.write_bytes(content)
    extract_drawio(mock_writer, drawio)
    assert mock_writer.write.called


def test_extract_drawio_full_parser(tmp_path, mock_writer):
    """Test drawio XML parsing with full structure."""
    drawio_file = tmp_path / "full.drawio"
    drawio_file.write_bytes(b"""<mxfile host="diagrams.net">
        <diagram>
            <mxGraphModel>
                <root>
                    <mxCell id="0"/>
                    <mxCell id="1" parent="0"/>
                    <mxCell id="2" value="Test Cell" vertex="1" parent="1">
                        <mxGeometry x="160" y="120" width="120" height="60"/>
                    </mxCell>
                </root>
            </mxGraphModel>
        </diagram>
    </mxfile>""")
    extract_drawio(mock_writer, drawio_file)
    assert mock_writer.write.called


def test_extract_drawio_unicode_error(tmp_path, mock_writer):
    """Test extract_drawio with invalid UTF-8 encoding."""
    drawio = tmp_path / "binary.drawio"
    drawio.write_bytes(b"\x01")  # size > 0 so stat() passes
    with patch("builtins.open", side_effect=UnicodeDecodeError("utf-8", b"", 0, 1, "invalid")):
        extract_drawio(mock_writer, drawio)
    mock_writer.write.assert_called_with("[BINARY: binary.drawio - Invalid Encoding]\n")


def test_extract_drawio_parse_error(tmp_path, mock_writer):
    """Test extract_drawio with invalid XML (ET.ParseError handler)."""
    drawio = tmp_path / "broken.drawio"
    drawio.write_text("not valid xml <<<", encoding="utf-8")
    extract_drawio(mock_writer, drawio)
    assert "[XML PARSE ERROR: broken.drawio" in mock_writer.write.call_args[0][0]


def test_extract_drawio_compressed_coverage(tmp_path):
    """Test drawio handling in copycat integration."""
    drawio_file = tmp_path / "diagram.drawio"
    drawio_file.write_text("""<mxfile host="app.diagrams.net">
    <diagram name="Page-1" id="page1">
    <mxGraphModel dx="1200" dy="800" grid="1" gridSize="10"
    guides="1" tooltips="1" connect="1" arrows="1" fold="1"
    page="1" pageScale="1" pageWidth="827" pageHeight="1169"
    math="0" shadow="0">
        <root>
            <mxCell id="0"/>
            <mxCell id="1" parent="0"/>
            <mxCell id="2" value="TEST CELL 1" style="text;html=1;"
            vertex="1" parent="1">
                <mxGeometry x="100" y="100" width="120" height="60"
                as="geometry"/>
            </mxCell>
        </root>
    </mxGraphModel>
    </diagram>
    </mxfile>""", encoding="utf-8")

    run_copycat(Namespace(
        input=str(tmp_path),
        output=str(tmp_path),
        types=["diagram"],
        recursive=False,
        max_size=float("inf"),
    ))

    report = next(tmp_path.glob("combined_copycat_*.txt"))
    report_text = report.read_text(encoding="utf-8")
    assert "DIAGRAM: 1 Datei" in report_text
    assert "diagram.drawio" in report_text


# ==================== RUN COPYCAT INTEGRATION TESTS ====================

def test_run_copycat_basic(tmp_path, run_args):
    """Test basic copycat execution."""
    (tmp_path / "test.py").touch()
    
    run_copycat(run_args())
    
    reports = list(tmp_path.glob("combined_copycat_*.txt"))
    assert len(reports) == 1
    content = reports[0].read_text()
    assert "test.py" in content
    assert "CODE" in content
    assert "Serial #1" in content


@pytest.mark.parametrize("input_exists", [True, False])
def test_run_copycat_input_validation(tmp_path, run_args, input_exists):
    """Test input validation."""
    input_path = tmp_path if input_exists else tmp_path / "nonexistent"
    
    if input_exists:
        (tmp_path / "test.py").touch()
    
    args = run_args(input_path=input_path)
    
    with patch("builtins.print") as mock_print:
        run_copycat(args)
        if not input_exists:
            mock_print.assert_called()


def test_run_copycat_binary_encoding_error(tmp_path, run_args):
    """Test handling of binary/encoding errors."""
    binary_code = tmp_path / "fake.py"
    binary_code.write_bytes(b"\xff\x00")
    
    run_copycat(run_args())
    
    report = next(tmp_path.glob("combined_copycat_*.txt"))
    content = report.read_text(encoding="utf-8")
    assert "(Binary oder ungültiges Encoding - übersprungen)" in content


def test_run_copycat_recursive(tmp_path, run_args):
    """Test recursive file discovery."""
    (tmp_path / "sub" / "test.py").mkdir(parents=True)
    (tmp_path / "sub" / "test.py").touch()
    
    run_copycat(run_args(recursive=True))
    
    report = next(tmp_path.glob("combined_copycat_*.txt"))
    assert "test.py" in report.read_text()


def test_run_copycat_type_filter(tmp_path, run_args):
    """Test type filtering."""
    (tmp_path / "code.py").touch()
    (tmp_path / "style.css").touch()
    
    run_copycat(run_args(types=["code"]))
    
    report = next(tmp_path.glob("combined_copycat_*.txt"))
    assert "CODE: 1 Datei" in report.read_text()


def test_run_copycat_max_size_filter(tmp_path, run_args):
    """Test file size filtering."""
    (tmp_path / "small.py").write_bytes(b"x" * 100)
    (tmp_path / "large.bin").write_bytes(b"x" * 2_000_000)
    
    run_copycat(run_args(types=["all"], max_size=1.0))
    
    report = next(tmp_path.glob("combined_copycat_*.txt"))
    assert "large.bin" not in report.read_text()


def test_run_copycat_archive_rotation(tmp_path, run_args):
    """Test report archiving on new run."""
    (tmp_path / "test.py").write_text("def hello(): pass")
    
    run_copycat(run_args())
    assert next(tmp_path.glob("combined_copycat_1.txt")).exists()
    
    run_copycat(run_args())
    assert next(tmp_path.glob("combined_copycat_2.txt")).exists()
    
    with pytest.raises(StopIteration):
        next(tmp_path.glob("combined_copycat_1.txt"))
    
    run_copycat(run_args())
    assert next(tmp_path.glob("combined_copycat_3.txt")).exists()


def test_run_copycat_self_protection(tmp_path, run_args):
    """Test that test scripts are included properly."""
    (tmp_path / "test_copycat.py").write_text("# test script")
    (tmp_path / "test.py").write_text("def hello(): pass")
    
    run_copycat(run_args())
    
    report = next(tmp_path.glob("combined_copycat_*.txt"))
    assert "test.py" in report.read_text()


@pytest.mark.parametrize("types,expected", [
    (["code"], "CODE: 1 Datei"),
    (["code", "web"], "WEB:"),
])
def test_run_copycat_multi_type(tmp_path, run_args, types, expected):
    """Test multiple type filtering."""
    (tmp_path / "test.py").touch()
    (tmp_path / "style.css").touch()
    
    run_copycat(run_args(types=types))
    
    report = next(tmp_path.glob("combined_copycat_*.txt"))
    assert expected in report.read_text()


def test_run_copycat_all_types(tmp_path, run_args):
    """Test 'all' type filtering."""
    (tmp_path / "test.py").touch()
    (tmp_path / "style.css").touch()
    (tmp_path / "data.sql").touch()
    (tmp_path / "config.json").write_text("{}")
    (tmp_path / "README.md").write_text("# Docs")
    (tmp_path / "requirements.txt").write_text("py")
    (tmp_path / "image.png").write_bytes(b"PNG")
    (tmp_path / "audio.mp3").write_bytes(b"ID3")
    (tmp_path / "diagram.drawio").write_text("<mxfile><diagram></diagram></mxfile>")

    run_copycat(run_args(types=["all"]))
    
    report = next(tmp_path.glob("combined_copycat_*.txt"))
    assert "Gesamt:" in report.read_text()


def test_run_copycat_invalid_types(tmp_path, run_args):
    """Test invalid type handling."""
    (tmp_path / "test.py").write_text("def hello(): pass")
    
    run_copycat(run_args(types=["xyz"]))
    
    report = next(tmp_path.glob("combined_copycat_*.txt"))
    assert "Gesamt: 0 Dateien" in report.read_text()


def test_run_copycat_git_integration(tmp_path, run_args):
    """Test git info in copycat report."""
    (tmp_path / ".git").mkdir()
    (tmp_path / "test.py").touch()
    
    run_copycat(run_args())
    
    report = next(tmp_path.glob("combined_copycat_*.txt"))
    assert "GIT:" in report.read_text()


def test_run_copycat_binary_recursive(tmp_path, run_args):
    """Test binary file handling in recursive mode."""
    (tmp_path / "sub" / "test.png").mkdir(parents=True)
    (tmp_path / "sub" / "test.png").touch()
    
    run_copycat(run_args(types=["img"], recursive=True))
    
    report = next(tmp_path.glob("combined_copycat_*.txt"))
    assert "test.png" in report.read_text()


def test_run_copycat_line_counting(tmp_path, run_args):
    """Test code line counting."""
    code_file = tmp_path / "test.py"
    code_file.write_text("line1\nline2\nline3\n")
    
    run_copycat(run_args())
    
    report = next(tmp_path.glob("combined_copycat_*.txt"))
    assert "test.py" in report.read_text()


def test_run_copycat_flat_skips_combined_output(tmp_path, run_args):
    """Test that files named 'combined_copycat...' are skipped in flat mode."""
    (tmp_path / "combined_copycat_prev.txt").write_text("old output")
    (tmp_path / "notes.txt").write_text("notes")
    run_copycat(run_args(types=["docs"]))
    report = next(tmp_path.glob("combined_copycat_*.txt"))
    assert "combined_copycat_prev" not in report.read_text()


# ==================== ARCHIVE TESTS ====================

def test_move_to_archive(tmp_path):
    """Test report archiving."""
    old_file = tmp_path / "combined_copycat_1.txt"
    old_file.touch()
    
    move_to_archive(tmp_path, "combined_copycat_1.txt")
    
    archive = tmp_path / "CopyCat_Archive" / "combined_copycat_1.txt"
    assert archive.exists()


def test_move_to_archive_permission(tmp_path, monkeypatch):
    """Test archive with permission error."""
    old_file = tmp_path / "combined_copycat_1.txt"
    old_file.touch()
    
    def mock_move(src, dst):
        raise PermissionError()
    
    monkeypatch.setattr("shutil.move", mock_move)
    move_to_archive(tmp_path, "combined_copycat_1.txt")


def test_move_to_archive_no_op(tmp_path):
    """Test archive when file doesn't exist is a no-op."""
    move_to_archive(tmp_path, "combined_copycat_99.txt")  # file does not exist
    assert not (tmp_path / "CopyCat_Archive" / "combined_copycat_99.txt").exists()


# ==================== MAIN ENTRYPOINT TEST ====================

def test_main_entrypoint(tmp_path):
    """Test __main__ block execution."""
    import runpy
    with patch("sys.argv", ["CopyCat.py", "-i", str(tmp_path), "-o", str(tmp_path)]):
        runpy.run_path(
            str(Path(__file__).parent / "CopyCat.py"),
            run_name="__main__",
        )
    assert list(tmp_path.glob("combined_copycat_*.txt"))


# ==================== FORMAT TESTS (MILESTONE 10) ====================

def test_run_copycat_format_json_basic(tmp_path, run_args):
    """Test JSON output format: valid JSON with required keys."""
    (tmp_path / "main.py").write_text("def hello(): pass\n")
    run_copycat(run_args(fmt="json"))

    reports = list(tmp_path.glob("combined_copycat_*.json"))
    assert len(reports) == 1
    data = json.loads(reports[0].read_text(encoding="utf-8"))
    assert "files" in data
    assert "types" in data
    assert "version" in data
    assert data["version"] == "2.9"
    assert data["files"] >= 1
    assert "code" in data["types"]


def test_run_copycat_format_json_no_git(tmp_path, run_args):
    """Test JSON output: git is None when no repo."""
    (tmp_path / "app.py").write_text("x = 1\n")
    run_copycat(run_args(fmt="json"))
    data = json.loads(next(tmp_path.glob("combined_copycat_*.json")).read_text())
    assert data["git"] is None


def test_run_copycat_format_json_with_git(tmp_path, run_args):
    """Test JSON output: git dict populated when repo present."""
    (tmp_path / ".git").mkdir()
    (tmp_path / "app.py").write_text("x = 1\n")
    with patch("subprocess.run") as mock_run:
        mock_run.return_value.stdout = "main\n"
        mock_run.return_value.returncode = 0
        run_copycat(run_args(fmt="json"))
    data = json.loads(next(tmp_path.glob("combined_copycat_*.json")).read_text())
    assert data["git"] is not None
    assert "branch" in data["git"]


def test_run_copycat_format_json_code_lines_error(tmp_path):
    """Test JSON output: lines=None when file read fails during line counting."""
    code_file = tmp_path / "bad.py"
    code_file.write_text("x = 1\n")

    files = {k: [] for k in TYPE_FILTERS}
    files["code"] = [code_file]
    out_path = tmp_path / "out.json"
    args = Namespace(recursive=False, types=["code"], max_size=float("inf"), format="json")

    real_open = open

    def patched_open(f, *a, **kw):
        # Block reading the code file for line counting (no mode arg = "r")
        if Path(f) == code_file and ("r" in (a[0] if a else kw.get("mode", "r"))):
            raise OSError("denied")
        return real_open(f, *a, **kw)

    with patch("builtins.open", side_effect=patched_open):
        _write_json(out_path, files, args, tmp_path, "No Git", 1)

    data = json.loads(out_path.read_text())
    assert data["details"]["code"][0]["lines"] is None


def test_run_copycat_format_md_basic(tmp_path, run_args):
    """Test Markdown output format: contains headers and table."""
    (tmp_path / "script.py").write_text("print('hi')\n")
    run_copycat(run_args(fmt="md"))

    reports = list(tmp_path.glob("combined_copycat_*.md"))
    assert len(reports) == 1
    content = reports[0].read_text(encoding="utf-8")
    assert "# CopyCat v2.9 Report" in content
    assert "## Übersicht" in content
    assert "## Code-Details" in content
    assert "script.py" in content


def test_run_copycat_format_md_binary_section(tmp_path, run_args):
    """Test Markdown output: binary type section (non-code)."""
    (tmp_path / "image.png").write_bytes(b"PNG")
    run_copycat(run_args(types=["img"], fmt="md"))
    content = next(tmp_path.glob("combined_copycat_*.md")).read_text()
    assert "## IMG" in content
    assert "image.png" in content


def test_run_copycat_format_md_unicode_error(tmp_path, run_args):
    """Test Markdown code block: UnicodeDecodeError handled."""
    bad = tmp_path / "bad.py"
    bad.write_bytes(b"\xff\x00")
    run_copycat(run_args(fmt="md"))
    content = next(tmp_path.glob("combined_copycat_*.md")).read_text(encoding="utf-8")
    assert "übersprungen" in content


def test_run_copycat_format_md_read_exception(tmp_path, run_args):
    """Test Markdown code block: generic read exception handled."""
    code = tmp_path / "test.py"
    code.write_text("x = 1")
    real_open = open

    def patched_open(f, *a, **kw):
        if Path(f) == code and "r" in (a[0] if a else kw.get("mode", "r")):
            raise OSError("denied")
        return real_open(f, *a, **kw)

    with patch("builtins.open", side_effect=patched_open):
        run_copycat(run_args(fmt="md"))
    content = next(tmp_path.glob("combined_copycat_*.md")).read_text()
    assert "Fehler beim Lesen" in content


def test_run_copycat_format_txt_default_unchanged(tmp_path, run_args):
    """Test that default format=txt still produces .txt report."""
    (tmp_path / "test.py").write_text("pass\n")
    run_copycat(run_args())
    reports = list(tmp_path.glob("combined_copycat_*.txt"))
    assert len(reports) == 1
    assert "CopyCat v2.9" in reports[0].read_text()


def test_run_copycat_archive_cross_format(tmp_path, run_args):
    """Test that archive picks up files of all extensions."""
    (tmp_path / "combined_copycat_1.txt").write_text("old txt")
    (tmp_path / "combined_copycat_2.json").write_text("{}")
    (tmp_path / "test.py").write_text("pass")
    run_copycat(run_args(fmt="md"))
    archive = tmp_path / "CopyCat_Archive"
    assert (archive / "combined_copycat_1.txt").exists()
    assert (archive / "combined_copycat_2.json").exists()
    md_reports = list(tmp_path.glob("combined_copycat_*.md"))
    assert len(md_reports) == 1


def test_write_json_direct(tmp_path):
    """Direct test of _write_json helper (code + non-code types)."""
    files = {k: [] for k in TYPE_FILTERS}
    code_file = tmp_path / "sample.py"
    code_file.write_text("x = 1\n")
    files["code"] = [code_file]
    img_file = tmp_path / "logo.png"
    img_file.write_bytes(b"PNG")
    files["img"] = [img_file]

    out_path = tmp_path / "out.json"
    args = Namespace(recursive=False, types=["code", "img"], max_size=float("inf"), format="json")
    _write_json(out_path, files, args, tmp_path, "Branch: dev | Last Commit: abc123", 7)

    data = json.loads(out_path.read_text())
    assert data["git"]["branch"] == "dev"
    assert data["git"]["commit"] == "abc123"
    assert data["serial"] == 7
    assert "code" in data["details"]
    assert data["details"]["code"][0]["lines"] is not None
    # non-code type should not have "lines" key
    assert "img" in data["details"]
    assert "lines" not in data["details"]["img"][0]


def test_write_md_direct(tmp_path):
    """Direct test of _write_md helper."""
    files = {k: [] for k in TYPE_FILTERS}
    code_file = tmp_path / "hello.py"
    code_file.write_text("print('hello')\n")
    files["code"] = [code_file]
    img_file = tmp_path / "logo.png"
    img_file.write_bytes(b"PNG")
    files["img"] = [img_file]

    buf = StringIO()
    args = Namespace(recursive=False, types=["code", "img"], max_size=float("inf"), format="md")
    _write_md(buf, files, args, tmp_path, "No Git", 3)

    out = buf.getvalue()
    assert "# CopyCat v2.9 Report" in out
    assert "hello.py" in out
    assert "## IMG" in out
    assert "| **Serial** | #3 |" in out


# ==================== SEARCH TESTS (MILESTONE 11) ====================

def test_search_in_file_found(tmp_path):
    """search_in_file returns matching lines with line numbers."""
    f = tmp_path / "code.py"
    f.write_text("x = 1\n# TODO: fix\ndef hello(): pass\n")
    hits = search_in_file(f, "TODO")
    assert len(hits) == 1
    assert hits[0][0] == 2
    assert "TODO" in hits[0][1]


def test_search_in_file_multiple_matches(tmp_path):
    """search_in_file finds multiple matching lines."""
    f = tmp_path / "code.py"
    f.write_text("# TODO: a\nx = 1\n# TODO: b\n")
    hits = search_in_file(f, "TODO")
    assert len(hits) == 2
    assert hits[0][0] == 1
    assert hits[1][0] == 3


def test_search_in_file_no_match(tmp_path):
    """search_in_file returns empty list when pattern not found."""
    f = tmp_path / "code.py"
    f.write_text("x = 1\ndef hello(): pass\n")
    assert search_in_file(f, "TODO") == []


def test_search_in_file_invalid_regex(tmp_path):
    """search_in_file returns empty list for invalid regex."""
    f = tmp_path / "code.py"
    f.write_text("x = 1\n")
    assert search_in_file(f, "[invalid(") == []


def test_search_in_file_unicode_error(tmp_path):
    """search_in_file returns empty list on UnicodeDecodeError."""
    f = tmp_path / "bad.py"
    f.write_bytes(b"\xff\x00\xab")
    assert search_in_file(f, "TODO") == []


def test_search_in_file_os_error(tmp_path):
    """search_in_file returns empty list on OSError."""
    f = tmp_path / "locked.py"
    f.write_text("x = 1")
    with patch("builtins.open", side_effect=OSError("denied")):
        assert search_in_file(f, "TODO") == []


def test_search_in_file_regex_pattern(tmp_path):
    """search_in_file supports full regex patterns."""
    f = tmp_path / "code.py"
    f.write_text("def foo():\ndef bar():\nx = 1\n")
    hits = search_in_file(f, r"^def ")
    assert len(hits) == 2


def test_build_search_results_basic(tmp_path):
    """_build_search_results finds matches in searchable types only."""
    files = {k: [] for k in TYPE_FILTERS}
    py = tmp_path / "app.py"
    py.write_text("# TODO: fix this\nx = 1\n")
    files["code"] = [py]
    img = tmp_path / "logo.png"
    img.write_bytes(b"PNG")
    files["img"] = [img]

    results = _build_search_results(files, "TODO")
    assert py in results
    assert img not in results
    assert results[py][0][1].strip() == "# TODO: fix this"


def test_build_search_results_no_matches(tmp_path):
    """_build_search_results returns empty dict when nothing matches."""
    files = {k: [] for k in TYPE_FILTERS}
    py = tmp_path / "clean.py"
    py.write_text("x = 1\n")
    files["code"] = [py]

    results = _build_search_results(files, "FIXME")
    assert results == {}


def test_build_search_results_skips_non_searchable(tmp_path):
    """_build_search_results skips img, audio, diagram types."""
    files = {k: [] for k in TYPE_FILTERS}
    img = tmp_path / "logo.png"
    img.write_bytes(b"TODO")
    files["img"] = [img]
    audio = tmp_path / "song.mp3"
    audio.write_bytes(b"TODO")
    files["audio"] = [audio]

    results = _build_search_results(files, "TODO")
    assert results == {}


def test_build_search_results_multiple_types(tmp_path):
    """_build_search_results searches code, web, docs, etc."""
    files = {k: [] for k in TYPE_FILTERS}
    py = tmp_path / "app.py"
    py.write_text("# TODO in code\n")
    html = tmp_path / "index.html"
    html.write_text("<!-- TODO in web -->\n")
    files["code"] = [py]
    files["web"] = [html]

    results = _build_search_results(files, "TODO")
    assert py in results
    assert html in results


@pytest.mark.parametrize("argv,expected_search", [
    (["test_copycat.py"], None),
    (["test_copycat.py", "-S", "TODO"], "TODO"),
    (["test_copycat.py", "--search", "def |class "], "def |class "),
    (["test_copycat.py", "-S", r"TODO|FIXME"], "TODO|FIXME"),
])
def test_parse_arguments_search(argv, expected_search):
    """Test --search / -S argument parsing."""
    with patch("sys.argv", argv):
        args = parse_arguments()
        assert args.search == expected_search


def test_run_copycat_search_txt_integration(tmp_path, run_args):
    """Integration: TXT report contains SUCHERGEBNISSE section with matches."""
    (tmp_path / "main.py").write_text("# TODO: fix this\nx = 1\n# TODO: add tests\n")
    (tmp_path / "clean.py").write_text("x = 1\ny = 2\n")
    run_copycat(run_args(search="TODO"))
    content = next(tmp_path.glob("combined_copycat_*.txt")).read_text(encoding="utf-8")
    assert "SUCHERGEBNISSE" in content
    assert "TODO" in content
    assert "main.py" in content
    assert 'SUCHE: "TODO"' in content


@pytest.mark.parametrize("fmt,present,absent", [
    ("txt", ['SUCHE: "FIXME"'], ["SUCHERGEBNISSE"]),
    ("md", [], ["Suchergebnisse"]),
])
def test_run_copycat_search_no_matches(tmp_path, run_args, fmt, present, absent):
    """Integration: report with search but no matches (no results section)."""
    (tmp_path / "main.py").write_text("x = 1\n")
    run_copycat(run_args(fmt=fmt, search="FIXME"))
    content = next(tmp_path.glob(f"combined_copycat_*.{fmt}")).read_text(encoding="utf-8")
    for s in present:
        assert s in content
    for s in absent:
        assert s not in content


def test_run_copycat_search_json_integration(tmp_path, run_args):
    """Integration: JSON report contains search key and matches in details."""
    (tmp_path / "app.py").write_text("def hello(): pass\ndef world(): pass\n")
    run_copycat(run_args(fmt="json", search="def "))
    data = json.loads(next(tmp_path.glob("combined_copycat_*.json")).read_text())
    assert data["search"] is not None
    assert data["search"]["pattern"] == "def "
    assert data["search"]["total_matches"] >= 2
    assert data["search"]["files_matched"] == 1
    code_entry = data["details"]["code"][0]
    assert "matches" in code_entry
    assert len(code_entry["matches"]) >= 2
    assert code_entry["matches"][0]["line"] == 1


def test_run_copycat_search_json_no_search(tmp_path, run_args):
    """Integration: JSON report has search=None when --search not provided."""
    (tmp_path / "app.py").write_text("x = 1\n")
    run_copycat(run_args(fmt="json"))
    data = json.loads(next(tmp_path.glob("combined_copycat_*.json")).read_text())
    assert data["search"] is None
    # no "matches" key when search is None
    assert "matches" not in data["details"]["code"][0]


def test_run_copycat_search_md_integration(tmp_path, run_args):
    """Integration: MD report contains Suchergebnisse table."""
    (tmp_path / "utils.py").write_text("# FIXME: broken\nx = 1\n")
    run_copycat(run_args(fmt="md", search="FIXME"))
    content = next(tmp_path.glob("combined_copycat_*.md")).read_text(encoding="utf-8")
    assert "## Suchergebnisse: `FIXME`" in content
    assert "utils.py" in content
    assert "FIXME" in content


def test_run_copycat_search_invalid_regex(tmp_path, run_args):
    """Integration: invalid regex produces report without crash."""
    (tmp_path / "app.py").write_text("x = 1\n")
    run_copycat(run_args(search="[invalid("))
    reports = list(tmp_path.glob("combined_copycat_*.txt"))
    assert len(reports) == 1
    content = reports[0].read_text(encoding="utf-8")
    assert "SUCHERGEBNISSE" not in content


def test_write_txt_search_direct(tmp_path):
    """Direct _write_txt: search section appears with matches."""
    files = {k: [] for k in TYPE_FILTERS}
    py = tmp_path / "mod.py"
    py.write_text("# TODO: fix\nx = 1\n")
    files["code"] = [py]
    search_results = {py: [(1, "# TODO: fix")]}

    buf = StringIO()
    args = Namespace(recursive=False, types=["code"], max_size=float("inf"), format="txt", search="TODO")
    _write_txt(buf, files, args, tmp_path, "No Git", 1, search_pattern="TODO", search_results=search_results)
    out = buf.getvalue()
    assert "SUCHERGEBNISSE" in out
    assert "mod.py" in out
    assert "L1: # TODO: fix" in out
    assert 'SUCHE: "TODO"' in out


def test_write_md_search_direct(tmp_path):
    """Direct _write_md: Suchergebnisse table with pipe-escaped text."""
    files = {k: [] for k in TYPE_FILTERS}
    py = tmp_path / "mod.py"
    py.write_text("x = 1\n")
    files["code"] = [py]
    search_results = {py: [(1, "x | y")]}

    buf = StringIO()
    args = Namespace(recursive=False, types=["code"], max_size=float("inf"), format="md", search="x")
    _write_md(buf, files, args, tmp_path, "No Git", 1, search_pattern="x", search_results=search_results)
    out = buf.getvalue()
    assert "## Suchergebnisse: `x`" in out
    assert r"x \| y" in out
    assert "| **Suche** |" in out


def test_write_json_search_direct(tmp_path):
    """Direct _write_json: search key + matches in entries."""
    files = {k: [] for k in TYPE_FILTERS}
    py = tmp_path / "mod.py"
    py.write_text("# TODO\n")
    files["code"] = [py]
    sr = {py: [(1, "# TODO")]}

    out_path = tmp_path / "out.json"
    args = Namespace(recursive=False, types=["code"], max_size=float("inf"), format="json", search="TODO")
    _write_json(out_path, files, args, tmp_path, "No Git", 2, search_pattern="TODO", search_results=sr)

    data = json.loads(out_path.read_text())
    assert data["search"]["pattern"] == "TODO"
    assert data["search"]["total_matches"] == 1
    assert data["search"]["files_matched"] == 1
    assert data["details"]["code"][0]["matches"] == [{"line": 1, "text": "# TODO"}]

