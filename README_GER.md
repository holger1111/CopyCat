# CopyCat v2.9 - Projekt-Dokumentierer


## Automatisiert Code + Diagramme + Medien zu Text-Report

[![Tests](https://github.com/holger1111/CopyCat/actions/workflows/ci.yml/badge.svg)](https://github.com/holger1111/CopyCat/actions)
[![Coverage](https://codecov.io/gh/holger1111/CopyCat/branch/main/graph/badge.svg)](https://codecov.io/gh/holger1111/CopyCat)


### Hauptfunktionen


| Feature		| Beschreibung						|
|-----------------------|-------------------------------------------------------|
| Code-Analyse		| Zeilenanzahl + Quellcode (Java/Python/C++/etc.)	|
| Draw.io		| Extraktion aller Cells (ID, Text, Position), ZIP + Compressed-Support	|
| Medien		| MIME-Type, Größe, Audio-Dauer (WAV/MP3/FLAC)		|
| Notebooks/CSV		| Jupyter `.ipynb` Zellen-Extraktion + `.csv`-Support	|
| Selbstschutz		| Ignoriert CopyCat.py & alte Reports			|
| Serial-System		| Automatisches Archiv (CopyCat_Archive)		|
| Git-Integration	| Branch + Commit-Hash					|
| Ausgabeformate	| TXT / JSON / Markdown / Jinja2-Template (`--format`, `--template`)	|
| Inhaltssuche		| Parallele Regex-Suche über Dateiinhalte (`--search`)	|
| Diff-Modus		| Zwei Reports vergleichen (`--diff`)			|
| Merge-Modus		| Mehrere Reports zusammenführen (`--merge`)		|
| Watch-Modus		| Automatischer Re-Run bei Änderungen (`--watch`, `--cooldown`)	|
| Plugin-System		| Eigene Dateitypen per `.py`-Plugin hinzufügen (`--plugin-dir`)	|
| Pre-commit Hook	| Als Git-Hook installieren (`--install-hook`)		|
| Konfigurationsdatei	| `copycat.conf` auto-geladen; CLI überschreibt	|
| Performance		| Rekursiv/Flach, Size-Filter + Progress		|
| GUI			| Grafische Oberfläche via `CopyCat_GUI.py` (Drag & Drop)	|
| Web-Interface		| Browser-UI via Flask (`python CopyCat_Web.py`)	|
| VS Code Extension	| Reports direkt aus dem Editor starten (`copycat-vscode/`)	|
| CI-Artefakte		| PyInstaller `.exe`-Builds via GitHub Actions		|


### GUI

```bash
python CopyCat_GUI.py    # Öffnet die grafische Oberfläche
```

Alle CLI-Optionen sind als UI-Elemente verfügbar. Der Fortschritts-Output wird live im Fenster angezeigt.
Erfordert Python mit tkinter (in der Standardinstallation enthalten).


### VS Code Extension

Der Ordner `copycat-vscode/` enthält eine TypeScript-Extension, die CopyCat direkt in VS Code integriert.

**Befehle (Befehlspalette / Status Bar):**

| Befehl | Beschreibung |
|---|---|
| `CopyCat: Report erstellen` | Flachen Report für den aktuellen Workspace erstellen |
| `CopyCat: Report erstellen (rekursiv)` | Rekursiven Report erstellen |

**Einstellungen (`Datei → Einstellungen → Einstellungen → CopyCat`):**

| Einstellung | Beschreibung | Standard |
|---|---|---|
| `copycat.pythonPath` | Pfad zum Python-Interpreter | auto-detect |
| `copycat.scriptPath` | Pfad zu `CopyCat.py` | Workspace-Root |
| `copycat.outputFormat` | `txt` / `json` / `md` | `txt` |
| `copycat.maxSizeMb` | Max. Dateigröße in MB (0 = unbegrenzt) | `0` |
| `copycat.excludePatterns` | Glob-Muster zum Ausschließen, z.B. `["dist/", "*.min.js"]` | `[]` |
| `copycat.extraArgs` | Zusätzliche CLI-Argumente | `[]` |

**Build & Installation:**
```bash
cd copycat-vscode
npm install
npm run compile       # TypeScript → out/extension.js
npm run package       # erstellt copycat-0.1.0.vsix
# VS Code: Erweiterungen → ⋯ → VSIX installieren
```


### Konsolenbefehle


```bash
python CopyCat.py                              # Standard (flach, alle Typen, txt)
python CopyCat.py -i C:\Projekt               # Eingabeordner
python CopyCat.py -o docs                     # Ausgabeordner
python CopyCat.py -t code,diagram             # Nur Code+Diagramme
python CopyCat.py -r -s 5                     # Rekursiv, max 5MB
python CopyCat.py -f json                     # JSON-Ausgabe
python CopyCat.py -f md                       # Markdown-Ausgabe
python CopyCat.py -S "TODO|FIXME"             # Nach TODOs suchen
python CopyCat.py --template report.j2        # Benutzerdefinierte Jinja2-Ausgabe
python CopyCat.py -w --cooldown 3             # Watch-Modus, 3 s Cooldown
python CopyCat.py --diff report1.txt report2.txt  # Zwei Reports vergleichen
python CopyCat.py --merge r1.txt r2.txt       # Reports zusammenführen
python CopyCat.py --install-hook C:\Projekt   # Git pre-commit Hook installieren
python CopyCat.py -v                          # Ausführlich (DEBUG)
python CopyCat.py -q                          # Nur Warnungen
python CopyCat.py --help                      # Hilfe
# Konfigurationsdatei wird automatisch aus CWD oder Skript-Ordner geladen:
python CopyCat.py                             # nutzt copycat.conf falls vorhanden
```


### Parameter


| Flag				| Beschreibung								| Default	|
|-------------------------------|-----------------------------------------------------------------------|---------------|
| `-i`, `--input`		| Eingabeordner								| Skriptordner	|
| `-o`, `--output`		| Ausgabeordner								| Eingabeordner	|
| `-t`, `--types`		| Typen: `code web db config docs deps img audio diagram notebook` oder `all`	| `all`	|
| `-r`, `--recursive`		| Rekursive Suche in Unterordnern					| false		|
| `-s`, `--max-size`		| Max Größe MB								| unbegrenzt	|
| `-f`, `--format`		| Ausgabeformat: `txt`, `json`, `md`					| `txt`		|
| `-S`, `--search`		| Regex-Suchmuster (z.B. `TODO\|FIXME`, `def `)			| None		|
| `-E`, `--exclude`		| Glob-Muster oder Ordner ausschließen (z.B. `*.min.js` `dist/` `node_modules/`)	| None	|
| `-v`, `--verbose`		| Ausführliche Ausgabe (DEBUG-Level)					| aus		|
| `-q`, `--quiet`		| Nur Warnungen ausgeben						| aus		|
| `--template`			| Pfad zu einer Jinja2-Template-Datei (`.j2`); erfordert `pip install jinja2`	| None	|
| `-w`, `--watch`		| Watch-Modus: Re-Run bei Dateiänderungen; erfordert `pip install watchdog`	| aus	|
| `--cooldown`			| Wartezeit (Sek.) nach letzter Änderung vor Re-Run (Watch-Modus)	| `2.0`		|
| `--diff A B`			| Zwei CopyCat-Reports vergleichen und Unterschiede anzeigen		| —		|
| `--merge R [R ...]`		| Mehrere CopyCat-Reports zu einem zusammenführen			| —		|
| `--plugin-dir DIR`		| Plugins aus diesem Verzeichnis laden (Standard: `plugins/` neben CopyCat.py)	| —	|
| `--list-plugins`		| Geladene Plugins anzeigen und beenden					| aus		|
| `--install-hook DIR`		| CopyCat als Git pre-commit Hook im angegebenen Projektordner installieren	| —	|

### Flach vs Rekursiv


| Modus		| Flag		| Verhalten		| Performance		|
|---------------|---------------|-----------------------|-----------------------|
| **Flach**	| (default)	| Nur Hauptordner	| Schnell		|
| **Rekursiv**	| '-r'		| Alle Unterordner	| Optimal mit -s	|


### Dateitypen


| Kategorie	| Dateien							| Tests		|
|---------------|---------------------------------------------------------------|---------------|
| code		| \*.java, \*.py, \*.spec, \*.cpp, \*.c				| 5 Dateien	|
| web		| \*.html, \*.css, \*.js, \*.ts, \*.jsx				| 5 leere	|
| db		| \*.sql, \*.db, \*.sqlite					| 3 Dateien	|
| config	| \*.json, \*.yaml, \*.xml, \*.properties, \*.env		| 8 Dateien	|
| docs		| \*.md, \*.txt, \*.log, \*.docx				| 8 Dateien	|
| deps		| requirements.txt, package.json, pom.xml, go.mod		| Definiert	|
| img		| \*.png, \*.jpg, \*.gif, \*.bmp, \*.webp, \*.svg, \*.ico       | 7 Dateien	|
| audio		| \*.mp3, \*.wav, \*.ogg, \*.m4a, \*.flac			| 5 Dateien	|
| diagram	| \*.drawio, \*.dia, \*.puml					| 6 Edge-Cases	|
| notebook	| \*.ipynb, \*.csv						| enthalten	|


### CLI-Beispiele:


```bash
CopyCat.py -t code diagram	# Nur Code + Diagramme
CopyCat.py -t web db config	# 3 spezifische Kategorien
CopyCat.py -t all		# Alle 9 Kategorien
CopyCat.py -i tests -r		# Rekursiv
CopyCat.py -s 1			# Max Dateigröße 1 MB
```


### Ausgabe-Beispiel (v2.9)


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


### Draw.io-Extraktion


- ALLE Cells: ID, Text/HTML, Position (x,y)

- ZIP-Fallback: Binäre .drawio (ZIP) → XML-Eintrag extrahieren → parsen

- Compressed: Base64/zlib (raw deflate)/URL-unquote (draw.io Standardformat)

- Edge-Cases (20+ Tests):

	- Leer: [EMPTY: test.drawio]

	- Corrupt: [XML PARSE ERROR]

	- Binär (kein ZIP): [BINARY: name - Invalid Encoding]

	- Leeres ZIP: [ZIP EMPTY: name]

	- Ungültiger Compressed-Inhalt: 0 Cells, 0 Texte, 0 Unique (kein Crash)

	- Zu groß (>1MB): [SKIPPED: name - exceeds 1MB limit]

- Limits: <1MB

- Statistik: Cells/Texte/Unique

**Beispiel komplex.drawio:**

DIAGRAM Test_komplex.drawio: 152 Cells, 45 Texte, 23 Unique


### Einsatzmöglichkeiten


1. **IHK-Prüfung:** git init && CopyCat.py && git commit -m "Portfolio"

2. **Git-Backup:** CopyCat.py -i C:\Projekt -o Reports

3. **Täglicher Report:** Cron/PS: 1 Textdatei statt 50+ Files

**Ausbilder:** "Zeig Code+UML!" → CopyCat.py -t code,diagram


### Plugin-System


CopyCat v2.9 unterstützt eigene Dateitypen per Plugin. Lege eine `.py`-Datei in den Ordner `plugins/` (neben `CopyCat.py`) oder gib ein benutzerdefiniertes Verzeichnis mit `--plugin-dir` an.


**Minimales Plugin (`plugins/meintyp.py`):**

```python
TYPE_NAME = "meintyp"      # eindeutiger Typname
PATTERNS  = ["*.meintyp"]  # Glob-Muster
```

**Mit benutzerdefiniertem Renderer:**

```python
TYPE_NAME = "proto"
PATTERNS  = ["*.proto"]

def render_file(path, writer, args):
    """Wird einmal pro Datei beim TXT/Markdown-Report aufgerufen."""
    writer.write(f"[PROTO: {path.name}]\n")
    writer.write(path.read_text(encoding="utf-8"))
```

**CLI-Nutzung:**

```bash
python CopyCat.py --plugin-dir ./meineplugins -t proto    # Plugin-Typ verwenden
python CopyCat.py --list-plugins                          # Geladene Plugins anzeigen
python CopyCat.py --plugin-dir ./meineplugins --list-plugins
```

**Regeln:**

| Regel | Detail |
|---|---|
| Dateiname | Beliebige `.py`-Datei (Dateien mit `_` am Anfang werden ignoriert) |
| `TYPE_NAME` | Muss ein nicht-leerer String sein, der nicht bereits von einem eingebauten Typ verwendet wird |
| `PATTERNS` | Muss eine nicht-leere Liste von nicht-leeren Strings sein |
| `render_file` | Optional; fehlt sie, wird `list_binary_file()` als Fallback genutzt |
| Fehler | Defekte Plugins werden mit Warnung übersprungen; andere Plugins laden weiterhin |
| Idempotenz | Ein Typname wird pro Sitzung nur einmal registriert |

Das Beispiel-Plugin `plugins/example_proto.py` liegt CopyCat bei und dient als Kopiervorlage.


### Web-Interface

CopyCat v2.9 enthält eine Browser-Oberfläche auf Flask-Basis.

**Start:**
```bash
pip install flask
python CopyCat_Web.py                        # http://localhost:5000
python CopyCat_Web.py --port 8080 --host 0.0.0.0
```

**Routen:**

| Route | Methode | Beschreibung |
|---|---|---|
| `/` | GET | HTML-Formular mit allen Optionen |
| `/run` | POST | CopyCat ausführen, Report direkt anzeigen |
| `/download?path=…` | GET | Report herunterladen (nur `combined_copycat_*.{txt,json,md}`) |
| `/api/run` | POST (JSON) | REST-API – liefert `{"status":"ok","report":"<Pfad>"}` |

**JSON-API-Beispiel:**
```bash
curl -s -X POST http://localhost:5000/api/run \
  -H "Content-Type: application/json" \
  -d '{"input": "/mein/projekt", "format": "txt", "types": ["code"]}'
```


### PyInstaller / EXE-Artefakte

GitHub Actions baut bei jedem Push automatisch `.exe`-Dateien (Windows, kein Python erforderlich).

Download im **Actions**-Tab → letzter Lauf → **Artifacts**:

| Artefakt | Beschreibung |
|---|---|
| `CopyCat-exe` | CLI-Tool (`CopyCat.exe`) |
| `CopyCat-Web-exe` | Web-Interface (`CopyCat_Web.exe`) |

**Lokal bauen:**
```bash
pip install pyinstaller jinja2 watchdog flask
pyinstaller CopyCat.spec        # → dist/CopyCat.exe
pyinstaller CopyCat_Web.spec    # → dist/CopyCat_Web.exe
```


### Technik


- pathlib: Glob/rglob (rekursiv optimiert)

- argparse: CLI (Komma-Split, nargs="*")

- ElementTree: XML-Parsing

- struct.unpack: WAV-Dauer (Header)

- .gitignore: Skip-Regeln (fnmatch)

- Serial: Regex-Validierung + Archiv-Rotation

- zipfile: ZIP-komprimierte .drawio-Dateien (Fallback)

- base64 + zlib + urllib.parse.unquote: Dekodierung komprimierter draw.io-Diagramme

- configparser (stdlib): `copycat.conf` Key=Value Config-Loader
- `concurrent.futures.ThreadPoolExecutor`: parallele Regex-Suche über Dateien
- `threading` + `watchdog`: Watch-Modus (automatischer Re-Run bei Änderungen)
- `jinja2` (optional): benutzerdefinierte Template-Ausgabe (`pip install jinja2`)
- `tkinterdnd2` (optional): Drag-&-Drop-Unterstützung in der GUI (`pip install tkinterdnd2`)


### Fehlerbehandlung


````text
UnicodeDecodeError	→ [BINARY SKIPPED]
ET.ParseError		→ [XML PARSE ERROR]
0-Byte			→ [EMPTY]
OSError			→ Silent Skip + Logging
Rest			→ [ERROR: datei]
````
**Beispiel:** DIAGRAM INVALID XML: test.drawio


###  Performance-Tuning (v2.9)


**Für große Projekte (1000+ Files):**

| Szenario	| Flags		| Progress	| Speed		|
|---------------|---------------|---------------|---------------|
| Standard	| -		| Nein 		| Blitz		|
| Limit		| --max-size 10	| Nein		| Schnell	|
| Rekursiv	| -r		| Auto		| 3x langsamer	|
| Optimal	| -r --max-size 1	| Live		| Optimal	|

**Beispiele:**
```bash
CopyCat.py -r --max-size 1     # Rekursiv + Progress
CopyCat.py --max-size 10       # Flach, kein Progress
```
Ausgabe bei Filter: → 1274 geprüft, Filter OK


### Ausgabeformate


CopyCat v2.9 unterstützt drei Ausgabeformate über das `-f` / `--format`-Flag:


| Format | Flag | Ausgabedatei | Beschreibung |
|--------|------|--------------|--------------|
| **TXT** | `-f txt` (Standard) | `combined_copycat_N.txt` | Menschenlesbarer Text-Report |
| **JSON** | `-f json` | `combined_copycat_N.json` | Strukturierte maschinenlesbare Daten |
| **Markdown** | `-f md` | `combined_copycat_N.md` | GitHub-fertige Dokumentation |


**JSON-Schema-Beispiel:**

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
        "matches": [{"line": 7, "text": "# TODO: beheben"}] }
    ]
  }
}
````


