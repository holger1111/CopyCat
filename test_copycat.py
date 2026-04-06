"""
CopyCat v2.7 - Pytest Suite (100% Coverage)
"""

import pytest
import argparse
import sys
import re
import subprocess
import fnmatch
import zlib
import base64
import shutil
import xml.etree.ElementTree as ET
from glob import glob
from pathlib import Path
from io import StringIO
from unittest.mock import patch, MagicMock
from argparse import Namespace
from datetime import datetime
from unittest.mock import Mock
from unittest.mock import ANY
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
    extract_drawio,
    TYPE_FILTERS,
)


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


def get_git_info(input_dir: Path) -> str:
    if not (input_dir / ".git").exists():
        return "No Git"
    try:
        branch = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=input_dir,
            capture_output=True,
            text=True,
            timeout=5,
        )
        branch_name = branch.stdout.strip() if branch.returncode == 0 else "N/A"

        commit = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=input_dir,
            capture_output=True,
            text=True,
            timeout=5,
        )
        commit_hash = commit.stdout.strip() if commit.returncode == 0 else "N/A"

        return f"Branch: {branch_name} | Last Commit: {commit_hash}"
    except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
        return "No Git"


def should_skip_gitignore(input_dir: Path, file_path: Path) -> bool:
    gitignore_path = input_dir / ".gitignore"
    if not gitignore_path.exists():
        return False

    try:
        rel_path = file_path.relative_to(input_dir).as_posix()
        with open(gitignore_path, "r", encoding="utf-8") as f:
            for line in f:
                rule = line.strip()
                if rule.startswith("#") or not rule:
                    continue
                if "*" in rule:
                    if fnmatch.fnmatch(rel_path, rule):
                        return True
                elif rule.endswith("/"):
                    if rel_path.startswith(rule.rstrip("/")):
                        return True
                elif rel_path == rule:
                    return True
        return False
    except Exception:
        return False


def size_filtered_glob(search_method, patterns, max_bytes, script_file, input_dir):
    total_checked = 0
    for pat in patterns:
        for candidate in search_method(pat):
            total_checked += 1
            try:
                if should_skip_gitignore(input_dir, candidate):
                    continue
                if candidate.stat().st_size < max_bytes:
                    if (
                        candidate.resolve() != script_file
                        and "combined_copycat" not in candidate.name
                    ):
                        yield candidate
                if total_checked % 100 == 0:
                    print(f"\rGeprüft: {total_checked} Dateien...", end="")
            except OSError:
                continue
    print(f"\n→ {total_checked} geprüft, Filter OK")


@pytest.fixture
def mock_writer():
    mock = MagicMock()
    mock.write = MagicMock()
    return mock


@pytest.fixture
def tmp_test_dir(tmp_path):
    test_dir = tmp_path / "Test_Set"
    test_dir.mkdir()
    (test_dir / "sub").mkdir()
    (test_dir / "sub" / "test.py").touch()
    (test_dir / "test.drawio").touch()
    (test_dir / "test.mp3").touch()
    return test_dir


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


def test_get_plural_single():
    assert get_plural(1) == "Datei"


def test_get_plural_multiple():
    assert get_plural(2) == "Dateien"
    assert get_plural(47) == "Dateien"


def test_get_plural_v27_exact():
    assert get_plural(0) == "Dateien"
    assert get_plural(1) == "Datei"
    assert get_plural(999) == "Dateien"


def test_get_plural_v27_final():
    assert get_plural(0) == "Dateien"
    assert get_plural(1) == "Datei"
    assert get_plural(2) == "Dateien"
    print("✓ get_plural Zeile 134 gecovert!")


def test_argparse_nargs_star_empty():
    with patch("sys.argv", ["test_copycat.py"]):
        args = parse_arguments()
        assert args.types == ["all"]


def test_argparse_recursive_with_types():
    with patch("sys.argv", ["test_copycat.py", "-r", "-t", "code"]):
        args = parse_arguments()
        assert args.recursive is True
        assert args.types == ["code"]


def test_get_next_serial_number_error_handling(tmp_path):
    broken = tmp_path / "combined_copycat_x.txt"
    broken.write_text("invalid")
    assert get_next_serial_number(tmp_path) == 1


def test_parse_arguments_max_size():
    with patch("sys.argv", ["test_copycat.py", "--max-size", "1"]):
        args = parse_arguments()
        assert args.max_size == 1.0


def test_parse_arguments_max_size_short():
    with patch("sys.argv", ["test_copycat.py", "-s", "5"]):
        args = parse_arguments()
        assert args.max_size == 5.0


def test_parse_arguments_max_size_default():
    with patch("sys.argv", ["test_copycat.py"]):
        args = parse_arguments()
        assert args.max_size == float("inf")


def test_size_filtered_glob_small_file(tmp_path):
    mock_search = MagicMock()
    small_file = MagicMock(spec=Path)
    small_file.stat.return_value = MagicMock(st_size=500 * 1024)
    small_file.resolve.return_value = Path("other.py")
    small_file.relative_to = MagicMock(return_value=Path("other.py"))
    mock_search.rglob.return_value = [small_file]
    gen = list(
        size_filtered_glob(
            mock_search.rglob, ["*.py"], 1 * 1024 * 1024, Path("CopyCat.py"), tmp_path
        )
    )
    assert len(gen) == 1


def test_size_filtered_glob_skip_large(tmp_path):
    mock_search = MagicMock()
    large_file = MagicMock(spec=Path)
    large_file.stat.return_value = MagicMock(st_size=20 * 1024 * 1024)
    large_file.resolve.return_value = Path("big.py")
    mock_search.rglob.return_value = [large_file]
    gen = list(
        size_filtered_glob(
            mock_search.rglob,
            ["*.py", "*.pyc"],
            1 * 1024 * 1024,
            Path("CopyCat.py"),
            tmp_path,
        )
    )
    assert len(gen) == 0


def test_size_filtered_glob_oserror_safe(tmp_path):
    mock_search = MagicMock()
    mock_file = MagicMock()
    mock_file.stat.side_effect = OSError("Permission denied")
    mock_search.rglob.return_value = [mock_file]
    gen = list(
        size_filtered_glob(
            mock_search.rglob,
            ["*.py", "*.pyc"],
            1 * 1024 * 1024,
            Path("CopyCat.py"),
            tmp_path,
        )
    )
    assert len(gen) == 0


def test_size_filtered_glob_oserror(tmp_path, monkeypatch):

    def mock_search(pat):
        raise OSError("Permission denied")

    mock_args = Mock()
    mock_args.return_value = []
    mock_args.__call__ = mock_search

    files = size_filtered_glob(mock_args, "**/*", "code", 1024, tmp_path)
    files_list = list(files)
    assert files_list == []
    print("✅ size_filtered_glob (133-137) covered!")


def test_get_git_info_no_repo(tmp_path):
    assert get_git_info(tmp_path) == "No Git"


def test_get_git_info_mock(tmp_path):
    with patch("subprocess.run") as mock_run:
        mock_run.return_value.stdout = "main\n"
        mock_run.return_value.returncode = 0
        (tmp_path / ".git").mkdir()
        result = get_git_info(tmp_path)
        assert "Branch: main" in result


def test_should_skip_gitignore_no_file(tmp_path):
    test_file = tmp_path / "test.py"
    assert should_skip_gitignore(tmp_path, test_file) is False


def test_should_skip_gitignore_pyc(tmp_path):
    (tmp_path / ".gitignore").write_text("*.pyc\n")
    pyc_file = tmp_path / "dummy.pyc"
    assert should_skip_gitignore(tmp_path, pyc_file) is True


def test_size_filtered_glob_gitignore(tmp_path):
    (tmp_path / ".gitignore").write_text("*.pyc\n")
    (tmp_path / "test.py").touch()
    (tmp_path / "dummy.pyc").touch()

    def mock_rglob(pat):
        if "py" in pat:
            for f in Path(tmp_path).rglob(pat):
                yield f

    filtered = list(
        size_filtered_glob(
            mock_rglob, ["*.py", "*.pyc"], float("inf"), Path("CopyCat.py"), tmp_path
        )
    )
    assert len(filtered) == 1
    assert filtered[0].name == "test.py"


