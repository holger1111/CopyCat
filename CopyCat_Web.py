"""
CopyCat v2.9 – Web-Interface (Flask)

Start:  python CopyCat_Web.py
        python CopyCat_Web.py --port 8080 --host 0.0.0.0
Öffne:  http://localhost:5000

Erfordert: pip install flask
"""

import argparse
import io
import logging
import os
import re
import sys
import threading
from argparse import Namespace
from pathlib import Path

try:
    from flask import Flask, Response, jsonify, redirect, render_template_string, request, url_for
except ImportError as _e:  # pragma: no cover
    print("Flask ist nicht installiert. Bitte: pip install flask")  # pragma: no cover
    sys.exit(1)  # pragma: no cover

from CopyCat import TYPE_FILTERS, load_plugins, run_copycat

# ── Flask-App ────────────────────────────────────────────────────────────────
app = Flask(__name__)
_run_lock = threading.Lock()

# ── HTML-Template (inline, kein separates templates/-Verzeichnis nötig) ──────
_TEMPLATE = """<!DOCTYPE html>
<html lang="de">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>CopyCat v2.9 Web</title>
  <style>
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: system-ui, sans-serif; background: #f0f2f5; color: #1a1a2e; min-height: 100vh; }
    header { background: #16213e; color: #e0e0e0; padding: 1rem 2rem; display: flex; align-items: center; gap: 1rem; }
    header h1 { font-size: 1.4rem; font-weight: 700; letter-spacing: .03em; }
    header span { font-size: .85rem; opacity: .6; }
    main { max-width: 860px; margin: 2rem auto; padding: 0 1rem; }
    .card { background: #fff; border-radius: 10px; box-shadow: 0 2px 8px rgba(0,0,0,.08); padding: 1.5rem; margin-bottom: 1.5rem; }
    .card h2 { font-size: 1rem; font-weight: 600; margin-bottom: 1rem; color: #16213e; border-bottom: 2px solid #e8ecf0; padding-bottom: .5rem; }
    label { display: block; font-size: .85rem; font-weight: 500; margin-bottom: .25rem; color: #444; }
    input[type=text], input[type=number], select {
      width: 100%; padding: .5rem .75rem; border: 1px solid #cdd5e0; border-radius: 6px;
      font-size: .9rem; margin-bottom: .9rem; background: #fafbfc;
    }
    input:focus, select:focus { outline: 2px solid #4a90d9; border-color: #4a90d9; }
    .row { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; }
    .checkboxes { display: flex; flex-wrap: wrap; gap: .5rem; margin-bottom: .9rem; }
    .checkboxes label { display: flex; align-items: center; gap: .3rem; font-weight: 400;
      background: #f0f2f5; border-radius: 4px; padding: .25rem .6rem; cursor: pointer; }
    .checkboxes input[type=checkbox] { margin: 0; }
    button[type=submit] {
      background: #16213e; color: #fff; border: none; border-radius: 6px;
      padding: .65rem 1.75rem; font-size: .95rem; font-weight: 600; cursor: pointer;
      transition: background .15s;
    }
    button[type=submit]:hover { background: #0f3460; }
    .flash { padding: .75rem 1rem; border-radius: 6px; margin-bottom: 1rem; font-size: .9rem; }
    .flash.error { background: #fde8e8; color: #c0392b; border: 1px solid #f5c6cb; }
    .flash.success { background: #e8f5e9; color: #27ae60; border: 1px solid #c3e6cb; }
    .report-box { background: #1a1a2e; color: #c8d3e0; border-radius: 8px; padding: 1rem;
      font-family: 'Courier New', monospace; font-size: .8rem; white-space: pre-wrap;
      max-height: 500px; overflow-y: auto; }
    .dl-link { display: inline-block; margin-top: .75rem; color: #4a90d9; font-size: .85rem; text-decoration: none; }
    .dl-link:hover { text-decoration: underline; }
    .plugins-list { font-size: .85rem; color: #555; }
    .plugins-list li { margin: .2rem 0; list-style: disc; margin-left: 1.2rem; }
  </style>
</head>
<body>
  <header>
    <h1>&#128008; CopyCat v2.9</h1>
    <span>Web-Interface</span>
  </header>
  <main>
    {% if error %}
    <div class="flash error">{{ error }}</div>
    {% endif %}

    <form method="post" action="/run">
      <div class="card">
        <h2>Ordner &amp; Ausgabe</h2>
        <div class="row">
          <div>
            <label for="input_dir">Eingabeordner</label>
            <input type="text" id="input_dir" name="input_dir" value="{{ form.input_dir }}" placeholder="/pfad/zum/projekt">
          </div>
          <div>
            <label for="output_dir">Ausgabeordner (leer = Eingabeordner)</label>
            <input type="text" id="output_dir" name="output_dir" value="{{ form.output_dir }}" placeholder="/pfad/zur/ausgabe">
          </div>
        </div>
      </div>

      <div class="card">
        <h2>Dateitypen</h2>
        <div class="checkboxes">
          <label><input type="checkbox" name="types" value="all" {% if 'all' in form.types %}checked{% endif %}> alle</label>
          {% for t in all_types %}
          <label><input type="checkbox" name="types" value="{{ t }}" {% if t in form.types %}checked{% endif %}> {{ t }}</label>
          {% endfor %}
        </div>
      </div>

      <div class="card">
        <h2>Optionen</h2>
        <div class="row">
          <div>
            <label for="fmt">Ausgabeformat</label>
            <select id="fmt" name="fmt">
              {% for f in ['txt', 'json', 'md'] %}
              <option value="{{ f }}" {% if form.fmt == f %}selected{% endif %}>{{ f }}</option>
              {% endfor %}
            </select>
          </div>
          <div>
            <label for="max_size">Max. Dateigröße (MB, 0 = unbegrenzt)</label>
            <input type="number" id="max_size" name="max_size" value="{{ form.max_size }}" min="0" step="0.1">
          </div>
        </div>
        <div class="row">
          <div>
            <label for="search">Suche (Regex, leer = keine)</label>
            <input type="text" id="search" name="search" value="{{ form.search }}" placeholder="TODO|FIXME">
          </div>
          <div>
            <label for="plugin_dir">Plugin-Verzeichnis (leer = Standard)</label>
            <input type="text" id="plugin_dir" name="plugin_dir" value="{{ form.plugin_dir }}" placeholder="plugins/">
          </div>
        </div>
        <label style="display:flex;align-items:center;gap:.5rem;margin-bottom:.9rem;">
          <input type="checkbox" name="recursive" {% if form.recursive %}checked{% endif %}> Rekursiv
        </label>
      </div>

      <div class="card">
        <h2>Plugins</h2>
        {% if plugins %}
        <ul class="plugins-list">
          {% for p in plugins %}
          <li><strong>{{ p.name }}</strong>: {{ p.patterns }} — {{ p.renderer }}</li>
          {% endfor %}
        </ul>
        {% else %}
        <span class="plugins-list">Keine Plugins geladen (kein Plugin-Verzeichnis angegeben oder leer).</span>
        {% endif %}
      </div>

      <button type="submit">&#9654; Report erstellen</button>
    </form>

    {% if report %}
    <div class="card" style="margin-top:1.5rem;">
      <h2>Report</h2>
      <div class="report-box">{{ report }}</div>
      {% if report_path %}
      <a class="dl-link" href="/download?path={{ report_path | urlencode }}">&#8595; Report herunterladen</a>
      {% endif %}
    </div>
    {% endif %}
  </main>
</body>
</html>"""