**Markdown-Ausgabe** enthält `#`-Überschriften, Übersichtstabellen, Fenced-Code-Blöcke für jede Quelldatei sowie Dateitabellen für Binärtypen.


```bash
# Beispiele
python CopyCat.py -f json -i C:\Projekt    # JSON-Report
python CopyCat.py -f md -r                 # Rekursiver Markdown-Report
python CopyCat.py                          # Standard TXT (unverändert)
```


Alle drei Formate verwenden dasselbe Serial-System und die Archiv-Rotation.


### Inhaltssuche


CopyCat v2.9 unterstützt Regex-basierte Inhaltssuche über alle Textdateien via `--search` / `-S`:


```bash
python CopyCat.py -S "TODO|FIXME"          # Alle TODOs und FIXMEs finden
python CopyCat.py -S "def " -t code        # Alle Funktionsdefinitionen
python CopyCat.py -S "class " -f json      # Klassendefinitionen als JSON
python CopyCat.py -r -S "import " -t code  # Alle Imports (rekursiv)
```


**TXT-Ausgabe** — Suchzusammenfassung im Header + `SUCHERGEBNISSE`-Abschnitt:

````text
SUCHE: "TODO" → 3 Treffer in 2 Dateien
...
==================== SUCHERGEBNISSE ====================
Muster: "TODO" → 3 Treffer in 2 Dateien

  main.py:
    L7: # TODO: beheben
    L42: # TODO: Tests hinzufügen
  utils.py:
    L15: # TODO: refaktorieren