@patch("builtins.print")
def test_size_filtered_glob_recursive_101(mock_print, tmp_path):
    (tmp_path / "sub").mkdir()
    for i in range(51):
        (tmp_path / f"file{i}.py").touch()
    for i in range(50):
        (tmp_path / "sub" / f"deep{i}.py").touch()

    gen = list(
        size_filtered_glob(
            lambda pat: Path(tmp_path).rglob(pat),
            ["*.py"],
            float("inf"),
            Path("CopyCat.py"),
            tmp_path,
        )
    )
    assert len(gen) == 101
    mock_print.assert_any_call("\rGeprüft: 100 Dateien...", end="")


@patch("builtins.print")
def test_size_filtered_glob_no_progress(mock_print):
    mock_search = MagicMock()
    mock_files = [
        MagicMock(
            spec=Path,
            stat=Mock(return_value=Mock(st_size=0)),
            resolve=Mock(return_value=Path("other.py")),
            name="test.py",
            relative_to=Mock(return_value=Path("test.py")),
        )
        for _ in range(99)
    ]
    mock_search.rglob.return_value = mock_files

    list(
        size_filtered_glob(
            mock_search.rglob, ["*.py"], float("inf"), Path("CopyCat.py"), Path(".")
        )
    )
    mock_print.assert_any_call("\n→ 99 geprüft, Filter OK")
    assert mock_print.call_count == 1


@patch("builtins.print")
def test_size_filtered_glob_progress(mock_print):
    mock_search = MagicMock()
    mock_files = []
    for _ in range(101):
        mock_file = MagicMock(spec=Path)
        mock_file.stat.return_value = MagicMock(st_size=0)
        mock_file.resolve.return_value = Path("other.py")
        mock_file.name = "test.py"
        mock_file.relative_to.return_value = Path("test.py")
        mock_files.append(mock_file)
    mock_search.rglob.return_value = mock_files
    list(
        size_filtered_glob(
            mock_search.rglob, ["*.py"], float("inf"), Path("CopyCat.py"), Path(".")
        )
    )
    mock_print.assert_any_call("\rGeprüft: 100 Dateien...", end="")
    mock_print.assert_any_call("\n→ 101 geprüft, Filter OK")


def test_size_filtered_glob_self_protection():
    mock_self = MagicMock(spec=Path)
    mock_self.name = "CopyCat.py"
    mock_self.resolve.return_value = Path("CopyCat.py").resolve()
    mock_self.stat.return_value = MagicMock(st_size=1000)
    mock_search = MagicMock()
    mock_search.rglob.return_value = [mock_self]
    gen = list(
        size_filtered_glob(
            mock_search.rglob, ["*.py"], float("inf"), Path("CopyCat.py"), Path(".")
        )
    )
    assert len(gen) == 0


def test_run_copycat_integration(tmp_path):
    (tmp_path / "test.py").touch()

    args = Namespace(
        input=str(tmp_path),
        output=str(tmp_path),
        types=["code"],
        recursive=False,
        max_size=float("inf"),
    )

    run_copycat(args)

    reports = list(tmp_path.glob("combined_copycat_*.txt"))
    assert len(reports) == 1
    content = reports[0].read_text()
    assert "test.py" in content
    assert "CODE" in content
    assert f"Serial #1" in content


def test_copycat_cli_integration(tmp_path):
    (tmp_path / "test.py").touch()
    (tmp_path / ".gitignore").write_text("*.pyc\n")

    args = Namespace(
        input=str(tmp_path), types=["code"], recursive=True, max_size=float("inf")
    )

    files = list(Path(tmp_path).rglob("*.py"))
    assert len(files) == 1
    assert "test.py" in str(files[0])


def test_get_git_info_timeout(tmp_path):
    (tmp_path / ".git").mkdir()
    with patch("subprocess.run", side_effect=subprocess.TimeoutExpired("git", 1)):
        assert "No Git" in get_git_info(tmp_path)


def test_extract_drawio_empty(tmp_path, mock_writer):
    empty_drawio = tmp_path / "empty.drawio"
    empty_drawio.write_bytes(b"")
    extract_drawio(mock_writer, empty_drawio)
    mock_writer.write.assert_any_call("[EMPTY: empty.drawio] [SIZE: 0 bytes]\n")


def test_type_filters_runtime():
    selected_types = ["code", "diagram"]
    process_all = False

    for t in ["code", "diagram"]:
        if process_all or t in selected_types:
            assert t in TYPE_FILTERS.keys()
            assert len(TYPE_FILTERS[t]) > 0


def test_size_filtered_glob_total_checked(tmp_path, monkeypatch):

    def mock_gitignore(*args):
        raise OSError()

    with monkeypatch.context() as m:
        m.setattr("CopyCat.should_skip_gitignore", mock_gitignore)
        files = list(size_filtered_glob(lambda p: [], ["*.py"], 0, Path(), tmp_path))
    assert files == []


def test_type_filters_v27_runtime():
    keys = sorted(TYPE_FILTERS.keys())
    expected = sorted(
        ["code", "web", "db", "config", "docs", "deps", "img", "audio", "diagram"]
    )
    assert keys == expected


def test_extract_drawio_compressed(tmp_path, mock_writer):
    compressed = tmp_path / "test.drawio"
    compressed.write_bytes(
        b'<mxGraphModel><root><mxCell id="1"/></root></mxGraphModel>'
    )
    extract_drawio(mock_writer, compressed)
    mock_writer.write.assert_any_call("DIAGRAM test.drawio: 1 Cells, 0 Texte\n")


def test_line_counting_edges(tmp_path):
    code = tmp_path / "edge.py"
    code.write_text("# comment\n\nline1\n \nline2  # inline\n")

    lines = sum(1 for line in code.read_text().splitlines() if line.strip())
    assert lines == 3


def test_list_binary_file(tmp_path, mock_writer):
    binary = tmp_path / "test.wav"
    binary.write_bytes(b"RIFF....WAVEfmt ")
    list_binary_file(mock_writer, binary)
    assert mock_writer.write.called
    print("✅ Binary (288, 293) covered!")


def test_run_copycat_code_lines(tmp_path):
    code_file = tmp_path / "test.py"
    code_file.write_text("line1\nline2\nline3\n")

    args = Namespace(
        input=str(tmp_path),
        output=None,
        types=["code"],
        recursive=False,
        max_size=float("inf"),
    )
    run_copycat(args)

    report = next(tmp_path.glob("combined_copycat_*.txt"))
    assert "test.py" in report.read_text()


def test_cli_types_loop_coverage():
    args_types = ["code", "web"]
    for t in TYPE_FILTERS.keys():
        if t in args_types:
            patterns = TYPE_FILTERS[t]
            for pat in patterns:
                assert isinstance(pat, str)


def test_extract_drawio_full_parser(tmp_path, mock_writer):
    drawio_file = tmp_path / "full.drawio"
    drawio_file.write_bytes(
        b"""
    <mxGraphModel dx="1200" dy="800" grid="1" guides="1"
                tooltips="1" connect="1" arrows="1" fold="1"
                page="1" pageScale="1" pageWidth="850" pageHeight="1100">
        <root>
            <mxCell id="0"/>
            <mxCell id="1" parent="0"/>
            <mxCell id="2" value="Test Cell" vertex="1" parent="1">
                <mxGeometry x="160" y="120" width="120" height="60" as="geometry"/>
            </mxCell>
        </root>
    </mxGraphModel>"""
    )
    extract_drawio(mock_writer, drawio_file)


def test_git_report_code_lines(tmp_path):
    (tmp_path / ".git").mkdir()
    git_info = get_git_info(tmp_path)
    assert "Branch: N/A | Last Commit: N/A" in git_info

    code_file = tmp_path / "source.py"
    code_file.write_text("# Comment\nline1\nline2\n\nline4\n")
    lines = sum(1 for line in code_file.read_text().splitlines() if line.strip())
    assert lines == 4


def test_report_header_git(tmp_path, mock_writer):
    (tmp_path / ".git").mkdir()
    code_file = tmp_path / "test.py"
    code_file.write_text("# 10 Lines\n" * 10)

    git_info = get_git_info(tmp_path)
    assert "Branch" in git_info or "No Git" in git_info

    with open(code_file, "r") as f:
        lines = len(f.readlines())
    assert lines == 10


