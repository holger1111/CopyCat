# -*- coding: utf-8 -*-
"""Patch-Skript: --git-url in GUI, Web, Tests und READMEs einbauen."""

import sys
import os

os.chdir(os.path.dirname(os.path.abspath(__file__)))

# ─────────────────────────────────────────────────────────────────────────────
# 1. CopyCat_GUI.py
# ─────────────────────────────────────────────────────────────────────────────
gui = open('CopyCat_GUI.py', encoding='utf-8').read()
gui_ok = []

# __init__: self._git_url_var nach self._stats_var
OLD = '        self._stats_var = tk.BooleanVar(value=False)\n        self._watch_stop_event = None'
NEW = '        self._stats_var = tk.BooleanVar(value=False)\n        self._git_url_var = tk.StringVar()\n        self._watch_stop_event = None'
if OLD in gui:
    gui = gui.replace(OLD, NEW, 1)
    gui_ok.append('__init__ git_url_var')
elif 'self._git_url_var' in gui:
    gui_ok.append('__init__ git_url_var (already present)')
else:
    print('WARN: __init__ stats_var not found')

# _build_ui: Git-URL row=2 in frm_io after the Ausgabe row
OLD2 = (
    '        ttk.Button(frm_io, text="\u2026", width=3, command=self._browse_output).grid(row=1, column=2, pady=(4, 0))\n'
    '\n'
    '        if _DND_AVAILABLE:'
)
NEW2 = (
    '        ttk.Button(frm_io, text="\u2026", width=3, command=self._browse_output).grid(row=1, column=2, pady=(4, 0))\n'
    '\n'
    '        ttk.Label(frm_io, text="Git-URL:").grid(row=2, column=0, sticky="w", pady=(4, 0))\n'
    '        ttk.Entry(frm_io, textvariable=self._git_url_var, width=55).grid(row=2, column=1, padx=4, pady=(4, 0))\n'
    '\n'
    '        if _DND_AVAILABLE:'
)
if OLD2 in gui:
    gui = gui.replace(OLD2, NEW2, 1)
    gui_ok.append('_build_ui git_url row')
elif '"Git-URL:"' in gui:
    gui_ok.append('_build_ui git_url row (already present)')
else:
    print('WARN: _build_ui browse_output not found')

# _load_config: git_url nach stats
OLD3 = (
    '        if "stats" in cfg:\n'
    '            self._stats_var.set(cfg["stats"].lower() in ("true", "yes", "1"))'
)
NEW3 = (
    '        if "stats" in cfg:\n'
    '            self._stats_var.set(cfg["stats"].lower() in ("true", "yes", "1"))\n'
    '        if "git_url" in cfg:\n'
    '            self._git_url_var.set(cfg["git_url"])'
)
if OLD3 in gui:
    gui = gui.replace(OLD3, NEW3, 1)
    gui_ok.append('_load_config git_url')
elif 'git_url_var.set' in gui:
    gui_ok.append('_load_config git_url (already present)')
else:
    print('WARN: _load_config stats block not found')

# _save_config: git_url nach stats
OLD4 = (
    '        if self._stats_var.get():\n'
    '            lines.append("stats = true")\n'
    '        try:'
)
NEW4 = (
    '        if self._stats_var.get():\n'
    '            lines.append("stats = true")\n'
    '        git_url = self._git_url_var.get().strip()\n'
    '        if git_url:\n'
    '            lines.append(f"git_url = {git_url}")\n'
    '        try:'
)
if OLD4 in gui:
    gui = gui.replace(OLD4, NEW4, 1)
    gui_ok.append('_save_config git_url')
elif 'git_url_var.get()' in gui:
    gui_ok.append('_save_config git_url (already present)')
else:
    print('WARN: _save_config stats block not found')

# _build_args: git_url hinzufuegen
OLD5 = (
    '            stats=self._stats_var.get(),\n'
    '        )'
)
NEW5 = (
    '            stats=self._stats_var.get(),\n'
    '            git_url=self._git_url_var.get().strip() or None,\n'
    '        )'
)
if OLD5 in gui:
    gui = gui.replace(OLD5, NEW5, 1)
    gui_ok.append('_build_args git_url')
