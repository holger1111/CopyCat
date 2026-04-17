"""
CopyCat GUI v1.0
Grafische Oberfläche für CopyCat v2.9
"""

import argparse
import os
import sys
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from CopyCat import run_copycat

TYPES = ["code", "web", "db", "config", "docs", "deps", "img", "audio", "diagram"]


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
    def __init__(self, root: tk.Tk):
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
        self._type_vars = {t: tk.BooleanVar(value=True) for t in TYPES}

        self._build_ui()

    # ── UI-Aufbau ─────────────────────────────────────────────────────────────

    def _build_ui(self):  # pragma: no cover
        pad = {"padx": 8, "pady": 4}

        # Eingabeordner
        frm_io = ttk.LabelFrame(self._root, text="Ordner", padding=6)
        frm_io.pack(fill="x", **pad)

        ttk.Label(frm_io, text="Eingabe:").grid(row=0, column=0, sticky="w")
        ttk.Entry(frm_io, textvariable=self._input_var, width=55).grid(row=0, column=1, padx=4)
        ttk.Button(frm_io, text="…", width=3, command=self._browse_input).grid(row=0, column=2)

        ttk.Label(frm_io, text="Ausgabe:").grid(row=1, column=0, sticky="w", pady=(4, 0))
        ttk.Entry(frm_io, textvariable=self._output_var, width=55).grid(row=1, column=1, padx=4, pady=(4, 0))
        ttk.Button(frm_io, text="…", width=3, command=self._browse_output).grid(row=1, column=2, pady=(4, 0))

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
            values=["txt", "json", "md"],
            state="readonly",
            width=6,
        ).grid(row=0, column=4, sticky="w")

        ttk.Label(frm_opt, text="Suche (Regex):").grid(row=1, column=0, sticky="w", padx=6, pady=(6, 0))
        ttk.Entry(frm_opt, textvariable=self._search_var, width=40).grid(
            row=1, column=1, columnspan=4, sticky="w", pady=(6, 0)
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

        ttk.Button(frm_btn, text="✖  Ausgabe leeren", command=self._clear_output).pack(side="right", padx=4)

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
            if not self._output_var.get():
                self._output_var.set(folder)

    def _browse_output(self):
        folder = filedialog.askdirectory(title="Ausgabeordner wählen")
        if folder:
            self._output_var.set(folder)

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
        if folder and os.path.isdir(folder) and hasattr(os, "startfile"):
            os.startfile(folder)

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

        return argparse.Namespace(
            input=self._input_var.get().strip() or None,
            output=self._output_var.get().strip() or None,
            types=selected,
            recursive=self._recursive_var.get(),
            max_size=max_size,
            format=self._format_var.get(),
            search=search,
        )

    def _on_run(self):
        try:
            args = self._build_args()
        except ValueError as exc:
            messagebox.showerror("Eingabefehler", str(exc))
            return

        self._run_btn.configure(state="disabled")
        self._open_btn.configure(state="disabled")
        self._clear_output()

        old_stdout = sys.stdout
        sys.stdout = RedirectText(self._output_text)

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
                self._root.after(0, lambda: self._run_btn.configure(state="normal"))

        threading.Thread(target=task, daemon=True).start()


def main():  # pragma: no cover
    root = tk.Tk()
    CopyCatGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