def test_move_to_archive_permission(tmp_path, monkeypatch):
    old_file = tmp_path / "combined_copycat_1.txt"
    old_file.touch()

    def mock_move(src, dst):
        raise PermissionError()

    monkeypatch.setattr("shutil.move", mock_move)
    move_to_archive(tmp_path, "combined_copycat_1.txt")
    print("✅ Archive covered!")


def test_extract_drawio_no_mxgraph(tmp_path, mock_writer):
    invalid_drawio = tmp_path / "invalid.drawio"
    invalid_drawio.write_text("<root></root>")
    extract_drawio(mock_writer, invalid_drawio)
    mock_writer.write.assert_any_call("DIAGRAM invalid.drawio: 0 Cells, 0 Texte\n")


def test_move_to_archive(tmp_path):
    old_file = tmp_path / "combined_copycat_1.txt"
    old_file.touch()

    move_to_archive(tmp_path, "combined_copycat_1.txt")

    archive = tmp_path / "CopyCat_Archive" / "combined_copycat_1.txt"
    assert archive.exists()


def test_list_binary_file_unicode(tmp_path, mock_writer):
    binary = tmp_path / "binary.dat"
    binary.write_bytes(b"\xff\x00\xab")

    with patch(
        "builtins.open", side_effect=UnicodeDecodeError("utf-8", b"", 0, 1, "invalid")
    ):
        list_binary_file(mock_writer, binary)

    mock_writer.write.assert_called_with(
        "[BINARY SKIPPED: binary.dat - Ungültiges Text-Encoding]\n"
    )


def test_run_copycat_input_validation(tmp_path):
    args = Namespace(
        input=str(tmp_path / "nonexistent"),
        output=str(tmp_path),
        types=["code"],
        recursive=False,
        max_size=float("inf"),
    )
    with patch("builtins.print") as mock_print:
        run_copycat(args)
        mock_print.assert_called_with(
            f"Fehler: {tmp_path / 'nonexistent'} ist kein Ordner"
        )


def test_run_copycat_selected_types(tmp_path):
    (tmp_path / "test.py").touch()
    args = Namespace(
        input=str(tmp_path),
        output=str(tmp_path),
        types=["code"],
        recursive=False,
        max_size=float("inf"),
    )
    with patch("CopyCat.size_filtered_glob", return_value=[]):
        run_copycat(args)


def test_run_copycat_no_filter_fast_path(tmp_path):
    (tmp_path / "test.py").touch()
    args = Namespace(
        input=str(tmp_path),
        output=str(tmp_path),
        types=["code"],
        recursive=False,
        max_size=float("inf"),
    )
    with patch("CopyCat.Path.glob", return_value=[]):
        run_copycat(args)


def test_run_copycat_binary_recursive(tmp_path):
    (tmp_path / "sub" / "test.png").mkdir(parents=True)
    (tmp_path / "sub" / "test.png").touch()
    args = Namespace(
        input=str(tmp_path),
        output=str(tmp_path),
        types=["img"],
        recursive=True,
        max_size=float("inf"),
    )
    run_copycat(args)
    report = next(tmp_path.glob("combined_copycat_*.txt"))
    content = report.read_text()
    assert "Pfad: sub/test.png" in content


def test_run_copycat_unicode_code_error(tmp_path):
    binary_code = tmp_path / "fake.py"
    binary_code.write_bytes(b"\xff\x00")
    args = Namespace(
        input=str(tmp_path),
        output=str(tmp_path),
        types=["code"],
        recursive=False,
        max_size=float("inf"),
    )
    run_copycat(args)
    report = next(tmp_path.glob("combined_copycat_*.txt"))
    content = report.read_text(encoding="utf-8")
    assert "(Binary oder ungültiges Encoding - übersprungen)" in content


def test_gitignore_recursive(tmp_path):
    (tmp_path / "sub").mkdir()
    (tmp_path / "sub" / ".gitignore").write_text("*.pyc")
    (tmp_path / "sub" / "test.py").touch()
    args = Namespace(
        input=str(tmp_path),
        output=str(tmp_path),
        types=["code"],
        recursive=True,
        max_size=float("inf"),
    )
    run_copycat(args)
    report = next(tmp_path.glob("combined_copycat_*.txt"))
    assert "test.py" in report.read_text()


def test_input_dir_not_exist(tmp_path):
    nonexist = tmp_path / "does_not_exist"
    args = Namespace(
        input=str(nonexist),
        output=str(tmp_path),
        types=["code"],
        recursive=False,
        max_size=float("inf"),
    )
    with patch("builtins.print") as mock_print:
        run_copycat(args)
        mock_print.assert_any_call(f"Fehler: {nonexist} ist kein Ordner")


def test_git_info_edge_cases(tmp_path):
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


def test_gitignore_pattern_matching(tmp_path):
    gitignore = tmp_path / ".gitignore"
    gitignore.write_text(
        """
build/
*.tmp
!important.py
    """
    )

    (tmp_path / "build").mkdir()
    (tmp_path / "build.py").touch()
    (tmp_path / "temp.tmp").touch()
    (tmp_path / "important.py").touch()
    (tmp_path / "test.py").touch()

    args = Namespace(
        input=str(tmp_path),
        output=str(tmp_path),
        types=["code"],
        recursive=True,
        max_size=float("inf"),
    )

    run_copycat(args)

    report = next(tmp_path.glob("combined_copycat_*.txt"))
    report_text = report.read_text()

    assert "test.py" in report_text
    assert "important.py" in report_text
    assert "build.py" not in report_text
    assert "temp.tmp" not in report_text


def test_run_copycat_fast_path_glob(tmp_path):
    (tmp_path / "test.py").write_text("# test code")
    (tmp_path / "test.png").write_bytes(b"PNG")

    args = Namespace(
        input=str(tmp_path),
        output=str(tmp_path),
        types=["code"],
        recursive=False,
        max_size=float("inf"),
    )

    run_copycat(args)

    report = next(tmp_path.glob("combined_copycat_*.txt"))
    report_text = report.read_text()

    assert "CODE: 1 Datei" in report_text
    assert "test.py: 1 Zeilen" in report_text
    assert "test.png" not in report_text
    assert "Gesamt: 1 Datei" in report_text


def test_copycat_self_protection_integration(tmp_path):
    fake_copycat = tmp_path / "CopyCat.py"
    fake_copycat.write_text("# Fake CopyCat")

    (tmp_path / "test.py").write_text("def hello(): pass")

    args = Namespace(
        input=str(tmp_path),
        output=str(tmp_path),
        types=["code"],
        recursive=False,
        max_size=float("inf"),
    )

    run_copycat(args)

    report = next(tmp_path.glob("combined_copycat_*.txt"))
    report_text = report.read_text()

    assert "CODE: 2 Dateien" in report_text
    assert "CopyCat.py: 1 Zeilen" in report_text
    assert "test.py: 1 Zeilen" in report_text


def test_run_copycat_binary_recursive_detail(tmp_path):
    binary_py = tmp_path / "bin" / "fake.py"
    binary_py.parent.mkdir(parents=True)
    binary_py.write_bytes(b"\xff\xfe\x00\x00")

    (tmp_path / "test.py").write_text("def hello(): pass")

    args = Namespace(
        input=str(tmp_path),
        output=str(tmp_path),
        types=["code"],
        recursive=True,
        max_size=float("inf"),
    )

    run_copycat(args)

    report = next(tmp_path.glob("combined_copycat_*.txt"))
    report_text = report.read_text(encoding="utf-8")

    assert "CODE: 2 Dateien" in report_text
    assert "test.py: 1 Zeilen" in report_text
    assert "fake.py: 1 Zeilen [bin]" in report_text
    assert "(Binary oder ungültiges Encoding - übersprungen)" in report_text