def _build_args(form) -> Namespace:
    """Baut ein argparse.Namespace aus einem Flask-Formular."""
    types_raw = form.getlist("types")
    if not types_raw or "all" in types_raw:
        types = ["all"]
    else:
        types = [t for t in types_raw if t in TYPE_FILTERS]
        if not types:
            types = ["all"]

    try:
        max_size = float(form.get("max_size", "0") or "0")
    except ValueError:
        max_size = 0.0
    max_size = float("inf") if max_size <= 0 else max_size

    input_dir = form.get("input_dir", "").strip() or None
    output_dir = form.get("output_dir", "").strip() or None
    search = form.get("search", "").strip() or None
    plugin_dir = form.get("plugin_dir", "").strip() or None

    return Namespace(
        input=input_dir,
        output=output_dir,
        types=types,
        recursive="recursive" in form,
        max_size=max_size,
        format=form.get("fmt", "txt"),
        search=search,
        template=None,
        watch=False,
        cooldown=2.0,
        plugin_dir=plugin_dir,
        list_plugins=False,
        diff=None,
        merge=None,
        install_hook=None,
        verbose=False,
        quiet=True,
    )


def _form_defaults():
    return {
        "input_dir": "",
        "output_dir": "",
        "types": ["all"],
        "fmt": "txt",
        "max_size": "0",
        "search": "",
        "plugin_dir": "",
        "recursive": False,
    }


def _get_plugins(plugin_dir_str):  # pragma: no branch
    """Gibt Liste von Plugin-Infos zurück ohne den globalen Zustand zu verändern."""
    from CopyCat import TYPE_FILTERS as TF, PLUGIN_RENDERERS as PR, _loaded_plugins as LP
    import CopyCat
    if not plugin_dir_str:
        return []
    plugin_dir = Path(plugin_dir_str)
    if not plugin_dir.is_dir():
        return []
    # Snapshot vorher
    tf_before = set(TF.keys())
    load_plugins(plugin_dir)
    result = []
    for t in TF:
        if t not in tf_before:
            pats = ", ".join(TF[t])
            renderer = "benutzerdefinierter Renderer" if PR.get(t) else "Standard-Renderer"
            result.append({"name": t, "patterns": pats, "renderer": renderer})
    return result


@app.route("/", methods=["GET"])
def index():
    return render_template_string(
        _TEMPLATE,
        form=_form_defaults(),
        all_types=list(TYPE_FILTERS.keys()),
        plugins=[],
        report=None,
        report_path=None,
        error=None,
    )