elif 'git_url=self._git_url_var' in gui:
    gui_ok.append('_build_args git_url (already present)')
else:
    print('WARN: _build_args stats not found')

open('CopyCat_GUI.py', 'w', encoding='utf-8').write(gui)
print('GUI OK:', gui_ok)

# ─────────────────────────────────────────────────────────────────────────────
# 2. CopyCat_Web.py
# ─────────────────────────────────────────────────────────────────────────────
web = open('CopyCat_Web.py', encoding='utf-8').read()
web_ok = []

# _TEMPLATE: git_url input nach output_dir row, before Dateitypen
OLD_T = (
    '          </div>\n'
    '        </div>\n'
    '      </div>\n'
    '\n'
    '      <div class="card">\n'
    '        <h2>Dateitypen</h2>'
)
NEW_T = (
    '          </div>\n'
    '        </div>\n'
    '        <div>\n'
    '          <label for="git_url">Git-URL (optional, ersetzt Eingabeordner)</label>\n'
    '          <input type="text" id="git_url" name="git_url" value="{{ form.git_url }}" placeholder="https://github.com/user/repo">\n'
    '        </div>\n'
    '      </div>\n'
    '\n'
    '      <div class="card">\n'
    '        <h2>Dateitypen</h2>'
)
if OLD_T in web:
    web = web.replace(OLD_T, NEW_T, 1)
    web_ok.append('_TEMPLATE git_url input')
elif 'label for="git_url"' in web:
    web_ok.append('_TEMPLATE git_url (already present)')
else:
    print('WARN: _TEMPLATE Dateitypen marker not found')

# _build_args: git_url nach stats
OLD_BA = (
    '      incremental="incremental" in form,\n'
    '      stats="stats" in form,\n'
    '    )'
)
NEW_BA = (
    '      incremental="incremental" in form,\n'
    '      stats="stats" in form,\n'
    '      git_url=form.get("git_url", "").strip() or None,\n'
    '    )'
)
if OLD_BA in web:
    web = web.replace(OLD_BA, NEW_BA, 1)
    web_ok.append('_build_args git_url')
elif 'git_url=form.get("git_url"' in web:
    web_ok.append('_build_args git_url (already present)')
else:
    print('WARN: _build_args stats not found')

# _form_defaults: git_url hinzufuegen
OLD_FD = (
    '        "stats": False,\n'
    '    }'
)
NEW_FD = (
    '        "stats": False,\n'
    '        "git_url": "",\n'
    '    }'
)
if OLD_FD in web:
    web = web.replace(OLD_FD, NEW_FD, 1)
    web_ok.append('_form_defaults git_url')
elif '"git_url": ""' in web:
    web_ok.append('_form_defaults git_url (already present)')
else:
    print('WARN: _form_defaults stats not found')