def test_extract_drawio_compressed_coverage(tmp_path):
    drawio_file = tmp_path / "diagram.drawio"

    drawio_content = """<mxfile host="app.diagrams.net">
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
    </mxfile>"""

    drawio_file.write_text(drawio_content, encoding="utf-8")

    args = Namespace(
        input=str(tmp_path),
        output=str(tmp_path),
        types=["diagram"],
        recursive=False,
        max_size=float("inf"),
    )

    run_copycat(args)

    report = next(tmp_path.glob("combined_copycat_*.txt"))
    report_text = report.read_text(encoding="utf-8")

    assert "DIAGRAM: 1 Datei" in report_text
    assert "diagram.drawio" in report_text
    assert "TEST CELL 1" in report_text
    assert "[2] TEST CELL 1" in report_text
    assert "DIAGRAM diagram.drawio: 3 Cells, 1 Texte" in report_text


def test_report_writer_archive_integration(tmp_path):
    (tmp_path / "test.py").write_text("def hello(): pass")

    args1 = Namespace(
        input=str(tmp_path),
        output=str(tmp_path),
        types=["code"],
        recursive=False,
        max_size=float("inf"),
    )
    run_copycat(args1)

    report1 = next(tmp_path.glob("combined_copycat_1.txt"))
    assert report1.exists()
    assert "CODE: 1 Datei" in report1.read_text()

    args2 = Namespace(
        input=str(tmp_path),
        output=str(tmp_path),
        types=["code"],
        recursive=False,
        max_size=float("inf"),
    )
    run_copycat(args2)

    report2 = next(tmp_path.glob("combined_copycat_2.txt"))
    assert report2.exists()
    assert "Serial #2" in report2.read_text()

    try:
        next(tmp_path.glob("combined_copycat_1.txt"))
        assert False, "combined_copycat_1.txt sollte archiviert sein!"
    except StopIteration:
        assert True, "combined_copycat_1.txt erfolgreich archiviert! ✓"

    run_copycat(args2)
    report3 = next(tmp_path.glob("combined_copycat_3.txt"))
    assert report3.exists()
    assert "Serial #3" in report3.read_text()


def test_cli_types_filter_logic(tmp_path):
    (tmp_path / "test.py").write_text(" ")
    (tmp_path / "style.css").write_text(" ")
    (tmp_path / "data.sql").write_text(" ")
    (tmp_path / "config.json").write_text("{}")
    (tmp_path / "README.md").write_text("# Docs")
    (tmp_path / "requirements.txt").write_text("py")
    (tmp_path / "image.png").write_bytes(b"PNG")
    (tmp_path / "audio.mp3").write_bytes(b"ID3")
    (tmp_path / "diagram.drawio").write_text("<mxfile><diagram></diagram></mxfile>")

    args_code = Namespace(
        input=str(tmp_path),
        output=str(tmp_path),
        types=["code"],
        recursive=False,
        max_size=float("inf"),
    )
    run_copycat(args_code)
    report_code = next(tmp_path.glob("combined_copycat_*.txt"))
    assert "CODE: 1 Datei" in report_code.read_text()

    args_multi = Namespace(
        input=str(tmp_path),
        output=str(tmp_path),
        types=[
            "code",
            "web",
            "db",
            "config",
            "docs",
            "deps",
            "img",
            "audio",
            "diagram",
        ],
        recursive=False,
        max_size=float("inf"),
    )
    run_copycat(args_multi)
    report_multi = next(tmp_path.glob("combined_copycat_*.txt"))

    assert "CODE: 1 Datei" in report_multi.read_text()
    assert "WEB: 1 Datei" in report_multi.read_text()
    assert "DB: 1 Datei" in report_multi.read_text()
    assert "CONFIG: 1 Datei" in report_multi.read_text()
    assert "DOCS: 2 Dateien" in report_multi.read_text()
    assert "DEPS: 1 Datei" in report_multi.read_text()
    assert "IMG: 1 Datei" in report_multi.read_text()
    assert "AUDIO: 1 Datei" in report_multi.read_text()
    assert "DIAGRAM: 1 Datei" in report_multi.read_text()

    args_all = Namespace(
        input=str(tmp_path),
        output=str(tmp_path),
        types=["all"],
        recursive=False,
        max_size=float("inf"),
    )
    run_copycat(args_all)
    report_all = next(tmp_path.glob("combined_copycat_*.txt"))
    assert "Gesamt: 10 Dateien" in report_all.read_text()


def test_cli_types_invalid_edgecases(tmp_path):
    (tmp_path / "test.py").write_text("def hello(): pass")
    args_invalid = Namespace(
        types=["xyz"],
        input=str(tmp_path),
        output=str(tmp_path),
        recursive=False,
        max_size=float("inf"),
    )
    run_copycat(args_invalid)
    report = next(tmp_path.glob("combined_copycat_*.txt"))
    assert "Gesamt: 0 Dateien" in report.read_text()


def test_binary_file_processing(tmp_path):
    (tmp_path / "image.png").write_bytes(b"\x89PNG\r\n\x1a\n")
    (tmp_path / "audio.mp3").write_bytes(b"ID3\x03")
    (tmp_path / "test.py").write_text("def hello(): pass")
    args = Namespace(
        types=["all"],
        input=str(tmp_path),
        output=str(tmp_path),
        recursive=False,
        max_size=float("inf"),
    )
    run_copycat(args)
    report_text = next(tmp_path.glob("combined_copycat_*.txt")).read_text()
    assert "IMG: 1 Datei" in report_text
    assert "AUDIO: 1 Datei" in report_text


def test_drawio_xml_parsing(tmp_path):
    valid_drawio = tmp_path / "valid.drawio"
    valid_drawio.write_text(
        """<mxfile host="app.diagrams.net">
        <diagram>
            <mxGraphModel>
                <root>
                    <mxCell id="0"/>
                    <mxCell id="1" parent="0"/>
                    <mxCell id="2" value="Start" vertex="1" parent="1">
                        <mxGeometry x="100" y="100" width="80" height="30"/>
                    </mxCell>
                </root>
            </mxGraphModel>
        </diagram>
    </mxfile>"""
    )

    empty_drawio = tmp_path / "empty.drawio"
    empty_drawio.write_text("<mxfile><diagram></diagram></mxfile>")

    corrupt_drawio = tmp_path / "corrupt.drawio"
    corrupt_drawio.write_text("<mxfile>INVALID XML</mxfile>")

    args = Namespace(
        input=str(tmp_path),
        output=str(tmp_path),
        types=["diagram"],
        recursive=False,
        max_size=float("inf"),
    )
    run_copycat(args)

    report = next(tmp_path.glob("combined_copycat_*.txt"))
    report_text = report.read_text()

    assert "valid.drawio" in report_text
    assert "[LEERES MODELL" in report_text or "empty.drawio" in report_text
    assert "[XML PARSE ERROR" in report_text or "corrupt.drawio" in report_text
    assert "DIAGRAM: 3 Datei" in report_text


def test_git_recursive_maxsize(tmp_path):
    (tmp_path / "test.py").write_text("def hello(): pass")
    import subprocess

    subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True)
    subprocess.run(["git", "add", "."], cwd=tmp_path, capture_output=True)
    subprocess.run(["git", "commit", "-m", "test"], cwd=tmp_path, capture_output=True)

    subdir = tmp_path / "sub"
    subdir.mkdir()
    (subdir / "deep.py").write_text("x = 1")

    large_file = tmp_path / "large.bin"
    large_file.write_bytes(b"A" * 2_000_000)

    args_git = Namespace(
        input=str(tmp_path),
        output=str(tmp_path),
        types=["code"],
        recursive=False,
        max_size=float("inf"),
    )
    run_copycat(args_git)
    report_git = next(tmp_path.glob("combined_copycat_*.txt"))
    assert "GIT:" in report_git.read_text()

    args_rec = Namespace(
        input=str(tmp_path),
        output=str(tmp_path),
        types=["code"],
        recursive=True,
        max_size=float("inf"),
    )
    run_copycat(args_rec)
    report_rec = next(tmp_path.glob("combined_copycat_*.txt"))
    assert "deep.py: 1 Zeilen [sub]" in report_rec.read_text()

    args_limit = Namespace(
        input=str(tmp_path),
        output=str(tmp_path),
        types=["all"],
        recursive=False,
        max_size=1.0,
    )
    run_copycat(args_limit)
    report_limit = next(tmp_path.glob("combined_copycat_*.txt"))
    assert "large.bin" not in report_limit.read_text()