@app.route("/run", methods=["POST"])
def run():
    form_data = {
        "input_dir": request.form.get("input_dir", "").strip(),
        "output_dir": request.form.get("output_dir", "").strip(),
        "types": request.form.getlist("types") or ["all"],
        "fmt": request.form.get("fmt", "txt"),
        "max_size": request.form.get("max_size", "0"),
        "search": request.form.get("search", "").strip(),
        "plugin_dir": request.form.get("plugin_dir", "").strip(),
        "recursive": "recursive" in request.form,
    }

    # Pflichtfeld: Eingabeordner
    if not form_data["input_dir"]:
        return render_template_string(
            _TEMPLATE,
            form=form_data,
            all_types=list(TYPE_FILTERS.keys()),
            plugins=[],
            report=None,
            report_path=None,
            error="Bitte einen Eingabeordner angeben.",
        )

    input_dir = Path(form_data["input_dir"])
    if not input_dir.is_dir():
        return render_template_string(
            _TEMPLATE,
            form=form_data,
            all_types=list(TYPE_FILTERS.keys()),
            plugins=[],
            report=None,
            report_path=None,
            error=f"Eingabeordner existiert nicht: {input_dir}",
        )

    plugins = _get_plugins(form_data["plugin_dir"])

    args = _build_args(request.form)

    error = None
    report_text = None
    report_path = None

    with _run_lock:
        try:
            run_copycat(args)
            # Letzten erstellten Report einlesen
            out_dir = Path(args.output or str(input_dir))
            fmt = args.format
            reports = sorted(out_dir.glob(f"combined_copycat_*.{fmt}"))
            if reports:
                last_report = reports[-1]
                report_path = str(last_report)
                try:
                    report_text = last_report.read_text(encoding="utf-8")
                except Exception:
                    report_text = f"[Report-Datei konnte nicht gelesen werden: {last_report}]"
            else:
                report_text = "(Kein Report erstellt – ggf. keine passenden Dateien gefunden)"
        except Exception as exc:
            error = str(exc)

    return render_template_string(
        _TEMPLATE,
        form=form_data,
        all_types=list(TYPE_FILTERS.keys()),
        plugins=plugins,
        report=report_text,
        report_path=report_path,
        error=error,
    )


@app.route("/download")
def download():
    path_str = request.args.get("path", "")
    if not path_str:
        return "Kein Pfad angegeben.", 400
    p = Path(path_str)
    if not p.is_file():
        return "Datei nicht gefunden.", 404
    # Sicherheitscheck: nur combined_copycat_*.{txt,json,md} erlaubt
    if not re.fullmatch(r"combined_copycat_\d+\.(txt|json|md)", p.name):
        return "Nicht erlaubt.", 403
    content = p.read_bytes()
    mime = {"txt": "text/plain", "json": "application/json", "md": "text/markdown"}.get(
        p.suffix.lstrip("."), "application/octet-stream"
    )
    return Response(
        content,
        mimetype=mime,
        headers={"Content-Disposition": f'attachment; filename="{p.name}"'},
    )


@app.route("/api/run", methods=["POST"])
def api_run():
    """JSON-API: POST {"input": "...", "types": [...], "format": "txt", ...}"""
    data = request.get_json(silent=True) or {}
    if not data.get("input"):
        return jsonify({"error": "Feld 'input' fehlt"}), 400

    input_dir = Path(data["input"])
    if not input_dir.is_dir():
        return jsonify({"error": f"Eingabeordner existiert nicht: {input_dir}"}), 400

    form_like = {
        "input_dir": data.get("input", ""),
        "output_dir": data.get("output", ""),
        "types": data.get("types", ["all"]),
        "fmt": data.get("format", "txt"),
        "max_size": str(data.get("max_size", 0)),
        "search": data.get("search", ""),
        "plugin_dir": data.get("plugin_dir", ""),
    }
    if data.get("recursive"):
        form_like["recursive"] = "on"

    class _FakeForm:
        def get(self, key, default=""):
            return form_like.get(key, default)
        def getlist(self, key):
            val = form_like.get(key, [])
            return val if isinstance(val, list) else [val]
        def __contains__(self, item):
            return item in form_like

    args = _build_args(_FakeForm())
    with _run_lock:
        try:
            run_copycat(args)
        except Exception as exc:
            return jsonify({"error": str(exc)}), 500

    out_dir = Path(args.output or str(input_dir))
    fmt = args.format
    reports = sorted(out_dir.glob(f"combined_copycat_*.{fmt}"))
    if reports:
        last_report = reports[-1]
        return jsonify({
            "status": "ok",
            "report": str(last_report),
            "name": last_report.name,
        })
    return jsonify({"status": "ok", "report": None})


def _parse_web_args():
    parser = argparse.ArgumentParser(description="CopyCat v2.9 Web-Interface")
    parser.add_argument("--host", default="127.0.0.1", help="Bind-Adresse (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=5000, help="Port (default: 5000)")
    parser.add_argument("--debug", action="store_true", help="Flask Debug-Modus")
    return parser.parse_args()


if __name__ == "__main__":  # pragma: no cover
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    web_args = _parse_web_args()
    print(f"CopyCat Web-Interface läuft auf http://{web_args.host}:{web_args.port}")
    app.run(host=web_args.host, port=web_args.port, debug=web_args.debug)
