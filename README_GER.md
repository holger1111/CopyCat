# CopyCat v2.9 - Projekt-Dokumentierer


## Automatisiert Code + Diagramme + Medien zu Text-Report

[![Tests](https://img.shields.io/badge/Tests-PASSED-brightgreen?style=flat-square&logo=github-actions)](https://github.com/holger1111/CopyCat/actions)
[![Coverage](https://img.shields.io/badge/Coverage-100%25-brightgreen?style=flat-square&logo=codecov)](https://codecov.io/gh/holger1111/CopyCat)


### Hauptfunktionen


| Feature		| Beschreibung						|
|-----------------------|-------------------------------------------------------|
| Code-Analyse		| Zeilenanzahl + Quellcode (Java/Python/C++/etc.)	|
| Draw.io		| 100% Extraktion aller Cells (ID, Text, Position)	|
| Medien		| MIME-Type, Größe, Audio-Dauer (WAV/MP3/FLAC)		|
| Selbstschutz		| Ignoriert CopyCat.py & alte Reports			|
| Serial-System		| Automatisches Archiv (CopyCat_Archive)		|
| Git-Integration	| Branch + Commit-Hash					|
| Ausgabeformate	| TXT / JSON / Markdown (`--format`)			|
| Inhaltssuche		| Regex-Suche über Dateiinhalte (`--search`)		|
| Performance		| Rekursiv/Flach, Size-Filter + Progress		|


### Konsolenbefehle


```bash
python CopyCat.py                    # Standard (flach, alle Typen, txt)
python CopyCat.py -i C:\Projekt      # Eingabeordner
python CopyCat.py -o docs            # Ausgabeordner
python CopyCat.py -t code,diagram    # Nur Code+Diagramme
python CopyCat.py -r -s 5            # Rekursiv, max 5MB
python CopyCat.py -f json            # JSON-Ausgabe
python CopyCat.py -f md              # Markdown-Ausgabe
python CopyCat.py -S "TODO|FIXME"    # Nach TODOs suchen
python CopyCat.py --help             # Hilfe
```


### Parameter


| Flag				| Beschreibung								| Default	|
|-------------------------------|-----------------------------------------------------------------------|---------------|
| -i,--input			| Eingabeordner								| Skriptordner	|
| -o,--output | Ausgabeordner 	| Eingabeordner								|		|
| -t,--types			| Typen: 'ode web db config docs deps img audio diagram' oder 'all'	| 'all'		|
| -r,--recursive		| Rekursive Suche  in Unterordnern					| false (flach)	|
| -s,--max-size			| Max Größe MB								| unbegrenzt	|| -f,--format			| Ausgabeformat: txt, json, md					| txt		|
| -S,--search			| Regex-Suchmuster (z.B. 'TODO\|FIXME', 'def ')			| None		|

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
DIAGRAM test.drawio: 152 Cells, 45 Texte
  [cell-2] Test Node...
````


### Draw.io-Extraktion


- ALLE Cells: ID, Text/HTML, Position (x,y)

- ZIP-Fallback: drawio.zip → XML

- Compressed: Base64/zlib/unquote (Standard)

- Edge-Cases (20+ Tests):

	- Leer: [EMPTY: test.drawio]

	- Corrupt: [XML PARSE ERROR]

	- Binary: [ENCODING ERROR]

- Limits: <1MB (keine Bilder extrahiert)

- Statistik: Cells/Texte/Unique

**Beispiel komplex.drawio:**

DIAGRAMM Test_komplex.drawio: 152 Cells, 45 Texte, 23 Unique


### Einsatzmöglichkeiten


1. **IHK-Prüfung:** git init && CopyCat.py && git commit -m "Portfolio"

2. **Git-Backup:** CopyCat.py -i C:\Projekt -o Reports

3. **Täglicher Report:** Cron/PS: 1 Textdatei statt 50+ Files

**Ausbilder:** "Zeig Code+UML!" → CopyCat.py -t code,diagram


### Technik


- pathlib: Glob/rglob (rekursiv optimiert)

- argparse: CLI (Komma-Split, nargs="*")

- ElementTree: XML-Parsing

- struct.unpack: WAV-Dauer (Header)

- .gitignore: Skip-Regeln (fnmatch)

- Serial: Regex-Validierung + Archiv-Rotation


### Fehlerbehandlung


````text
UnicodeDecodeError	→ [BINARY SKIPPED]
ET.ParseError		→ [XML PARSE ERROR]
0-Byte			→ [EMPTY]
OSError			→ Silent Skip + Logging
Rest			→ [ERROR: datei]
````
**Beispiel:** DIAGRAMM INVALID XML: test.drawio


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

README.md

README_GER.md

.gitignore


### Entwickler-Guide


**Vor jedem Commit (100% Sync):**

1. pytest test_copycat.py -v --cov → 100% PASSED

2. README.md + README_GER.md + Code SYNCHRON

3. git commit -m "feat: X | Tests 100%"

**Tests:** 100% Coverage (CLI, Serial, Gitignore, Draw.io, max-size, 1000+ Edge-Cases)

**CI:** GitHub Actions → pytest + Coverage-Badges

**Frage:** Ist CopyCat jetzt einfacher zu verstehen/wartbar?

- ✓ pathlib Dateisystem
- ✓ argparse CLI
- ✓ XML-Parsing ElementTree
- ✓ Exception-Handling (gezielte)
- ✓ Binary-Analyse struct
- ✓ Glob vs rglob (Performance)


### Demo Fachinformatiker

1 Text-Report = Code + UML + Medien ✓