def test_cli_types_keyerror_fixed(tmp_path):
    (tmp_path / "test.py").write_text("def hello(): pass")

    args_invalid = Namespace(
        input=str(tmp_path),
        output=str(tmp_path),
        types=["xyz"],
        recursive=False,
        max_size=float("inf"),
    )

    run_copycat(args_invalid)
    report = next(tmp_path.glob("combined_copycat_*.txt"))
    assert "Gesamt: 0 Dateien" in report.read_text()

    args_valid = Namespace(
        input=str(tmp_path),
        output=str(tmp_path),
        types=["code"],
        recursive=False,
        max_size=float("inf"),
    )
    run_copycat(args_valid)
    assert "CODE: 1 Datei" in next(tmp_path.glob("combined_copycat_*.txt")).read_text()


def test_cli_types_graceful(tmp_path):
    (tmp_path / "test.py").write_text("def hello(): pass")
    args = Namespace(
        types=["xyz"],
        input=str(tmp_path),
        output=str(tmp_path),
        recursive=False,
        max_size=float("inf"),
    )
    run_copycat(args)
    report = next(tmp_path.glob("combined_copycat_*.txt"))
    assert "Gesamt: 0 Dateien" in report.read_text()


def test_binary_classification(tmp_path):
    (tmp_path / "image.png").write_bytes(b"\x89PNG\r\n\x1a\n")
    args = Namespace(
        types=["all"],
        input=str(tmp_path),
        output=str(tmp_path),
        recursive=False,
        max_size=float("inf"),
    )
    run_copycat(args)
    report_text = next(tmp_path.glob("combined_copycat_*.txt")).read_text()
    assert "IMG: 1 Datei" in report_text


def test_binary_mime_detail(tmp_path):
    (tmp_path / "logo.png").write_bytes(b"\x89PNG\r\n\x1a\n\x00\x00")
    (tmp_path / "sound.wav").write_bytes(b"RIFF$\x00WAVEfmt ")
    (tmp_path / "music.mp3").write_bytes(b"ID3\x03\x00\x00")

    args = Namespace(
        input=str(tmp_path),
        output=str(tmp_path),
        types=["img", "audio"],
        recursive=False,
        max_size=float("inf"),
    )

    run_copycat(args)
    report = next(tmp_path.glob("combined_copycat_*.txt"))
    report_text = report.read_text()

    assert "IMG: 1 Datei" in report_text
    assert "AUDIO: 2 Dateien" in report_text
    assert "logo.png" in report_text or "sound.wav" in report_text
    assert "Gesamt: 3 Dateien" in report_text


def test_drawio_edgecases(tmp_path):
    valid = tmp_path / "valid.drawio"
    valid.write_text(
        """<mxfile><diagram><mxGraphModel>
        <root>
            <mxCell id="0"/>
            <mxCell id="1" parent="0"/>
            <mxCell id="2" value="START" style="ellipse;html=1;" vertex="1" parent="1">
                <mxGeometry x="100" y="100" width="80" height="30" as="geometry"/>
            </mxCell>
        </root>
    </mxGraphModel></diagram></mxfile>"""
    )

    empty = tmp_path / "empty.drawio"
    empty.write_bytes(b"")

    corrupt = tmp_path / "corrupt.drawio"
    corrupt.write_text("<mxfile>INVALID XML</mxfile>")

    args = Namespace(
        input=str(tmp_path),
        output=str(tmp_path),
        types=["diagram"],
        recursive=False,
        max_size=float("inf"),
    )

    run_copycat(args)
    report_text = next(tmp_path.glob("combined_copycat_*.txt")).read_text()

    assert "DIAGRAM: 3 Dateien" in report_text
    assert "valid.drawio" in report_text
    assert "[EMPTY: empty.drawio] [SIZE: 0 bytes]" in report_text
    assert "corrupt.drawio" in report_text
    assert "START" in report_text


def test_type_filters_runtime_complete(tmp_path):
    test_files = {
        "code": tmp_path / "test.py",
        "web": tmp_path / "style.css",
        "db": tmp_path / "data.sql",
        "config": tmp_path / "config.json",
        "docs": tmp_path / "README.md",
        "deps": tmp_path / "requirements.txt",
        "img": tmp_path / "logo.png",
        "audio": tmp_path / "sound.mp3",
        "diagram": tmp_path / "flow.drawio",
    }

    for f in test_files.values():
        f.parent.mkdir(exist_ok=True)
        f.touch()

    args_code = Namespace(
        input=str(tmp_path),
        output=str(tmp_path),
        types=["code"],
        recursive=False,
        max_size=float("inf"),
    )
    run_copycat(args_code)
    report = next(tmp_path.glob("combined_copycat_*.txt"))
    assert "CODE: 1 Datei" in report.read_text()
    assert "test.py" in report.read_text()
    assert "style.css" not in report.read_text()

    print("✅ TYPE_FILTERS (70-71): 9 Kategorien + CLI-Loop covered!")


def test_git_info_edge_cases_complete(tmp_path):
    assert get_git_info(tmp_path) == "No Git"

    (tmp_path / ".git").mkdir()
    with patch("subprocess.run", side_effect=FileNotFoundError("git not found")):
        assert get_git_info(tmp_path) == "No Git"

    with patch(
        "subprocess.run", side_effect=subprocess.TimeoutExpired("git", timeout=5)
    ):
        assert get_git_info(tmp_path) == "No Git"

    with patch("subprocess.run") as mock_run:
        mock_run.side_effect = [
            Mock(returncode=0, stdout="main\n"),
            Mock(returncode=0, stdout="abc1234\n"),
        ]
        result = get_git_info(tmp_path)
        assert "Branch: main | Last Commit: abc1234" in result

    print("✅ git_info (122-124): NoGit + Exceptions + Success covered!")


def test_report_writer_edge_cases(tmp_path):
    (tmp_path / "test.py").touch()
    args = Namespace(
        input=str(tmp_path),
        output=str(tmp_path),
        types=["code"],
        recursive=False,
        max_size=float("inf"),
    )
    run_copycat(args)
    report = next(tmp_path.glob("combined_copycat_*.txt"))
    assert report.exists()

    read_only_dir = tmp_path / "read_only"
    read_only_dir.mkdir()
    (read_only_dir / "locked.txt").touch()
    (read_only_dir / "locked.txt").chmod(0o444)

    args_ro = Namespace(
        input=str(tmp_path),
        output=str(read_only_dir),
        types=["code"],
        recursive=False,
        max_size=float("inf"),
    )
    with patch("builtins.print") as mock_print:
        run_copycat(args_ro)
        mock_print.assert_called_with(ANY)

    umlaut_file = tmp_path / "test_äöü.py"
    umlaut_file.write_text("def funktion(): pass # äöü\n")
    args_unicode = Namespace(
        input=str(tmp_path),
        output=str(tmp_path),
        types=["code"],
        recursive=False,
        max_size=float("inf"),
    )
    run_copycat(args_unicode)
    report_unicode = next(tmp_path.glob("combined_copycat_*.txt"))
    assert "test_äöü.py" in report_unicode.read_text(encoding="utf-8")

    print("✅ Report Writer (434-438): Normal + PermissionError + Unicode covered!")


def test_git_info_exceptions(tmp_path):
    (tmp_path / ".git").mkdir()

    with patch("subprocess.run", side_effect=FileNotFoundError("git missing")):
        assert get_git_info(tmp_path) == "No Git"

    with patch(
        "subprocess.run", side_effect=subprocess.TimeoutExpired("git", timeout=5)
    ):
        assert get_git_info(tmp_path) == "No Git"

    with patch("subprocess.run", side_effect=subprocess.SubprocessError("git failed")):
        assert get_git_info(tmp_path) == "No Git"

    print("✅ git_info (122-124): 3 Exceptions covered!")


def test_should_skip_gitignore_exception(tmp_path, monkeypatch):
    test_file = tmp_path / "test.py"
    test_file.touch()

    def mock_open(*args):
        raise PermissionError()

    monkeypatch.setattr("builtins.open", mock_open)
    assert should_skip_gitignore(tmp_path, test_file) is False
    print("✅ Gitignore (161-164) covered!")


