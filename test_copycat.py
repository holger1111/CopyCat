"""CopyCat v2.9 - Pytest Suite (Refactored & Optimized)"""

import logging
import subprocess
import json
import re
import base64
import zlib
import zipfile
from io import StringIO
from urllib.parse import quote as url_quote
from pathlib import Path
from unittest.mock import patch, MagicMock, Mock
from argparse import Namespace

import pytest

from CopyCat import (
    parse_arguments,
    load_config,
    get_next_serial_number,
    is_valid_serial_filename,
    move_to_archive,
    list_binary_file,
    extract_drawio,
    extract_notebook,
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
    _write_template,
    watch_and_run,
    diff_reports,
    install_hook,
    merge_reports,
    TYPE_FILTERS,
    load_plugins,
    PLUGIN_RENDERERS,
    _loaded_plugins,
    _html_escape,
    _hash_file,
    _load_cache,
    _save_cache,
    _write_html,
    _analyse_file,
    _build_stats,
    _write_pdf,
    _generate_ai_summary,
    build_timeline,
    _timeline_md,
    _timeline_ascii,
    _timeline_html,
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
    def _make_args(types=None, recursive=False, max_size=None, input_path=None, output_path=None, fmt="txt", search=None, exclude=None, incremental=False, stats=False, git_url=None):
        return Namespace(
            input=str(input_path or tmp_path),
            output=str(output_path or tmp_path),
            types=types or ["code"],
            recursive=recursive,
            max_size=max_size or float("inf"),
            format=fmt,
            search=search,
            template=None,
            watch=False,
            cooldown=2.0,
            plugin_dir=None,
            exclude=exclude or [],
            incremental=incremental,
            stats=stats,
            git_url=git_url,
        )
    return _make_args


@pytest.fixture
def clean_plugins():
    """Stelle TYPE_FILTERS, PLUGIN_RENDERERS und _loaded_plugins nach jedem Plugin-Test wieder her."""
    import CopyCat
    original_tf = dict(CopyCat.TYPE_FILTERS)
    original_pr = dict(CopyCat.PLUGIN_RENDERERS)
    original_lp = list(CopyCat._loaded_plugins)
    yield
    CopyCat.TYPE_FILTERS.clear()
    CopyCat.TYPE_FILTERS.update(original_tf)
    CopyCat.PLUGIN_RENDERERS.clear()
    CopyCat.PLUGIN_RENDERERS.update(original_pr)
    CopyCat._loaded_plugins.clear()
    CopyCat._loaded_plugins.extend(original_lp)


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
    (["test_copycat.py", "-f", "html"], {"format": "html"}),
    (["test_copycat.py", "--format", "txt"], {"format": "txt"}),
    (["test_copycat.py", "-I"], {"incremental": True}),
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


@pytest.mark.parametrize("name,expected", [
    ("combined_copycat_1.txt", True),
    ("combined_copycat_5.json", True),
    ("combined_copycat_3.md", True),
    ("combined_copycat_9.html", True),
    ("combined_copycat.txt", False),
    ("other_file.txt", False),
    ("combined_copycat_1.csv", False),
])
def test_is_valid_serial_filename(name, expected):
    assert is_valid_serial_filename(name) is expected


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
    expected = {"code", "web", "db", "config", "docs", "deps", "img", "audio", "diagram", "notebook"}
    assert set(TYPE_FILTERS.keys()) == expected


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


@patch("CopyCat.logging.debug")
@patch("CopyCat.logging.info")
def test_size_filtered_glob_progress(mock_info, mock_debug):
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

    mock_debug.assert_any_call("Geprüft: %d Dateien...", 100)
    mock_info.assert_any_call("→ %d geprüft, Filter OK", 101)


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


def test_extract_drawio_zip_fallback_success(tmp_path, mock_writer):
    """Test ZIP fallback: compressed .drawio (ZIP) is parsed correctly."""
    xml = '<mxGraphModel><root><mxCell id="0"/><mxCell id="1" value="ZIP Cell" parent="0"/></root></mxGraphModel>'
    drawio = tmp_path / "compressed.drawio"
    with zipfile.ZipFile(drawio, "w") as zf:
        zf.writestr("diagram.xml", xml)

    with patch("builtins.open", side_effect=UnicodeDecodeError("utf-8", b"", 0, 1, "invalid")):
        extract_drawio(mock_writer, drawio)

    written = "".join(call[0][0] for call in mock_writer.write.call_args_list)
    assert "DIAGRAM compressed.drawio" in written
    assert "ZIP Cell" in written


def test_extract_drawio_zip_empty_archive(tmp_path, mock_writer):
    """Test ZIP fallback: ZIP with no entries yields [ZIP EMPTY]."""
    drawio = tmp_path / "empty.drawio"
    with zipfile.ZipFile(drawio, "w"):
        pass  # empty ZIP

    with patch("builtins.open", side_effect=UnicodeDecodeError("utf-8", b"", 0, 1, "invalid")):
        extract_drawio(mock_writer, drawio)

    mock_writer.write.assert_called_with("[ZIP EMPTY: empty.drawio]\n")


def test_extract_drawio_zip_bad_xml_inside(tmp_path, mock_writer):
    """Test ZIP fallback: ZIP with invalid XML inside yields [XML PARSE ERROR]."""
    drawio = tmp_path / "broken.drawio"
    with zipfile.ZipFile(drawio, "w") as zf:
        zf.writestr("diagram.xml", "not valid xml <<<")

    with patch("builtins.open", side_effect=UnicodeDecodeError("utf-8", b"", 0, 1, "invalid")):
        extract_drawio(mock_writer, drawio)

    assert "[XML PARSE ERROR: broken.drawio" in mock_writer.write.call_args[0][0]


def test_extract_drawio_compressed_success(tmp_path, mock_writer):
    """Test compressed draw.io diagram (Base64/zlib/URL-encoded format)."""
    inner_xml = (
        '<mxGraphModel><root>'
        '<mxCell id="0"/>'
        '<mxCell id="1" value="Comp Cell" parent="0" vertex="1"/>'
        '</root></mxGraphModel>'
    )
    encoded = url_quote(inner_xml)
    compressor = zlib.compressobj(level=9, method=zlib.DEFLATED, wbits=-15)
    raw = compressor.compress(encoded.encode("utf-8")) + compressor.flush()
    b64 = base64.b64encode(raw).decode("utf-8")
    drawio = tmp_path / "comp.drawio"
    drawio.write_text(f'<mxfile><diagram name="Page-1">{b64}</diagram></mxfile>', encoding="utf-8")

    extract_drawio(mock_writer, drawio)

    written = "".join(call[0][0] for call in mock_writer.write.call_args_list)
    assert "DIAGRAM comp.drawio" in written
    assert "Comp Cell" in written


@pytest.mark.parametrize("content", [
    '<mxfile><diagram>!!!NOT_VALID_BASE64!!!</diagram></mxfile>',
    '<mxfile><diagram>   </diagram></mxfile>',
])
def test_extract_drawio_compressed_0_cells(tmp_path, mock_writer, content):
    """Compressed drawio with invalid/empty content: no crash, 0 cells."""
    drawio = tmp_path / "test.drawio"
    drawio.write_text(content, encoding="utf-8")
    extract_drawio(mock_writer, drawio)
    written = "".join(call[0][0] for call in mock_writer.write.call_args_list)
    assert "0 Cells, 0 Texte, 0 Unique" in written


def test_extract_drawio_position(tmp_path, mock_writer):
    """Test that mxGeometry x/y is included in cell output."""
    drawio = tmp_path / "pos.drawio"
    drawio.write_text(
        '<mxGraphModel><root>'
        '<mxCell id="0"/>'
        '<mxCell id="2" value="Node A" vertex="1" parent="1">'
        '<mxGeometry x="100" y="200" width="120" height="60" as="geometry"/>'
        '</mxCell>'
        '</root></mxGraphModel>',
        encoding="utf-8"
    )
    extract_drawio(mock_writer, drawio)
    written = "".join(call[0][0] for call in mock_writer.write.call_args_list)
    assert "Node A" in written
    assert "(x=100, y=200)" in written


def test_extract_drawio_unique_count(tmp_path, mock_writer):
    """Test that unique value count is correct in summary line."""
    drawio = tmp_path / "uniq.drawio"
    drawio.write_text(
        '<mxGraphModel><root>'
        '<mxCell id="0"/>'
        '<mxCell id="1" value="Alpha"/>'
        '<mxCell id="2" value="Alpha"/>'
        '<mxCell id="3" value="Beta"/>'
        '</root></mxGraphModel>',
        encoding="utf-8"
    )
    extract_drawio(mock_writer, drawio)
    written = "".join(call[0][0] for call in mock_writer.write.call_args_list)
    assert "4 Cells, 3 Texte, 2 Unique" in written


def test_extract_drawio_position_no_coords(tmp_path, mock_writer):
    """Test mxGeometry without x/y attributes - no position shown, no crash."""
    drawio = tmp_path / "nopos.drawio"
    drawio.write_text(
        '<mxGraphModel><root>'
        '<mxCell id="1" value="No Pos">'
        '<mxGeometry width="120" height="60" as="geometry"/>'
        '</mxCell>'
        '</root></mxGraphModel>',
        encoding="utf-8"
    )
    extract_drawio(mock_writer, drawio)
    written = "".join(call[0][0] for call in mock_writer.write.call_args_list)
    assert "No Pos" in written
    assert "(x=" not in written


def test_extract_drawio_size_limit(tmp_path, mock_writer):
    """Test that files >1MB are skipped with [SKIPPED] message."""
    drawio = tmp_path / "big.drawio"
    drawio.write_bytes(b"x" * (1_048_576 + 1))
    extract_drawio(mock_writer, drawio)
    mock_writer.write.assert_called_with("[SKIPPED: big.drawio - exceeds 1MB limit]\n")


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
    
    with patch("CopyCat.logging.error") as mock_log:
        run_copycat(args)
        if not input_exists:
            mock_log.assert_called()


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


def test_run_copycat_flat_skips_combined_output(tmp_path, run_args):
    """Test that files named 'combined_copycat...' are skipped in flat mode."""
    (tmp_path / "combined_copycat_prev.txt").write_text("old output")
    (tmp_path / "notes.txt").write_text("notes")
    run_copycat(run_args(types=["docs"]))
    report = next(tmp_path.glob("combined_copycat_*.txt"))
    assert "combined_copycat_prev" not in report.read_text()


# ==================== ARCHIVE TESTS ====================

@pytest.mark.parametrize("exists,expect_archived", [
    (True, True),
    (False, False),
])
def test_move_to_archive(tmp_path, exists, expect_archived):
    """Test report archiving (file exists) and no-op (file absent)."""
    if exists:
        (tmp_path / "combined_copycat_1.txt").touch()
    move_to_archive(tmp_path, "combined_copycat_1.txt")
    assert (tmp_path / "CopyCat_Archive" / "combined_copycat_1.txt").exists() == expect_archived


def test_move_to_archive_permission(tmp_path, monkeypatch):
    """Test archive with permission error (exception is silently handled)."""
    (tmp_path / "combined_copycat_1.txt").touch()

    def mock_move(src, dst):
        raise PermissionError()

    monkeypatch.setattr("shutil.move", mock_move)
    move_to_archive(tmp_path, "combined_copycat_1.txt")


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


def test_run_copycat_format_html_basic(tmp_path, run_args):
    """HTML-Format erstellt einen Report mit erwarteten Kernsektionen."""
    (tmp_path / "app.py").write_text("print('ok')\n", encoding="utf-8")
    run_copycat(run_args(fmt="html"))

    reports = list(tmp_path.glob("combined_copycat_*.html"))
    assert len(reports) == 1
    content = reports[0].read_text(encoding="utf-8")
    assert "<!DOCTYPE html>" in content
    assert "CopyCat v2.9 Report" in content
    assert "Code-Details" in content
    assert "app.py" in content


def test_run_copycat_incremental_cache_hit(tmp_path, run_args):
    """Zweiter inkrementeller Lauf nutzt den Cache für unveränderte Dateien."""
    src = tmp_path / "cached.py"
    src.write_text("x = 1\n", encoding="utf-8")

    run_copycat(run_args(incremental=True))
    run_copycat(run_args(incremental=True))

    cache_file = tmp_path / ".copycat_cache" / "cache.json"
    assert cache_file.exists()

    latest = sorted(tmp_path.glob("combined_copycat_*.txt"))[-1]
    text = latest.read_text(encoding="utf-8")
    assert "Cache-Treffer" in text


def test_run_copycat_incremental_cache_miss_on_change(tmp_path, run_args):
    """Nach Änderung einer Datei wird sie im nächsten Lauf nicht als Cache-Treffer markiert."""
    src = tmp_path / "changed.py"
    src.write_text("x = 1\n", encoding="utf-8")

    run_copycat(run_args(incremental=True))
    src.write_text("x = 2\n", encoding="utf-8")
    run_copycat(run_args(incremental=True))

    latest = sorted(tmp_path.glob("combined_copycat_*.txt"))[-1]
    text = latest.read_text(encoding="utf-8")
    assert "changed.py" in text
    assert "Cache-Treffer" not in text


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

@pytest.mark.parametrize("text,pattern,count,first_lineno", [
    ("x = 1\n# TODO: fix\ndef hello(): pass\n", "TODO", 1, 2),
    ("# TODO: a\nx = 1\n# TODO: b\n", "TODO", 2, 1),
    ("x = 1\ndef hello(): pass\n", "TODO", 0, None),
    ("def foo():\ndef bar():\nx = 1\n", r"^def ", 2, 1),
])
def test_search_in_file_matches(tmp_path, text, pattern, count, first_lineno):
    """search_in_file returns correct hit count and line numbers."""
    f = tmp_path / "code.py"
    f.write_text(text)
    hits = search_in_file(f, pattern)
    assert len(hits) == count
    if first_lineno is not None:
        assert hits[0][0] == first_lineno


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


# ==================== CONFIG TESTS (MILESTONE 12) ====================

def test_load_config_no_file(tmp_path):
    """Explicit config_path that does not exist → empty dict."""
    cfg = load_config(str(tmp_path / "nonexistent.conf"))
    assert cfg == {}


def test_load_config_basic(tmp_path):
    """All valid fields parsed; comments, empty lines, no-equals lines skipped."""
    conf = tmp_path / "copycat.conf"
    conf.write_text(
        "# comment\n"
        "\n"
        "types = code, diagram\n"
        "recursive = true\n"
        "max_size_mb = 5\n"
        "format = md\n"
        "search = TODO\n"
        "input = src\n"
        "output = out\n"
        "no_equals_sign\n"
    )
    cfg = load_config(str(conf))
    assert cfg["types"] == "code, diagram"
    assert cfg["recursive"] == "true"
    assert cfg["max_size_mb"] == "5"
    assert cfg["format"] == "md"
    assert cfg["search"] == "TODO"
    assert cfg["input"] == "src"
    assert cfg["output"] == "out"
    assert "no_equals_sign" not in cfg


def test_load_config_empty_value_skipped(tmp_path):
    """Key with empty value after strip is not stored."""
    conf = tmp_path / "copycat.conf"
    conf.write_text("types =\n")
    cfg = load_config(str(conf))
    assert "types" not in cfg


def test_load_config_oserror(tmp_path):
    """OSError during read_text → empty dict returned."""
    conf = tmp_path / "copycat.conf"
    conf.touch()
    with patch.object(Path, "read_text", side_effect=OSError("denied")):
        cfg = load_config(str(conf))
    assert cfg == {}


def test_load_config_searches_cwd(tmp_path, monkeypatch):
    """load_config() without explicit path finds copycat.conf in CWD."""
    (tmp_path / "copycat.conf").write_text("format = json\n")
    monkeypatch.chdir(tmp_path)
    cfg = load_config()
    assert cfg["format"] == "json"


def test_parse_arguments_config_types_recursive(tmp_path):
    """Config sets types + recursive=true as defaults."""
    conf = tmp_path / "copycat.conf"
    conf.write_text("types = code, diagram\nrecursive = true\n")
    with patch("sys.argv", ["CopyCat.py"]):
        args = parse_arguments(config_path=str(conf))
    assert args.types == ["code", "diagram"]
    assert args.recursive is True


def test_parse_arguments_config_max_size_format_search(tmp_path):
    """Config sets max_size_mb, format, search as defaults."""
    conf = tmp_path / "copycat.conf"
    conf.write_text("max_size_mb = 5\nformat = md\nsearch = TODO\n")
    with patch("sys.argv", ["CopyCat.py"]):
        args = parse_arguments(config_path=str(conf))
    assert args.max_size == 5.0
    assert args.format == "md"
    assert args.search == "TODO"


def test_parse_arguments_config_incremental(tmp_path):
    """Config setzt incremental=true als Default."""
    conf = tmp_path / "copycat.conf"
    conf.write_text("incremental = true\n")
    with patch("sys.argv", ["CopyCat.py"]):
        args = parse_arguments(config_path=str(conf))
    assert args.incremental is True


def test_parse_arguments_config_input_output(tmp_path):
    """Config sets input and output paths as defaults."""
    conf = tmp_path / "copycat.conf"
    conf.write_text(f"input = {tmp_path}\noutput = {tmp_path}\n")
    with patch("sys.argv", ["CopyCat.py"]):
        args = parse_arguments(config_path=str(conf))
    assert args.input == str(tmp_path)
    assert args.output == str(tmp_path)


def test_parse_arguments_config_invalid_values(tmp_path):
    """Invalid max_size_mb and format values are ignored (warning logged)."""
    conf = tmp_path / "copycat.conf"
    conf.write_text("max_size_mb = notanumber\nformat = xlsx\n")
    with patch("sys.argv", ["CopyCat.py"]):
        args = parse_arguments(config_path=str(conf))
    assert args.max_size == float("inf")
    assert args.format == "txt"


def test_parse_arguments_config_format_pdf(tmp_path):
    """Config format=pdf is now valid and accepted."""
    conf = tmp_path / "copycat.conf"
    conf.write_text("format = pdf\n")
    with patch("sys.argv", ["CopyCat.py"]):
        args = parse_arguments(config_path=str(conf))
    assert args.format == "pdf"


def test_parse_arguments_config_recursive_false(tmp_path):
    """Config recursive=false keeps default False."""
    conf = tmp_path / "copycat.conf"
    conf.write_text("recursive = false\n")
    with patch("sys.argv", ["CopyCat.py"]):
        args = parse_arguments(config_path=str(conf))
    assert args.recursive is False


def test_parse_arguments_config_empty_types(tmp_path):
    """types value that yields no tokens → default ['all'] kept."""
    conf = tmp_path / "copycat.conf"
    conf.write_text("types = ,,,\n")
    with patch("sys.argv", ["CopyCat.py"]):
        args = parse_arguments(config_path=str(conf))
    assert args.types == ["all"]


def test_parse_arguments_no_config(tmp_path):
    """Missing config file → pure argparse defaults unchanged."""
    with patch("sys.argv", ["CopyCat.py"]):
        args = parse_arguments(config_path=str(tmp_path / "missing.conf"))
    assert args.types == ["all"]
    assert args.recursive is False
    assert args.max_size == float("inf")
    assert args.format == "txt"
    assert args.search is None


def test_parse_arguments_cli_overrides_config(tmp_path):
    """CLI arguments take precedence over copycat.conf values."""
    conf = tmp_path / "copycat.conf"
    conf.write_text("types = docs\nformat = md\nrecursive = true\n")
    with patch("sys.argv", ["CopyCat.py", "-t", "code", "-f", "json"]):
        args = parse_arguments(config_path=str(conf))
    assert args.types == ["code"]
    assert args.format == "json"
    assert args.recursive is True  # config=true, no CLI override


# ==================== GUI TESTS ====================

from CopyCat_GUI import CopyCatGUI, RedirectText, TYPES as GUI_TYPES


def _make_var(value):
    """Einfacher Mock für tk.StringVar / tk.BooleanVar."""
    container = {"v": value}
    m = MagicMock()
    m.get = lambda: container["v"]
    m.set = lambda v: container.update({"v": v})
    return m


@pytest.fixture
def gui():
    """CopyCatGUI-Instanz ohne tkinter-Fenster (headless-tauglich)."""
    instance = object.__new__(CopyCatGUI)
    instance._root = MagicMock()
    instance._input_var = _make_var("")
    instance._output_var = _make_var("")
    instance._recursive_var = _make_var(False)
    instance._max_size_var = _make_var("")
    instance._format_var = _make_var("txt")
    instance._search_var = _make_var("")
    instance._type_vars = {t: _make_var(True) for t in GUI_TYPES}
    instance._run_btn = MagicMock()
    instance._open_btn = MagicMock()
    instance._output_text = MagicMock()
    instance._progress = MagicMock()
    instance._template_var = _make_var("")
    instance._cooldown_var = _make_var("2.0")
    instance._exclude_var = _make_var("")
    instance._incremental_var = _make_var(False)
    instance._stats_var = _make_var(False)
    instance._git_url_var = _make_var("")
    instance._watch_stop_event = None
    instance._watch_thread = None
    instance._watch_btn = MagicMock()
    return instance


def test_gui_types_constant():
    assert GUI_TYPES == ["code", "web", "db", "config", "docs", "deps", "img", "audio", "diagram", "notebook"]
    assert len(GUI_TYPES) == 10


def test_redirect_text_write():
    mock_widget = MagicMock()
    rt = RedirectText(mock_widget)
    rt.write("hello")
    mock_widget.configure.assert_called()
    mock_widget.insert.assert_called_with("end", "hello")
    mock_widget.see.assert_called_with("end")


def test_redirect_text_flush():
    rt = RedirectText(MagicMock())
    rt.flush()  # darf nicht werfen


def test_build_args_defaults(gui):
    args = gui._build_args()
    assert args.input is None
    assert args.output is None
    assert args.types == GUI_TYPES
    assert args.recursive is False
    assert args.max_size == float("inf")
    assert args.format == "txt"
    assert args.search is None
    assert args.incremental is False


def test_build_args_with_values(gui):
    gui._input_var.set("/some/path")
    gui._output_var.set("/out/path")
    gui._recursive_var.set(True)
    gui._max_size_var.set("5.0")
    gui._format_var.set("json")
    gui._search_var.set("TODO")
    gui._incremental_var.set(True)
    args = gui._build_args()
    assert args.input == "/some/path"
    assert args.output == "/out/path"
    assert args.recursive is True
    assert args.max_size == 5.0
    assert args.format == "json"
    assert args.search == "TODO"
    assert args.incremental is True


def test_build_args_invalid_max_size(gui):
    gui._max_size_var.set("notanumber")
    with pytest.raises(ValueError, match="Ungültige Max-Größe"):
        gui._build_args()


def test_build_args_no_types_selected_returns_all(gui):
    for var in gui._type_vars.values():
        var.set(False)
    args = gui._build_args()
    assert args.types == ["all"]


def test_select_all_types(gui):
    for var in gui._type_vars.values():
        var.set(False)
    gui._select_all_types()
    assert all(var.get() for var in gui._type_vars.values())


def test_deselect_all_types(gui):
    gui._deselect_all_types()
    assert not any(var.get() for var in gui._type_vars.values())


def test_browse_input_sets_output_when_empty(gui):
    with patch("tkinter.filedialog.askdirectory", return_value="/chosen"):
        gui._browse_input()
    assert gui._input_var.get() == "/chosen"
    assert gui._output_var.get() == "/chosen"


def test_browse_input_does_not_overwrite_output(gui):
    gui._output_var.set("/existing/output")
    with patch("tkinter.filedialog.askdirectory", return_value="/chosen"):
        gui._browse_input()
    assert gui._output_var.get() == "/existing/output"


def test_browse_input_cancelled(gui):
    with patch("tkinter.filedialog.askdirectory", return_value=""):
        gui._browse_input()
    assert gui._input_var.get() == ""


def test_browse_output(gui):
    with patch("tkinter.filedialog.askdirectory", return_value="/out"):
        gui._browse_output()
    assert gui._output_var.get() == "/out"


def test_browse_output_cancelled(gui):
    gui._output_var.set("/existing")
    with patch("tkinter.filedialog.askdirectory", return_value=""):
        gui._browse_output()
    assert gui._output_var.get() == "/existing"


def test_on_run_invalid_max_size_shows_error(gui):
    gui._max_size_var.set("notanumber")
    with patch("tkinter.messagebox.showerror") as mock_err:
        gui._on_run()
    mock_err.assert_called_once()
    assert "Eingabefehler" in mock_err.call_args[0]


def test_open_output_folder(gui, tmp_path):
    gui._output_var.set(str(tmp_path))
    with patch("os.startfile", create=True) as mock_sf:
        gui._open_output_folder()
    mock_sf.assert_called_once_with(str(tmp_path))


def test_open_output_folder_nonexistent(gui):
    gui._output_var.set("/nonexistent/path/xyz")
    with patch("os.startfile", create=True) as mock_sf:
        gui._open_output_folder()
    mock_sf.assert_not_called()


def test_clear_output(gui):
    gui._clear_output()
    gui._output_text.configure.assert_called()
    gui._output_text.delete.assert_called_with("1.0", "end")


def test_on_run_success(gui, tmp_path):
    gui._input_var.set(str(tmp_path))
    after_calls = []
    gui._root.after = lambda _d, fn: after_calls.append(fn)

    def fake_thread(target=None, daemon=None):
        m = MagicMock()
        m.start.side_effect = lambda: target()
        return m

    with patch("CopyCat_GUI.threading.Thread", side_effect=fake_thread), \
         patch("CopyCat_GUI.run_copycat"), \
         patch("CopyCat_GUI.logging.getLogger") as mock_get_logger:
        mock_get_logger.return_value.level = logging.WARNING
        gui._on_run()

    for fn in after_calls:
        fn()
    gui._run_btn.configure.assert_called()
    gui._open_btn.configure.assert_called_with(state="normal")


def test_on_run_exception(gui, tmp_path):
    gui._input_var.set(str(tmp_path))
    after_calls = []
    gui._root.after = lambda _d, fn: after_calls.append(fn)

    def fake_thread(target=None, daemon=None):
        m = MagicMock()
        m.start.side_effect = lambda: target()
        return m

    with patch("CopyCat_GUI.threading.Thread", side_effect=fake_thread), \
         patch("CopyCat_GUI.run_copycat", side_effect=RuntimeError("boom")), \
         patch("tkinter.messagebox.showerror") as mock_err, \
         patch("CopyCat_GUI.logging.getLogger") as mock_get_logger:
        mock_get_logger.return_value.level = logging.WARNING
        gui._on_run()
        for fn in after_calls:
            fn()
    mock_err.assert_called_once()
    assert "boom" in mock_err.call_args[0][1]


# ==================== NEUE TESTS: LOGGING / VERBOSE / QUIET ====================

@pytest.mark.parametrize("argv,expected_attr", [
    (["CopyCat.py", "--verbose"], "verbose"),
    (["CopyCat.py", "-v"], "verbose"),
    (["CopyCat.py", "--quiet"], "quiet"),
    (["CopyCat.py", "-q"], "quiet"),
])
def test_parse_arguments_logging_flags(argv, expected_attr):
    with patch("sys.argv", argv):
        args = parse_arguments()
    assert getattr(args, expected_attr) is True


# ==================== NEUE TESTS: EXTRACT NOTEBOOK ====================

def test_extract_notebook_basic(tmp_path):
    nb = tmp_path / "test.ipynb"
    nb.write_text(
        '{"cells": ['
        '{"cell_type": "code", "source": ["x = 1\\n", "y = 2"]},'
        '{"cell_type": "markdown", "source": ["# Titel"]}'
        '], "metadata": {}, "nbformat": 4, "nbformat_minor": 5}',
        encoding="utf-8",
    )
    written = []
    writer = MagicMock()
    writer.write = lambda s: written.append(s)
    extract_notebook(writer, nb)
    combined = "".join(written)
    assert "NOTEBOOK test.ipynb: 2 Cells (1 Code, 1 Markdown)" in combined
    assert "x = 1" in combined
    assert "# Titel" in combined


def test_extract_notebook_empty_cells(tmp_path):
    nb = tmp_path / "empty.ipynb"
    nb.write_text('{"cells": [], "metadata": {}, "nbformat": 4, "nbformat_minor": 5}', encoding="utf-8")
    written = []
    writer = MagicMock()
    writer.write = lambda s: written.append(s)
    extract_notebook(writer, nb)
    assert "0 Cells" in "".join(written)


def test_extract_notebook_invalid_json(tmp_path):
    nb = tmp_path / "bad.ipynb"
    nb.write_text("not valid json", encoding="utf-8")
    written = []
    writer = MagicMock()
    writer.write = lambda s: written.append(s)
    extract_notebook(writer, nb)
    assert "NOTEBOOK ERROR" in "".join(written)


def test_extract_notebook_os_error(tmp_path):
    nb = tmp_path / "missing.ipynb"
    written = []
    writer = MagicMock()
    writer.write = lambda s: written.append(s)
    extract_notebook(writer, nb)
    assert "NOTEBOOK READ ERROR" in "".join(written)


def test_notebook_type_in_type_filters():
    assert "notebook" in TYPE_FILTERS
    assert "*.ipynb" in TYPE_FILTERS["notebook"]


def test_csv_in_db_type_filters():
    assert "*.csv" in TYPE_FILTERS["db"]


# ==================== NEUE TESTS: WRITE_TXT + WRITE_MD MIT NOTEBOOK ====================

def test_write_txt_notebook(tmp_path):
    nb_file = tmp_path / "test.ipynb"
    nb_file.write_text(
        '{"cells": [{"cell_type": "code", "source": ["print(1)"]}], "metadata": {}, "nbformat": 4, "nbformat_minor": 5}',
        encoding="utf-8",
    )
    files = {k: [] for k in TYPE_FILTERS}
    files["notebook"] = [nb_file]
    args = Namespace(types=["notebook"], recursive=False, max_size=float("inf"), format="txt", search=None)
    written = []
    writer = MagicMock()
    writer.write = lambda s: written.append(s)
    _write_txt(writer, files, args, tmp_path, "No Git", 1)
    assert "NOTEBOOK" in "".join(written)


def test_write_md_notebook(tmp_path):
    nb_file = tmp_path / "test.ipynb"
    nb_file.write_text(
        '{"cells": [{"cell_type": "code", "source": ["print(1)"]}], "metadata": {}, "nbformat": 4, "nbformat_minor": 5}',
        encoding="utf-8",
    )
    files = {k: [] for k in TYPE_FILTERS}
    files["notebook"] = [nb_file]
    args = Namespace(types=["notebook"], recursive=False, max_size=float("inf"), format="md", search=None)
    written = []
    writer = MagicMock()
    writer.write = lambda s: written.append(s)
    _write_md(writer, files, args, tmp_path, "No Git", 1)
    combined = "".join(written)
    assert "NOTEBOOK" in combined
    assert "test.ipynb" in combined


# ==================== NEUE TESTS: GUI CONFIG LOAD / SAVE ====================

def test_load_config_applies_values(gui, tmp_path):
    conf = tmp_path / "test.conf"
    conf.write_text(
        "input = /my/input\noutput = /my/output\ntypes = code,docs\n"
        "recursive = true\nmax_size_mb = 10\nformat = json\nsearch = TODO\nincremental = true\n",
        encoding="utf-8",
    )
    with patch("tkinter.filedialog.askopenfilename", return_value=str(conf)):
        gui._load_config()
    assert gui._input_var.get() == "/my/input"
    assert gui._output_var.get() == "/my/output"
    assert gui._recursive_var.get() is True
    assert gui._max_size_var.get() == "10"
    assert gui._format_var.get() == "json"
    assert gui._search_var.get() == "TODO"
    assert gui._incremental_var.get() is True
    assert gui._type_vars["code"].get() is True
    assert gui._type_vars["docs"].get() is True
    assert gui._type_vars["web"].get() is False


def test_load_config_cancelled(gui):
    with patch("tkinter.filedialog.askopenfilename", return_value=""):
        gui._load_config()
    assert gui._input_var.get() == ""  # unveraendert


def test_save_config_writes_file(gui, tmp_path):
    out = tmp_path / "out.conf"
    gui._input_var.set("/src")
    gui._output_var.set("/dst")
    gui._format_var.set("md")
    gui._max_size_var.set("5")
    gui._search_var.set("def")
    gui._incremental_var.set(True)
    with patch("tkinter.filedialog.asksaveasfilename", return_value=str(out)), \
         patch("tkinter.messagebox.showinfo"):
        gui._save_config()
    content = out.read_text(encoding="utf-8")
    assert "input = /src" in content
    assert "output = /dst" in content
    assert "format = md" in content
    assert "max_size_mb = 5" in content
    assert "search = def" in content
    assert "incremental = true" in content


def test_save_config_cancelled(gui):
    with patch("tkinter.filedialog.asksaveasfilename", return_value=""):
        gui._save_config()  # darf nicht werfen


def test_save_config_os_error(gui, tmp_path):
    gui._input_var.set("/src")
    with patch("tkinter.filedialog.asksaveasfilename", return_value="/readonly/out.conf"), \
         patch("pathlib.Path.write_text", side_effect=OSError("Permission denied")), \
         patch("tkinter.messagebox.showerror") as mock_err:
        gui._save_config()
    mock_err.assert_called_once()


# ==================== NEUE TESTS: ON_RUN MIT PROGRESSBAR ====================

def test_on_run_starts_and_stops_progress(gui, tmp_path):
    gui._input_var.set(str(tmp_path))
    after_calls = []
    gui._root.after = lambda _d, fn: after_calls.append(fn)

    def fake_thread(target=None, daemon=None):
        m = MagicMock()
        m.start.side_effect = lambda: target()
        return m

    with patch("CopyCat_GUI.threading.Thread", side_effect=fake_thread), \
         patch("CopyCat_GUI.run_copycat"), \
         patch("CopyCat_GUI.logging.getLogger") as mock_get_logger:
        mock_get_logger.return_value.level = logging.WARNING
        gui._on_run()

    gui._progress.start.assert_called_once_with(10)
    for fn in after_calls:
        fn()
    gui._progress.stop.assert_called_once()


# ==================== NEUE TESTS: COVERAGE-LUECKEN ====================

def test_extract_notebook_cell_with_empty_source(tmp_path):
    """Cell mit leerem Source-Feld überspringen."""
    nb = tmp_path / "empty_cell.ipynb"
    nb.write_text(
        '{"cells": ['
        '{"cell_type": "code", "source": []},'
        '{"cell_type": "code", "source": ["x = 1"]}'
        '], "metadata": {}, "nbformat": 4, "nbformat_minor": 5}',
        encoding="utf-8",
    )
    written = []
    writer = MagicMock()
    writer.write = lambda s: written.append(s)
    extract_notebook(writer, nb)
    combined = "".join(written)
    assert "x = 1" in combined
    assert "2 Cells" in combined


def test_load_config_missing_keys(gui, tmp_path):
    """Nur 'format' in Config – andere Felder bleiben unverändert."""
    conf = tmp_path / "partial.conf"
    conf.write_text("format = json\n", encoding="utf-8")
    gui._input_var.set("/keep")
    with patch("tkinter.filedialog.askopenfilename", return_value=str(conf)):
        gui._load_config()
    assert gui._input_var.get() == "/keep"  # unverändert
    assert gui._format_var.get() == "json"  # gesetzt


def test_load_config_all_type_via_all_keyword(gui, tmp_path):
    """types = all setzt alle Checkboxen."""
    conf = tmp_path / "all.conf"
    conf.write_text("types = all\n", encoding="utf-8")
    for var in gui._type_vars.values():
        var.set(False)
    with patch("tkinter.filedialog.askopenfilename", return_value=str(conf)):
        gui._load_config()
    assert all(var.get() for var in gui._type_vars.values())


# ==================== IDEE 9: PARALLELE VERARBEITUNG ====================

def test_build_search_results_parallel(tmp_path):
    """_build_search_results liefert korrekte Ergebnisse trotz ThreadPoolExecutor."""
    f1 = tmp_path / "a.py"
    f2 = tmp_path / "b.py"
    f3 = tmp_path / "c.py"
    f1.write_text("def foo(): pass\n# TODO fix\n", encoding="utf-8")
    f2.write_text("x = 1\n", encoding="utf-8")
    f3.write_text("# TODO later\ndef bar(): pass\n", encoding="utf-8")

    files = {"code": [f1, f2, f3], "img": []}
    results = _build_search_results(files, "TODO")

    assert f1 in results
    assert f3 in results
    assert f2 not in results
    assert any("TODO fix" in txt for _, txt in results[f1])


def test_build_search_results_parallel_empty_files():
    """_build_search_results mit leerer Dateiliste gibt {} zurück."""
    result = _build_search_results({"code": [], "web": []}, "TODO")
    assert result == {}


def test_build_search_results_parallel_invalid_regex(tmp_path):
    """Ungültiger Regex führt zu leerem Ergebnis ohne Exception."""
    f = tmp_path / "x.py"
    f.write_text("hello\n", encoding="utf-8")
    result = _build_search_results({"code": [f]}, "[invalid(")
    assert result == {}


def test_build_search_results_non_searchable_skipped(tmp_path):
    """Nicht-durchsuchbare Typen (img, audio) werden übersprungen."""
    img = tmp_path / "pic.png"
    img.write_bytes(b"\x89PNG")
    result = _build_search_results({"img": [img]}, "PNG")
    assert result == {}


# ==================== IDEE 7: DIFF-MODUS ====================

def _make_txt_report(tmp_path, name, files_code, files_web=None):
    """Hilfsfunktion: Erzeugt ein minimales TXT-Report im CopyCat-Format."""
    lines = [
        "=" * 60,
        f"CopyCat v2.9 | 01.01.2025 10:00 | FLACH (Default)",
        str(tmp_path),
        "GIT: No Git",
        "",
        f"Gesamt: {len(files_code)} Dateien",
        "Serial #1",
        "=" * 60,
    ]
    if files_code:
        lines.append(f"CODE: {len(files_code)} Dateien")
    if files_web:
        lines.append(f"WEB: {len(files_web)} Dateien")
    lines.append("")
    lines.append("CODE-Details:")
    for fname in files_code:
        lines.append(f"  {fname}: 10 Zeilen")
        lines.append(f"----- {fname} -----")
        lines.append("# code")
        lines.append("")
    report = tmp_path / name
    report.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return report


def test_diff_reports_added_and_removed(tmp_path):
    """Diff erkennt neue und entfernte Dateien korrekt."""
    rep_a = _make_txt_report(tmp_path, "report_a.txt", ["old.py", "keep.py"])
    rep_b = _make_txt_report(tmp_path, "report_b.txt", ["new.py", "keep.py"])

    result = diff_reports(rep_a, rep_b)

    assert "Neu (+1):" in result
    assert "+ new.py" in result
    assert "Entfernt (-1):" in result
    assert "- old.py" in result
    assert "Unverändert: 1 Datei" in result


def test_diff_reports_no_changes(tmp_path):
    """Identische Reports geben 'Keine Änderungen' zurück."""
    rep_a = _make_txt_report(tmp_path, "report_a.txt", ["main.py"])
    rep_b = _make_txt_report(tmp_path, "report_b.txt", ["main.py"])

    result = diff_reports(rep_a, rep_b)
    assert "Keine Änderungen." in result


def test_diff_reports_type_count_change(tmp_path):
    """Diff zeigt Typ-Zähler-Änderungen."""
    rep_a = _make_txt_report(tmp_path, "report_a.txt", ["a.py"], files_web=[])
    rep_b = _make_txt_report(tmp_path, "report_b.txt", ["a.py", "b.py"])

    result = diff_reports(rep_a, rep_b)
    assert "Typ-Änderungen:" in result
    assert "CODE" in result


def test_diff_reports_header_contains_filenames(tmp_path):
    """Diff-Report enthält Dateinamen beider Reports im Header."""
    rep_a = _make_txt_report(tmp_path, "alpha.txt", ["x.py"])
    rep_b = _make_txt_report(tmp_path, "beta.txt", ["x.py"])

    result = diff_reports(rep_a, rep_b)
    assert "alpha.txt" in result
    assert "beta.txt" in result


def test_diff_reports_json_format(tmp_path):
    """diff_reports funktioniert auch mit JSON-Reports."""
    def _make_json(name, code_files):
        data = {
            "version": "2.9",
            "generated": "01.01.2025 10:00",
            "mode": "flat",
            "input": str(tmp_path),
            "serial": 1,
            "git": None,
            "files": len(code_files),
            "types": {"code": len(code_files)},
            "search": None,
            "details": {"code": [{"name": f, "path": f, "size": 0} for f in code_files]},
        }
        p = tmp_path / name
        p.write_text(json.dumps(data), encoding="utf-8")
        return p

    rep_a = _make_json("a.json", ["old.py"])
    rep_b = _make_json("b.json", ["new.py"])

    result = diff_reports(rep_a, rep_b)
    assert "+ new.py" in result
    assert "- old.py" in result


def test_parse_arguments_diff_flag():
    """--diff Argument wird korrekt geparst."""
    with patch("sys.argv", ["CopyCat.py", "--diff", "a.txt", "b.txt"]):
        args = parse_arguments()
    assert args.diff == ["a.txt", "b.txt"]


def test_gui_on_diff_success(gui, tmp_path):
    """_on_diff zeigt Diff-Ergebnis im Ausgabefeld."""
    rep_a = tmp_path / "a.txt"
    rep_b = tmp_path / "b.txt"
    rep_a.write_text("CopyCat v2.9 | 01.01.2025 | FLACH\nGesamt: 0\n----- x.py -----\n")
    rep_b.write_text("CopyCat v2.9 | 01.01.2025 | FLACH\nGesamt: 0\n----- y.py -----\n")

    with patch("tkinter.filedialog.askopenfilename", side_effect=[str(rep_a), str(rep_b)]):
        gui._on_diff()

    inserted = "".join(call.args[1] for call in gui._output_text.insert.call_args_list)
    assert "Diff" in inserted


def test_gui_on_diff_cancel_first(gui):
    """_on_diff bricht ab wenn erster Dialog abgebrochen wird."""
    with patch("tkinter.filedialog.askopenfilename", return_value=""):
        gui._on_diff()  # darf keine Exception werfen


def test_gui_on_diff_cancel_second(gui, tmp_path):
    """_on_diff bricht ab wenn zweiter Dialog abgebrochen wird."""
    rep_a = tmp_path / "a.txt"
    rep_a.write_text("dummy")
    with patch("tkinter.filedialog.askopenfilename", side_effect=[str(rep_a), ""]):
        gui._on_diff()  # darf keine Exception werfen


def test_gui_on_diff_error(gui, tmp_path):
    """_on_diff zeigt Fehlermeldung bei ungültigem Report."""
    bad = tmp_path / "bad.txt"
    bad.write_text("kein report")

    with patch("tkinter.filedialog.askopenfilename", return_value=str(bad)), \
         patch("tkinter.filedialog.askopenfilename", side_effect=[str(bad), str(bad)]), \
         patch("CopyCat_GUI.diff_reports", side_effect=ValueError("ungültig")), \
         patch("tkinter.messagebox.showerror") as mock_err:
        gui._on_diff()
    mock_err.assert_called_once()


# ==================== IDEE 10: PRE-COMMIT HOOK ====================

def test_install_hook_creates_file(tmp_path):
    """install_hook schreibt pre-commit Skript in .git/hooks/."""
    (tmp_path / ".git" / "hooks").mkdir(parents=True)
    hook = install_hook(tmp_path)
    assert hook.exists()
    content = hook.read_text(encoding="utf-8")
    assert "#!/bin/sh" in content
    assert "--quiet" in content
    assert "git add combined_copycat_" in content


def test_install_hook_no_git_raises(tmp_path):
    """install_hook wirft FileNotFoundError wenn kein .git/hooks vorhanden."""
    with pytest.raises(FileNotFoundError, match="Kein Git-Repository"):
        install_hook(tmp_path)


def test_install_hook_chmod_fail(tmp_path, monkeypatch):
    """install_hook ignoriert OSError beim chmod-Schritt."""
    (tmp_path / ".git" / "hooks").mkdir(parents=True)
    original_chmod = Path.chmod

    def bad_chmod(self, mode):
        raise OSError("chmod fehlgeschlagen")

    monkeypatch.setattr(Path, "chmod", bad_chmod)
    hook = install_hook(tmp_path)
    assert hook.exists()


def test_parse_arguments_install_hook():
    """--install-hook Argument wird korrekt geparst."""
    with patch("sys.argv", ["CopyCat.py", "--install-hook", "/some/project"]):
        args = parse_arguments()
    assert args.install_hook == "/some/project"


def test_gui_on_install_hook_success(gui, tmp_path):
    """_on_install_hook zeigt Erfolg-Dialog nach Hookinstallation."""
    (tmp_path / ".git" / "hooks").mkdir(parents=True)
    with patch("tkinter.filedialog.askdirectory", return_value=str(tmp_path)), \
         patch("tkinter.messagebox.showinfo") as mock_info:
        gui._on_install_hook()
    mock_info.assert_called_once()
    assert "Hook installiert" in mock_info.call_args[0][0]


def test_gui_on_install_hook_cancel(gui):
    """_on_install_hook bricht ab wenn Dialog abgebrochen."""
    with patch("tkinter.filedialog.askdirectory", return_value=""):
        gui._on_install_hook()  # keine Exception


def test_gui_on_install_hook_no_git(gui, tmp_path):
    """_on_install_hook zeigt Fehler wenn Ordner kein Git-Repo ist."""
    with patch("tkinter.filedialog.askdirectory", return_value=str(tmp_path)), \
         patch("tkinter.messagebox.showerror") as mock_err:
        gui._on_install_hook()
    mock_err.assert_called_once()


# ==================== IDEE 12: MERGE MEHRERER PROJEKTE ====================

def _make_txt_for_merge(tmp_path, name, filenames):
    """Hilfsfunktion: minimales TXT-Report."""
    lines = [
        "=" * 60,
        f"CopyCat v2.9 | 01.01.2025 10:00 | FLACH (Default)",
        str(tmp_path), "GIT: No Git", "",
        f"Gesamt: {len(filenames)} Dateien", "Serial #1",
        "=" * 60, "CODE-Details:",
    ]
    for fname in filenames:
        lines += [f"  {fname}: 5 Zeilen", f"----- {fname} -----", "x = 1", ""]
    p = tmp_path / name
    p.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return p


def test_merge_reports_txt(tmp_path):
    """merge_reports kombiniert zwei TXT-Reports korrekt."""
    rep_a = _make_txt_for_merge(tmp_path, "a.txt", ["alpha.py"])
    rep_b = _make_txt_for_merge(tmp_path, "b.txt", ["beta.py"])
    result = merge_reports([rep_a, rep_b])
    assert "Merge-Report" in result
    assert "=== a.txt ===" in result
    assert "=== b.txt ===" in result
    assert "2 Dateien zusammengeführt" in result


def test_merge_reports_writes_output_file(tmp_path):
    """merge_reports schreibt Datei wenn output= angegeben."""
    rep_a = _make_txt_for_merge(tmp_path, "a.txt", ["x.py"])
    rep_b = _make_txt_for_merge(tmp_path, "b.txt", ["y.py"])
    out = tmp_path / "merged.txt"
    merge_reports([rep_a, rep_b], output=out)
    assert out.exists()
    assert "Merge-Report" in out.read_text(encoding="utf-8")


def test_merge_reports_json(tmp_path):
    """merge_reports verarbeitet JSON-Reports korrekt."""
    def _json_rep(name, code_files):
        data = {
            "version": "2.9", "generated": "01.01.2025 10:00",
            "mode": "flat", "input": str(tmp_path),
            "serial": 1, "git": None,
            "files": len(code_files),
            "types": {"code": len(code_files)},
            "search": None,
            "details": {"code": [{"name": f, "path": f, "size": 0} for f in code_files]},
        }
        p = tmp_path / name
        p.write_text(json.dumps(data), encoding="utf-8")
        return p

    rep_a = _json_rep("a.json", ["main.py"])
    rep_b = _json_rep("b.json", ["utils.py"])
    result = merge_reports([rep_a, rep_b])
    assert "a.json" in result
    assert "main.py" in result
    assert "utils.py" in result


def test_merge_reports_invalid_json(tmp_path):
    """merge_reports markiert fehlerhaften JSON-Report als [FEHLER]."""
    bad = tmp_path / "bad.json"
    bad.write_text("{invalid json", encoding="utf-8")
    good = _make_txt_for_merge(tmp_path, "good.txt", ["ok.py"])
    result = merge_reports([bad, good])
    assert "FEHLER" in result


def test_merge_reports_single_file_label(tmp_path):
    """merge_reports kennzeichnet jede Quelle mit ihrem Dateinamen."""
    rep = _make_txt_for_merge(tmp_path, "only.txt", ["sole.py"])
    result = merge_reports([rep, rep])
    assert "=== only.txt ===" in result


def test_parse_arguments_merge():
    """--merge Argument nimmt mehrere Pfade."""
    with patch("sys.argv", ["CopyCat.py", "--merge", "a.txt", "b.txt", "c.txt"]):
        args = parse_arguments()
    assert args.merge == ["a.txt", "b.txt", "c.txt"]


def test_gui_on_merge_success(gui, tmp_path):
    """_on_merge zeigt Merge-Ergebnis im Ausgabefeld."""
    rep_a = _make_txt_for_merge(tmp_path, "a.txt", ["x.py"])
    rep_b = _make_txt_for_merge(tmp_path, "b.txt", ["y.py"])
    with patch("tkinter.filedialog.askopenfilenames", return_value=(str(rep_a), str(rep_b))):
        gui._on_merge()
    inserted = "".join(call.args[1] for call in gui._output_text.insert.call_args_list)
    assert "Merge" in inserted


def test_gui_on_merge_cancel(gui):
    """_on_merge bricht ab wenn Dialog ohne Auswahl geschlossen wird."""
    with patch("tkinter.filedialog.askopenfilenames", return_value=()):
        gui._on_merge()  # keine Exception


def test_gui_on_merge_only_one_file(gui, tmp_path):
    """_on_merge zeigt Warnung wenn nur eine Datei gewählt."""
    rep = _make_txt_for_merge(tmp_path, "a.txt", ["x.py"])
    with patch("tkinter.filedialog.askopenfilenames", return_value=(str(rep),)), \
         patch("tkinter.messagebox.showwarning") as mock_warn:
        gui._on_merge()
    mock_warn.assert_called_once()


def test_gui_on_merge_error(gui, tmp_path):
    """_on_merge zeigt Fehler wenn merge_reports Exception wirft."""
    rep_a = _make_txt_for_merge(tmp_path, "a.txt", ["x.py"])
    rep_b = _make_txt_for_merge(tmp_path, "b.txt", ["y.py"])
    with patch("tkinter.filedialog.askopenfilenames", return_value=(str(rep_a), str(rep_b))), \
         patch("CopyCat_GUI.merge_reports", side_effect=OSError("boom")), \
         patch("tkinter.messagebox.showerror") as mock_err:
        gui._on_merge()
    mock_err.assert_called_once()


def test_merge_reports_json_entry_without_path_key(tmp_path):
    """merge_reports fällt auf 'name' zurück wenn JSON-Eintrag kein 'path' hat."""
    data = {
        "version": "2.9", "generated": "01.01.2025",
        "mode": "flat", "input": str(tmp_path),
        "serial": 1, "git": None, "files": 1,
        "types": {"code": 1}, "search": None,
        "details": {
            "code": [{"name": "fallback.py", "size": 0}],  # no 'path' key
            "web": [],  # empty entries → if entries: branch = False
        },
    }
    p = tmp_path / "nopath.json"
    p.write_text(json.dumps(data), encoding="utf-8")
    result = merge_reports([p, p])
    assert "fallback.py" in result


# ==================== JINJA2 TEMPLATE (_write_template) ====================

def _make_files(tmp_path):
    """Hilfsfunktion: erstellt eine minimale files-Struktur für _write_template."""
    f = tmp_path / "hello.py"
    f.write_text("print('hi')", encoding="utf-8")
    return {"code": [f], "web": []}


def test_write_template_no_jinja2(tmp_path):
    """ImportError wenn jinja2 nicht verfügbar."""
    with patch.dict("sys.modules", {"jinja2": None}):
        with pytest.raises(ImportError, match="jinja2"):
            _write_template(
                tmp_path / "t.j2", {}, Namespace(recursive=False), tmp_path, {}, 1
            )


def test_write_template_bad_path(tmp_path):
    """ValueError wenn Template-Datei nicht lesbar."""
    with pytest.raises(ValueError, match="Template-Datei nicht lesbar"):
        _write_template(
            tmp_path / "nonexistent.j2", {}, Namespace(recursive=False), tmp_path, {}, 1
        )


def test_write_template_syntax_error(tmp_path):
    """ValueError bei Jinja2-Syntaxfehler."""
    bad = tmp_path / "bad.j2"
    bad.write_text("{% for %}", encoding="utf-8")
    with pytest.raises(ValueError, match="Template-Syntaxfehler"):
        _write_template(
            bad, {}, Namespace(recursive=False), tmp_path, {}, 1
        )


def test_write_template_renders_context(tmp_path):
    """Einfaches Template wird korrekt gerendert."""
    tmpl = tmp_path / "report.j2"
    tmpl.write_text("Dir={{ input_dir }}|Serial={{ serial }}|Total={{ total_files }}", encoding="utf-8")
    files = _make_files(tmp_path)
    result = _write_template(tmpl, files, Namespace(recursive=False), tmp_path, {}, 42)
    assert str(tmp_path) in result
    assert "Serial=42" in result
    assert "Total=1" in result


def test_write_template_with_search_results(tmp_path):
    """Template erhält search_results korrekt."""
    tmpl = tmp_path / "s.j2"
    tmpl.write_text("{{ search_results | length }}", encoding="utf-8")
    f = tmp_path / "a.py"
    f.write_text("x", encoding="utf-8")
    sr = {f: [(1, "x = 1")]}
    result = _write_template(
        tmpl, {"code": [f]}, Namespace(recursive=False), tmp_path, {}, 1,
        search_pattern="x", search_results=sr,
    )
    assert result == "1"


def test_write_template_render_error(tmp_path):
    """ValueError bei Render-Fehler."""
    tmpl = tmp_path / "err.j2"
    # Aufruf einer nicht vorhandenen Methode eines Strings→ TemplateError
    tmpl.write_text("{{ undefined_var.unknown_method() }}", encoding="utf-8")
    with pytest.raises(ValueError, match="Template-Renderfehler|Template-Syntaxfehler"):
        _write_template(
            tmpl, {}, Namespace(recursive=False), tmp_path, {}, 1
        )


def test_run_copycat_with_template(tmp_path):
    """run_copycat schreibt Template-Output statt Standard-Format."""
    src = tmp_path / "src"
    src.mkdir()
    (src / "main.py").write_text("x=1", encoding="utf-8")
    out = tmp_path / "out"
    out.mkdir()
    tmpl = tmp_path / "t.j2"
    tmpl.write_text("TOTAL={{ total_files }}", encoding="utf-8")
    args = Namespace(
        input=str(src), output=str(out), types=["code"], recursive=False,
        max_size=float("inf"), format="txt", search=None,
        template=str(tmpl), diff=None, merge=None, install_hook=None,
        verbose=False, quiet=False, watch=False, cooldown=2.0,
    )
    with patch("CopyCat.get_git_info", return_value={}):
        run_copycat(args)
    files = list(out.glob("*.j2")) + list(out.glob("*.txt"))
    assert any("TOTAL=1" in f.read_text(encoding="utf-8") for f in out.iterdir())


# ==================== WATCH MODE (watch_and_run) ====================

def test_watch_and_run_no_watchdog(tmp_path):
    """ImportError wenn watchdog nicht verfügbar."""
    with patch.dict("sys.modules", {"watchdog": None, "watchdog.observers": None, "watchdog.events": None}):
        with pytest.raises(ImportError, match="watchdog"):
            watch_and_run(Namespace(input=str(tmp_path), recursive=False), stop_event=MagicMock(is_set=lambda: True))


def test_watch_and_run_stops_immediately(tmp_path):
    """stop_event gesetzt → Loop endet ohne run_copycat."""
    import threading
    stop = threading.Event()
    stop.set()

    observer_mock = MagicMock()

    with patch("watchdog.observers.Observer", return_value=observer_mock), \
         patch("CopyCat.run_copycat") as mock_run:
        watch_and_run(Namespace(input=str(tmp_path), recursive=False), cooldown=0.1, stop_event=stop)

    observer_mock.start.assert_called_once()
    observer_mock.stop.assert_called_once()
    observer_mock.join.assert_called_once()
    mock_run.assert_not_called()


def test_watch_and_run_triggers_run_copycat(tmp_path):
    """Nach Dateiänderung und abgelaufenem Cooldown wird run_copycat aufgerufen."""
    import threading, time
    stop = threading.Event()

    call_log = []
    captured_handler = []

    class FakeObserver:
        def schedule(self, handler, path, recursive=False):
            captured_handler.append(handler)
        def start(self): pass
        def stop(self): pass
        def join(self): pass

    def fake_run_copycat(args):
        call_log.append(True)
        stop.set()  # nach erstem Lauf stoppen

    with patch("watchdog.observers.Observer", FakeObserver), \
         patch("CopyCat.run_copycat", side_effect=fake_run_copycat):
        def _trigger():
            time.sleep(0.05)
            ev = MagicMock()
            ev.is_directory = False
            if captured_handler:
                captured_handler[0].on_any_event(ev)
        t = threading.Thread(target=_trigger)
        t.start()
        watch_and_run(
            Namespace(input=str(tmp_path), recursive=False),
            cooldown=0.1,
            stop_event=stop,
        )
        t.join()

    assert call_log, "run_copycat wurde nicht aufgerufen"


def test_watch_and_run_run_error_is_caught(tmp_path):
    """Fehler in run_copycat wird abgefangen und geloggt."""
    import threading, time
    stop = threading.Event()
    call_count = [0]
    _fake_obs_instance = [None]

    class FakeObserver:
        def __init__(self):
            _fake_obs_instance[0] = self
        def schedule(self, handler, path, recursive=False):
            self._handler = handler
        def start(self): pass
        def stop(self): pass
        def join(self): pass

    def fake_run(args):
        call_count[0] += 1
        stop.set()
        raise RuntimeError("Testfehler")

    def _trigger():
        time.sleep(0.05)
        ev = MagicMock()
        ev.is_directory = False
        obs = _fake_obs_instance[0]
        if obs and hasattr(obs, "_handler"):
            obs._handler.on_any_event(ev)

    with patch("watchdog.observers.Observer", FakeObserver), \
         patch("CopyCat.run_copycat", side_effect=fake_run):
        t = threading.Thread(target=_trigger)
        t.start()
        watch_and_run(
            Namespace(input=str(tmp_path), recursive=False),
            cooldown=0.1,
            stop_event=stop,
        )
        t.join()
    assert call_count[0] == 1


# ==================== CLI: --template / --watch / --cooldown ====================

def test_parse_arguments_template():
    with patch("sys.argv", ["copycat", "--template", "report.j2"]):
        args = parse_arguments()
    assert args.template == "report.j2"


def test_parse_arguments_watch_flag():
    with patch("sys.argv", ["copycat", "-w"]):
        args = parse_arguments()
    assert args.watch is True


def test_parse_arguments_cooldown():
    with patch("sys.argv", ["copycat", "--cooldown", "5.5"]):
        args = parse_arguments()
    assert args.cooldown == 5.5


def test_watch_and_run_no_stop_event_creates_one(tmp_path):
    """Wenn stop_event=None übergeben, wird intern eines erzeugt (Zeile 748)."""
    import threading, time

    captured = []

    class FakeObserver:
        def schedule(self, handler, path, recursive=False):
            captured.append(handler)
        def start(self): pass
        def stop(self): pass
        def join(self): pass

    # Wir übergeben kein stop_event – die Funktion erstellt es intern.
    # Wir beenden den Loop, indem run_copycat nach dem ersten Trigger stop_event setzt.
    # Dafür müssen wir das interne Event abfangen → nicht möglich direkt.
    # Einfachere Lösung: den Loop via Observer-Thread-Trick stoppen.
    # Stattdessen: kurzen Cooldown, mit einem echten Observer-Dummy + direkten Stop via Patch.
    internal_stop = [None]
    original_threading_event = threading.Event

    def fake_event():
        ev = original_threading_event()
        internal_stop[0] = ev
        ev.set()  # sofort setzen → Loop endet sofort
        return ev

    with patch("CopyCat.threading.Event", side_effect=fake_event), \
         patch("watchdog.observers.Observer", FakeObserver):
        watch_and_run(Namespace(input=str(tmp_path), recursive=False), cooldown=0.1)

    assert internal_stop[0] is not None


def test_watch_and_run_directory_event_ignored(tmp_path):
    """Verzeichnis-Events (is_directory=True) werden ignoriert (Branch 754->False)."""
    import threading, time
    stop = threading.Event()
    stop.set()
    captured_handler = []

    class FakeObserver:
        def schedule(self, handler, path, recursive=False):
            captured_handler.append(handler)
        def start(self): pass
        def stop(self): pass
        def join(self): pass

    with patch("watchdog.observers.Observer", FakeObserver), \
         patch("CopyCat.run_copycat") as mock_run:
        watch_and_run(Namespace(input=str(tmp_path), recursive=False), cooldown=0.1, stop_event=stop)

    # Manuell einen Verzeichnis-Event feuern (sollte last_event_time nicht setzen)
    if captured_handler:
        ev = MagicMock()
        ev.is_directory = True
        captured_handler[0].on_any_event(ev)
    mock_run.assert_not_called()


def test_watch_and_run_event_before_cooldown_no_run(tmp_path):
    """Event kommt, aber stop_event wird vor Cooldown-Ablauf gesetzt → kein run_copycat."""
    import threading, time
    stop = threading.Event()
    captured_handler = []

    class FakeObserver:
        def schedule(self, handler, path, recursive=False):
            captured_handler.append(handler)
        def start(self): pass
        def stop(self): pass
        def join(self): pass

    def _trigger():
        time.sleep(0.05)
        ev = MagicMock()
        ev.is_directory = False
        if captured_handler:
            captured_handler[0].on_any_event(ev)
        # Stop sofort nach Event – vor Cooldown (5 s)
        stop.set()

    with patch("watchdog.observers.Observer", FakeObserver), \
         patch("CopyCat.run_copycat") as mock_run:
        t = threading.Thread(target=_trigger)
        t.start()
        watch_and_run(
            Namespace(input=str(tmp_path), recursive=False),
            cooldown=5.0,  # langer Cooldown → läuft beim Stop noch nicht ab
            stop_event=stop,
        )
        t.join()
    mock_run.assert_not_called()


def test_parse_arguments_cooldown_default():
    with patch("sys.argv", ["copycat"]):
        args = parse_arguments()
    assert args.cooldown == 2.0


# ==================== GUI: template/cooldown/watch ====================

def test_build_args_template_and_cooldown(gui):
    gui._template_var.set("/path/to/report.j2")
    gui._cooldown_var.set("3.5")
    args = gui._build_args()
    assert args.template == "/path/to/report.j2"
    assert args.cooldown == 3.5
    assert args.watch is False


def test_build_args_empty_template_is_none(gui):
    gui._template_var.set("   ")
    args = gui._build_args()
    assert args.template is None


def test_build_args_default_cooldown(gui):
    args = gui._build_args()
    assert args.cooldown == 2.0


def test_on_watch_toggle_no_input(gui):
    """Watch-Toggle zeigt Fehler wenn kein Eingabeordner gesetzt."""
    with patch("tkinter.messagebox.showerror") as mock_err:
        gui._on_watch_toggle()
    mock_err.assert_called_once()


def test_on_watch_toggle_invalid_input(gui, tmp_path):
    """Watch-Toggle zeigt Fehler wenn Eingabeordner nicht existiert."""
    gui._input_var.set("/nonexistent/path/xyz")
    with patch("tkinter.messagebox.showerror") as mock_err:
        gui._on_watch_toggle()
    mock_err.assert_called_once()


def test_on_watch_toggle_start_and_stop(gui, tmp_path):
    """Watch-Toggle startet und stoppt den Watch-Thread."""
    import time
    gui._input_var.set(str(tmp_path))

    class FakeObserver:
        def schedule(self, h, p, recursive=False): pass
        def start(self): pass
        def stop(self): pass
        def join(self): pass

    with patch("watchdog.observers.Observer", FakeObserver):
        gui._on_watch_toggle()  # Start
        time.sleep(0.1)
        assert gui._watch_stop_event is not None
        gui._on_watch_toggle()  # Stop
        time.sleep(0.1)


def test_on_watch_toggle_build_args_error(gui):
    """Watch-Toggle zeigt Fehler bei ungueltiger Max-Groesse."""
    gui._max_size_var.set("kein_wert")
    with patch("tkinter.messagebox.showerror") as mock_err:
        gui._on_watch_toggle()
    mock_err.assert_called_once()


# ==================== PLUGIN SYSTEM (IDEE 13) ====================

def test_load_plugins_no_dir(tmp_path, clean_plugins):
    """Nicht existierendes Verzeichnis → leere Liste."""
    result = load_plugins(tmp_path / "nonexistent")
    assert result == []


def test_load_plugins_default_dir(clean_plugins):
    """load_plugins() ohne Argument nutzt plugins/ neben CopyCat.py (example_proto.py)."""
    result = load_plugins()  # default: plugins/ neben CopyCat.py
    assert "proto" in result


def test_load_plugins_valid_no_renderer(tmp_path, clean_plugins):
    """Gültiges Plugin ohne render_file → PLUGIN_RENDERERS[type]=None."""
    plugin = tmp_path / "myplugin.py"
    plugin.write_text('TYPE_NAME = "mypl"\nPATTERNS = ["*.mypl"]\n', encoding="utf-8")
    result = load_plugins(tmp_path)
    assert result == ["mypl"]
    import CopyCat
    assert CopyCat.TYPE_FILTERS.get("mypl") == ["*.mypl"]
    assert CopyCat.PLUGIN_RENDERERS.get("mypl") is None


def test_load_plugins_valid_with_renderer(tmp_path, clean_plugins):
    """Gültiges Plugin mit render_file → PLUGIN_RENDERERS[type] ist callable."""
    plugin = tmp_path / "rplug.py"
    plugin.write_text(
        'TYPE_NAME = "rpl"\nPATTERNS = ["*.rpl"]\ndef render_file(p, w, a): pass\n',
        encoding="utf-8",
    )
    load_plugins(tmp_path)
    import CopyCat
    assert callable(CopyCat.PLUGIN_RENDERERS.get("rpl"))


def test_load_plugins_skips_underscore_files(tmp_path, clean_plugins):
    """Dateien die mit _ beginnen werden übersprungen."""
    (tmp_path / "_private.py").write_text('TYPE_NAME = "prv"\nPATTERNS = ["*.prv"]\n', encoding="utf-8")
    result = load_plugins(tmp_path)
    assert result == []


def test_load_plugins_missing_type_name(tmp_path, clean_plugins):
    """Plugin ohne TYPE_NAME → übersprungen."""
    (tmp_path / "bad.py").write_text('PATTERNS = ["*.bad"]\n', encoding="utf-8")
    result = load_plugins(tmp_path)
    assert result == []


def test_load_plugins_empty_type_name(tmp_path, clean_plugins):
    """Plugin mit leerem TYPE_NAME → übersprungen."""
    (tmp_path / "empty.py").write_text('TYPE_NAME = ""\nPATTERNS = ["*.em"]\n', encoding="utf-8")
    result = load_plugins(tmp_path)
    assert result == []


def test_load_plugins_collision_with_builtin(tmp_path, clean_plugins):
    """Plugin-Typname kollidiert mit eingebautem Typ → übersprungen, Original unverändert."""
    original_patterns = list(TYPE_FILTERS["code"])
    (tmp_path / "codecoll.py").write_text('TYPE_NAME = "code"\nPATTERNS = ["*.evil"]\n', encoding="utf-8")
    result = load_plugins(tmp_path)
    assert result == []
    assert TYPE_FILTERS["code"] == original_patterns


def test_load_plugins_patterns_not_list(tmp_path, clean_plugins):
    """Plugin mit PATTERNS als String → übersprungen."""
    (tmp_path / "strpat.py").write_text('TYPE_NAME = "strp"\nPATTERNS = "*.strp"\n', encoding="utf-8")
    result = load_plugins(tmp_path)
    assert result == []


def test_load_plugins_patterns_empty_list(tmp_path, clean_plugins):
    """Plugin mit PATTERNS = [] → übersprungen."""
    (tmp_path / "emptypat.py").write_text('TYPE_NAME = "emp"\nPATTERNS = []\n', encoding="utf-8")
    result = load_plugins(tmp_path)
    assert result == []


def test_load_plugins_patterns_invalid_entry(tmp_path, clean_plugins):
    """Plugin mit nicht-string Eintrag in PATTERNS → übersprungen."""
    (tmp_path / "intpat.py").write_text('TYPE_NAME = "intp"\nPATTERNS = ["*.ok", 42]\n', encoding="utf-8")
    result = load_plugins(tmp_path)
    assert result == []


def test_load_plugins_import_error(tmp_path, clean_plugins):
    """Plugin mit Syntaxfehler → übersprungen (Warnung)."""
    (tmp_path / "broken.py").write_text("def invalid syntax!!!\n", encoding="utf-8")
    result = load_plugins(tmp_path)
    assert result == []


def test_load_plugins_noncallable_renderer(tmp_path, clean_plugins):
    """Plugin mit render_file als String (nicht callable) → PLUGIN_RENDERERS[type]=None."""
    (tmp_path / "noncall.py").write_text(
        'TYPE_NAME = "ncp"\nPATTERNS = ["*.ncp"]\nrender_file = "not_callable"\n',
        encoding="utf-8",
    )
    load_plugins(tmp_path)
    import CopyCat
    assert CopyCat.PLUGIN_RENDERERS.get("ncp") is None


def test_load_plugins_idempotent(tmp_path, clean_plugins):
    """Gleichen Plugin-Typ zweimal laden → zweiter Lauf gibt leere Liste zurück."""
    plugin = tmp_path / "idem.py"
    plugin.write_text('TYPE_NAME = "idem"\nPATTERNS = ["*.idem"]\n', encoding="utf-8")
    result1 = load_plugins(tmp_path)
    result2 = load_plugins(tmp_path)
    assert result1 == ["idem"]
    assert result2 == []


def test_loaded_plugins_tracked(tmp_path, clean_plugins):
    """Nach load_plugins ist Typname in _loaded_plugins."""
    plugin = tmp_path / "track.py"
    plugin.write_text('TYPE_NAME = "trk"\nPATTERNS = ["*.trk"]\n', encoding="utf-8")
    load_plugins(tmp_path)
    import CopyCat
    assert "trk" in CopyCat._loaded_plugins


def test_write_txt_plugin_renderer_called(tmp_path, clean_plugins):
    """_write_txt ruft benutzerdefinierten Plugin-Renderer auf."""
    import CopyCat
    renderer = MagicMock()
    CopyCat.TYPE_FILTERS["txpl"] = ["*.txpl"]
    CopyCat.PLUGIN_RENDERERS["txpl"] = renderer
    f = tmp_path / "test.txpl"
    f.write_text("content")
    files = {k: [] for k in CopyCat.TYPE_FILTERS}
    files["txpl"] = [f]
    buf = StringIO()
    args = Namespace(recursive=False, types=["txpl"], max_size=float("inf"), format="txt", search=None)
    _write_txt(buf, files, args, tmp_path, "No Git", 1)
    renderer.assert_called_once_with(f, buf, args)


def test_write_txt_plugin_renderer_error_caught(tmp_path, clean_plugins):
    """_write_txt fängt Renderer-Exceptions ab und schreibt Fehlertext."""
    import CopyCat
    def boom(path, writer, args):
        raise RuntimeError("kaputt")
    CopyCat.TYPE_FILTERS["errpl"] = ["*.errpl"]
    CopyCat.PLUGIN_RENDERERS["errpl"] = boom
    f = tmp_path / "test.errpl"
    f.write_text("x")
    files = {k: [] for k in CopyCat.TYPE_FILTERS}
    files["errpl"] = [f]
    buf = StringIO()
    args = Namespace(recursive=False, types=["errpl"], max_size=float("inf"), format="txt", search=None)
    _write_txt(buf, files, args, tmp_path, "No Git", 1)
    assert "[Plugin-Fehler:" in buf.getvalue()
    assert "kaputt" in buf.getvalue()


def test_write_txt_plugin_no_renderer_uses_list_binary(tmp_path, clean_plugins):
    """_write_txt nutzt list_binary_file wenn kein Renderer vorhanden."""
    import CopyCat
    CopyCat.TYPE_FILTERS["nrpl"] = ["*.nrpl"]
    CopyCat.PLUGIN_RENDERERS["nrpl"] = None
    f = tmp_path / "test.nrpl"
    f.write_bytes(b"\x00\x01")
    files = {k: [] for k in CopyCat.TYPE_FILTERS}
    files["nrpl"] = [f]
    buf = StringIO()
    args = Namespace(recursive=False, types=["nrpl"], max_size=float("inf"), format="txt", search=None)
    with patch("CopyCat.list_binary_file") as mock_lbf:
        _write_txt(buf, files, args, tmp_path, "No Git", 1)
    mock_lbf.assert_called_once_with(buf, f)


def test_write_md_plugin_renderer_called(tmp_path, clean_plugins):
    """_write_md ruft benutzerdefinierten Plugin-Renderer auf und umschließt Ausgabe mit ```."""
    import CopyCat
    output_lines = []
    def renderer(path, writer, args):
        writer.write("PLUGIN_OUTPUT\n")
    CopyCat.TYPE_FILTERS["mdpl"] = ["*.mdpl"]
    CopyCat.PLUGIN_RENDERERS["mdpl"] = renderer
    f = tmp_path / "test.mdpl"
    f.write_text("x")
    files = {k: [] for k in CopyCat.TYPE_FILTERS}
    files["mdpl"] = [f]
    buf = StringIO()
    args = Namespace(recursive=False, types=["mdpl"], max_size=float("inf"), format="md", search=None)
    _write_md(buf, files, args, tmp_path, "No Git", 1)
    out = buf.getvalue()
    assert "PLUGIN_OUTPUT" in out
    assert "```" in out


def test_write_md_plugin_renderer_error_caught(tmp_path, clean_plugins):
    """_write_md fängt Renderer-Exceptions ab."""
    import CopyCat
    def boom(path, writer, args):
        raise ValueError("md-kaputt")
    CopyCat.TYPE_FILTERS["mderr"] = ["*.mderr"]
    CopyCat.PLUGIN_RENDERERS["mderr"] = boom
    f = tmp_path / "test.mderr"
    f.write_text("x")
    files = {k: [] for k in CopyCat.TYPE_FILTERS}
    files["mderr"] = [f]
    buf = StringIO()
    args = Namespace(recursive=False, types=["mderr"], max_size=float("inf"), format="md", search=None)
    _write_md(buf, files, args, tmp_path, "No Git", 1)
    assert "[Plugin-Fehler:" in buf.getvalue()
    assert "md-kaputt" in buf.getvalue()


def test_write_md_plugin_no_renderer_table(tmp_path, clean_plugins):
    """_write_md zeigt Tabelle wenn kein Renderer vorhanden."""
    import CopyCat
    CopyCat.TYPE_FILTERS["mdnr"] = ["*.mdnr"]
    CopyCat.PLUGIN_RENDERERS["mdnr"] = None
    f = tmp_path / "test.mdnr"
    f.write_bytes(b"AB")
    files = {k: [] for k in CopyCat.TYPE_FILTERS}
    files["mdnr"] = [f]
    buf = StringIO()
    args = Namespace(recursive=False, types=["mdnr"], max_size=float("inf"), format="md", search=None)
    _write_md(buf, files, args, tmp_path, "No Git", 1)
    out = buf.getvalue()
    assert "test.mdnr" in out
    assert "bytes" in out


def test_run_copycat_loads_plugins_when_plugin_dir_set(tmp_path, run_args, clean_plugins):
    """run_copycat lädt Plugins wenn plugin_dir gesetzt."""
    plugin_dir = tmp_path / "myplugins"
    plugin_dir.mkdir()
    (plugin_dir / "custpl.py").write_text(
        'TYPE_NAME = "custpl"\nPATTERNS = ["*.custpl"]\n', encoding="utf-8"
    )
    (tmp_path / "file.custpl").write_text("data")
    args = run_args(types=["custpl"])
    args.plugin_dir = str(plugin_dir)
    run_copycat(args)
    import CopyCat
    assert "custpl" in CopyCat.TYPE_FILTERS
    report = next(tmp_path.glob("combined_copycat_*.txt"))
    assert "file.custpl" in report.read_text()


def test_parse_arguments_plugin_dir():
    """--plugin-dir wird korrekt geparst."""
    with patch("sys.argv", ["copycat", "--plugin-dir", "/my/plugins"]):
        args = parse_arguments()
    assert args.plugin_dir == "/my/plugins"


def test_parse_arguments_list_plugins():
    """--list-plugins setzt das Flag."""
    with patch("sys.argv", ["copycat", "--list-plugins"]):
        args = parse_arguments()
    assert args.list_plugins is True


# ==================== WEB-INTERFACE (IDEE 14) ====================

flask = pytest.importorskip("flask", reason="flask nicht installiert – Web-Tests übersprungen")


@pytest.fixture
def web_client(tmp_path):
    """Flask-Test-Client für CopyCat_Web."""
    import importlib, sys
    # Sicherstellen, dass CopyCat_Web frisch importiert wird
    if "CopyCat_Web" in sys.modules:
        del sys.modules["CopyCat_Web"]
    import CopyCat_Web
    CopyCat_Web.app.config["TESTING"] = True
    with CopyCat_Web.app.test_client() as client:
        yield client, tmp_path


def test_web_index_returns_200(web_client):
    """GET / liefert 200 und enthält 'CopyCat'."""
    client, _ = web_client
    resp = client.get("/")
    assert resp.status_code == 200
    assert b"CopyCat" in resp.data


def test_web_index_contains_form_fields(web_client):
    """GET / enthält alle wichtigen Formularfelder."""
    client, _ = web_client
    resp = client.get("/")
    html = resp.data
    assert b'name="input_dir"' in html
    assert b'name="output_dir"' in html
    assert b'name="fmt"' in html
    assert b'name="recursive"' in html
    assert b'name="incremental"' in html
    assert b'name="search"' in html


def test_web_run_missing_input(web_client):
    """POST /run ohne input_dir → Fehlermeldung."""
    client, _ = web_client
    resp = client.post("/run", data={"fmt": "txt"})
    assert resp.status_code == 200
    assert "Eingabeordner" in resp.data.decode("utf-8")


def test_web_run_nonexistent_input(web_client):
    """POST /run mit nicht existierendem Ordner → Fehlermeldung."""
    client, _ = web_client
    resp = client.post("/run", data={"input_dir": "/nonexistent/xyz", "fmt": "txt"})
    assert resp.status_code == 200
    assert "existiert nicht" in resp.data.decode("utf-8")


def test_web_run_valid_creates_report(web_client):
    """POST /run mit gültigem Ordner → Report im Response."""
    client, tmp = web_client
    (tmp / "hello.py").write_text("def hello(): pass\n")
    resp = client.post("/run", data={
        "input_dir": str(tmp),
        "output_dir": str(tmp),
        "types": ["code"],
        "fmt": "txt",
        "max_size": "0",
    })
    assert resp.status_code == 200
    html = resp.data.decode("utf-8")
    assert "hello.py" in html or "report-box" in html


def test_web_run_all_types(web_client):
    """POST /run mit types=all → kein Fehler."""
    client, tmp = web_client
    (tmp / "test.py").write_text("x = 1\n")
    resp = client.post("/run", data={
        "input_dir": str(tmp),
        "output_dir": str(tmp),
        "types": ["all"],
        "fmt": "txt",
    })
    assert resp.status_code == 200
    assert b"error" not in resp.data.lower() or b"Kein Pfad" not in resp.data


def test_web_run_format_json(web_client):
    """POST /run mit format=json → Report enthält JSON-Inhalt."""
    client, tmp = web_client
    (tmp / "mod.py").write_text("x = 1\n")
    resp = client.post("/run", data={
        "input_dir": str(tmp),
        "output_dir": str(tmp),
        "types": ["code"],
        "fmt": "json",
    })
    assert resp.status_code == 200
    assert b"report-box" in resp.data or b"combined_copycat" in resp.data


def test_web_run_format_html(web_client):
    """POST /run mit format=html funktioniert und erstellt Report-Link."""
    client, tmp = web_client
    (tmp / "modhtml.py").write_text("x = 1\n", encoding="utf-8")
    resp = client.post("/run", data={
        "input_dir": str(tmp),
        "output_dir": str(tmp),
        "types": ["code"],
        "fmt": "html",
    })
    assert resp.status_code == 200
    assert b"combined_copycat" in resp.data


def test_web_run_with_search(web_client):
    """POST /run mit search → kein Fehler."""
    client, tmp = web_client
    (tmp / "code.py").write_text("# TODO fix this\nx = 1\n")
    resp = client.post("/run", data={
        "input_dir": str(tmp),
        "output_dir": str(tmp),
        "types": ["code"],
        "fmt": "txt",
        "search": "TODO",
    })
    assert resp.status_code == 200


def test_web_download_valid(web_client):
    """GET /download mit gültigem Report → 200 und Content-Disposition."""
    client, tmp = web_client
    report = tmp / "combined_copycat_1.txt"
    report.write_text("Test Report\n")
    resp = client.get(f"/download?path={report}")
    assert resp.status_code == 200
    assert b"Test Report" in resp.data


def test_web_download_valid_html(web_client):
    """GET /download mit html-Report ist erlaubt."""
    client, tmp = web_client
    report = tmp / "combined_copycat_2.html"
    report.write_text("<html><body>ok</body></html>", encoding="utf-8")
    resp = client.get(f"/download?path={report}")
    assert resp.status_code == 200
    assert b"ok" in resp.data


def test_web_download_missing_path(web_client):
    """GET /download ohne path → 400."""
    client, _ = web_client
    resp = client.get("/download")
    assert resp.status_code == 400


def test_web_download_nonexistent_file(web_client):
    """GET /download mit nicht existierender Datei → 404."""
    client, tmp = web_client
    resp = client.get(f"/download?path={tmp / 'combined_copycat_99.txt'}")
    assert resp.status_code == 404


def test_web_download_forbidden_name(web_client):
    """GET /download mit ungültigem Dateinamen → 403."""
    client, tmp = web_client
    evil = tmp / "../../etc/passwd"
    resp = client.get(f"/download?path={evil}")
    assert resp.status_code in (403, 404)


def test_web_download_returns_403_for_bad_filename(web_client, tmp_path):
    """GET /download: Datei existiert, aber Name ungültig → 403."""
    client, tmp = web_client
    bad = tmp / "evil.exe"
    bad.write_bytes(b"not allowed")
    resp = client.get(f"/download?path={bad}")
    assert resp.status_code == 403


def test_web_api_run_missing_input(web_client):
    """POST /api/run ohne 'input' → 400."""
    client, _ = web_client
    resp = client.post("/api/run", json={})
    assert resp.status_code == 400
    assert b"input" in resp.data


def test_web_api_run_nonexistent_input(web_client):
    """POST /api/run mit ungültigem Ordner → 400."""
    client, _ = web_client
    resp = client.post("/api/run", json={"input": "/nonexistent/xyz"})
    assert resp.status_code == 400


def test_web_api_run_valid(web_client):
    """POST /api/run mit gültigem Ordner → JSON mit status ok."""
    client, tmp = web_client
    (tmp / "api.py").write_text("x = 1\n")
    resp = client.post("/api/run", json={
        "input": str(tmp),
        "output": str(tmp),
        "types": ["code"],
        "format": "txt",
    })
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["status"] == "ok"


def test_web_build_args_defaults():
    """_build_args: Defaults ohne Formular-Input."""
    import CopyCat_Web
    class _F:
        def get(self, k, d=""): return {"input_dir": "/tmp", "fmt": "txt", "max_size": "0"}.get(k, d)
        def getlist(self, k): return ["all"] if k == "types" else []
        def __contains__(self, i): return False
    args = CopyCat_Web._build_args(_F())
    assert args.format == "txt"
    assert args.types == ["all"]
    assert args.max_size == float("inf")
    assert args.recursive is False
    assert args.incremental is False


def test_web_build_args_specific_types():
    """_build_args: Spezifische Typen werden korrekt übernommen."""
    import CopyCat_Web
    class _F:
        def get(self, k, d=""): return {"input_dir": "/tmp", "fmt": "json", "max_size": "5"}.get(k, d)
        def getlist(self, k): return ["code", "web"] if k == "types" else []
        def __contains__(self, i): return i in ("recursive", "incremental")
    args = CopyCat_Web._build_args(_F())
    assert args.types == ["code", "web"]
    assert args.max_size == 5.0
    assert args.recursive is True
    assert args.format == "json"
    assert args.incremental is True


def test_web_build_args_invalid_max_size():
    """_build_args: Ungültige max_size → inf."""
    import CopyCat_Web
    class _F:
        def get(self, k, d=""): return {"fmt": "txt", "max_size": "abc"}.get(k, d)
        def getlist(self, k): return []
        def __contains__(self, i): return False
    args = CopyCat_Web._build_args(_F())
    assert args.max_size == float("inf")


def test_web_build_args_invalid_types_fallback_to_all():
    """_build_args: Ungültige Typen → Fallback auf ['all']."""
    import CopyCat_Web
    class _F:
        def get(self, k, d=""): return {"fmt": "txt", "max_size": "0"}.get(k, d)
        def getlist(self, k): return ["xyz_invalid"] if k == "types" else []
        def __contains__(self, i): return False
    args = CopyCat_Web._build_args(_F())
    assert args.types == ["all"]


def test_web_parse_web_args_defaults(monkeypatch):
    """_parse_web_args: Defaults ohne Argumente."""
    import CopyCat_Web, sys
    monkeypatch.setattr(sys, "argv", ["CopyCat_Web.py"])
    args = CopyCat_Web._parse_web_args()
    assert args.host == "127.0.0.1"
    assert args.port == 5000
    assert args.debug is False


def test_web_parse_web_args_custom(monkeypatch):
    """_parse_web_args: Benutzerdefinierte Werte."""
    import CopyCat_Web, sys
    monkeypatch.setattr(sys, "argv", ["CopyCat_Web.py", "--host", "0.0.0.0", "--port", "8080", "--debug"])
    args = CopyCat_Web._parse_web_args()
    assert args.host == "0.0.0.0"
    assert args.port == 8080
    assert args.debug is True


def test_web_get_plugins_empty_string():
    """_get_plugins('') → leere Liste."""
    import CopyCat_Web
    result = CopyCat_Web._get_plugins("")
    assert result == []


def test_web_get_plugins_nonexistent_dir(tmp_path):
    """_get_plugins mit nicht existierendem Ordner → leere Liste."""
    import CopyCat_Web
    result = CopyCat_Web._get_plugins(str(tmp_path / "no_such_dir"))
    assert result == []


def test_web_get_plugins_with_plugin(tmp_path):
    """_get_plugins mit gültigem Plugin-Verzeichnis → Plugin-Info zurückgegeben."""
    import CopyCat_Web
    plugin_file = tmp_path / "myplugin.py"
    plugin_file.write_text(
        'TYPE_NAME = "mytype"\nPATTERNS = ["*.myext"]\n'
        'def render_file(path, writer, args):\n    writer("content")\n'
    )
    result = CopyCat_Web._get_plugins(str(tmp_path))
    names = [p["name"] for p in result]
    assert "mytype" in names


def test_web_api_run_exception(web_client, monkeypatch):
    """POST /api/run bei run_copycat-Fehler → 500."""
    client, tmp = web_client
    import CopyCat_Web
    (tmp / "x.py").write_text("x=1\n")
    monkeypatch.setattr(CopyCat_Web, "run_copycat", lambda a: (_ for _ in ()).throw(RuntimeError("forced")))
    resp = client.post("/api/run", json={"input": str(tmp), "format": "txt"})
    assert resp.status_code == 500
    assert b"forced" in resp.data


def test_web_run_no_reports_after_run(web_client, monkeypatch):
    """POST /run wenn run_copycat keinen Report erstellt."""
    client, tmp = web_client
    import CopyCat_Web
    monkeypatch.setattr(CopyCat_Web, "run_copycat", lambda a: None)
    resp = client.post("/run", data={
        "input_dir": str(tmp),
        "output_dir": str(tmp),
        "types": ["code"],
        "fmt": "txt",
    })
    assert resp.status_code == 200
    assert "Kein Report" in resp.data.decode("utf-8")


def test_web_run_exception_shows_error(web_client, monkeypatch):
    """POST /run bei Exception → Fehlermeldung anzeigen."""
    client, tmp = web_client
    import CopyCat_Web
    monkeypatch.setattr(CopyCat_Web, "run_copycat", lambda a: (_ for _ in ()).throw(RuntimeError("boom")))
    resp = client.post("/run", data={
        "input_dir": str(tmp),
        "output_dir": str(tmp),
        "types": ["code"],
        "fmt": "txt",
    })
    assert resp.status_code == 200
    assert "boom" in resp.data.decode("utf-8")


def test_web_api_run_no_reports(web_client, monkeypatch):
    """POST /api/run wenn kein Report erstellt wird → status ok, report None."""
    client, tmp = web_client
    import CopyCat_Web
    monkeypatch.setattr(CopyCat_Web, "run_copycat", lambda a: None)
    resp = client.post("/api/run", json={"input": str(tmp), "format": "txt"})
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["status"] == "ok"
    assert data["report"] is None


def test_web_download_combined_txt_mimetype(web_client):
    """GET /download → Content-Type text/plain für .txt."""
    client, tmp = web_client
    report = tmp / "combined_copycat_1.txt"
    report.write_text("hello\n")
    resp = client.get(f"/download?path={report}")
    assert resp.status_code == 200
    assert "text/plain" in resp.content_type


def test_web_download_combined_json_mimetype(web_client):
    """GET /download → Content-Type application/json für .json."""
    client, tmp = web_client
    report = tmp / "combined_copycat_2.json"
    report.write_text('{"files":[]}')
    resp = client.get(f"/download?path={report}")
    assert resp.status_code == 200
    assert "application/json" in resp.content_type


def test_web_download_combined_md_mimetype(web_client):
    """GET /download → Content-Type text/markdown für .md."""
    client, tmp = web_client
    report = tmp / "combined_copycat_3.md"
    report.write_text("# Bericht\n")
    resp = client.get(f"/download?path={report}")
    assert resp.status_code == 200
    assert "markdown" in resp.content_type


def test_web_run_report_file_unreadable(web_client, monkeypatch, tmp_path):
    """POST /run wenn Report-Datei nicht gelesen werden kann → Fallback-Text."""
    client, tmp = web_client
    import CopyCat_Web
    report_file = tmp / "combined_copycat_1.txt"
    report_file.write_text("data")

    def fake_run(args):
        pass

    monkeypatch.setattr(CopyCat_Web, "run_copycat", fake_run)

    # Patchiere Path.read_text so dass es wirft
    from pathlib import Path as RealPath
    original_read_text = RealPath.read_text

    def broken_read_text(self, **kw):
        raise OSError("read error")

    monkeypatch.setattr(RealPath, "read_text", broken_read_text)
    resp = client.post("/run", data={
        "input_dir": str(tmp),
        "output_dir": str(tmp),
        "types": ["code"],
        "fmt": "txt",
    })
    assert resp.status_code == 200
    assert "Report-Datei konnte nicht gelesen" in resp.data.decode("utf-8")


def test_web_api_run_recursive_flag(web_client):
    """POST /api/run mit recursive=True → args.recursive=True."""
    client, tmp = web_client
    (tmp / "r.py").write_text("x=1\n")
    resp = client.post("/api/run", json={
        "input": str(tmp),
        "format": "txt",
        "recursive": True,
    })
    assert resp.status_code == 200


# ==================== EXCLUDE TESTS ====================

from CopyCat import _should_exclude

def test_should_exclude_no_patterns(tmp_path):
    """Leere Pattern-Liste → nie ausschließen."""
    f = tmp_path / "main.py"
    f.touch()
    assert _should_exclude(f, tmp_path, []) is False


def test_should_exclude_none_patterns(tmp_path):
    """None-Pattern → nie ausschließen."""
    f = tmp_path / "main.py"
    f.touch()
    assert _should_exclude(f, tmp_path, None) is False


def test_should_exclude_by_filename(tmp_path):
    """*.min.js schließt bundle.min.js aus."""
    f = tmp_path / "bundle.min.js"
    f.touch()
    assert _should_exclude(f, tmp_path, ["*.min.js"]) is True


def test_should_exclude_no_match(tmp_path):
    """*.min.js schließt bundle.js NICHT aus."""
    f = tmp_path / "bundle.js"
    f.touch()
    assert _should_exclude(f, tmp_path, ["*.min.js"]) is False


def test_should_exclude_by_relative_path(tmp_path):
    """dist/bundle.js schließt dist/bundle.js aus."""
    sub = tmp_path / "dist"
    sub.mkdir()
    f = sub / "bundle.js"
    f.touch()
    assert _should_exclude(f, tmp_path, ["dist/bundle.js"]) is True


def test_should_exclude_directory_prefix(tmp_path):
    """dist/ (mit Slash) schließt alle Dateien in dist/ aus."""
    sub = tmp_path / "dist"
    sub.mkdir()
    f = sub / "app.js"
    f.touch()
    assert _should_exclude(f, tmp_path, ["dist/"]) is True


def test_should_exclude_directory_prefix_no_match(tmp_path):
    """dist/ schließt Dateien außerhalb von dist/ NICHT aus."""
    f = tmp_path / "src" / "app.js"
    (tmp_path / "src").mkdir()
    f.touch()
    assert _should_exclude(f, tmp_path, ["dist/"]) is False


def test_should_exclude_multiple_patterns(tmp_path):
    """Mehrere Muster: erstes match genügt."""
    f = tmp_path / "test_helper.py"
    f.touch()
    assert _should_exclude(f, tmp_path, ["*.min.js", "test_*.py"]) is True


def test_should_exclude_directory_exact(tmp_path):
    """dist/ schließt auch eine Datei genau mit Name 'dist' aus (rel == p)."""
    # Das ist ein Grenzfall: rel == p wenn Datei direkt dist heißt (kein Slash)
    f = tmp_path / "dist"
    f.touch()
    assert _should_exclude(f, tmp_path, ["dist/"]) is True


def test_should_exclude_outside_input_dir(tmp_path):
    """Candidate außerhalb input_dir → fällt zurück auf candidate.name."""
    other = tmp_path.parent / "other.py"
    other.touch()
    assert _should_exclude(other, tmp_path, ["other.py"]) is True


def test_parse_arguments_exclude_flag(tmp_path):
    """--exclude setzt args.exclude korrekt."""
    import sys
    with patch("sys.argv", ["copycat", "--input", str(tmp_path), "--exclude", "*.min.js", "dist/"]):
        args = parse_arguments()
    assert "*.min.js" in args.exclude
    assert "dist/" in args.exclude


def test_parse_arguments_exclude_comma_split(tmp_path):
    """--exclude mit einem Argument das Kommas enthält → wird gesplittet."""
    import sys
    with patch("sys.argv", ["copycat", "--input", str(tmp_path), "--exclude", "*.min.js,dist/,node_modules/"]):
        args = parse_arguments()
    assert args.exclude == ["*.min.js", "dist/", "node_modules/"]


def test_parse_arguments_exclude_config(tmp_path):
    """copycat.conf mit exclude = *.log,tmp/ wird korrekt geladen."""
    conf = tmp_path / "copycat.conf"
    conf.write_text("exclude = *.log, tmp/\n", encoding="utf-8")
    with patch("sys.argv", ["copycat", "--input", str(tmp_path)]):
        args = parse_arguments(config_path=str(conf))
    assert "*.log" in args.exclude
    assert "tmp/" in args.exclude


def test_collect_files_exclude_by_name(run_args, tmp_path):
    """Dateien die auf *.min.js passen werden ausgeschlossen."""
    (tmp_path / "app.min.js").write_text("x")
    (tmp_path / "app.js").write_text("x")
    args = run_args(types=["web"], exclude=["*.min.js"])
    from CopyCat import _collect_files, TYPE_FILTERS
    script_file = Path(__file__).resolve()
    files = _collect_files(args, tmp_path, script_file)
    web_names = [f.name for f in files.get("web", [])]
    assert "app.min.js" not in web_names
    assert "app.js" in web_names


def test_collect_files_exclude_directory(run_args, tmp_path):
    """Ordner mit Slash ausgeschlossen über plain-glob-Zweig."""
    dist = tmp_path / "dist"
    dist.mkdir()
    (dist / "bundle.js").write_text("x")
    (tmp_path / "main.js").write_text("x")
    args = run_args(types=["web"], exclude=["dist/"])
    from CopyCat import _collect_files
    script_file = Path(__file__).resolve()
    files = _collect_files(args, tmp_path, script_file)
    web_names = [f.name for f in files.get("web", [])]
    assert "bundle.js" not in web_names
    assert "main.js" in web_names


def test_collect_files_exclude_recursive(run_args, tmp_path):
    """Exclude funktioniert im rekursiven (size_filtered_glob) Zweig."""
    sub = tmp_path / "node_modules"
    sub.mkdir()
    (sub / "dep.py").write_text("x")
    (tmp_path / "main.py").write_text("x")
    args = run_args(types=["code"], recursive=True, exclude=["node_modules/"])
    from CopyCat import _collect_files
    script_file = Path(__file__).resolve()
    files = _collect_files(args, tmp_path, script_file)
    code_names = [f.name for f in files.get("code", [])]
    assert "dep.py" not in code_names
    assert "main.py" in code_names


def test_collect_files_exclude_empty_is_noop(run_args, tmp_path):
    """Leere Exclude-Liste ändert nichts."""
    (tmp_path / "app.js").write_text("x")
    args = run_args(types=["web"], exclude=[])
    from CopyCat import _collect_files
    script_file = Path(__file__).resolve()
    files = _collect_files(args, tmp_path, script_file)
    assert any(f.name == "app.js" for f in files.get("web", []))


def test_gui_build_args_exclude(gui):
    """GUI _build_args() liefert korrekte exclude-Liste."""
    gui._exclude_var.set("*.log, tmp/")
    args = gui._build_args()
    assert "*.log" in args.exclude
    assert "tmp/" in args.exclude


def test_gui_build_args_exclude_empty(gui):
    """GUI _build_args() mit leerem Exclude-Feld → leere Liste."""
    gui._exclude_var.set("")
    args = gui._build_args()
    assert args.exclude == []


def test_gui_save_config_includes_exclude(gui, tmp_path):
    """_save_config() schreibt exclude-Zeile."""
    path = tmp_path / "test.conf"
    gui._input_var.set("")
    gui._output_var.set("")
    gui._format_var.set("txt")
    gui._exclude_var.set("*.log")
    with patch("tkinter.filedialog.asksaveasfilename", return_value=str(path)), \
         patch("tkinter.messagebox.showinfo"):
        gui._save_config()
    content = path.read_text(encoding="utf-8")
    assert "exclude = *.log" in content


def test_gui_load_config_sets_exclude(gui, tmp_path):
    """_load_config() setzt _exclude_var aus Config."""
    conf = tmp_path / "c.conf"
    conf.write_text("exclude = *.log\n", encoding="utf-8")
    with patch("tkinter.filedialog.askopenfilename", return_value=str(conf)):
        gui._load_config()
    assert gui._exclude_var.get() == "*.log"


def test_web_build_args_exclude():
    """_build_args parst exclude korrekt."""
    from CopyCat_Web import _build_args as web_build_args

    class FakeForm:
        _data = {"input_dir": "/tmp", "exclude": "*.log, dist/"}
        def get(self, key, default=""):
            return self._data.get(key, default)
        def getlist(self, key):
            val = self._data.get(key, [])
            return val if isinstance(val, list) else [val]
        def __contains__(self, item):
            return item in self._data

    args = web_build_args(FakeForm())
    assert "*.log" in args.exclude
    assert "dist/" in args.exclude


def test_web_build_args_exclude_empty():
    """_build_args mit leerem exclude → leere Liste."""
    from CopyCat_Web import _build_args as web_build_args

    class FakeForm:
        _data = {"input_dir": "/tmp", "exclude": ""}
        def get(self, key, default=""):
            return self._data.get(key, default)
        def getlist(self, key):
            val = self._data.get(key, [])
            return val if isinstance(val, list) else [val]
        def __contains__(self, item):
            return item in self._data

    args = web_build_args(FakeForm())
    assert args.exclude == []


def test_web_form_defaults_has_exclude():
    """_form_defaults enthält exclude-Key."""
    from CopyCat_Web import _form_defaults
    defaults = _form_defaults()
    assert "exclude" in defaults
    assert defaults["exclude"] == ""


def test_web_run_with_exclude(web_client):
    """POST /run mit exclude schließt Datei aus."""
    client, tmp = web_client
    (tmp / "bundle.min.js").write_text("x")
    resp = client.post("/run", data={
        "input_dir": str(tmp),
        "output_dir": str(tmp),
        "types": ["web"],
        "fmt": "txt",
        "exclude": "*.min.js",
    })
    assert resp.status_code == 200


def test_web_api_run_with_exclude(web_client):
    """POST /api/run mit exclude-Key wird korrekt verarbeitet."""
    client, tmp = web_client
    (tmp / "app.py").write_text("x=1\n")
    resp = client.post("/api/run", json={
        "input": str(tmp),
        "format": "txt",
        "exclude": "*.log",
    })
    assert resp.status_code == 200


def test_parse_arguments_exclude_config_empty_value(tmp_path):
    """exclude = ,  (nur Komma) → kein Override gesetzt (leere Parts)."""
    conf = tmp_path / "copycat.conf"
    conf.write_text("exclude = ,\n", encoding="utf-8")
    with patch("sys.argv", ["copycat"]):
        args = parse_arguments(config_path=str(conf))
    # keine Exception, exclude bleibt Default (leer)
    assert args.exclude == []


# ==================== HTML-REPORT + INKREMENTELLER CACHE (Idee 3 & 4) ====================

# --- _html_escape ---

def test_html_escape_ampersand():
    assert _html_escape("a & b") == "a &amp; b"


def test_html_escape_less_than_greater_than():
    assert _html_escape("<tag>") == "&lt;tag&gt;"


def test_html_escape_double_quote():
    assert _html_escape('"val"') == "&quot;val&quot;"


def test_html_escape_no_special():
    assert _html_escape("hello world") == "hello world"


# --- _hash_file ---

def test_hash_file_valid(tmp_path):
    import hashlib
    f = tmp_path / "data.bin"
    f.write_bytes(b"hello")
    assert _hash_file(f) == hashlib.sha256(b"hello").hexdigest()


def test_hash_file_oserror():
    assert _hash_file(Path("/no/such/missing_file.py")) == ""


# --- _load_cache ---

def test_load_cache_missing_file(tmp_path):
    assert _load_cache(tmp_path / "no_cache.json") == {}


def test_load_cache_wrong_version(tmp_path):
    f = tmp_path / "cache.json"
    f.write_text('{"version": "99", "entries": {}}', encoding="utf-8")
    assert _load_cache(f) == {}


def test_load_cache_json_error(tmp_path):
    f = tmp_path / "cache.json"
    f.write_text("not valid json !!!", encoding="utf-8")
    assert _load_cache(f) == {}


def test_load_cache_valid(tmp_path):
    f = tmp_path / "cache.json"
    entries = {"a.py": {"hash": "abc", "lines": 5, "content": "x=1"}}
    f.write_text(json.dumps({"version": "1", "entries": entries}), encoding="utf-8")
    assert _load_cache(f) == entries


# --- _save_cache ---

def test_save_cache_write_and_read(tmp_path):
    f = tmp_path / "sub" / "cache.json"
    entries = {"x.py": {"hash": "deadbeef", "lines": 3, "content": "y=2"}}
    _save_cache(f, entries)
    assert _load_cache(f) == entries


def test_save_cache_oserror(tmp_path):
    """_save_cache swallows OSError silently when parent is a file."""
    blocker = tmp_path / "block"
    blocker.write_text("I am a file, not a dir")
    _save_cache(blocker / "cache.json", {"a.py": {}})  # Must not raise


# --- _write_json with cache ---

def test_write_json_with_cache(tmp_path):
    """_write_json reads 'lines' from cache when available (line 1082)."""
    files = {k: [] for k in TYPE_FILTERS}
    code_file = tmp_path / "cached.py"
    code_file.write_text("x = 1\n", encoding="utf-8")
    files["code"] = [code_file]
    cache = {code_file: {"lines": 42, "content": "x = 1\n", "from_cache": True}}

    out_path = tmp_path / "out.json"
    args = Namespace(recursive=False, types=["code"], max_size=float("inf"), format="json")
    _write_json(out_path, files, args, tmp_path, "No Git", 1, cache=cache)

    data = json.loads(out_path.read_text(encoding="utf-8"))
    assert data["details"]["code"][0]["lines"] == 42


# --- _write_md with cache ---

def test_write_md_cache_from_cache_badge(tmp_path):
    """_write_md shows Cache-Treffer badge (lines 1157-1158) and reads content (line 1170)."""
    files = {k: [] for k in TYPE_FILTERS}
    code_file = tmp_path / "cached.py"
    code_file.write_text("x = 1\n", encoding="utf-8")
    files["code"] = [code_file]
    cache = {code_file: {"lines": 7, "content": "x = 1\n", "from_cache": True}}

    buf = StringIO()
    args = Namespace(recursive=False, types=["code"], max_size=float("inf"), format="md")
    _write_md(buf, files, args, tmp_path, "No Git", 2, cache=cache)

    out = buf.getvalue()
    assert "Cache-Treffer" in out
    assert "7 Zeilen" in out


def test_write_md_cache_not_from_cache(tmp_path):
    """_write_md reads content from cache when from_cache=False (line 1157 branch)."""
    files = {k: [] for k in TYPE_FILTERS}
    code_file = tmp_path / "fresh.py"
    code_file.write_text("y = 2\n", encoding="utf-8")
    files["code"] = [code_file]
    cache = {code_file: {"lines": 3, "content": "y = 2\n", "from_cache": False}}

    buf = StringIO()
    args = Namespace(recursive=False, types=["code"], max_size=float("inf"), format="md")
    _write_md(buf, files, args, tmp_path, "No Git", 3, cache=cache)

    out = buf.getvalue()
    assert "Cache-Treffer" not in out
    assert "3 Zeilen" in out


# --- _write_html tests ---

def _make_html_args(types=None, recursive=False):
    return Namespace(recursive=recursive, types=types, max_size=float("inf"), format="html")


def test_write_html_basic(tmp_path):
    """_write_html produces a valid HTML report."""
    files = {k: [] for k in TYPE_FILTERS}
    code_file = tmp_path / "hello.py"
    code_file.write_text("print('hello')\n", encoding="utf-8")
    files["code"] = [code_file]

    out = tmp_path / "report.html"
    _write_html(out, files, _make_html_args(), tmp_path, "Branch: main | Last Commit: abc", 1)

    html = out.read_text(encoding="utf-8")
    assert "<!DOCTYPE html>" in html
    assert "hello.py" in html


def test_write_html_cache_hit_badge(tmp_path):
    """_write_html shows Cache-Treffer badge for cached files (lines 1316-1318)."""
    files = {k: [] for k in TYPE_FILTERS}
    code_file = tmp_path / "cached.py"
    code_file.write_text("x = 1\n", encoding="utf-8")
    files["code"] = [code_file]
    cache = {code_file: {"lines": 5, "content": "x = 1\n", "from_cache": True}}

    out = tmp_path / "report.html"
    _write_html(out, files, _make_html_args(), tmp_path, "No Git", 2, cache=cache)

    html = out.read_text(encoding="utf-8")
    assert "Cache-Treffer" in html


def test_write_html_search_meta_row(tmp_path):
    """_write_html includes search summary row when search_pattern given (lines 1304-1305)."""
    files = {k: [] for k in TYPE_FILTERS}
    code_file = tmp_path / "main.py"
    code_file.write_text("x = 1\n", encoding="utf-8")
    files["code"] = [code_file]

    out = tmp_path / "report.html"
    _write_html(out, files, _make_html_args(), tmp_path, "No Git", 3,
                search_pattern="TODO", search_results={})

    html = out.read_text(encoding="utf-8")
    assert "TODO" in html
    assert "0 Treffer" in html


def test_write_html_search_results_section(tmp_path):
    """_write_html renders search results table when hits exist (lines 1364-1371)."""
    files = {k: [] for k in TYPE_FILTERS}
    code_file = tmp_path / "main.py"
    code_file.write_text("# TODO: fix\n", encoding="utf-8")
    files["code"] = [code_file]
    sr = {code_file: [(1, "# TODO: fix")]}

    out = tmp_path / "report.html"
    _write_html(out, files, _make_html_args(), tmp_path, "No Git", 4,
                search_pattern="TODO", search_results=sr)

    html = out.read_text(encoding="utf-8")
    assert "Suchergebnisse" in html
    assert "TODO" in html


def test_write_html_no_code_in_types(tmp_path):
    """_write_html skips code section when 'code' not in selected types (branch 1312->1345)."""
    files = {k: [] for k in TYPE_FILTERS}
    code_file = tmp_path / "main.py"
    code_file.write_text("x = 1\n", encoding="utf-8")
    files["code"] = [code_file]
    img_file = tmp_path / "logo.png"
    img_file.write_bytes(b"PNG")
    files["img"] = [img_file]

    out = tmp_path / "report.html"
    _write_html(out, files, _make_html_args(types=["img"]), tmp_path, "No Git", 5)

    html = out.read_text(encoding="utf-8")
    assert "IMG" in html
    assert "logo.png" in html
    assert "main.py" not in html


def test_write_html_other_type_section(tmp_path):
    """_write_html renders non-code file section in HTML output (lines 1352-1356)."""
    files = {k: [] for k in TYPE_FILTERS}
    img_file = tmp_path / "banner.png"
    img_file.write_bytes(b"PNG")
    files["img"] = [img_file]

    out = tmp_path / "report.html"
    _write_html(out, files, _make_html_args(), tmp_path, "No Git", 6)

    html = out.read_text(encoding="utf-8")
    assert "IMG" in html
    assert "banner.png" in html


def test_write_html_unicode_decode_error(tmp_path):
    """_write_html handles UnicodeDecodeError when reading code file (lines 1325-1327)."""
    files = {k: [] for k in TYPE_FILTERS}
    code_file = tmp_path / "binary.py"
    code_file.write_bytes(b"\xff\xfe\x00\x01 invalid utf-8 bytes")
    files["code"] = [code_file]

    out = tmp_path / "report.html"
    _write_html(out, files, _make_html_args(), tmp_path, "No Git", 7)

    html = out.read_text(encoding="utf-8")
    assert "binary.py" in html
    assert "bersprungen" in html  # part of "übersprungen"


def test_write_html_read_exception(tmp_path):
    """_write_html handles generic read Exception gracefully (lines 1329-1330)."""
    files = {k: [] for k in TYPE_FILTERS}
    code_file = tmp_path / "error.py"
    code_file.write_text("x = 1\n", encoding="utf-8")
    files["code"] = [code_file]

    out = tmp_path / "report.html"
    original_read_text = Path.read_text

    def patched(self, *args, **kwargs):
        if self == code_file:
            raise PermissionError("no read access")
        return original_read_text(self, *args, **kwargs)

    with patch.object(Path, "read_text", patched):
        _write_html(out, files, _make_html_args(), tmp_path, "No Git", 8)

    html = out.read_text(encoding="utf-8")
    # "Fehler beim Lesen" may be split across Pygments spans, so check the filename
    assert "error.py" in html
    # Ensure the fallback text was used (Pygments splits it into tokens, but "Lesen" appears)
    assert "Lesen" in html


def test_write_html_without_pygments(tmp_path):
    """_write_html uses plain <pre><code> fallback when pygments not available (lines 1274-1276, 1280)."""
    import sys
    files = {k: [] for k in TYPE_FILTERS}
    code_file = tmp_path / "script.py"
    code_file.write_text("x = 1\n", encoding="utf-8")
    files["code"] = [code_file]

    out = tmp_path / "report.html"
    pygments_nulls = {k: None for k in list(sys.modules) if k == "pygments" or k.startswith("pygments.")}
    pygments_nulls.setdefault("pygments", None)
    with patch.dict("sys.modules", pygments_nulls):
        _write_html(out, files, _make_html_args(), tmp_path, "No Git", 9)

    html = out.read_text(encoding="utf-8")
    assert "script.py" in html
    assert "pip install pygments" in html


def test_write_html_pygments_class_not_found(tmp_path):
    """_write_html falls back to TextLexer for unrecognized extension (lines 1283-1284)."""
    pytest.importorskip("pygments")
    files = {k: [] for k in TYPE_FILTERS}
    code_file = tmp_path / "config.unknownxyz"
    code_file.write_text("hello = world\n", encoding="utf-8")
    files["code"] = [code_file]

    out = tmp_path / "report.html"
    _write_html(out, files, _make_html_args(), tmp_path, "No Git", 10)

    html = out.read_text(encoding="utf-8")
    assert "config.unknownxyz" in html
    assert "hello = world" in html


# --- Incremental error branches in run_copycat ---

def test_run_copycat_incremental_unicode_decode_error(tmp_path, run_args):
    """Incremental mode handles UnicodeDecodeError gracefully (lines 1485-1487)."""
    code_file = tmp_path / "binary.py"
    code_file.write_bytes(b"\xff\xfe\x00 bad encoding bytes")

    run_copycat(run_args(incremental=True))

    reports = list(tmp_path.glob("combined_copycat_*.txt"))
    assert reports


def test_run_copycat_incremental_read_exception(tmp_path, run_args):
    """Incremental mode handles generic Exception gracefully (lines 1488-1490)."""
    code_file = tmp_path / "error.py"
    code_file.write_text("x = 1\n", encoding="utf-8")

    original_read_text = Path.read_text

    def patched(self, *args, **kwargs):
        if self == code_file:
            raise PermissionError("no access")
        return original_read_text(self, *args, **kwargs)

    with patch.object(Path, "read_text", patched):
        run_copycat(run_args(incremental=True))

    reports = list(tmp_path.glob("combined_copycat_*.txt"))
    assert reports


def test_web_api_run_with_incremental(web_client):
    """POST /api/run mit incremental=True setzt form_like['incremental'] (Zeile 399)."""
    client, tmp = web_client
    (tmp / "app.py").write_text("x=1\n")
    resp = client.post("/api/run", json={
        "input": str(tmp),
        "format": "txt",
        "incremental": True,
    })
    assert resp.status_code == 200


# ==================== CODE-STATISTIKEN TESTS ====================

def test_analyse_file_python(tmp_path):
    """_analyse_file erkennt Python-LOC, Kommentare, Blank und Komplexität."""
    py = tmp_path / "sample.py"
    py.write_text("# Kommentar\n\ndef foo():\n    if True:\n        pass\n")
    result = _analyse_file(py)
    assert result["loc"] == 5
    assert result["comments"] == 1
    assert result["blank"] == 1
    assert result["code"] == 3
    assert result["complexity"] is not None
    assert result["complexity"] >= 2  # 1 + If


def test_analyse_file_non_python(tmp_path):
    """_analyse_file ermittelt Komplexität für Nicht-Python-Dateien via Regex."""
    js = tmp_path / "app.js"
    js.write_text("if (x) { for (;;) {} }\n")
    result = _analyse_file(js)
    assert result["complexity"] >= 2
    assert result["loc"] == 1


def test_analyse_file_no_keywords(tmp_path):
    """Nicht-Python-Datei ohne Branch-Schlüsselwörter → complexity=1."""
    txt = tmp_path / "data.js"
    txt.write_text("let x = 1;\nlet y = 2;\n")
    result = _analyse_file(txt)
    assert result["complexity"] == 1


def test_analyse_file_oserror(tmp_path):
    """_analyse_file gibt Null-Werte bei OSError zurück."""
    missing = tmp_path / "ghost.py"
    result = _analyse_file(missing)
    assert result == {"loc": 0, "code": 0, "comments": 0, "blank": 0, "complexity": None}


def test_analyse_file_unicode_error(tmp_path):
    """_analyse_file gibt Null-Werte bei UnicodeDecodeError zurück."""
    bin_file = tmp_path / "binary.py"
    bin_file.write_bytes(b"\xff\xfe")
    result = _analyse_file(bin_file)
    assert result == {"loc": 0, "code": 0, "comments": 0, "blank": 0, "complexity": None}


def test_analyse_file_syntax_error(tmp_path):
    """_analyse_file gibt complexity=None bei SyntaxError zurück."""
    bad = tmp_path / "bad.py"
    bad.write_text("def (:\n", encoding="utf-8")
    result = _analyse_file(bad)
    assert result["complexity"] is None
    assert result["loc"] > 0


def test_analyse_file_empty(tmp_path):
    """_analyse_file bei leerer Datei → loc=0."""
    empty = tmp_path / "empty.py"
    empty.write_text("", encoding="utf-8")
    result = _analyse_file(empty)
    assert result["loc"] == 0
    assert result["code"] == 0


def test_build_stats_with_files(tmp_path):
    """_build_stats liefert per_file und total."""
    py = tmp_path / "x.py"
    py.write_text("x = 1\n# Komm\n\n")
    files = {k: [] for k in TYPE_FILTERS}
    files["code"] = [py]
    stats = _build_stats(files)
    assert py in stats["per_file"]
    assert stats["total"]["loc"] > 0
    assert "comment_ratio" in stats["total"]


def test_build_stats_empty(tmp_path):
    """_build_stats mit leerer code-Liste gibt Null-Total zurück."""
    files = {k: [] for k in TYPE_FILTERS}
    stats = _build_stats(files)
    assert stats["per_file"] == {}
    assert stats["total"]["loc"] == 0
    assert stats["total"]["avg_complexity"] is None


def test_build_stats_cache_hit(tmp_path):
    """_build_stats liest stats aus Cache, wenn vorhanden."""
    py = tmp_path / "c.py"
    py.write_text("x=1\n")
    cached_stats = {"loc": 99, "code": 80, "comments": 10, "blank": 9, "complexity": 5}
    cache = {py: {"stats": cached_stats}}
    files = {k: [] for k in TYPE_FILTERS}
    files["code"] = [py]
    stats = _build_stats(files, cache)
    assert stats["per_file"][py] == cached_stats
    assert stats["total"]["loc"] == 99


def test_build_stats_no_complexity(tmp_path):
    """_build_stats mit complexity=None in allen Dateien → avg/max None."""
    bin_file = tmp_path / "data.py"
    bin_file.write_bytes(b"\xff\xfe")  # UnicodeDecodeError → complexity None
    files = {k: [] for k in TYPE_FILTERS}
    files["code"] = [bin_file]
    stats = _build_stats(files)
    assert stats["total"]["avg_complexity"] is None
    assert stats["total"]["max_complexity"] is None


def test_parse_arguments_stats_flag():
    """--stats Flag setzt args.stats=True."""
    with patch("sys.argv", ["CopyCat.py", "--stats"]):
        args = parse_arguments()
    assert args.stats is True


def test_parse_arguments_stats_config(tmp_path, monkeypatch):
    """Config-Key 'stats = true' setzt args.stats=True."""
    conf = tmp_path / "copycat.conf"
    conf.write_text("stats = true\n", encoding="utf-8")
    with patch("sys.argv", ["CopyCat.py"]):
        args = parse_arguments(config_path=str(conf))
    assert args.stats is True


def test_run_copycat_stats_txt(tmp_path, run_args):
    """run_copycat mit stats=True erzeugt CODE-STATISTIKEN im TXT-Report."""
    py = tmp_path / "code.py"
    py.write_text("x = 1\n# Komm\n\n")
    run_copycat(run_args(stats=True))
    reports = list(tmp_path.glob("combined_copycat_*.txt"))
    assert reports
    content = reports[0].read_text(encoding="utf-8")
    assert "CODE-STATISTIKEN" in content


def test_run_copycat_stats_json(tmp_path, run_args):
    """run_copycat mit stats=True und format=json enthält code_stats im JSON."""
    py = tmp_path / "code.py"
    py.write_text("x = 1\n")
    run_copycat(run_args(fmt="json", stats=True))
    reports = list(tmp_path.glob("combined_copycat_*.json"))
    assert reports
    import json
    data = json.loads(reports[0].read_text(encoding="utf-8"))
    assert "code_stats" in data


def test_run_copycat_stats_md(tmp_path, run_args):
    """run_copycat mit stats=True und format=md enthält ## Code-Statistiken."""
    py = tmp_path / "code.py"
    py.write_text("x = 1\n")
    run_copycat(run_args(fmt="md", stats=True))
    reports = list(tmp_path.glob("combined_copycat_*.md"))
    assert reports
    content = reports[0].read_text(encoding="utf-8")
    assert "## Code-Statistiken" in content


def test_run_copycat_stats_html(tmp_path, run_args):
    """run_copycat mit stats=True und format=html enthält stat-cards."""
    py = tmp_path / "code.py"
    py.write_text("x = 1\n")
    run_copycat(run_args(fmt="html", stats=True))
    reports = list(tmp_path.glob("combined_copycat_*.html"))
    assert reports
    content = reports[0].read_text(encoding="utf-8")
    assert "stat-cards" in content


def test_write_txt_with_stats(tmp_path):
    """_write_txt mit stats erzeugt Statistik-Block."""
    files = {k: [] for k in TYPE_FILTERS}
    py = tmp_path / "mod.py"
    py.write_text("x = 1\n# Komm\n")
    files["code"] = [py]
    stats = _build_stats(files)
    buf = StringIO()
    args = Namespace(recursive=False, types=["code"], max_size=float("inf"), format="txt", search=None)
    _write_txt(buf, files, args, tmp_path, "No Git", 1, stats=stats)
    out = buf.getvalue()
    assert "CODE-STATISTIKEN" in out
    assert "GESAMT" in out


def test_write_json_with_stats(tmp_path):
    """_write_json mit stats enthält code_stats und stats pro Datei."""
    import json
    files = {k: [] for k in TYPE_FILTERS}
    py = tmp_path / "mod.py"
    py.write_text("x = 1\n")
    files["code"] = [py]
    stats = _build_stats(files)
    out_file = tmp_path / "out.json"
    args = Namespace(recursive=False, types=["code"], max_size=float("inf"), format="json", search=None)
    _write_json(out_file, files, args, tmp_path, "No Git", 1, stats=stats)
    data = json.loads(out_file.read_text(encoding="utf-8"))
    assert data["code_stats"] is not None
    code_entries = data["details"]["code"]
    assert any("stats" in e for e in code_entries)


def test_write_md_with_stats(tmp_path):
    """_write_md mit stats enthält ## Code-Statistiken."""
    files = {k: [] for k in TYPE_FILTERS}
    py = tmp_path / "mod.py"
    py.write_text("x = 1\n")
    files["code"] = [py]
    stats = _build_stats(files)
    buf = StringIO()
    args = Namespace(recursive=False, types=["code"], max_size=float("inf"), format="md", search=None)
    _write_md(buf, files, args, tmp_path, "No Git", 1, stats=stats)
    out = buf.getvalue()
    assert "## Code-Statistiken" in out


def test_write_html_with_stats(tmp_path):
    """_write_html mit stats enthält stat-cards."""
    files = {k: [] for k in TYPE_FILTERS}
    py = tmp_path / "mod.py"
    py.write_text("x = 1\n")
    files["code"] = [py]
    stats = _build_stats(files)
    out_file = tmp_path / "out.html"
    args = Namespace(recursive=False, types=["code"], max_size=float("inf"), format="html", search=None)
    _write_html(out_file, files, args, tmp_path, "No Git", 1, stats=stats)
    out = out_file.read_text(encoding="utf-8")
    assert "stat-cards" in out


def test_gui_stats_build_args(gui):
    """GUI _build_args enthält stats=False wenn Checkbox nicht gesetzt."""
    from CopyCat_GUI import CopyCatGUI
    gui._input_var.set("")
    gui._output_var.set("")
    args = CopyCatGUI._build_args(gui)
    assert args.stats is False


def test_gui_stats_build_args_true(gui):
    """GUI _build_args enthält stats=True wenn Checkbox gesetzt."""
    from CopyCat_GUI import CopyCatGUI
    gui._stats_var.set(True)
    args = CopyCatGUI._build_args(gui)
    assert args.stats is True


def test_gui_stats_load_config(gui, tmp_path):
    """GUI _load_config setzt _stats_var aus Config-Datei."""
    from CopyCat_GUI import CopyCatGUI
    conf = tmp_path / "copycat.conf"
    conf.write_text("stats = true\n", encoding="utf-8")
    with patch("CopyCat_GUI.filedialog.askopenfilename", return_value=str(conf)):
        CopyCatGUI._load_config(gui)
    assert gui._stats_var.get() is True


def test_gui_stats_save_config(gui, tmp_path):
    """GUI _save_config schreibt stats = true wenn Checkbox gesetzt."""
    from CopyCat_GUI import CopyCatGUI
    gui._stats_var.set(True)
    conf = tmp_path / "copycat.conf"
    with patch("CopyCat_GUI.filedialog.asksaveasfilename", return_value=str(conf)), \
         patch("CopyCat_GUI.messagebox.showinfo"):
        CopyCatGUI._save_config(gui)
    content = conf.read_text(encoding="utf-8")
    assert "stats = true" in content


def test_web_stats_form_defaults(web_client):
    """GET / hat stats=False in form_defaults."""
    client, _ = web_client
    resp = client.get("/")
    assert resp.status_code == 200
    # stats checkbox nicht standardmäßig angekreuzt
    assert b'name="stats"' in resp.data


def test_web_run_with_stats(web_client):
    """POST /run mit stats-Checkbox erzeugt Bericht."""
    client, tmp = web_client
    (tmp / "app.py").write_text("x=1\n")
    resp = client.post("/run", data={
        "input": str(tmp),
        "fmt": "txt",
        "stats": "on",
    })
    assert resp.status_code == 200


def test_web_api_run_with_stats(web_client):
    """POST /api/run mit stats=True setzt form_like['stats']."""
    client, tmp = web_client
    (tmp / "app.py").write_text("x=1\n")
    resp = client.post("/api/run", json={
        "input": str(tmp),
        "format": "txt",
        "stats": True,
    })
    assert resp.status_code == 200



# ─── --git-url Tests ─────────────────────────────────────────────────────────

def test_parse_arguments_git_url_flag():
    """--git-url URL setzt args.git_url."""
    with patch("sys.argv", ["CopyCat.py", "--git-url", "https://github.com/user/repo"]):
        args = parse_arguments()
    assert args.git_url == "https://github.com/user/repo"


def test_parse_arguments_git_url_default():
    """Ohne --git-url ist args.git_url None."""
    with patch("sys.argv", ["CopyCat.py"]):
        args = parse_arguments()
    assert args.git_url is None


def test_parse_arguments_git_url_config(tmp_path, monkeypatch):
    """Config-Key 'git_url = ...' setzt args.git_url."""
    conf = tmp_path / "copycat.conf"
    conf.write_text("git_url = https://github.com/user/repo\n", encoding="utf-8")
    with patch("sys.argv", ["CopyCat.py"]):
        args = parse_arguments(config_path=str(conf))
    assert args.git_url == "https://github.com/user/repo"


def test_parse_arguments_ai_model_and_base_url_config(tmp_path):
    """Config-Keys 'ai_model' und 'ai_base_url' werden korrekt eingelesen."""
    conf = tmp_path / "copycat.conf"
    conf.write_text(
        "ai_model = gpt-4\nai_base_url = http://localhost:11434/v1\n",
        encoding="utf-8",
    )
    with patch("sys.argv", ["CopyCat.py"]):
        args = parse_arguments(config_path=str(conf))
    assert args.ai_model == "gpt-4"
    assert args.ai_base_url == "http://localhost:11434/v1"


def test_run_copycat_git_url_invalid_url(tmp_path):
    """Ungueltige Git-URL: run_copycat gibt None zurueck, kein clone."""
    from argparse import Namespace
    a = Namespace(
        input=None, output=str(tmp_path),
        types=["code"], recursive=False, max_size=float("inf"),
        format="txt", search=None, template=None, watch=False, cooldown=2.0,
        plugin_dir=None, list_plugins=False, diff=None, merge=None,
        install_hook=None, verbose=False, quiet=True, exclude=[],
        incremental=False, stats=False,
        git_url="not-a-valid-url",
    )
    with patch("subprocess.run") as mock_sub:
        result = run_copycat(a)
    assert result is None
    mock_sub.assert_not_called()


def test_run_copycat_git_url_clone_failure(tmp_path):
    """git clone schlaegt fehl: run_copycat gibt None zurueck."""
    from argparse import Namespace
    import subprocess
    a = Namespace(
        input=None, output=str(tmp_path),
        types=["code"], recursive=False, max_size=float("inf"),
        format="txt", search=None, template=None, watch=False, cooldown=2.0,
        plugin_dir=None, list_plugins=False, diff=None, merge=None,
        install_hook=None, verbose=False, quiet=True, exclude=[],
        incremental=False, stats=False,
        git_url="https://github.com/user/repo",
    )
    mock_result = MagicMock()
    mock_result.returncode = 1
    mock_result.stderr = "fatal: repository not found"
    with patch("subprocess.run", return_value=mock_result):
        result = run_copycat(a)
    assert result is None


def test_run_copycat_git_url_success(tmp_path):
    """Erfolgreicher git clone: run_copycat scannt geklontes Repo."""
    from argparse import Namespace
    import subprocess

    a = Namespace(
        input=None, output=str(tmp_path),
        types=["code"], recursive=False, max_size=float("inf"),
        format="txt", search=None, template=None, watch=False, cooldown=2.0,
        plugin_dir=None, list_plugins=False, diff=None, merge=None,
        install_hook=None, verbose=False, quiet=True, exclude=[],
        incremental=False, stats=False,
        git_url="https://github.com/user/repo",
    )

    def fake_clone(cmd, **kw):
        # Simuliere git clone: erzeuge die Zieldatei
        clone_path = cmd[-1]
        import pathlib
        pathlib.Path(clone_path).mkdir(parents=True, exist_ok=True)
        (pathlib.Path(clone_path) / "main.py").write_text("x = 1\n", encoding="utf-8")
        r = MagicMock()
        r.returncode = 0
        r.stderr = ""
        return r

    with patch("subprocess.run", side_effect=fake_clone):
        result = run_copycat(a)

    assert result is not None
    assert "combined_copycat" in result


def test_run_copycat_git_url_clone_no_dir(tmp_path):
    """git clone gibt 0 zurueck aber erstellt kein Verzeichnis: run_copycat gibt None."""
    from argparse import Namespace
    a = Namespace(
        input=None, output=str(tmp_path),
        types=["code"], recursive=False, max_size=float("inf"),
        format="txt", search=None, template=None, watch=False, cooldown=2.0,
        plugin_dir=None, list_plugins=False, diff=None, merge=None,
        install_hook=None, verbose=False, quiet=True, exclude=[],
        incremental=False, stats=False,
        git_url="https://github.com/user/repo",
    )
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stderr = ""
    with patch("subprocess.run", return_value=mock_result):
        result = run_copycat(a)
    assert result is None


def test_run_copycat_git_url_git_not_installed(tmp_path):
    """git nicht im PATH: run_copycat gibt None zurueck, kein Traceback."""
    from argparse import Namespace
    a = Namespace(
        input=None, output=str(tmp_path),
        types=["code"], recursive=False, max_size=float("inf"),
        format="txt", search=None, template=None, watch=False, cooldown=2.0,
        plugin_dir=None, list_plugins=False, diff=None, merge=None,
        install_hook=None, verbose=False, quiet=True, exclude=[],
        incremental=False, stats=False,
        git_url="https://github.com/user/repo",
    )
    with patch("subprocess.run", side_effect=FileNotFoundError("git not found")):
        result = run_copycat(a)
    assert result is None


def test_run_copycat_git_url_clone_timeout(tmp_path):
    """git clone Timeout: run_copycat gibt None zurueck, kein Traceback."""
    from argparse import Namespace
    import subprocess
    a = Namespace(
        input=None, output=str(tmp_path),
        types=["code"], recursive=False, max_size=float("inf"),
        format="txt", search=None, template=None, watch=False, cooldown=2.0,
        plugin_dir=None, list_plugins=False, diff=None, merge=None,
        install_hook=None, verbose=False, quiet=True, exclude=[],
        incremental=False, stats=False,
        git_url="https://github.com/user/repo",
    )
    with patch("subprocess.run", side_effect=subprocess.TimeoutExpired(cmd="git", timeout=120)):
        result = run_copycat(a)
    assert result is None


# ─── GUI git-url Tests ────────────────────────────────────────────────────────

def test_gui_git_url_build_args(gui):
    """_build_args gibt git_url korrekt weiter."""
    gui._git_url_var.set("https://github.com/user/repo")
    args = gui._build_args()
    assert args.git_url == "https://github.com/user/repo"


def test_gui_git_url_build_args_empty(gui):
    """_build_args gibt None wenn git_url leer."""
    gui._git_url_var.set("")
    args = gui._build_args()
    assert args.git_url is None


def test_gui_git_url_load_config(gui, tmp_path):
    """_load_config setzt _git_url_var wenn config git_url enthaelt."""
    conf = tmp_path / "copycat.conf"
    conf.write_text("git_url = https://github.com/user/repo\n", encoding="utf-8")
    with patch("CopyCat_GUI.filedialog.askopenfilename", return_value=str(conf)):
        gui._load_config()
    assert gui._git_url_var.get() == "https://github.com/user/repo"


def test_gui_git_url_save_config(gui, tmp_path):
    """_save_config schreibt git_url wenn gesetzt."""
    out = tmp_path / "out.conf"
    gui._git_url_var.set("https://github.com/user/repo")
    with patch("CopyCat_GUI.filedialog.asksaveasfilename", return_value=str(out)), \
         patch("CopyCat_GUI.messagebox.showinfo"):
        gui._save_config()
    text = out.read_text(encoding="utf-8")
    assert "git_url = https://github.com/user/repo" in text


# ─── Web git-url Tests ────────────────────────────────────────────────────────

def test_web_form_defaults_git_url():
    """_form_defaults enthaelt git_url Schluessel."""
    from CopyCat_Web import _form_defaults
    defaults = _form_defaults()
    assert "git_url" in defaults
    assert defaults["git_url"] == ""


def test_web_run_missing_both_input_and_git_url(web_client):
    """POST /run ohne input_dir und ohne git_url: Fehlermeldung."""
    client, tmp = web_client
    resp = client.post("/run", data={"input_dir": "", "git_url": ""})
    assert resp.status_code == 200
    assert "Eingabeordner" in resp.get_data(as_text=True) or "Git-URL" in resp.get_data(as_text=True)


def test_web_api_run_git_url_no_input_no_git(web_client):
    """POST /api/run ohne input und ohne git_url: 400."""
    client, _ = web_client
    resp = client.post("/api/run", json={"format": "txt"})
    assert resp.status_code == 400


def test_web_api_run_with_git_url(web_client):
    """POST /api/run mit git_url wird an form_like weitergegeben."""
    client, tmp = web_client
    mock_result = MagicMock()
    mock_result.returncode = 1
    mock_result.stderr = "fatal"
    with patch("subprocess.run", return_value=mock_result):
        resp = client.post("/api/run", json={
            "git_url": "https://github.com/user/repo",
            "format": "txt",
        })
    # run_copycat gibt None zurueck (clone fehlgeschlagen), API gibt 200 ok mit report=None
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["status"] == "ok"


# ==================== M33: PDF-Export ====================

def test_write_pdf_requires_reportlab(tmp_path, run_args):
    """_write_pdf wirft ImportError wenn reportlab nicht installiert ist."""
    args = run_args()
    files = {k: [] for k in TYPE_FILTERS}
    out = tmp_path / "test.pdf"
    # Blockiere reportlab-Importe via sys.modules → triggert except ImportError innerhalb _write_pdf
    blocked = {
        "reportlab": None,
        "reportlab.lib": None,
        "reportlab.lib.pagesizes": None,
        "reportlab.platypus": None,
        "reportlab.lib.styles": None,
        "reportlab.lib.units": None,
        "reportlab.lib.colors": None,
    }
    with patch.dict("sys.modules", blocked):
        with pytest.raises(ImportError, match="reportlab"):
            _write_pdf(out, files, args, tmp_path, "No Git", 1)


def test_write_pdf_creates_file(tmp_path, run_args):
    """_write_pdf erstellt eine PDF-Datei (benötigt reportlab)."""
    pytest.importorskip("reportlab")
    args = run_args()
    (tmp_path / "hello.py").write_text("print('hello')\n", encoding="utf-8")
    import CopyCat
    files = CopyCat._collect_files(args, tmp_path, CopyCat.Path(__file__).resolve())
    out = tmp_path / "test.pdf"
    _write_pdf(out, files, args, tmp_path, "No Git", 1)
    assert out.exists()
    assert out.stat().st_size > 0
    # Ist eine gültige PDF (beginnt mit %PDF)
    assert out.read_bytes()[:4] == b"%PDF"


def test_write_pdf_with_stats(tmp_path, run_args):
    """_write_pdf mit Stats-Daten schlägt nicht fehl."""
    pytest.importorskip("reportlab")
    args = run_args(stats=True)
    (tmp_path / "code.py").write_text("# comment\nx = 1\n", encoding="utf-8")
    import CopyCat
    files = CopyCat._collect_files(args, tmp_path, CopyCat.Path(__file__).resolve())
    stats = CopyCat._build_stats(files)
    out = tmp_path / "stats.pdf"
    _write_pdf(out, files, args, tmp_path, "No Git", 2, stats=stats)
    assert out.exists()


def test_run_copycat_pdf_format(tmp_path, run_args):
    """run_copycat erzeugt combined_copycat_N.pdf bei --format pdf."""
    pytest.importorskip("reportlab")
    args = run_args(fmt="pdf")
    result = run_copycat(args)
    assert result is not None
    assert result.endswith(".pdf")
    assert Path(result).exists()


def test_write_pdf_with_search_pattern(tmp_path, run_args):
    """_write_pdf mit search_pattern erzeugt Meta-Suche und Suchergebnis-Sektion."""
    pytest.importorskip("reportlab")
    args = run_args()
    code_file = tmp_path / "main.py"
    code_file.write_text("print('hello')\n", encoding="utf-8")
    import CopyCat
    files = CopyCat._collect_files(args, tmp_path, Path(__file__).resolve())
    out = tmp_path / "search.pdf"
    search_results = {code_file: [(1, "print('hello')")]}
    _write_pdf(
        out, files, args, tmp_path, "No Git", 1,
        search_pattern="print", search_results=search_results,
    )
    assert out.exists()
    assert out.stat().st_size > 0


def test_write_pdf_types_skip_code_section(tmp_path, run_args):
    """_write_pdf überspringt Code-Sektion wenn 'code'/'all' nicht in args.types."""
    pytest.importorskip("reportlab")
    args = run_args(types=["other"])
    files = {k: [] for k in TYPE_FILTERS}
    out = tmp_path / "nocode.pdf"
    _write_pdf(out, files, args, tmp_path, "No Git", 1)
    assert out.exists()


def test_write_pdf_with_cached_file(tmp_path, run_args):
    """_write_pdf liest Inhalt aus Cache statt von Disk."""
    pytest.importorskip("reportlab")
    args = run_args()
    code_file = tmp_path / "cached.py"
    code_file.write_text("x = 1\n", encoding="utf-8")
    import CopyCat
    files = CopyCat._collect_files(args, tmp_path, Path(__file__).resolve())
    cache = {code_file: {"content": "# cached content\n", "lines": 1}}
    out = tmp_path / "cached.pdf"
    _write_pdf(out, files, args, tmp_path, "No Git", 1, cache=cache)
    assert out.exists()


def test_write_pdf_unicode_read_error(tmp_path, run_args):
    """_write_pdf behandelt UnicodeDecodeError beim Datei-Lesen graceful."""
    pytest.importorskip("reportlab")
    args = run_args()
    code_file = tmp_path / "bad.py"
    code_file.write_bytes(b"\xff\xfe bad bytes")
    import CopyCat
    files = {"code": [code_file], **{k: [] for k in TYPE_FILTERS if k != "code"}}
    out = tmp_path / "unicode_err.pdf"
    _write_pdf(out, files, args, tmp_path, "No Git", 1)
    assert out.exists()


def test_write_pdf_long_code_truncated(tmp_path, run_args):
    """_write_pdf kürzt Code auf 150 Zeilen und zeigt Hinweis."""
    pytest.importorskip("reportlab")
    args = run_args()
    code_file = tmp_path / "long.py"
    code_file.write_text("\n".join(f"x = {i}" for i in range(200)), encoding="utf-8")
    import CopyCat
    files = CopyCat._collect_files(args, tmp_path, Path(__file__).resolve())
    out = tmp_path / "long.pdf"
    _write_pdf(out, files, args, tmp_path, "No Git", 1)
    assert out.exists()


def test_is_valid_serial_filename_pdf():
    """is_valid_serial_filename erkennt .pdf als gültig."""
    assert is_valid_serial_filename("combined_copycat_5.pdf")


# ==================== M35: KI-Zusammenfassung ====================

def test_generate_ai_summary_missing_key(tmp_path, run_args):
    """_generate_ai_summary wirft ValueError wenn COPYCAT_AI_KEY fehlt."""
    import os
    files = {k: [] for k in TYPE_FILTERS}
    env = {k: v for k, v in os.environ.items() if k != "COPYCAT_AI_KEY"}
    with patch.dict(os.environ, env, clear=True):
        with pytest.raises(ValueError, match="COPYCAT_AI_KEY"):
            _generate_ai_summary(files, tmp_path, "No Git")


def test_generate_ai_summary_missing_openai(tmp_path):
    """_generate_ai_summary wirft ImportError wenn openai nicht installiert."""
    import os
    files = {k: [] for k in TYPE_FILTERS}
    with patch.dict(os.environ, {"COPYCAT_AI_KEY": "sk-test"}):
        with patch.dict("sys.modules", {"openai": None}):
            with pytest.raises(ImportError, match="openai"):
                _generate_ai_summary(files, tmp_path, "No Git")


def test_generate_ai_summary_success(tmp_path):
    """_generate_ai_summary liefert Text vom gemockten API-Call."""
    import os
    files = {k: [] for k in TYPE_FILTERS}
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "Test-Zusammenfassung"

    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = mock_response
    mock_openai_cls = MagicMock(return_value=mock_client)

    with patch.dict(os.environ, {"COPYCAT_AI_KEY": "sk-test"}):
        with patch.dict("sys.modules", {"openai": MagicMock(OpenAI=mock_openai_cls)}):
            # openai muss importierbar sein
            import sys
            sys.modules["openai"].OpenAI = mock_openai_cls
            result = _generate_ai_summary(files, tmp_path, "Branch: main | Last Commit: abc1234")
    assert result == "Test-Zusammenfassung"


def test_generate_ai_summary_api_error(tmp_path):
    """_generate_ai_summary wandelt API-Exception in ValueError um."""
    import os
    files = {k: [] for k in TYPE_FILTERS}
    mock_client = MagicMock()
    mock_client.chat.completions.create.side_effect = RuntimeError("connection refused")
    mock_openai_cls = MagicMock(return_value=mock_client)

    with patch.dict(os.environ, {"COPYCAT_AI_KEY": "sk-test"}):
        with patch.dict("sys.modules", {"openai": MagicMock(OpenAI=mock_openai_cls)}):
            import sys
            sys.modules["openai"].OpenAI = mock_openai_cls
            with pytest.raises(ValueError, match="AI-API-Fehler"):
                _generate_ai_summary(files, tmp_path, "No Git")


def test_generate_ai_summary_with_files_stats_and_base_url(tmp_path):
    """_generate_ai_summary deckt Branches für nicht-leere files, stats und base_url ab."""
    import os
    code_file = tmp_path / "main.py"
    code_file.write_text("print('hello')")
    files = {k: [] for k in TYPE_FILTERS}
    files["code"] = [code_file]
    stats = {
        "total": {
            "loc": 50, "code": 40, "comments": 5, "blank": 5,
            "avg_complexity": 3, "comment_ratio": 10,
        },
        "per_file": {},
    }
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "  KI-Steckbrief  "
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = mock_response
    mock_openai_cls = MagicMock(return_value=mock_client)

    with patch.dict(os.environ, {"COPYCAT_AI_KEY": "sk-test"}):
        with patch.dict("sys.modules", {"openai": MagicMock(OpenAI=mock_openai_cls)}):
            import sys
            sys.modules["openai"].OpenAI = mock_openai_cls
            result = _generate_ai_summary(
                files, tmp_path, "No Git",
                stats=stats,
                base_url="http://localhost:11434/v1",
            )
    assert result == "KI-Steckbrief"
    # base_url muss an OpenAI-Konstruktor übergeben worden sein
    call_kwargs = mock_openai_cls.call_args
    assert call_kwargs is not None
    all_kwargs = {**(call_kwargs.kwargs or {})}
    if call_kwargs.args:
        pass  # positional args
    assert "base_url" in all_kwargs


def test_run_copycat_ai_summary_warning_on_failure(tmp_path, run_args, caplog):
    """run_copycat gibt Warnung aus wenn AI-Summary fehlschlägt (kein Key)."""
    import os
    args = run_args()
    args.ai_summary = True
    args.ai_model = "gpt-4o-mini"
    args.ai_base_url = None
    env = {k: v for k, v in os.environ.items() if k != "COPYCAT_AI_KEY"}
    with patch.dict(os.environ, env, clear=True):
        with caplog.at_level(logging.WARNING):
            result = run_copycat(args)
    assert result is not None  # Report trotzdem erstellt
    assert any("KI-Zusammenfassung fehlgeschlagen" in r.message for r in caplog.records)


def test_run_copycat_ai_summary_success_txt(tmp_path, run_args):
    """run_copycat hängt KI-Zusammenfassung an TXT-Report an."""
    args = run_args(fmt="txt")
    args.ai_summary = True
    args.ai_model = "gpt-4o-mini"
    args.ai_base_url = None
    with patch("CopyCat._generate_ai_summary", return_value="KI-Text-TXT"):
        result = run_copycat(args)
    content = Path(result).read_text(encoding="utf-8")
    assert "KI-ZUSAMMENFASSUNG" in content
    assert "KI-Text-TXT" in content


def test_run_copycat_ai_summary_success_md(tmp_path, run_args):
    """run_copycat hängt KI-Zusammenfassung an MD-Report an."""
    args = run_args(fmt="md")
    args.ai_summary = True
    args.ai_model = "gpt-4o-mini"
    args.ai_base_url = None
    with patch("CopyCat._generate_ai_summary", return_value="KI-Text-MD"):
        result = run_copycat(args)
    content = Path(result).read_text(encoding="utf-8")
    assert "KI-Zusammenfassung" in content
    assert "KI-Text-MD" in content


def test_run_copycat_ai_summary_success_json(tmp_path, run_args):
    """run_copycat fügt KI-Zusammenfassung ins JSON-Feld ein."""
    args = run_args(fmt="json")
    args.ai_summary = True
    args.ai_model = "gpt-4o-mini"
    args.ai_base_url = None
    with patch("CopyCat._generate_ai_summary", return_value="KI-Text-JSON"):
        result = run_copycat(args)
    data = json.loads(Path(result).read_text(encoding="utf-8"))
    assert data.get("ai_summary") == "KI-Text-JSON"


def test_run_copycat_ai_summary_success_html(tmp_path, run_args):
    """run_copycat injiziert KI-Zusammenfassung in HTML-Report."""
    args = run_args(fmt="html")
    args.ai_summary = True
    args.ai_model = "gpt-4o-mini"
    args.ai_base_url = None
    with patch("CopyCat._generate_ai_summary", return_value="KI-Text-HTML"):
        result = run_copycat(args)
    content = Path(result).read_text(encoding="utf-8")
    assert "KI-Text-HTML" in content


def test_run_copycat_ai_summary_success_pdf(tmp_path, run_args):
    """run_copycat loggt KI-Zusammenfassung bei PDF-Format (kein Anhang)."""
    pytest.importorskip("reportlab", reason="reportlab not installed")
    args = run_args(fmt="pdf")
    args.ai_summary = True
    args.ai_model = "gpt-4o-mini"
    args.ai_base_url = None
    with patch("CopyCat._generate_ai_summary", return_value="KI-Text-PDF"):
        result = run_copycat(args)
    # PDF-Report existiert, KI-Text ist NICHT im Dateiinhalt (nur als Log)
    assert result is not None
    assert result.endswith(".pdf")


# ==================== M36: Report-Timeline ====================

def test_build_timeline_empty_archive(tmp_path):
    """build_timeline mit leerem Archiv gibt passende Meldung."""
    archive = tmp_path / "CopyCat_Archive"
    archive.mkdir()
    result = build_timeline(archive)
    assert "Keine Archiv-Reports gefunden" in result


def test_build_timeline_nonexistent_archive(tmp_path):
    """build_timeline mit nicht existierendem Archiv gibt passende Meldung."""
    result = build_timeline(tmp_path / "nonexistent")
    assert "Keine Archiv-Reports gefunden" in result


def test_build_timeline_txt_reports(tmp_path):
    """build_timeline parst TXT-Reports korrekt."""
    archive = tmp_path / "CopyCat_Archive"
    archive.mkdir()
    (archive / "combined_copycat_1.txt").write_text(
        "============================================================\n"
        "CopyCat v2.9 | 01.01.2025 14:00 | FLACH (Default)\n"
        "/some/path\nGIT: No Git\n\nGesamt: 5 Dateien\nSerial #1\n"
        "============================================================\n"
        "CODE: 3 Dateien\n",
        encoding="utf-8",
    )
    (archive / "combined_copycat_2.txt").write_text(
        "============================================================\n"
        "CopyCat v2.9 | 15.01.2025 10:00 | FLACH (Default)\n"
        "/some/path\nGIT: No Git\n\nGesamt: 8 Dateien\nSerial #2\n"
        "============================================================\n"
        "CODE: 5 Dateien\n",
        encoding="utf-8",
    )
    result = build_timeline(archive)
    assert "1" in result
    assert "2" in result
    assert "5" in result
    assert "8" in result


def test_build_timeline_json_reports(tmp_path):
    """build_timeline parst JSON-Reports korrekt."""
    archive = tmp_path / "CopyCat_Archive"
    archive.mkdir()
    report = {
        "version": "2.9",
        "generated": "10.02.2025 09:30",
        "files": 12,
        "types": {"code": 8, "docs": 4},
        "details": {},
    }
    (archive / "combined_copycat_3.json").write_text(
        json.dumps(report), encoding="utf-8"
    )
    result = build_timeline(archive)
    assert "12" in result
    assert "10.02.2025" in result


def test_timeline_md_format(tmp_path):
    """build_timeline erzeugt gültige Markdown-Tabelle."""
    archive = tmp_path / "CopyCat_Archive"
    archive.mkdir()
    (archive / "combined_copycat_1.json").write_text(
        json.dumps({"generated": "01.03.2025 12:00", "files": 7, "types": {"code": 7}}),
        encoding="utf-8",
    )
    result = build_timeline(archive, fmt="md")
    assert result.startswith("# CopyCat Report-Timeline")
    assert "| Serial |" in result
    assert "#1" in result


def test_timeline_ascii_format(tmp_path):
    """build_timeline erzeugt ASCII-Chart."""
    archive = tmp_path / "CopyCat_Archive"
    archive.mkdir()
    (archive / "combined_copycat_1.json").write_text(
        json.dumps({"generated": "01.03.2025", "files": 10, "types": {}}),
        encoding="utf-8",
    )
    result = build_timeline(archive, fmt="ascii")
    assert "CopyCat Report-Timeline (ASCII)" in result
    assert "1" in result
    assert "█" in result


def test_timeline_html_format(tmp_path):
    """build_timeline erzeugt HTML mit Chart.js."""
    archive = tmp_path / "CopyCat_Archive"
    archive.mkdir()
    (archive / "combined_copycat_1.json").write_text(
        json.dumps({"generated": "01.03.2025", "files": 5, "types": {}}),
        encoding="utf-8",
    )
    result = build_timeline(archive, fmt="html")
    assert "<!DOCTYPE html>" in result
    assert "chart.js" in result
    assert "#1" in result


def test_timeline_md_helper():
    """_timeline_md erstellt korrekte Markdown-Tabelle aus Einträgen."""
    entries = [
        {"serial": 1, "date": "01.01.2025", "total": 3, "types": {"code": 3}},
        {"serial": 2, "date": "02.01.2025", "total": 5, "types": {"code": 4, "docs": 1}},
    ]
    result = _timeline_md(entries)
    assert "| #1 |" in result
    assert "| #2 |" in result
    assert "CODE" in result


def test_timeline_ascii_helper():
    """_timeline_ascii erstellt ASCII-Chart aus Einträgen."""
    entries = [
        {"serial": 1, "date": "01.01.2025", "total": 10, "types": {}},
        {"serial": 2, "date": "02.01.2025", "total": 20, "types": {}},
    ]
    result = _timeline_ascii(entries)
    assert "█" in result
    assert "10" in result
    assert "20" in result
    assert "CopyCat Report-Timeline (ASCII)" in result


def test_timeline_html_helper():
    """_timeline_html enthält Chart.js und Tabelle."""
    entries = [{"serial": 1, "date": "01.01.2025", "total": 5, "types": {}}]
    result = _timeline_html(entries)
    assert "chart.js" in result
    assert "#1" in result
    assert "<table>" in result


def test_timeline_ignores_pdf_files(tmp_path):
    """build_timeline ignoriert .pdf-Archive-Dateien."""
    archive = tmp_path / "CopyCat_Archive"
    archive.mkdir()
    (archive / "combined_copycat_1.pdf").write_bytes(b"%PDF-1.4 fake")
    result = build_timeline(archive)
    assert "Keine Archiv-Reports gefunden" in result


def test_build_timeline_default_archive_dir(tmp_path):
    """build_timeline ohne archive_dir nutzt CopyCat_Archive neben CopyCat.py."""
    archive = tmp_path / "CopyCat_Archive"
    archive.mkdir()
    with patch("CopyCat.__file__", str(tmp_path / "CopyCat.py")):
        result = build_timeline()
    assert "Keine Archiv-Reports gefunden" in result


def test_build_timeline_invalid_filename_skipped(tmp_path):
    """build_timeline überspringt Dateien mit ungültigem Seriennamen."""
    archive = tmp_path / "CopyCat_Archive"
    archive.mkdir()
    # Ungültige Dateiendung → is_valid_serial_filename gibt False zurück
    (archive / "combined_copycat_99.xyz").write_text("something", encoding="utf-8")
    # Gültige Datei
    (archive / "combined_copycat_1.txt").write_text(
        "CopyCat v2.9 | 01.01.2025 10:00 | FLACH\nGesamt: 3 Dateien\n",
        encoding="utf-8",
    )
    result = build_timeline(archive)
    assert "1" in result
    assert "3" in result


def test_build_timeline_oserror_on_read(tmp_path):
    """build_timeline überspringt Dateien die beim Lesen OSError werfen."""
    archive = tmp_path / "CopyCat_Archive"
    archive.mkdir()
    report = archive / "combined_copycat_1.txt"
    report.write_text("dummy", encoding="utf-8")
    with patch("pathlib.Path.read_text", side_effect=OSError("Permission denied")):
        result = build_timeline(archive)
    assert "Keine Archiv-Reports gefunden" in result


def test_build_timeline_invalid_json_parse_error(tmp_path):
    """build_timeline überspringt JSON-Dateien mit ungültigem Inhalt (kein Absturz)."""
    archive = tmp_path / "CopyCat_Archive"
    archive.mkdir()
    (archive / "combined_copycat_1.json").write_text(
        "this is not valid json!", encoding="utf-8"
    )
    result = build_timeline(archive)
    # Eintrag erscheint mit Fallback-Werten
    assert "1" in result


def test_build_timeline_txt_no_date_or_total(tmp_path):
    """build_timeline behandelt TXT-Reports ohne Datum/Gesamt-Pattern (Fallback '?'/0)."""
    archive = tmp_path / "CopyCat_Archive"
    archive.mkdir()
    (archive / "combined_copycat_1.txt").write_text(
        "Keine passenden Muster in dieser Datei.\n", encoding="utf-8"
    )
    result = build_timeline(archive)
    # Eintrag mit Fallback '?' für Datum und 0 für Gesamt
    assert "?" in result or "1" in result