# /run route: git_url in form_data + validation update
OLD_RUN = (
    '      "stats": "stats" in request.form,\n'
    '    }\n'
    '\n'
    '    # Pflichtfeld: Eingabeordner\n'
    '    if not form_data["input_dir"]:\n'
    '        return render_template_string(\n'
    '            _TEMPLATE,\n'
    '            form=form_data,\n'
    '            all_types=list(TYPE_FILTERS.keys()),\n'
    '            plugins=[],\n'
    '            report=None,\n'
    '            report_path=None,\n'
    '            error="Bitte einen Eingabeordner angeben.",\n'
    '        )\n'
    '\n'
    '    input_dir = Path(form_data["input_dir"])\n'
    '    if not input_dir.is_dir():\n'
    '        return render_template_string(\n'
    '            _TEMPLATE,\n'
    '            form=form_data,\n'
    '            all_types=list(TYPE_FILTERS.keys()),\n'
    '            plugins=[],\n'
    '            report=None,\n'
    '            report_path=None,\n'
    '            error=f"Eingabeordner existiert nicht: {input_dir}",\n'
    '        )'
)
NEW_RUN = (
    '      "stats": "stats" in request.form,\n'
    '      "git_url": request.form.get("git_url", "").strip(),\n'
    '    }\n'
    '\n'
    '    git_url = form_data.get("git_url", "")\n'
    '    # Pflichtfeld: Eingabeordner (nicht noetig wenn git_url gesetzt)\n'
    '    if not form_data["input_dir"] and not git_url:\n'
    '        return render_template_string(\n'
    '            _TEMPLATE,\n'
    '            form=form_data,\n'
    '            all_types=list(TYPE_FILTERS.keys()),\n'
    '            plugins=[],\n'
    '            report=None,\n'
    '            report_path=None,\n'
    '            error="Bitte einen Eingabeordner oder eine Git-URL angeben.",\n'
    '        )\n'
    '\n'
    '    input_dir = Path(form_data["input_dir"]) if form_data["input_dir"] else None\n'
    '    if input_dir is not None and not input_dir.is_dir():\n'
    '        return render_template_string(\n'
    '            _TEMPLATE,\n'
    '            form=form_data,\n'
    '            all_types=list(TYPE_FILTERS.keys()),\n'
    '            plugins=[],\n'
    '            report=None,\n'
    '            report_path=None,\n'
    '            error=f"Eingabeordner existiert nicht: {input_dir}",\n'
    '        )'
)
if OLD_RUN in web:
    web = web.replace(OLD_RUN, NEW_RUN, 1)
    web_ok.append('/run form_data + validation')
elif '"git_url": request.form.get' in web:
    web_ok.append('/run form_data git_url (already present)')
else:
    print('WARN: /run stats validation not found')

# /run route: use run_copycat return value for report path
OLD_RUN2 = (
    '    with _run_lock:\n'
    '        try:\n'
    '            run_copycat(args)\n'
    '            # Letzten erstellten Report einlesen\n'
    '            out_dir = Path(args.output or str(input_dir))\n'
    '            fmt = args.format'
)
NEW_RUN2 = (
    '    with _run_lock:\n'
    '        try:\n'
    '            result_path = run_copycat(args)\n'
    '            # Letzten erstellten Report einlesen\n'
    '            out_dir = Path(args.output or str(input_dir or "."))\n'
    '            fmt = args.format'
)
if OLD_RUN2 in web:
    web = web.replace(OLD_RUN2, NEW_RUN2, 1)
    web_ok.append('/run run_copycat return')
elif 'result_path = run_copycat' in web:
    web_ok.append('/run run_copycat return (already present)')
else:
    print('WARN: /run run_copycat block not found')

# /api/run: git_url hinzufuegen
OLD_API = (
    '    if data.get("stats"):\n'
    '        form_like["stats"] = "on"\n'
    '\n'
    '    class _FakeForm:'
)
NEW_API = (
    '    if data.get("stats"):\n'
    '        form_like["stats"] = "on"\n'
    '    if data.get("git_url"):\n'
    '        form_like["git_url"] = data["git_url"]\n'
    '\n'
    '    class _FakeForm:'
)
if OLD_API in web:
    web = web.replace(OLD_API, NEW_API, 1)
    web_ok.append('/api/run git_url')
elif 'form_like["git_url"]' in web:
    web_ok.append('/api/run git_url (already present)')
else:
    print('WARN: /api/run stats not found')

# /api/run: allow git_url without input
OLD_API2 = (
    "    if not data.get(\"input\"):\n"
    "        return jsonify({\"error\": \"Feld 'input' fehlt\"}), 400\n"
    '\n'
    '    input_dir = Path(data["input"])\n'
    '    if not input_dir.is_dir():\n'
    "        return jsonify({\"error\": f\"Eingabeordner existiert nicht: {input_dir}\"}), 400"
)
NEW_API2 = (
    "    if not data.get(\"input\") and not data.get(\"git_url\"):\n"
    "        return jsonify({\"error\": \"Feld 'input' oder 'git_url' fehlt\"}), 400\n"
    '\n'
    '    input_dir = Path(data["input"]) if data.get("input") else None\n'
    '    if input_dir is not None and not input_dir.is_dir():\n'
    "        return jsonify({\"error\": f\"Eingabeordner existiert nicht: {input_dir}\"}), 400"
)
if OLD_API2 in web:
    web = web.replace(OLD_API2, NEW_API2, 1)
    web_ok.append('/api/run input validation')