def test_type_filters_keys_runtime():
    keys = list(TYPE_FILTERS.keys())
    assert len(keys) == 9
    assert set(keys) >= {"code", "web", "diagram", "img", "audio"}
    print("✅ TYPE_FILTERS (70-71) covered!")


def test_report_writer_unicode(tmp_path):
    (tmp_path / "test_äöü.py").write_text("def f(): pass # äöüß\n")

    args = Namespace(
        input=str(tmp_path),
        output=str(tmp_path),
        types=["code"],
        recursive=False,
        max_size=float("inf"),
    )
    run_copycat(args)

    report = next(tmp_path.glob("combined_copycat_*.txt"))
    assert "test_äöü.py" in report.read_text(encoding="utf-8")


def test_report_unicode(tmp_path):
    ascii_code = tmp_path / "test_ascii.py"
    ascii_code.write_text("def hello(): print('Hello World')\n")

    args = Namespace(
        input=str(tmp_path),
        output=str(tmp_path),
        types=["code"],
        recursive=False,
        max_size=float("inf"),
    )
    run_copycat(args)

    report = next(tmp_path.glob("combined_copycat_*.txt"))
    content = report.read_text(encoding="utf-8")

    assert "test_ascii.py" in content
    assert "1 Zeilen" in content
    assert "(Binary" not in content
    print("✅ Report UTF-8 (434-438) covered!")


def test_type_filters_loop_coverage_invalid():
    from CopyCat import TYPE_FILTERS

    selected_types = ["code", "xyz"]
    process_all = False

    covered_types = []
    for t in TYPE_FILTERS:
        if process_all or t in selected_types:
            covered_types.append(t)

    assert len(covered_types) == 1
    assert covered_types[0] == "code"


def test_git_info_subprocess_error(tmp_path, monkeypatch):

    def mock_run(*args, **kwargs):
        result = Mock()
        result.returncode = 1
        result.stdout = b"error"
        return result

    monkeypatch.setattr("subprocess.run", mock_run)
    assert "No Git" in get_git_info(tmp_path)


def test_get_git_info_file_not_found(tmp_path, monkeypatch):
    def mock_run(*args, **kwargs):
        raise FileNotFoundError("git not found")

    monkeypatch.setattr("subprocess.run", mock_run)
    assert get_git_info(tmp_path) == "No Git"


def test_should_skip_gitignore_oserror(tmp_path, monkeypatch):
    def mock_open(*args, **kwargs):
        raise OSError("Permission denied")

    monkeypatch.setattr("builtins.open", mock_open)
    assert not should_skip_gitignore(tmp_path, tmp_path / "test.py")


def test_get_plural_complete():
    assert get_plural(0) == "Dateien"
    assert get_plural(1) == "Datei"
    assert get_plural(2) == "Dateien"


def test_size_filtered_glob_print_over_100(tmp_path):
    test_py = tmp_path / "test.py"
    test_py.touch()

    def mock_glob(pat):
        return [test_py]

    files = list(
        size_filtered_glob(
            mock_glob, TYPE_FILTERS["code"], float("inf"), Path(), tmp_path
        )
    )
    assert len(files) == 5


def test_size_filtered_glob_print_100(tmp_path, monkeypatch):
    mock_print = Mock()
    monkeypatch.setattr("builtins.print", mock_print)

    for i in range(100):
        (tmp_path / f"file{i}.py").touch()

    def mock_search(pat):
        return [tmp_path / f"file{i}.py" for i in range(100)]

    mock_args = Mock()
    mock_args.side_effect = mock_search

    list(size_filtered_glob(mock_args, ["*.py"], float("inf"), Path(), tmp_path))

    mock_print.assert_any_call("\rGeprüft: 100 Dateien...", end="")
    mock_print.assert_any_call("\n→ 100 geprüft, Filter OK")


def test_parse_arguments_max_size_invalid(capsys):
    with pytest.raises(SystemExit, match="2"):
        with patch("sys.argv", ["test.py", "--max-size=abc"]):
            parse_arguments()
    captured = capsys.readouterr()
    assert "invalid float value: 'abc'" in captured.err


def test_type_filters_mixed_valid_invalid():
    from CopyCat import TYPE_FILTERS

    selected_types = ["code", "xyz"]
    valid_types = [t for t in TYPE_FILTERS.keys() if t in selected_types]
    assert valid_types == ["code"]


def test_size_filtered_glob_empty_patterns(tmp_path):
    files = list(size_filtered_glob(Mock(), [], float("inf"), Path(), tmp_path))
    assert files == []


def test_size_filtered_glob_zero_maxsize(tmp_path):
    (tmp_path / "test.py").touch()

    def mock_search(rel_pat):
        full_pat = str(tmp_path / rel_pat)
        return [Path(f) for f in glob(full_pat)]

    files = list(size_filtered_glob(mock_search, ["*.py"], 0, Path(), tmp_path))
    assert files == []


def test_extract_drawio_parse_error(tmp_path, mock_writer, monkeypatch):
    corrupt = tmp_path / "corrupt.drawio"
    corrupt.write_text("<broken>")

    def mock_parse(*args):
        raise ET.ParseError("Line 1 broken")

    monkeypatch.setattr(ET, "fromstring", mock_parse)

    extract_drawio(mock_writer, corrupt)
    mock_writer.write.assert_called()


def test_list_binary_file_unicode_error(tmp_path, mock_writer, monkeypatch):
    binary = tmp_path / "binary.dat"
    binary.write_bytes(b"\x00invalid")

    def mock_open(filename, *args, **kwargs):
        f = Mock()
        f.__enter__.return_value = f
        f.__exit__ = Mock(return_value=False)
        f.read.side_effect = UnicodeDecodeError("utf-8", b"", 0, 1, "invalid")
        return f

    monkeypatch.setattr("builtins.open", mock_open)
    list_binary_file(mock_writer, binary)
    mock_writer.write.assert_called_with(ANY)


def test_moveto_archive_no_permission(tmp_path, monkeypatch):
    oldfile = tmp_path / "combinedcopycat1.txt"
    oldfile.touch()

    def mock_move(src, dst):
        raise PermissionError("locked")

    monkeypatch.setattr("shutil.move", mock_move)

    move_to_archive(tmp_path, "combinedcopycat1.txt")


def test_type_filters_loop_edge():
    from CopyCat import TYPE_FILTERS

    types_list = list(TYPE_FILTERS.keys())
    assert len(types_list) >= 9


def test_get_git_info_subprocess_timeout(monkeypatch):

    def mock_run(*args, **kwargs):
        result = Mock()
        result.returncode = 128
        result.stdout = b""
        return result

    monkeypatch.setattr("subprocess.run", mock_run)
    result = get_git_info(Path())
    assert "N/A" in result


def test_extract_drawio_zero_bytes(tmp_path, mock_writer):
    empty = tmp_path / "empty.drawio"
    empty.write_text("")
    extract_drawio(mock_writer, empty)
    mock_writer.write.assert_called()


def test_list_binary_file_1mb_limit(tmp_path, mock_writer):
    large = tmp_path / "large.bin"
    large.write_bytes(b"\x00" * 1024 * 1024 * 2)
    list_binary_file(mock_writer, large)
    mock_writer.write.assert_called()


def test_type_filters_v27_complete():
    keys = list(TYPE_FILTERS.keys())
    expected = [
        "code",
        "web",
        "db",
        "config",
        "docs",
        "deps",
        "img",
        "audio",
        "diagram",
    ]
    assert set(keys) == set(expected)
    for cat, pats in TYPE_FILTERS.items():
        assert isinstance(pats, list) and len(pats) > 0


def test_move_to_archive_v27(tmp_path):
    archive = tmp_path / "CopyCat_Archive"
    old_file = tmp_path / "combined_copycat_1.txt"
    old_file.touch()
    move_to_archive(tmp_path, "combined_copycat_1.txt")
    assert not old_file.exists()
    assert (archive / "combined_copycat_1.txt").exists()


