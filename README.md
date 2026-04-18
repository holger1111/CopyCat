# CopyCat v2.9 - Project Documenter


## Automates Code + Diagrams + Media into Text Reports

[![Tests](https://github.com/holger1111/CopyCat/actions/workflows/ci.yml/badge.svg)](https://github.com/holger1111/CopyCat/actions)
[![Coverage](https://codecov.io/gh/holger1111/CopyCat/branch/main/graph/badge.svg)](https://codecov.io/gh/holger1111/CopyCat)


### Main Features


| Feature		| Description						|
|-----------------------|-------------------------------------------------------|
| Code Analysis		| Line count + source code (Java/Python/C++/etc.)	|
| Draw.io		| Extraction of all cells (ID, text, position), ZIP + compressed support	|
| Media			| MIME type, size, audio duration (WAV/MP3/FLAC)	|
| Notebooks/CSV		| Jupyter `.ipynb` cell extraction + `.csv` support	|
| Self-Protection	| Ignores CopyCat.py & old reports			|
| Serial System		| Automatic archive (CopyCat_Archive)			|
| Git Integration	| Branch + commit hash					|
| Output Formats	| TXT / JSON / Markdown / **HTML** (with syntax highlighting) / **PDF** / Jinja2 template (`--format`, `--template`)	|
| Incremental Cache	| Only re-scan changed files; SHA-256 cache in `.copycat_cache/` (`--incremental`)	|
| Code Statistics	| LOC, comment ratio, blank lines, cyclomatic complexity per file (`--stats`)	|
| Remote Repository	| Clone and scan any remote Git repo directly (`--git-url`)				|
| Content Search	| Parallel regex search across files (`--search`)	|
| Diff Mode		| Compare two reports (`--diff`)			|
| Merge Mode		| Combine multiple reports (`--merge`)			|
| Watch Mode		| Auto-rerun on file changes (`--watch`, `--cooldown`)	|
| Plugin System		| Add custom file types via `.py` plugins (`--plugin-dir`)	|
| Pre-commit Hook	| Install as Git hook (`--install-hook`)		|
| Config File		| `copycat.conf` auto-loaded; CLI overrides		|
| PDF Export		| Structured PDF with tables, code details, stats (`--format pdf`)	|
| AI Summary		| AI project brief via OpenAI-compatible API (`--ai-summary`)	|
| Report Timeline	| Visual history of archived reports (`--timeline`)	|
| Docker		| Run CopyCat without Python installation (`docker run`)	|
| Performance		| Recursive/flat, size filter + progress		|
| GUI			| Graphical interface via `CopyCat_GUI.py` (drag & drop, output preview)	|
| Web Interface		| Browser UI via Flask with optional token authentication (`--auth-token`)	|
| VS Code Extension	| Run reports from the editor with Jest unit tests (`copycat-vscode/`)	|
| CI Artifacts		| PyInstaller `.exe` builds via GitHub Actions		|


### GUI

```bash
python CopyCat_GUI.py    # Opens the graphical interface
```

All CLI options are available as UI controls. Progress output is displayed live in the window.
Requires Python with tkinter (included in standard installation).


### Web Interface

```bash
python CopyCat_Web.py                    # Start web UI on http://localhost:5000
python CopyCat_Web.py --port 8080        # Custom port
python CopyCat_Web.py --host 0.0.0.0     # Listen on all interfaces
```

**Security:**

By default, the web interface listens on `127.0.0.1` (localhost only) without authentication.

To enable token-based authentication:

```bash
# Option 1: Command-line argument
python CopyCat_Web.py --host 0.0.0.0 --auth-token "your-secret-token-here"

# Option 2: Environment variable
set COPYCAT_WEB_TOKEN=your-secret-token-here
python CopyCat_Web.py --host 0.0.0.0
```

When a token is configured, users must login with the token before accessing the interface. The token is compared using HMAC timing-safe comparison (`hmac.compare_digest()`) to prevent timing attacks.

**Warning:** Running with `--host 0.0.0.0` without authentication exposes the server to the network. Always use `--auth-token` for remote access.

**Commands (Command Palette / Status Bar):**

| Command | Description |
|---|---|
| `CopyCat: Report erstellen` | Run flat report for current workspace |
| `CopyCat: Report erstellen (rekursiv)` | Run recursive report |

**Settings (`File → Preferences → Settings → CopyCat`):**

| Setting | Description | Default |
|---|---|---|
| `copycat.pythonPath` | Python interpreter path | auto-detect |
| `copycat.scriptPath` | Path to `CopyCat.py` | workspace root |
| `copycat.outputFormat` | `txt` / `json` / `md` / `html` | `txt` |
| `copycat.maxSizeMb` | Max file size in MB (0 = unlimited) | `0` |
| `copycat.excludePatterns` | Glob patterns to exclude, e.g. `["dist/", "*.min.js"]` | `[]` |
| `copycat.extraArgs` | Additional CLI arguments | `[]` |

**Build & install:**
```bash
cd copycat-vscode
npm install
npm run compile       # TypeScript → out/extension.js
npm run package       # creates copycat-0.1.0.vsix
# VS Code: Extensions → ⋯ → Install from VSIX
```


### Console Commands


```bash
python CopyCat.py                              # Default (flat, all types, txt)
python CopyCat.py -i C:\Project               # Input folder
python CopyCat.py -o docs                     # Output folder
python CopyCat.py -t code,diagram             # Code + diagrams only
python CopyCat.py -r -s 5                     # Recursive, max 5MB
python CopyCat.py -f json                     # JSON output
python CopyCat.py -f md                       # Markdown output
python CopyCat.py -S "TODO|FIXME"             # Search for TODOs
python CopyCat.py --template report.j2        # Custom Jinja2 output
python CopyCat.py -w --cooldown 3             # Watch mode, 3 s cooldown
python CopyCat.py --diff report1.txt report2.txt  # Compare two reports
python CopyCat.py --merge r1.txt r2.txt       # Merge reports
python CopyCat.py --install-hook C:\Project   # Install Git pre-commit hook
python CopyCat.py -v                          # Verbose (DEBUG)
python CopyCat.py -q                          # Quiet (warnings only)
python CopyCat.py --help                      # Help
# Config file auto-loaded from CWD or script dir:
python CopyCat.py                             # uses copycat.conf if present
```


### Parameters


| Flag				| Description								| Default	|
|-------------------------------|-----------------------------------------------------------------------|---------------|
| `-i`, `--input`		| Input folder								| Script folder	|
| `-o`, `--output`		| Output folder								| Input folder	|
| `-t`, `--types`		| Types: `code web db config docs deps img audio diagram notebook` or `all`	| `all`	|
| `-r`, `--recursive`		| Recursive search in subfolders					| false		|
| `-s`, `--max-size`		| Max file size in MB							| unlimited	|
| `-f`, `--format`		| Output format: `txt`, `json`, `md`, `html`, `pdf`					| `txt`		|
| `-S`, `--search`		| Regex search pattern (e.g. `TODO\|FIXME`, `def `)		| None		|
| `-E`, `--exclude`		| Glob patterns or folders to exclude (e.g. `*.min.js` `dist/` `node_modules/`)	| None	|
| `-I`, `--incremental`	| Incremental mode: only re-scan changed files, cache in `.copycat_cache/`	| off	|
| `--stats`			| Code statistics: LOC, comment lines, blank lines, cyclomatic complexity		| off	|
| `--git-url URL`		| Clone and scan a remote Git repository					| —	|
| `-v`, `--verbose`		| Verbose output (DEBUG level)						| off		|
| `-q`, `--quiet`		| Quiet mode (warnings only)						| off		|
| `--template`			| Path to a Jinja2 template file (`.j2`); requires `pip install jinja2`	| None		|
| `-w`, `--watch`		| Watch mode: re-run on file changes; requires `pip install watchdog`	| off		|
| `--cooldown`			| Seconds to wait after last change before re-running (watch mode)	| `2.0`		|
| `--diff A B`			| Compare two CopyCat reports and show differences		| —		|
| `--merge R [R ...]`		| Merge multiple CopyCat reports into one			| —		|
| `--plugin-dir DIR`		| Load plugins from this directory (default: `plugins/` next to CopyCat.py)	| —	|
| `--list-plugins`		| Show loaded plugins and exit					| off		|
| `--install-hook DIR`		| Install CopyCat as Git pre-commit hook in the given project folder	| —		|
| `--ai-summary`		| Generate AI project brief via OpenAI-compatible API (key: `COPYCAT_AI_KEY` env var)	| off	|
| `--ai-model MODEL`		| LLM model name for AI summary							| `gpt-4o-mini`	|
| `--ai-base-url URL`		| Base URL for AI API (e.g. `http://localhost:11434/v1` for Ollama)		| None		|
| `--timeline`			| Generate a timeline from archived reports					| off		|
| `--timeline-format`		| Timeline format: `md`, `ascii`, `html`					| `md`		|

### Flat vs Recursive


| Mode		| Flag		| Behavior		| Performance		|
|---------------|---------------|-----------------------|-----------------------|
| **Flat**	| (default)	| Main folder only	| Lightning fast	|
| **Recursive**	| '-r'		| All subfolders	| Optimal w/ -s		|


### File Types


| Category	| Files								| Tests		|
|---------------|---------------------------------------------------------------|---------------|
| code		| \*.java, \*.py, \*.spec, \*.cpp, \*.c				| 5 files	|
| web		| \*.html, \*.css, \*.js, \*.ts, \*.jsx				| 5 empty	|
| db		| \*.sql, \*.db, \*.sqlite					| 3 files	|
| config	| \*.json, \*.yaml, \*.xml, \*.properties, \*.env		| 8 files	|
| docs		| \*.md, \*.txt, \*.log, \*.docx				| 8 files	|
| deps		| requirements.txt, package.json, pom.xml, go.mod		| Defined	|
| img		| \*.png, \*.jpg, \*.gif, \*.bmp, \*.webp, \*.svg, \*.ico       | 7 files	|
| audio		| \*.mp3, \*.wav, \*.ogg, \*.m4a, \*.flac			| 5 files	|
| diagram	| \*.drawio, \*.dia, \*.puml					| 6 edge cases	|
| notebook	| \*.ipynb, \*.csv						| included	|


### CLI Examples:


```bash
CopyCat.py -t code,diagram     # Code + diagrams only
CopyCat.py -t web,db,config    # 3 specific categories
CopyCat.py -t all              # All 9 categories
CopyCat.py -i tests -r         # Recursive
CopyCat.py -s 1                # Max 1MB
```


#### Output Example (v2.9)


````text
============================================================
CopyCat v2.9 | 13.04.2026 20:41 | REKURSIV
/projekt
GIT: Branch: main | Last Commit: a1b2c3d

Gesamt: 47 Dateien
Serial #4
SUCHE: "TODO" → 3 Treffer in 2 Dateien
============================================================
CODE: 2 Dateien    IMG: 5 Dateien   AUDIO: 5 Dateien  DIAGRAM: 1 Datei

CODE-Details:
  code.py: 42 Zeilen [sub]
----- code.py -----
def hello(): pass
...

==================== IMG ====================
[BINARY: image.png] [MIME: image/png] [SIZE: 12345 bytes]
  Pfad: sub/image.png

==================== DIAGRAM ====================
DIAGRAM test.drawio: 152 Cells, 45 Texte, 23 Unique
  [cell-2] Test Node... (x=160, y=120)
````


### Draw.io-Extraction 


- ALL Cells: ID, text/HTML, position (x,y)

- ZIP Fallback: binary .drawio (ZIP) → extract XML entry → parse

- Compressed: Base64/zlib (raw deflate)/URL-unquote (draw.io standard format)

- Edge Cases (20+ tests):

	- Empty: [EMPTY: test.drawio]

	- Corrupt: [XML PARSE ERROR]

	- Binary (not ZIP): [BINARY: name - Invalid Encoding]

	- Empty ZIP: [ZIP EMPTY: name]

	- Invalid compressed content: 0 Cells, 0 Texte, 0 Unique (no crash)

	- Oversized (>1MB): [SKIPPED: name - exceeds 1MB limit]

- Limits: <1MB

- Stats: Cells/Texte/Unique

**Example komplex.drawio:**

DIAGRAM Test_komplex.drawio: 152 Cells, 45 Texte, 23 Unique


### Use Cases


1. **Exam Portfolio:** git init && CopyCat.py && git commit -m "Portfolio"

2. **Git Backup:** CopyCat.py -i C:\Project -o Reports

3. **Daily Report:** Cron/PS: 1 text file instead of 50+ files

**Trainer:** "Show code+UML!" → CopyCat.py -t code,diagram


### Plugin System


CopyCat v2.9 supports custom file types via plugins. Place any `.py` file in the `plugins/` folder (next to `CopyCat.py`) or specify a custom directory with `--plugin-dir`.


**Minimal plugin (`plugins/mytype.py`):**

```python
TYPE_NAME = "mytype"          # unique type name
PATTERNS  = ["*.mytype"]      # glob patterns
```

**With custom renderer:**

```python
TYPE_NAME = "proto"
PATTERNS  = ["*.proto"]

def render_file(path, writer, args):
    """Called once per file during TXT/Markdown report generation."""
    writer.write(f"[PROTO: {path.name}]\n")
    writer.write(path.read_text(encoding="utf-8"))
```

**CLI usage:**

```bash
python CopyCat.py --plugin-dir ./myplugins -t proto    # use plugin type
python CopyCat.py --list-plugins                       # show loaded plugins
python CopyCat.py --plugin-dir ./myplugins --list-plugins
```

**Rules:**

| Rule | Detail |
|---|---|
| File naming | Any `.py` file (files starting with `_` are ignored) |
| `TYPE_NAME` | Must be a non-empty string not already used by a built-in type |
| `PATTERNS` | Must be a non-empty list of non-empty strings |
| `render_file` | Optional; if absent, `list_binary_file()` is used as fallback |
| Errors | Broken plugins are skipped with a warning; other plugins still load |
| Idempotency | A type name is only registered once per session |

The example plugin `plugins/example_proto.py` ships with CopyCat and serves as a copy-paste template.


### Web Interface

CopyCat v2.9 includes a browser-based UI powered by Flask.

**Start:**
```bash
pip install flask
python CopyCat_Web.py                        # http://localhost:5000
python CopyCat_Web.py --port 8080 --host 0.0.0.0
```

**Routes:**

| Route | Method | Description |
|---|---|---|
| `/` | GET | HTML form with all options |
| `/run` | POST | Run CopyCat, show report inline |
| `/download?path=…` | GET | Download report file (only `combined_copycat_*.{txt,json,md}`) |
| `/api/run` | POST (JSON) | REST API – returns `{"status":"ok","report":"<path>"}` |

**JSON API example:**
```bash
curl -s -X POST http://localhost:5000/api/run \
  -H "Content-Type: application/json" \
  -d '{"input": "/my/project", "format": "txt", "types": ["code"]}'
```


### PyInstaller / EXE Artifacts

GitHub Actions automatically builds standalone `.exe` files for every push (Windows, no Python required).

Download from the **Actions** tab → latest run → **Artifacts**:

| Artifact | Description |
|---|---|
| `CopyCat-exe` | CLI tool (`CopyCat.exe`) |
| `CopyCat-Web-exe` | Web interface (`CopyCat_Web.exe`) |

**Build locally:**
```bash
pip install pyinstaller jinja2 watchdog flask
pyinstaller CopyCat.spec        # → dist/CopyCat.exe
pyinstaller CopyCat_Web.spec    # → dist/CopyCat_Web.exe
```


### Technology


- pathlib: Glob/rglob (recursive optimized)

- argparse: CLI (comma-split, nargs="*")

- ElementTree: XML parsing

- struct.unpack: WAV duration (header)

- .gitignore: Skip rules (fnmatch)

- Serial: Regex validation + archive rotation

- zipfile: ZIP-compressed .drawio fallback

- base64 + zlib + urllib.parse.unquote: draw.io compressed diagram decoding

- configparser (stdlib): `copycat.conf` key=value config loader
- `concurrent.futures.ThreadPoolExecutor`: parallel regex search across files
- `threading` + `watchdog`: watch mode (auto-rerun on file changes)
- `jinja2` (optional): custom template output (`pip install jinja2`)
- `tkinterdnd2` (optional): drag & drop support in GUI (`pip install tkinterdnd2`)
- `reportlab` (optional): PDF export (`pip install reportlab`)
- `openai` (optional): AI summary (`pip install openai`)


### Error Handling


````text
UnicodeDecodeError	→ [BINARY SKIPPED]
ET.ParseError		→ [XML PARSE ERROR]
0-Byte			→ [EMPTY]
OSError			→ Silent skip + logging
Others			→ [ERROR: file]
````
**Example:** DIAGRAM INVALID XML: test.drawio


### Performance Tuning (v2.9)


**For large projects (1000+ files):**

| Scenario	| Flags			| Progress	| Speed		|
|---------------|-----------------------|---------------|---------------|
| Standard	| -			| No 		| Lightning	|
| Limit		| --max-size 10		| No		| Fast		|
| Recursive	| -r			| Auto		| 3x slower	|
| Optimal	| -r --max-size 1	| Live		| Optimal	|

**Examples:**
```bash
CopyCat.py -r --max-size 1     # Recursive + progress
CopyCat.py --max-size 10       # Flat, no progress
```
Filter output: → 1274 geprüft, Filter OK


### Output Formats


CopyCat v2.9 supports four output formats via the `-f` / `--format` flag:


| Format | Flag | Output File | Description |
|--------|------|-------------|-------------|
| **TXT** | `-f txt` (default) | `combined_copycat_N.txt` | Human-readable text report |
| **JSON** | `-f json` | `combined_copycat_N.json` | Structured machine-readable data |
| **Markdown** | `-f md` | `combined_copycat_N.md` | GitHub-ready documentation |
| **HTML** | `-f html` | `combined_copycat_N.html` | Self-contained HTML with syntax highlighting |
| **PDF** | `-f pdf` | `combined_copycat_N.pdf` | Structured PDF with meta table, code details, stats (`pip install reportlab`) |


**JSON Schema Example:**

````json
{
  "version": "2.9",
  "generated": "13.04.2026 20:41",
  "mode": "recursive",
  "input": "/projekt",
  "serial": 4,
  "git": { "branch": "main", "commit": "a1b2c3d" },
  "files": 47,
  "types": { "code": 5, "img": 3 },
  "search": { "pattern": "TODO", "total_matches": 3, "files_matched": 2 },
  "details": {
    "code": [
      { "name": "main.py", "path": "src/main.py", "size": 1234, "lines": 42,
        "matches": [{"line": 7, "text": "# TODO: fix this"}] }
    ]
  }
}
````


**Markdown output** includes `#` headers, summary tables, fenced code blocks for each source file, and file tables for binary types.

**HTML output** is a self-contained single file with collapsible `<details>` sections per file. Syntax highlighting is applied automatically when [Pygments](https://pygments.org/) is installed (`pip install pygments`); without it, plain `<pre>` blocks are used instead.


```bash
# Examples
python CopyCat.py -f json -i C:\Project    # JSON report
python CopyCat.py -f md -r                 # Recursive Markdown report
python CopyCat.py -f pdf                   # PDF report
python CopyCat.py                          # Default TXT (unchanged)
```


All formats use the same serial number system and archive rotation.


### PDF Export


CopyCat v2.9 can generate structured PDF reports via `--format pdf`:

```bash
pip install reportlab
python CopyCat.py -f pdf                        # PDF report
python CopyCat.py -f pdf -r --stats             # Recursive + code stats
```

The PDF contains:
- **Meta table**: date, mode, path, git info, file count, search pattern
- **Overview table**: file type counts
- **Code statistics** (when `--stats` is used): LOC, comments, blank lines, complexity
- **Code details**: source code per file (max 150 lines each; longer files are truncated with a note)
- **Search results table** (when `--search` is used)

> **Note:** Binary files and files with encoding errors are gracefully skipped.


### AI Summary


CopyCat v2.9 can generate an AI-powered project brief appended to any report:

```bash
pip install openai
set COPYCAT_AI_KEY=sk-...              # OpenAI key (Windows)
python CopyCat.py --ai-summary         # Append AI brief to TXT report
python CopyCat.py -f json --ai-summary # AI brief as JSON field "ai_summary"
python CopyCat.py -f html --ai-summary # AI brief injected into HTML
```

**Ollama (local, no API costs):**
```bash
ollama pull llama3
set COPYCAT_AI_KEY=ollama
python CopyCat.py --ai-summary --ai-base-url http://localhost:11434/v1 --ai-model llama3
```

**Security:** Only project metadata is sent to the API (file names, counts, git info) — **never source code content**.

| Option | Description | Default |
|---|---|---|
| `--ai-summary` | Generate and append AI project brief | off |
| `--ai-model MODEL` | LLM model name | `gpt-4o-mini` |
| `--ai-base-url URL` | Base URL for OpenAI-compatible API (e.g. Ollama) | None |

The API key is read **exclusively** from the `COPYCAT_AI_KEY` environment variable. It is never stored in config files or passed via CLI for security reasons. If the key is missing or the API call fails, a warning is logged and the report is still created.


### Report Timeline


CopyCat v2.9 can generate a visual history from the `CopyCat_Archive/` folder:

```bash
python CopyCat.py --timeline                      # Markdown table (default)
python CopyCat.py --timeline --timeline-format ascii  # ASCII bar chart
python CopyCat.py --timeline --timeline-format html   # Interactive Chart.js HTML
```

**Example Markdown output:**
```
| # | Date | Files | Types |
|---|------|-------|-------|
| #1 | 01.01.2025 | 12 | CODE: 8, DOCS: 4 |
| #2 | 15.01.2025 | 20 | CODE: 14, DOCS: 6 |
```

The GUI also includes a **📊 Timeline** button that shows the Markdown timeline in the output area.


### Docker


Run CopyCat without a Python installation:

```bash
# Build image
docker build -t copycat .

# Run (mounts current folder as /project)
docker run --rm -v "$(pwd):/project" copycat [OPTIONS]

# Examples
docker run --rm -v "$(pwd):/project" copycat -r -f json
docker run --rm -v "C:\MyProject:/project" copycat --stats -f pdf
```

The Docker image (`python:3.12-slim`) includes all optional dependencies: `reportlab`, `jinja2`, `watchdog`, `pygments`, `openai`.




### Content Search


CopyCat v2.9 supports regex-based content search across all text files via `--search` / `-S`:


```bash
python CopyCat.py -S "TODO|FIXME"          # Find all TODOs and FIXMEs
python CopyCat.py -S "def " -t code        # All function definitions
python CopyCat.py -S "class " -f json      # Class definitions as JSON
python CopyCat.py -r -S "import " -t code  # All imports (recursive)
```


**TXT output** — search summary in header + `SUCHERGEBNISSE` section:

````text
SUCHE: "TODO" → 3 Treffer in 2 Dateien
...
==================== SUCHERGEBNISSE ====================
Muster: "TODO" → 3 Treffer in 2 Dateien

  main.py:
    L7: # TODO: fix this
    L42: # TODO: add tests
  utils.py:
    L15: # TODO: refactor
````


**Searchable types:** `code`, `web`, `db`, `config`, `docs`, `deps`

**Not searched:** `img`, `audio`, `diagram` (binary content)

**Behavior details:**

| Situation | Result |
|---|---|
| Pattern found | Line number + trimmed snippet per match |
| No matches | Summary line shown, no results section |
| Invalid regex | Report created without search section |
| Binary file | Silently skipped |


### Configuration File


Create `copycat.conf` in your project folder (or the folder where you run the script). CopyCat loads it automatically — **CLI arguments always override config values**.


**Example `copycat.conf`:**

```ini
# copycat.conf
types = code, diagram
recursive = true
max_size_mb = 5
format = md
# search = TODO|FIXME
# input = src
# output = reports
```


**Supported keys:**

| Key | Type | Example | Description |
|---|---|---|---|
| `types` | list | `code, diagram` | File type categories (comma or space separated) |
| `recursive` | bool | `true` | Recursive search (`true`/`false`/`yes`/`no`/`1`/`0`) |
| `max_size_mb` | float | `5` | Max file size in MB |
| `format` | string | `md` | Output format: `txt`, `json`, `md`, `html` |
| `search` | string | `TODO\|FIXME` | Regex search pattern |
| `input` | path | `src` | Input folder |
| `output` | path | `reports` | Output folder |
| `exclude` | string | `*.min.js, dist/` | Glob patterns to exclude |
| `incremental` | bool | `true` | Enable incremental cache (`true`/`false`) |
| `stats` | bool | `true` | Enable code statistics (`true`/`false`) |
| `git_url` | string | — | Remote Git repository URL to clone and scan |
| `ai_model` | string | `gpt-4o-mini` | LLM model name for `--ai-summary` |
| `ai_base_url` | string | — | Base URL for AI API (e.g. Ollama) |


**Lookup order:** CWD → script directory. First file found wins.

**Syntax rules:** Lines starting with `#` are comments. Empty lines are ignored. Invalid values are silently skipped with a log warning.


**Without config file:**
```bash
python CopyCat.py -i src -r -t code,diagram -f md -s 5
```
**With `copycat.conf`:**
```bash
python CopyCat.py    # same result
```


### Git Support


CopyCat reads branch and commit info automatically from any Git repository and adds it to every report.


**Report header example:**

````text
GIT: Branch: main | Last Commit: a1b2c3d
````


**Behavior:**

| Situation | Output |
|---|---|
| Git repo with commits | `Branch: main \| Last Commit: a1b2c3d` |
| Detached HEAD | `Branch: HEAD \| Last Commit: a1b2c3d` |
| No `.git` folder | `No Git` |
| `git` not installed | `No Git` |
| Timeout (>5s) | `No Git` |


**`.gitignore` integration:**

CopyCat respects `.gitignore` rules in every scanned directory — both in flat and recursive mode.

````text
# Example .gitignore
*.log           → skipped
node_modules/   → skipped
build/          → skipped
!important.py   → NOT skipped (negation)
````

Subdirectory `.gitignore` files are also applied to files within that subdirectory:

````text
src/.gitignore  →  applies to all files under src/
````


### GitHub-Setup


**.gitignore:**

CopyCat_Archive/
combined_copycat*.txt
combined_copycat*.json
combined_copycat*.md
__pycache__/


**Commit includes:**

CopyCat.py

CopyCat_GUI.py

README.md

README_GER.md

.gitignore


### Developer Guide


**Before every commit (100% sync):**

1. `py -m pytest test_copycat.py --cov=. --cov-config=.coveragerc --cov-report=term-missing` → 100% PASSED

2. README.md + README_GER.md + Code SYNCHRONIZED

3. `git commit -m "feat/fix/docs/test/ci: description"`

**Tests:** 442 tests, 100% branch coverage (CLI, serial, gitignore, Draw.io, GUI, watch, templates, diff, merge, hook, plugins, PDF, AI, timeline, …)

**CI:** GitHub Actions → pytest + coverage badges (Codecov)

**Install optional dependencies:**
```bash
pip install jinja2 watchdog tkinterdnd2 reportlab openai
```

- ✓ pathlib filesystem
- ✓ argparse CLI
- ✓ ElementTree XML parsing
- ✓ Targeted exception handling
- ✓ Binary analysis (struct)
- ✓ Glob vs rglob (performance)
- ✓ ThreadPoolExecutor parallel search
- ✓ Jinja2 template rendering
- ✓ watchdog file-system events


### IT Specialist Demo

1 text report = Code + UML + Media ✓