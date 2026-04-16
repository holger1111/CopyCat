"""CopyCat v2.7 - Pytest Suite (Refactored & Optimized)"""

import subprocess
import struct
import re
from pathlib import Path
from unittest.mock import patch, MagicMock, Mock
from argparse import Namespace

import pytest

from CopyCat import (
    parse_arguments,
    get_next_serial_number,
    move_to_archive,
    list_binary_file,
    extract_drawio,
    get_git_info,
    should_skip_gitignore,
    get_plural,
    size_filtered_glob,
    run_copycat,
    TYPE_FILTERS,
)


# ==================== HELPER FUNCTIONS ====================

def is_valid_serial_filename(filename: str) -> bool:
    """Validate serial filename format."""
    pattern = r"^combined_copycat_(\d+)\.txt$"
    return bool(re.match(pattern, filename))


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
    def _make_args(types=None, recursive=False, max_size=None, input_path=None, output_path=None):
        return Namespace(
            input=str(input_path or tmp_path),
            output=str(output_path or tmp_path),
            types=types or ["code"],
            recursive=recursive,
            max_size=max_size or float("inf"),
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
    (["test_copycat.py"], {"types": ["all"], "recursive": False, "max_size": float("inf")}),
    (["test_copycat.py", "-r"], {"types": ["all"], "recursive": True}),
    (["test_copycat.py", "-t", "code", "diagram"], {"types": ["code", "diagram"]}),
    (["test_copycat.py", "-t", "code,diagram"], {"types": ["code", "diagram"]}),
    (["test_copycat.py", "-s", "5"], {"max_size": 5.0}),
    (["test_copycat.py", "-r", "-t", "code"], {"recursive": True, "types": ["code"]}),
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
])
def test_get_next_serial_number(tmp_path, files, expected):
    """Test serial number generation."""
    for fname in files:
        (tmp_path / fname).touch()
    assert get_next_serial_number(tmp_path) == expected


def test_is_valid_serial_filename():
    """Test serial filename validation."""
    assert is_valid_serial_filename("combined_copycat_1.txt") is True
    assert is_valid_serial_filename("combined_copycat.txt") is False
    assert is_valid_serial_filename("other_file.txt") is False


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


def test_get_git_info_edge_cases(tmp_path):
    """Test git info with edge cases in copycat integration."""
    args = Namespace(
        input=str(tmp_path),
        output=str(tmp_path),
        types=["code"],
        recursive=False,
        max_size=float("inf"),
    )
    with patch("subprocess.check_output") as mock_subprocess:
        mock_subprocess.side_effect = FileNotFoundError
        run_copycat(args)
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


def test_gitignore_pattern_matching(tmp_path):
    """Test complex gitignore pattern matching including negation."""
    (tmp_path / ".gitignore").write_text("*.py\nbuild/\n!important.py\n")

    (tmp_path / "build").mkdir()
    (tmp_path / "build" / "generated.py").touch()
    (tmp_path / "important.py").touch()
    (tmp_path / "test.py").touch()

    run_copycat(Namespace(
        input=str(tmp_path),
        output=str(tmp_path),
        types=["code"],
        recursive=True,
        max_size=float("inf"),
    ))

    report = next(tmp_path.glob("combined_copycat_*.txt"))
    report_text = report.read_text()
    assert "test.py" not in report_text        # blocked by *.py
    assert "important.py" in report_text       # negation un-ignores it


def test_gitignore_recursive(tmp_path):
    """Test that subdirectory .gitignore files are respected."""
    (tmp_path / "sub").mkdir()
    (tmp_path / "sub" / ".gitignore").write_text("*.py\n")
    (tmp_path / "sub" / "ignored.py").touch()
    (tmp_path / "visible.py").touch()

    run_copycat(Namespace(
        input=str(tmp_path),
        output=str(tmp_path),
        types=["code"],
        recursive=True,
        max_size=float("inf"),
    ))

    report = next(tmp_path.glob("combined_copycat_*.txt"))
    report_text = report.read_text()
    assert "visible.py" in report_text
    assert "ignored.py" not in report_text


def test_gitignore_flat_mode(tmp_path):
    """Test that gitignore is applied in non-recursive flat mode."""
    (tmp_path / ".gitignore").write_text("ignored.py\n")
    (tmp_path / "visible.py").touch()
    (tmp_path / "ignored.py").touch()

    run_copycat(Namespace(
        input=str(tmp_path),
        output=str(tmp_path),
        types=["code"],
        recursive=False,
        max_size=float("inf"),
    ))

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