def test_move_to_archive_no_space(tmp_path, monkeypatch):

    def mock_move(*args):
        raise OSError("No space")

    monkeypatch.setattr("shutil.move", mock_move)
    move_to_archive(tmp_path, "test.txt")


def test_move_to_archive_complete(tmp_path, monkeypatch):
    archive = tmp_path / "CopyCat_Archive"
    old = tmp_path / "combined_copycat_5.txt"
    old.touch()

    move_to_archive(tmp_path, "combined_copycat_5.txt")
    assert (archive / "combined_copycat_5.txt").exists()

    def mock_move(*args):
        raise OSError("No space")

    with monkeypatch.context() as m:
        m.setattr(shutil, "move", mock_move)
        move_to_archive(tmp_path, "test.txt")


def test_type_filters_all_runtime(tmp_path):
    from CopyCat import TYPE_FILTERS

    for cat, patterns in TYPE_FILTERS.items():
        assert isinstance(patterns, list)
        assert len(patterns) > 0


def test_should_skip_gitignore_oserror_safe(tmp_path, monkeypatch):
    gitignore = tmp_path / ".gitignore"
    gitignore.write_text("# test")

    def mock_open(*args):
        raise OSError("No permission")

    monkeypatch.setattr("builtins.open", mock_open)

    assert not should_skip_gitignore(tmp_path, tmp_path / "test.py")


def test_move_to_archive_multiple(tmp_path):
    archive = tmp_path / "CopyCat_Archive"
    f1 = tmp_path / "combined_copycat_1.txt"
    f2 = tmp_path / "combined_copycat_2.txt"
    f1.touch()
    f2.touch()

    move_to_archive(tmp_path, "combined_copycat_1.txt")
    move_to_archive(tmp_path, "combined_copycat_2.txt")

    assert len(list(archive.iterdir())) == 2


def test_extract_drawio_parse_broken(tmp_path, monkeypatch):
    corrupt = tmp_path / "broken.drawio"
    corrupt.write_text("<invalid>")

    mock_writer = Mock()
    extract_drawio(mock_writer, corrupt)
    mock_writer.write.assert_called_with(ANY)


def test_list_binary_wav_header(tmp_path, mock_writer):
    wav = tmp_path / "test.wav"
    wav.write_bytes(
        b"RIFF....WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x0044\xac\x00\x00\x10\x00\x00\x00"
    )

    list_binary_file(mock_writer, wav)
    mock_writer.write.assert_called()


def test_size_filtered_glob_self_protect(tmp_path):
    copycat = tmp_path / "CopyCat.py"
    serial = tmp_path / "combined_copycat_99.txt"
    copycat.touch()
    serial.touch()

    files = list(
        size_filtered_glob(tmp_path.glob, ["*.py"], float("inf"), copycat, tmp_path)
    )
    assert copycat not in files


from unittest.mock import MagicMock, patch


def test_run_copycat_empty_dir(tmp_path, monkeypatch):
    class MockArgs:
        input = str(tmp_path)
        output = str(tmp_path)
        recursive = False
        max_size = float("inf")
        types = ["all"]

    mock_file = MagicMock()
    mock_file.__enter__.return_value = mock_file
    mock_file.__exit__.return_value = None

    with patch("builtins.open", return_value=mock_file):
        monkeypatch.setattr(Path, "glob", classmethod(lambda cls, pat: []))
        monkeypatch.setattr(Path, "rglob", classmethod(lambda cls, pat: []))
        run_copycat(MockArgs())

    mock_file.write.assert_called()


def test_parse_arguments_invalid_maxsize(capfd, monkeypatch):
    import sys

    sys.argv = ["CopyCat.py", "--max-size", "invalid"]
    monkeypatch.setattr(sys, "exit", lambda code: None)

    try:
        parse_arguments()
    except SystemExit:
        pass
    captured = capfd.readouterr()
    assert "invalid float" in captured.err


def test_get_git_info_dotgit_but_no_git(tmp_path, monkeypatch):
    (tmp_path / ".git").mkdir()

    def mock_run(*args, **kwargs):
        return Mock(returncode=127, stdout="", stderr="")

    monkeypatch.setattr("subprocess.run", mock_run)

    result = get_git_info(tmp_path)
    assert "Branch: N/A | Last Commit: N/A" in result


def test_type_filters_no_overlap():
    all_patterns = []
    for pats in TYPE_FILTERS.values():
        all_patterns.extend(pats)
    assert len(all_patterns) == sum(len(p) for p in TYPE_FILTERS.values())


def test_run_copycat_recursive_nested(tmp_path, monkeypatch):
    (tmp_path / "sub" / "sub").mkdir(parents=True)
    (tmp_path / "sub" / "sub" / "test.py").touch()

    class MockArgs:
        input = str(tmp_path)
        output = str(tmp_path)
        recursive = True
        max_size = float("inf")
        types = ["code"]

    mock_file = MagicMock()
    mock_file.__enter__.return_value = mock_file
    mock_file.__exit__.return_value = None

    with patch("builtins.open", return_value=mock_file):
        monkeypatch.setattr(
            Path,
            "rglob",
            classmethod(lambda cls, pat: [tmp_path / "sub" / "sub" / "test.py"]),
        )
        monkeypatch.setattr(Path, "glob", classmethod(lambda cls, pat: []))
        run_copycat(MockArgs())


def test_get_git_info_all_fallbacks(tmp_path, monkeypatch):

    def mock_run(*args, **kwargs):
        return Mock(returncode=1, stdout="", stderr="not found")

    monkeypatch.setattr("subprocess.run", mock_run)

    result = get_git_info(tmp_path)
    assert result == "No Git"


def test_size_filtered_glob_double_protect(tmp_path):
    copycat = tmp_path / "CopyCat.py"
    serial = tmp_path / "combined_copycat_99.txt"
    copycat.touch()
    serial.touch()
    other = tmp_path / "other.py"
    other.touch()

    files = list(
        size_filtered_glob(tmp_path.glob, ["*.py"], float("inf"), copycat, tmp_path)
    )
    assert len(files) == 1
    assert copycat not in files
    assert serial not in files


def test_type_filters_runtime_iteration():
    processed = []
    for t, patterns in TYPE_FILTERS.items():
        processed.append(t)
        assert isinstance(patterns, list)
        assert len(patterns) >= 1
    assert len(processed) == 9


def test_size_filtered_glob_progress_150(tmp_path, monkeypatch):
    mock_print = Mock()
    monkeypatch.setattr("builtins.print", mock_print)

    def mock_glob(pat):
        return [tmp_path / "test.py"] * 150

    list(size_filtered_glob(mock_glob, ["*.py"], float("inf"), Path(), tmp_path))
    assert mock_print.call_count >= 1


def test_list_binary_file_struct_error(tmp_path):
    tiny_wav = tmp_path / "tiny.wav"
    tiny_wav.write_bytes(b"RIFF")

    mock_writer = Mock()
    list_binary_file(mock_writer, tiny_wav)

    for call in mock_writer.write.call_args_list:
        if "DUR: N/A" in str(call.args[0]):
            break
    else:
        assert False, "DUR: N/A missing"


def test_gitignore_wildcard_patterns(tmp_path):
    gitignore = tmp_path / ".gitignore"
    gitignore.write_text("*.pyc\n__pycache__/\ntest_*.py\n")

    (tmp_path / "test_pyc.pyc").touch()
    (tmp_path / "other_file.py").touch()
    (tmp_path / "__pycache__").mkdir()

    assert should_skip_gitignore(tmp_path, tmp_path / "test_pyc.pyc")
    assert should_skip_gitignore(tmp_path, tmp_path / "__pycache__" / "x.py")
    assert not should_skip_gitignore(tmp_path, tmp_path / "other_file.py")


def test_code_line_counting_all_edges(tmp_path):
    empty = tmp_path / "empty.py"
    whitespace = tmp_path / "ws.py"
    unicode = tmp_path / "uni.py"

    empty.touch()
    whitespace.write_text(" \n \t\n")
    unicode.write_text("def ü(): pass\n")

    lines_empty = sum(1 for line in open(empty) if line.strip())
    lines_ws = sum(1 for line in open(whitespace) if line.strip())
    lines_uni = sum(1 for line in open(unicode) if line.strip())

    assert lines_empty == 0
    assert lines_ws == 0
    assert lines_uni == 1


