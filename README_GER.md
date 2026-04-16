# CopyCat v2.7 - Projekt-Dokumentierer


## Automatisiert Code + Diagramme + Medien zu Text-Report

[![Tests](https://img.shields.io/badge/Tests-PASSED-brightgreen?style=flat-square&logo=github-actions)](https://github.com/holger1111/CopyCat/actions)
[![Coverage](https://img.shields.io/badge/Coverage->100%25-brightgreen?style=flat-square&logo=codecov)](https://codecov.io/gh/holger1111/CopyCat)


### Hauptfunktionen


| Feature		| Beschreibung						|
|-----------------------|-------------------------------------------------------|
| Code-Analyse		| Zeilenanzahl + Quellcode (Java/Python/C++/etc.)	|
| Draw.io		| 100% Extraktion aller Cells (ID, Text, Position)	|
| Medien		| MIME-Type, Größe, Audio-Dauer (WAV/MP3/FLAC)		|
| Selbstschutz		| Ignoriert CopyCat.py & alte Reports			|
| Serial-System		| Automatisches Archiv (CopyCat_Archive)		|
| Git-Integration	| Branch + Commit-Hash					|
| Performance		| Rekursiv/Flach, Size-Filter + Progress		|


### Konsolenbefehle


```bash
python CopyCat.py                    # Standard (flach, alle Typen)
python CopyCat.py -i C:\Projekt      # Eingabeordner
python CopyCat.py -o docs            # Ausgabeordner
python CopyCat.py -t code,diagram    # Nur Code+Diagramme
python CopyCat.py -r -s 5            # Rekursiv, max 5MB
python CopyCat.py --help             # Hilfe
```


### Parameter


| Flag				| Beschreibung								| Default	|
|-------------------------------|-----------------------------------------------------------------------|---------------|
| -i,--input			| Eingabeordner								| Skriptordner	|
| -o,--output | Ausgabeordner 	| Eingabeordner								|		|
| -t,--types			| Typen: 'ode web db config docs deps img audio diagram' oder 'all'	| 'all'		|
| -r,--recursive		| Rekursive Suche  in Unterordnern					| false (flach)	|
| -s,--max-size			| Max Größe MB								| unbegrenzt	|


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


### Ausgabe-Beispiel (v2.7)


````text
============================================================
CopyCat v2.7 | 13.04.2026 20:41 | REKURSIV
/projekt
GIT: Branch: main | Last Commit: a1b2c3d
Gesamt: 47 Dateien
Serial #4
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


###  Performance-Tuning (v2.7)


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


### GitHub-Setup


**.gitignore:**

CopyCat_Archive/
combined_copycat*.txt
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