elif "data.get(\"git_url\")" in web and "Feld 'input' oder 'git_url' fehlt" in web:
    web_ok.append('/api/run input validation (already present)')
else:
    print('WARN: /api/run input validation not found')

# /api/run: fix out_dir after run_copycat
OLD_API3 = (
    '    with _run_lock:\n'
    '        try:\n'
    '            run_copycat(args)\n'
    '        except Exception as exc:\n'
    '            return jsonify({"error": str(exc)}), 500\n'
    '\n'
    '    out_dir = Path(args.output or str(input_dir))'
)
NEW_API3 = (
    '    with _run_lock:\n'
    '        try:\n'
    '            run_copycat(args)\n'
    '        except Exception as exc:\n'
    '            return jsonify({"error": str(exc)}), 500\n'
    '\n'
    '    out_dir = Path(args.output or str(input_dir or "."))'
)
if OLD_API3 in web:
    web = web.replace(OLD_API3, NEW_API3, 1)
    web_ok.append('/api/run out_dir fix')
elif 'input_dir or "."' in web:
    web_ok.append('/api/run out_dir fix (already present)')
else:
    print('WARN: /api/run out_dir not found')

open('CopyCat_Web.py', 'w', encoding='utf-8').write(web)
print('Web OK:', web_ok)

# ─────────────────────────────────────────────────────────────────────────────
# 3. test_copycat.py: Fixtures + Tests
# ─────────────────────────────────────────────────────────────────────────────
tests = open('test_copycat.py', encoding='utf-8').read()
test_ok = []

# _make_args: git_url=None Parameter
OLD_MA = (
    'def _make_args(types=None, recursive=False, max_size=None, input_path=None, output_path=None, '
    'fmt="txt", search=None, exclude=None, incremental=False, stats=False):'
)
NEW_MA = (
    'def _make_args(types=None, recursive=False, max_size=None, input_path=None, output_path=None, '
    'fmt="txt", search=None, exclude=None, incremental=False, stats=False, git_url=None):'
)
if OLD_MA in tests:
    tests = tests.replace(OLD_MA, NEW_MA, 1)
    test_ok.append('_make_args signature')
elif 'git_url=None' in tests and '_make_args' in tests:
    test_ok.append('_make_args signature (already present)')
else:
    print('WARN: _make_args signature not found')

OLD_MA2 = (
    '            incremental=incremental,\n'
    '            stats=stats,\n'
    '        )\n'
    '    return _make_args'
)
NEW_MA2 = (
    '            incremental=incremental,\n'
    '            stats=stats,\n'
    '            git_url=git_url,\n'
    '        )\n'
    '    return _make_args'
)
if OLD_MA2 in tests:
    tests = tests.replace(OLD_MA2, NEW_MA2, 1)
    test_ok.append('_make_args Namespace')
elif 'git_url=git_url' in tests:
    test_ok.append('_make_args Namespace (already present)')
else:
    print('WARN: _make_args Namespace not found')

# gui fixture: _git_url_var
OLD_GUI = (
    '    instance._stats_var = _make_var(False)\n'
    '    instance._watch_stop_event = None'
)
NEW_GUI = (
    '    instance._stats_var = _make_var(False)\n'
    '    instance._git_url_var = _make_var("")\n'
    '    instance._watch_stop_event = None'
)
if OLD_GUI in tests:
    tests = tests.replace(OLD_GUI, NEW_GUI, 1)
    test_ok.append('gui fixture _git_url_var')
elif '_git_url_var = _make_var' in tests:
    test_ok.append('gui fixture _git_url_var (already present)')
else:
    print('WARN: gui fixture stats_var not found')