````


**Durchsuchbare Typen:** `code`, `web`, `db`, `config`, `docs`, `deps`

**Nicht durchsucht:** `img`, `audio`, `diagram` (Binärinhalte)

**Verhalten:**

| Situation | Ergebnis |
|---|---|
| Muster gefunden | Zeilennummer + Snippet je Treffer |
| Keine Treffer | Zusammenfassungszeile, kein Abschnitt |
| Ungültiges Regex | Report wird ohne Suchabschnitt erstellt |
| Binärdatei | Wird lautlos übersprungen |


### Konfigurationsdatei


Erstelle `copycat.conf` im Projektordner (oder dem Ordner, von dem aus du das Skript startest). CopyCat lädt die Datei automatisch — **CLI-Argumente überschreiben immer die Config-Werte**.


**Beispiel `copycat.conf`:**

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


**Unterstützte Schlüssel:**

| Schlüssel | Typ | Beispiel | Beschreibung |
|---|---|---|---|
| `types` | Liste | `code, diagram` | Dateityp-Kategorien (Komma oder Leerzeichen) |
| `recursive` | bool | `true` | Rekursive Suche (`true`/`false`/`yes`/`no`/`1`/`0`) |
| `max_size_mb` | float | `5` | Maximale Dateigröße in MB |
| `format` | string | `md` | Ausgabeformat: `txt`, `json`, `md` |
| `search` | string | `TODO\|FIXME` | Regex-Suchmuster |
| `input` | Pfad | `src` | Eingabeordner |
| `output` | Pfad | `reports` | Ausgabeordner |


