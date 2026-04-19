# CopyCat – Project Documenter

Run [CopyCat](https://github.com/holger1111/CopyCat) documentation reports directly from VS Code — no terminal required.

CopyCat scans a local folder and generates a consolidated report (TXT, JSON, Markdown, HTML, or PDF) containing all source files, diagrams, notebooks, and more — with a single click.

---

## Features

- **One-click report** via the status bar button or Command Palette
- **Recursive mode** to include all subdirectories
- **Multiple output formats**: TXT, JSON, Markdown, HTML, PDF
- **Language selection**: German (`de`) or English (`en`) report output
- **Auto-detection** of Python interpreter and `CopyCat.py` script
- **Fallback to CLI**: if `CopyCat.py` is not found, uses `copycat` from PATH (`pip install copycat-tool`)

---

## Requirements

Either:
- **Python** with `CopyCat.py` in your workspace root, or
- `copycat` installed via pip: `pip install copycat-tool`

---

## Usage

### Via Status Bar
Click the **`$(file-code) CopyCat`** button in the bottom status bar.

### Via Command Palette (`Ctrl+Shift+P`)
| Command | Description |
|---|---|
| `CopyCat: Report erstellen` | Generate report for current workspace |
| `CopyCat: Report erstellen (rekursiv)` | Generate report recursively |

---

## Extension Settings

| Setting | Default | Description |
|---|---|---|
| `copycat.pythonPath` | `` | Path to Python interpreter. Empty = auto-detect. |
| `copycat.scriptPath` | `` | Path to `CopyCat.py`. Empty = auto-detect in workspace root. |
| `copycat.outputFormat` | `txt` | Output format: `txt`, `json`, `md`, `html`, `pdf` |
| `copycat.maxSizeMb` | `0` | Max file size in MB (0 = unlimited) |
| `copycat.excludePatterns` | `[]` | Glob patterns to exclude, e.g. `["*.min.js", "dist/"]` |
| `copycat.lang` | `de` | Report language: `de` (German) or `en` (English) |
| `copycat.extraArgs` | `[]` | Additional CopyCat arguments, e.g. `["--search", "TODO\|FIXME"]` |

---

## How It Works

1. The extension detects Python and `CopyCat.py` automatically
2. It spawns a subprocess with the configured arguments
3. Output is streamed live into the **CopyCat** output channel
4. On success, a notification offers to open the output folder

---

## Source

[github.com/holger1111/CopyCat](https://github.com/holger1111/CopyCat)

---

## License

MIT