# New tests to append
new_tests = '''

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
    conf.write_text("git_url = https://github.com/user/repo\\n", encoding="utf-8")
    with patch("sys.argv", ["CopyCat.py"]):
        args = parse_arguments(config_path=str(conf))
    assert args.git_url == "https://github.com/user/repo"


def test_run_copycat_git_url_invalid_url(tmp_path, run_args):
    """Ungueltige Git-URL: run_copycat gibt None zurueck, kein clone."""
    args = run_args(_make_args=lambda **kw: kw)
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
        (pathlib.Path(clone_path) / "main.py").write_text("x = 1\\n", encoding="utf-8")
        r = MagicMock()
        r.returncode = 0
        r.stderr = ""
        return r

    with patch("subprocess.run", side_effect=fake_clone):
        result = run_copycat(a)

    assert result is not None
    assert "combined_copycat" in result


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
    conf.write_text("git_url = https://github.com/user/repo\\n", encoding="utf-8")
    with patch("CopyCat_GUI.filedialog.askopenfilename", return_value=str(conf)):
        gui._load_config()
    assert gui._git_url_var.get() == "https://github.com/user/repo"


def test_gui_git_url_save_config(gui, tmp_path):
    """_save_config schreibt git_url wenn gesetzt."""
    out = tmp_path / "out.conf"
    gui._git_url_var.set("https://github.com/user/repo")
    with patch("CopyCat_GUI.filedialog.asksaveasfilename", return_value=str(out)), \\
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
'''

if 'test_parse_arguments_git_url_flag' in tests:
    test_ok.append('new tests (already present)')
else:
    tests += new_tests
    test_ok.append('new tests appended')

open('test_copycat.py', 'w', encoding='utf-8').write(tests)
print('Tests OK:', test_ok)

# ─────────────────────────────────────────────────────────────────────────────
# 4. READMEs
# ─────────────────────────────────────────────────────────────────────────────
for readme_file in ('README.md', 'README_GER.md'):
    readme = open(readme_file, encoding='utf-8').read()
    readme_ok = []

    # Feature table: add git-url row after stats row
    for stats_row, git_url_row in [
        (
            '| Code Statistics       | LOC, comment ratio, blank lines, cyclomatic complexity per file (`--stats`)   |',
            '| Remote Repository     | Clone and scan any remote Git repo directly (`--git-url`)                      |',
        ),
        (
            '| Code-Statistiken      | LOC, Kommentaranteil, Leerzeilen, zyklomatische Komplexit\u00e4t (`--stats`) |',
            '| Remote-Repository     | Beliebiges Git-Repo klonen und direkt scannen (`--git-url`)                    |',
        ),
    ]:
        if stats_row in readme and git_url_row not in readme:
            readme = readme.replace(stats_row, stats_row + '\n' + git_url_row, 1)
            readme_ok.append('feature table')
        elif git_url_row in readme:
            readme_ok.append('feature table (already present)')

    # CLI table: add --git-url row
    for stats_cli, git_url_cli in [
        (
            '| `--stats`             |',
            '| `--git-url URL`       | Clone and scan a remote Git repository                                | —   |',
        ),
        (
            '| `--stats`             |',
            '| `--git-url URL`       | Remote-Git-Repository klonen und scannen                              | —   |',
        ),
    ]:
        idx = readme.find(stats_cli)
        if idx >= 0:
            # Find end of this row
            end = readme.find('\n', idx)
            if end >= 0 and git_url_cli not in readme:
                readme = readme[:end+1] + git_url_cli + '\n' + readme[end+1:]
                readme_ok.append('cli table')
            elif git_url_cli in readme:
                readme_ok.append('cli table (already present)')
            break

    # copycat.conf table: add git_url row
    for conf_stats, conf_git in [
        (
            '| `stats`           |',
            '| `git_url`         | Remote Git repository URL to clone and scan                           | —       |',
        ),
        (
            '| `stats`           |',
            '| `git_url`         | Remote-Git-Repository-URL zum Klonen und Scannen                      | —       |',
        ),
    ]:
        idx = readme.find(conf_stats)
        if idx >= 0:
            end = readme.find('\n', idx)
            if end >= 0 and conf_git not in readme:
                readme = readme[:end+1] + conf_git + '\n' + readme[end+1:]
                readme_ok.append('conf table')
            elif conf_git in readme:
                readme_ok.append('conf table (already present)')
            break

    open(readme_file, 'w', encoding='utf-8').write(readme)
    print(f'{readme_file} OK:', readme_ok)

print('Done.')