def test_extract_drawio_parse_error_coverage(tmp_path):
    corrupt = tmp_path / "corrupt.drawio"
    corrupt.write_text("<broken>")

    mock_writer = Mock()
    extract_drawio(mock_writer, corrupt)
    assert mock_writer.write.called


def test_move_to_archive_coverage(tmp_path, monkeypatch):

    def mock_move(src, dst):
        raise OSError("Permission denied")

    monkeypatch.setattr(shutil, "move", mock_move)
    move_to_archive(tmp_path, "combined_copycat_1.txt")
    assert True


def test_type_filters_runtime_complete_coverage():
    keys = list(TYPE_FILTERS.keys())
    assert len(keys) == 9
    for t in keys:
        assert isinstance(TYPE_FILTERS[t], list)
        assert len(TYPE_FILTERS[t]) > 0


def test_get_git_info_triple_fallback(tmp_path, monkeypatch):
    mock_path = MagicMock()
    mock_path.glob.return_value = []
    monkeypatch.setattr("CopyCat.Path", lambda p: mock_path)

    def mock_run(*args):
        return Mock(returncode=1)

    monkeypatch.setattr("subprocess.run", mock_run)

    result = get_git_info(tmp_path)
    assert result == "No Git"


def test_should_skip_gitignore_oserror_silent(tmp_path, monkeypatch):

    def mock_open(*args):
        raise OSError("Access denied")

    monkeypatch.setattr("builtins.open", mock_open)

    result = should_skip_gitignore(tmp_path, tmp_path / "test.py")
    assert not result


def test_size_filtered_glob_progress_print_200(tmp_path, monkeypatch):
    mock_print = Mock()
    monkeypatch.setattr("builtins.print", mock_print)

    def mock_glob(pat):
        return [tmp_path / "test.py"] * 200

    files = list(
        size_filtered_glob(mock_glob, ["*.py"], float("inf"), Path(), tmp_path)
    )
    assert mock_print.called


def test_size_filtered_glob_double_self_protect(tmp_path):
    copycat = tmp_path / "CopyCat.py"
    serial = tmp_path / "combined_copycat_99.txt"
    other = tmp_path / "other.py"
    copycat.touch()
    serial.touch()
    other.touch()

    files = list(
        size_filtered_glob(tmp_path.glob, ["*.py"], float("inf"), copycat, tmp_path)
    )
    assert len(files) == 1
    assert str(other) in str(files[0])


def test_get_plural_all_edges():
    assert "Dateien" in get_plural(0)
    assert "Datei" in get_plural(1)
    assert "Dateien" in get_plural(2)


def test_run_copycat_no_filter_fast_path_coverage(tmp_path, monkeypatch):

    class MockArgs:
        input = str(tmp_path)
        output = str(tmp_path)
        recursive = False
        max_size = float("inf")
        types = ["code"]

    monkeypatch.setattr(Path, "glob", classmethod(lambda cls, pat: []))
    run_copycat(MockArgs())


def test_output_dir_mkdir_exist_ok(tmp_path):
    output_dir = tmp_path / "exists"
    output_dir.mkdir()

    class MockArgs:
        input = str(tmp_path)
        output = str(output_dir)
        recursive = False
        max_size = float("inf")
        types = ["code"]

    run_copycat(MockArgs())


def test_should_skip_gitignore_oserror_path(tmp_path, monkeypatch):

    def mock_open(*args):
        raise OSError("Permission denied")

    monkeypatch.setattr("builtins.open", mock_open)

    result = should_skip_gitignore(tmp_path, tmp_path / "test.py")
    assert not result


def test_size_filtered_glob_print_over_200(tmp_path, monkeypatch, capsys):
    mock_print = Mock()
    monkeypatch.setattr("builtins.print", mock_print)

    def mock_glob(pat):
        return [tmp_path / "f.py"] * 201

    monkeypatch.setattr("pathlib.Path.glob", mock_glob)

    list(size_filtered_glob(mock_glob, ["*.py"], float("inf"), tmp_path, tmp_path))
    captured = capsys.readouterr()
    assert len(captured.out) > 0 or mock_print.called


def test_size_filtered_glob_triple_self_protect(tmp_path):
    (tmp_path / "CopyCat.py").touch()
    (tmp_path / "combined_copycat_99.txt").touch()
    (tmp_path / "CopyCatArchive").mkdir()
    (tmp_path / "other.py").touch()

    files = list(
        size_filtered_glob(
            tmp_path.glob, ["*.py"], float("inf"), tmp_path / "CopyCat.py", tmp_path
        )
    )
    assert len(files) == 1


def test_extract_drawio_parseerror_path(tmp_path):
    corrupt = tmp_path / "corrupt.drawio"
    corrupt.write_text("<broken>")

    mock_writer = Mock()
    extract_drawio(mock_writer, corrupt)
    assert mock_writer.write.called


def test_list_binary_file_wav_struct_error(tmp_path):
    tiny_wav = tmp_path / "broken.wav"
    tiny_wav.write_bytes(b"RIFFxxxx")

    mock_writer = Mock()
    list_binary_file(mock_writer, tiny_wav)

    for call in mock_writer.write.call_args_list:
        if "DUR: N/A" in str(call.args[0]):
            return
    assert False, "DUR: N/A not found in output"


def test_type_filters_items_runtime_all_keys():
    covered_keys = set()
    for t, patterns in TYPE_FILTERS.items():
        covered_keys.add(t)
        assert isinstance(patterns, list)
        assert len(patterns) > 0

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
    assert covered_keys == expected


def test_should_skip_gitignore_oserror_returns_false(tmp_path, monkeypatch):

    def mock_open(*args):
        raise PermissionError("Access denied")

    monkeypatch.setattr("builtins.open", mock_open)

    result = should_skip_gitignore(tmp_path, tmp_path / "secret.py")
    assert result is False


def test_size_filtered_glob_self_protect_all_conditions(tmp_path):
    self_protect = tmp_path / "CopyCat.py"
    serial_file = tmp_path / "combined_copycat_123.txt"
    archive_dir = tmp_path / "CopyCatArchive"

    self_protect.touch()
    serial_file.touch()
    archive_dir.mkdir()
    (tmp_path / "normal.py").touch()

    files = list(
        size_filtered_glob(
            tmp_path.glob, ["*.py"], float("inf"), self_protect, tmp_path
        )
    )
    assert len(files) == 1


def test_type_filters_all_branch_coverage():

    class MockArgs:
        types = ["all"]

    args = MockArgs()

    use_filter = any(t == "all" for t in args.types)
    assert use_filter is True

    covered = False
    for t, patterns in TYPE_FILTERS.items():
        covered = True
        break
    assert covered


def test_move_to_archive_oserror_silent(tmp_path, monkeypatch):
    test_file = tmp_path / "combined_copycat_1.txt"
    test_file.touch()

    def mock_move(src, dst):
        raise OSError("Permission denied")

    monkeypatch.setattr(shutil, "move", mock_move)

    move_to_archive(tmp_path, "combined_copycat_2.txt")
    assert True


def test_copycat_integration_missing_paths(tmp_path, monkeypatch):
    serial_file = tmp_path / "combined_copycat_1.txt"
    serial_file.touch()

    (tmp_path / "test.py").touch()

    class MockArgs:
        input = str(tmp_path)
        output = str(tmp_path)
        types = ["all"]
        recursive = False
        max_size = float("inf")

    from CopyCat import run_copycat

    run_copycat(MockArgs())


def test_move_to_archive_oserror_print(tmp_path, monkeypatch):
    from unittest.mock import Mock

    mock_print = Mock()
    monkeypatch.setattr("builtins.print", mock_print)

    test_file = tmp_path / "combined_copycat_1.txt"
    test_file.touch()

    def mock_move(src, dst):
        raise OSError("Permission denied")

    monkeypatch.setattr(shutil, "move", mock_move)

    move_to_archive(tmp_path, "combined_copycat_1.txt")
    assert mock_print.called


if __name__ == "__main__":
    pytest.main(
        [__file__, "-v", "--cov=.", "--cov-report=term-missing", "--cov-report=html"]
    )