**Suchreihenfolge:** Aktuelles Verzeichnis → Skript-Verzeichnis. Erste gefundene Datei gewinnt.

**Syntax-Regeln:** Zeilen mit `#` sind Kommentare. Leerzeilen werden ignoriert. Ungültige Werte werden mit Log-Warnung stillschweigend übersprungen.


**Ohne Konfigurationsdatei:**
```bash
python CopyCat.py -i src -r -t code,diagram -f md -s 5
```
**Mit `copycat.conf`:**
```bash
python CopyCat.py    # gleiches Ergebnis
```


### Git-Support


CopyCat liest Branch- und Commit-Informationen automatisch aus jedem Git-Repository und fügt sie in jeden Report ein.


**Report-Header Beispiel:**

````text
GIT: Branch: main | Last Commit: a1b2c3d
````


**Verhalten:**

| Situation | Ausgabe |
|---|---|
| Git-Repo mit Commits | `Branch: main \| Last Commit: a1b2c3d` |
| Detached HEAD | `Branch: HEAD \| Last Commit: a1b2c3d` |
| Kein `.git`-Ordner | `No Git` |
| `git` nicht installiert | `No Git` |
| Timeout (>5s) | `No Git` |


**`.gitignore`-Integration:**

CopyCat respektiert `.gitignore`-Regeln in jedem gescannten Verzeichnis — sowohl im Flach- als auch im Rekursiv-Modus.

