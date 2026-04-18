"""
CopyCat GUI v1.1
Grafische Oberfläche für CopyCat v2.9
"""

import argparse
import logging
import os
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from CopyCat import diff_reports, install_hook, load_config, merge_reports, run_copycat, watch_and_run

try:  # pragma: no cover
    from tkinterdnd2 import DND_FILES, TkinterDnD
    _DND_AVAILABLE = True
except ImportError:
    _DND_AVAILABLE = False

TYPES = ["code", "web", "db", "config", "docs", "deps", "img", "audio", "diagram", "notebook"]


class RedirectText:
    """Leitet sys.stdout in ein tkinter Text-Widget um."""

    def __init__(self, widget: tk.Text):
        self._widget = widget

    def write(self, text: str):
        self._widget.configure(state="normal")
        self._widget.insert("end", text)
        self._widget.see("end")
        self._widget.configure(state="disabled")

    def flush(self):
        pass


class CopyCatGUI:
    def __init__(self, root: tk.Tk):  # pragma: no cover
        self._root = root
        self._root.title("CopyCat v2.9")
        self._root.resizable(True, True)
        self._root.minsize(620, 600)

        self._input_var = tk.StringVar()
        self._output_var = tk.StringVar()
        self._recursive_var = tk.BooleanVar(value=False)
        self._max_size_var = tk.StringVar()
        self._format_var = tk.StringVar(value="txt")
        self._search_var = tk.StringVar()
        self._template_var = tk.StringVar()
        self._cooldown_var = tk.StringVar(value="2.0")
        self._exclude_var = tk.StringVar()
        self._incremental_var = tk.BooleanVar(value=False)
        self._stats_var = tk.BooleanVar(value=False)
        self._watch_stop_event = None
        self._type_vars = {t: tk.BooleanVar(value=True) for t in TYPES}

        self._build_ui()

    # ── UI-Aufbau ─────────────────────────────────────────────────────────────

    def _build_ui(self):  # pragma: no cover
        pad = {"padx": 8, "pady": 4}

        # Eingabeordner
        frm_io = ttk.LabelFrame(self._root, text="Ordner", padding=6)
        frm_io.pack(fill="x", **pad)

        ttk.Label(frm_io, text="Eingabe:").grid(row=0, column=0, sticky="w")
        _entry_in = ttk.Entry(frm_io, textvariable=self._input_var, width=55)
        _entry_in.grid(row=0, column=1, padx=4)
        ttk.Button(frm_io, text="…", width=3, command=self._browse_input).grid(row=0, column=2)

        ttk.Label(frm_io, text="Ausgabe:").grid(row=1, column=0, sticky="w", pady=(4, 0))
        _entry_out = ttk.Entry(frm_io, textvariable=self._output_var, width=55)
        _entry_out.grid(row=1, column=1, padx=4, pady=(4, 0))
        ttk.Button(frm_io, text="…", width=3, command=self._browse_output).grid(row=1, column=2, pady=(4, 0))

        if _DND_AVAILABLE:
            _entry_in.drop_target_register(DND_FILES)
            _entry_in.dnd_bind("<<Drop>>", self._on_drop_input)
            _entry_out.drop_target_register(DND_FILES)
            _entry_out.dnd_bind("<<Drop>>", self._on_drop_output)

        # Dateitypen
        frm_types = ttk.LabelFrame(self._root, text="Dateitypen", padding=6)
        frm_types.pack(fill="x", **pad)

        for i, t in enumerate(TYPES):
            ttk.Checkbutton(frm_types, text=t, variable=self._type_vars[t]).grid(
                row=i // 5, column=i % 5, sticky="w", padx=6
            )
        ttk.Button(frm_types, text="Alle", command=self._select_all_types).grid(
            row=1, column=4, sticky="e", padx=6
        )
        ttk.Button(frm_types, text="Keine", command=self._deselect_all_types).grid(
            row=1, column=3, sticky="e", padx=6
        )

        # Optionen
        frm_opt = ttk.LabelFrame(self._root, text="Optionen", padding=6)
        frm_opt.pack(fill="x", **pad)

        ttk.Checkbutton(frm_opt, text="Rekursiv", variable=self._recursive_var).grid(
            row=0, column=0, sticky="w", padx=6
        )

        ttk.Label(frm_opt, text="Max. Größe (MB):").grid(row=0, column=1, sticky="w", padx=(16, 4))
        ttk.Entry(frm_opt, textvariable=self._max_size_var, width=8).grid(row=0, column=2, sticky="w")

        ttk.Label(frm_opt, text="Format:").grid(row=0, column=3, sticky="w", padx=(16, 4))
        ttk.Combobox(
            frm_opt,
            textvariable=self._format_var,
            values=["txt", "json", "md", "html"],
            state="readonly",
            width=6,
        ).grid(row=0, column=4, sticky="w")

        ttk.Label(frm_opt, text="Suche (Regex):").grid(row=1, column=0, sticky="w", padx=6, pady=(6, 0))
        ttk.Entry(frm_opt, textvariable=self._search_var, width=40).grid(
            row=1, column=1, columnspan=4, sticky="w", pady=(6, 0)
        )

        ttk.Label(frm_opt, text="Ausschließen:").grid(row=3, column=0, sticky="w", padx=6, pady=(6, 0))
        ttk.Entry(frm_opt, textvariable=self._exclude_var, width=40).grid(
            row=3, column=1, columnspan=4, sticky="w", pady=(6, 0)
        )

        ttk.Checkbutton(frm_opt, text="Inkrementell (Cache)", variable=self._incremental_var).grid(
            row=3, column=4, columnspan=2, sticky="w", padx=(16, 0), pady=(6, 0)
        )

        ttk.Checkbutton(frm_opt, text="Code-Statistiken", variable=self._stats_var).grid(
            row=4, column=4, columnspan=2, sticky="w", padx=(16, 0), pady=(6, 0)
        )

        ttk.Label(frm_opt, text="Template (.j2):").grid(row=4, column=0, sticky="w", padx=6, pady=(6, 0))
        ttk.Entry(frm_opt, textvariable=self._template_var, width=30).grid(
            row=4, column=1, columnspan=2, sticky="w", padx=(0, 4), pady=(6, 0)
        )
        ttk.Button(frm_opt, text="…", width=3, command=self._browse_template).grid(
            row=4, column=3, sticky="w", pady=(6, 0)
        )
        ttk.Label(frm_opt, text="Cooldown (s):").grid(row=4, column=4, sticky="w", padx=(16, 4), pady=(6, 0))
        ttk.Entry(frm_opt, textvariable=self._cooldown_var, width=6).grid(
            row=4, column=5, sticky="w", pady=(6, 0)
        )

        # Buttons
        frm_btn = ttk.Frame(self._root, padding=4)
        frm_btn.pack(fill="x", padx=8)

        self._run_btn = ttk.Button(frm_btn, text="▶  Starten", command=self._on_run)
        self._run_btn.pack(side="left", padx=4)

        self._open_btn = ttk.Button(
            frm_btn, text="📂  Ordner öffnen", command=self._open_output_folder, state="disabled"
        )
        self._open_btn.pack(side="left", padx=4)

        ttk.Button(frm_btn, text="📥  Config laden", command=self._load_config).pack(side="left", padx=4)
        ttk.Button(frm_btn, text="💾  Config speichern", command=self._save_config).pack(side="left", padx=4)
        ttk.Button(frm_btn, text="⇄  Diff", command=self._on_diff).pack(side="left", padx=4)
        ttk.Button(frm_btn, text="📄  Merge", command=self._on_merge).pack(side="left", padx=4)
        ttk.Button(frm_btn, text="🔗  Hook", command=self._on_install_hook).pack(side="left", padx=4)
        self._watch_btn = ttk.Button(frm_btn, text="👁  Watch", command=self._on_watch_toggle)
        self._watch_btn.pack(side="left", padx=4)

        ttk.Button(frm_btn, text="✖  Ausgabe leeren", command=self._clear_output).pack(side="right", padx=4)

        # Fortschrittsanzeige
        self._progress = ttk.Progressbar(frm_btn, mode="indeterminate", length=80)
        self._progress.pack(side="right", padx=8)

        # Ausgabe
        frm_out = ttk.LabelFrame(self._root, text="Ausgabe", padding=6)
        frm_out.pack(fill="both", expand=True, padx=8, pady=4)

        self._output_text = tk.Text(frm_out, state="disabled", wrap="word", font=("Consolas", 9))
        sb = ttk.Scrollbar(frm_out, command=self._output_text.yview)
        self._output_text.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self._output_text.pack(fill="both", expand=True)

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _browse_input(self):
        folder = filedialog.askdirectory(title="Eingabeordner wählen")
        if folder:
            self._input_var.set(folder)
            self._output_var.set(self._output_var.get() or folder)

    def _browse_output(self):  # pragma: no cover
        folder = filedialog.askdirectory(title="Ausgabeordner wählen")
        if folder:
            self._output_var.set(folder)

    def _browse_template(self):  # pragma: no cover
        path = filedialog.askopenfilename(
            title="Jinja2-Template wählen",
            filetypes=[("Jinja2-Templates", "*.j2 *.jinja2 *.html"), ("Alle Dateien", "*.*")],
        )
        if path:
            self._template_var.set(path)

    def _select_all_types(self):
        for var in self._type_vars.values():
            var.set(True)

    def _deselect_all_types(self):
        for var in self._type_vars.values():
            var.set(False)

    def _clear_output(self):
        self._output_text.configure(state="normal")
        self._output_text.delete("1.0", "end")
        self._output_text.configure(state="disabled")

    def _open_output_folder(self):
        folder = self._output_var.get() or self._input_var.get()
        if folder and os.path.isdir(folder) and hasattr(os, "startfile"):  # pragma: no branch
            os.startfile(folder)

    # ── Config Load / Save ────────────────────────────────────────────────────

    def _load_config(self):
        path = filedialog.askopenfilename(
            title="Konfiguration laden",
            filetypes=[("Config-Dateien", "*.conf"), ("Alle Dateien", "*.*")],
        )
        if not path:
            return
        cfg = load_config(path)
        if "input" in cfg:
            self._input_var.set(cfg["input"])
        if "output" in cfg:
            self._output_var.set(cfg["output"])
        if "types" in cfg:
            parts = {t.strip() for t in cfg["types"].replace(",", " ").split()}
            for t, var in self._type_vars.items():
                var.set(t in parts or "all" in parts)
        if "recursive" in cfg:
            self._recursive_var.set(cfg["recursive"].lower() in ("true", "yes", "1"))
        if "max_size_mb" in cfg:
            self._max_size_var.set(cfg["max_size_mb"])
        if "format" in cfg and cfg["format"] in ("txt", "json", "md", "html"):
            self._format_var.set(cfg["format"])
        if "search" in cfg:
            self._search_var.set(cfg["search"])
        if "exclude" in cfg:
            self._exclude_var.set(cfg["exclude"])
        if "incremental" in cfg:
            self._incremental_var.set(cfg["incremental"].lower() in ("true", "yes", "1"))
        if "stats" in cfg:
            self._stats_var.set(cfg["stats"].lower() in ("true", "yes", "1"))

    def _save_config(self):
        path = filedialog.asksaveasfilename(
            title="Konfiguration speichern",
            defaultextension=".conf",
            filetypes=[("Config-Dateien", "*.conf"), ("Alle Dateien", "*.*")],
        )
        if not path:
            return
        selected = [t for t, var in self._type_vars.items() if var.get()]
        lines = [
            "# CopyCat Konfiguration",
            f"input = {self._input_var.get()}",
            f"output = {self._output_var.get()}",
            f"types = {','.join(selected) if selected else 'all'}",
            f"recursive = {'true' if self._recursive_var.get() else 'false'}",
            f"format = {self._format_var.get()}",
        ]
        max_size = self._max_size_var.get().strip()
        if max_size:
            lines.append(f"max_size_mb = {max_size}")
        search = self._search_var.get().strip()
        if search:
            lines.append(f"search = {search}")
        exclude = self._exclude_var.get().strip()
        if exclude:
            lines.append(f"exclude = {exclude}")
        if self._incremental_var.get():
            lines.append("incremental = true")
        if self._stats_var.get():
            lines.append("stats = true")
        try:
            Path(path).write_text("\n".join(lines) + "\n", encoding="utf-8")
            messagebox.showinfo("Gespeichert", f"Config gespeichert:\n{path}")
        except OSError as e:
            messagebox.showerror("Fehler", f"Speichern fehlgeschlagen:\n{e}")

    # ── Drag & Drop ───────────────────────────────────────────────────────────

    def _on_drop_input(self, event):  # pragma: no cover
        path = event.data.strip().strip("{}")
        if os.path.isdir(path):
            self._input_var.set(path)
            self._output_var.set(self._output_var.get() or path)

    def _on_drop_output(self, event):  # pragma: no cover
        path = event.data.strip().strip("{}")
        if os.path.isdir(path):
            self._output_var.set(path)

    # ── Diff ──────────────────────────────────────────────────────────────────

    def _on_diff(self):
        path_a = filedialog.askopenfilename(
            title="Report A wählen",
            filetypes=[("CopyCat Reports", "*.txt *.json *.md"), ("Alle Dateien", "*.*")],
        )
        if not path_a:
            return
        path_b = filedialog.askopenfilename(
            title="Report B wählen",
            filetypes=[("CopyCat Reports", "*.txt *.json *.md"), ("Alle Dateien", "*.*")],
        )
        if not path_b:
            return
        try:
            result = diff_reports(Path(path_a), Path(path_b))
        except Exception as exc:
            messagebox.showerror("Diff-Fehler", str(exc))
            return
        self._clear_output()
        self._output_text.configure(state="normal")
        self._output_text.insert("end", result)
        self._output_text.configure(state="disabled")

    # ── Merge ─────────────────────────────────────────────────────────────────

    def _on_merge(self):
        paths = filedialog.askopenfilenames(
            title="Reports zum Zusammenführen wählen",
            filetypes=[("CopyCat Reports", "*.txt *.json *.md"), ("Alle Dateien", "*.*")],
        )
        if not paths:
            return
        if len(paths) < 2:
            messagebox.showwarning("Merge", "Bitte mindestens 2 Reports auswählen.")
            return
        try:
            result = merge_reports([Path(p) for p in paths])
        except Exception as exc:
            messagebox.showerror("Merge-Fehler", str(exc))
            return
        self._clear_output()
        self._output_text.configure(state="normal")
        self._output_text.insert("end", result)
        self._output_text.configure(state="disabled")

    # ── Hook ─────────────────────────────────────────────────────────────────

    def _on_install_hook(self):
        project_dir = filedialog.askdirectory(
            title="Git-Projektordner wählen (enthält .git/)"
        )
        if not project_dir:
            return
        try:
            hook_path = install_hook(Path(project_dir))
            messagebox.showinfo(
                "Hook installiert",
                f"CopyCat pre-commit Hook installiert:\n{hook_path}",
            )
        except FileNotFoundError as exc:
            messagebox.showerror("Hook-Fehler", str(exc))

    # ── Run ───────────────────────────────────────────────────────────────────

    def _build_args(self):
        selected = [t for t, var in self._type_vars.items() if var.get()]
        if not selected:
            selected = ["all"]

        max_size_str = self._max_size_var.get().strip()
        try:
            max_size = float(max_size_str) if max_size_str else float("inf")
        except ValueError:
            raise ValueError(f"Ungültige Max-Größe: '{max_size_str}' (Zahl erwartet)")

        search = self._search_var.get().strip() or None
        exclude_raw = self._exclude_var.get().strip()
        exclude = [p.strip() for p in exclude_raw.replace(",", " ").split() if p.strip()] if exclude_raw else []

        return argparse.Namespace(
            input=self._input_var.get().strip() or None,
            output=self._output_var.get().strip() or None,
            types=selected,
            recursive=self._recursive_var.get(),
            max_size=max_size,
            format=self._format_var.get(),
            search=search,
            template=self._template_var.get().strip() or None,
            cooldown=float(self._cooldown_var.get().strip() or "2.0"),
            watch=False,
            exclude=exclude,
            incremental=self._incremental_var.get(),
            stats=self._stats_var.get(),
        )

    def _on_watch_toggle(self):  # pragma: no cover
        """Start or stop the background Watch thread."""
        if self._watch_stop_event is not None and not self._watch_stop_event.is_set():
            # Currently running → stop
            self._watch_stop_event.set()
            self._watch_btn.configure(text="👁  Watch")
            return

        try:
            args = self._build_args()
        except ValueError as exc:
            messagebox.showerror("Eingabefehler", str(exc))
            return

        if not args.input or not Path(args.input).is_dir():
            messagebox.showerror("Eingabefehler", "Bitte gültigen Eingabeordner angeben.")
            return

        self._watch_stop_event = threading.Event()
        widget_stream = RedirectText(self._output_text)
        _log_handler = logging.StreamHandler(widget_stream)
        _log_handler.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
        root_logger = logging.getLogger()
        root_logger.addHandler(_log_handler)

        stop_event = self._watch_stop_event

        def _run():
            try:
                watch_and_run(args, cooldown=args.cooldown, stop_event=stop_event)
            except Exception as exc:
                logging.error("Watch beendet: %s", exc)
            finally:
                root_logger.removeHandler(_log_handler)
                self._watch_stop_event = None
                try:
                    self._watch_btn.configure(text="👁  Watch")
                except Exception:
                    pass

        self._watch_btn.configure(text="■  Watch stoppen")
        threading.Thread(target=_run, daemon=True).start()

    def _on_run(self):
        try:
            args = self._build_args()
        except ValueError as exc:
            messagebox.showerror("Eingabefehler", str(exc))
            return

        self._run_btn.configure(state="disabled")
        self._open_btn.configure(state="disabled")
        self._clear_output()
        self._progress.start(10)

        old_stdout = sys.stdout
        widget_stream = RedirectText(self._output_text)
        sys.stdout = widget_stream

        _log_handler = logging.StreamHandler(widget_stream)
        _log_handler.setFormatter(logging.Formatter("%(message)s"))
        _log_handler.setLevel(logging.INFO)
        _root_logger = logging.getLogger()
        _prev_level = _root_logger.level
        _root_logger.setLevel(logging.INFO)
        _root_logger.addHandler(_log_handler)

        def task():
            try:
                run_copycat(args)
                self._root.after(0, lambda: self._open_btn.configure(state="normal"))
            except Exception as exc:
                msg = str(exc)
                self._root.after(
                    0,
                    lambda m=msg: messagebox.showerror("Fehler", f"CopyCat Fehler:\n{m}"),
                )
            finally:
                sys.stdout = old_stdout
                _root_logger.removeHandler(_log_handler)
                _root_logger.setLevel(_prev_level)
                self._root.after(0, self._progress.stop)
                self._root.after(0, lambda: self._run_btn.configure(state="normal"))

        threading.Thread(target=task, daemon=True).start()


def main():  # pragma: no cover
    root = TkinterDnD.Tk() if _DND_AVAILABLE else tk.Tk()
    CopyCatGUI(root)
    root.mainloop()


if __name__ == "__main__":  # pragma: no cover
    main()