````text
# Beispiel .gitignore
*.log           → übersprungen
node_modules/   → übersprungen
build/          → übersprungen
!important.py   → NICHT übersprungen (Negation)
````

Unterordner-`.gitignore`-Dateien werden ebenfalls auf Dateien in diesem Unterordner angewendet:

````text
src/.gitignore  →  gilt für alle Dateien unter src/
````


### GitHub-Setup


**.gitignore:**

CopyCat_Archive/
combined_copycat*.txt
combined_copycat*.json
combined_copycat*.md
__pycache__/


**Commit enthält:**

CopyCat.py

CopyCat_GUI.py

README.md

README_GER.md

.gitignore


### Entwickler-Guide


**Vor jedem Commit (100 % Sync):**

1. `py -m pytest test_copycat.py --cov=. --cov-config=.coveragerc --cov-report=term-missing` → 100 % PASSED

2. README.md + README_GER.md + Code SYNCHRON

3. `git commit -m "feat/fix/docs/test/ci: Beschreibung"`

**Tests:** 262 Tests, 100 % Branch-Coverage (CLI, Serial, Gitignore, Draw.io, GUI, Watch, Templates, Diff, Merge, Hook, Plugins, …)

**CI:** GitHub Actions → pytest + Coverage-Badges (Codecov)

**Optionale Abhängigkeiten installieren:**
```bash
pip install jinja2 watchdog tkinterdnd2
```

- ✓ pathlib Dateisystem
- ✓ argparse CLI
- ✓ ElementTree XML-Parsing
- ✓ Exception-Handling (gezielte)
- ✓ Binary-Analyse (struct)
- ✓ Glob vs rglob (Performance)
- ✓ ThreadPoolExecutor parallele Suche
- ✓ Jinja2 Template-Rendering
- ✓ watchdog Dateisystem-Events


### Demo Fachinformatiker

1 Text-Report = Code + UML + Medien ✓