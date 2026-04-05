# CopyCat v2.5 - Projekt-Dokumentierer

\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_

## Automatisiert Code + Diagramme + Medien zu Text-Report

\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_



[![Tests](https://github.com/holger1111/CopyCat/workflows/CI/badge.svg?branch=main)](https://github.com/holger1111/CopyCat/actions)
[![Coverage](https://codecov.io/gh/holger1111/CopyCat/branch/main/graph/badge.svg)](https://codecov.io/gh/holger1111/CopyCat)



### Hauptfunktionen



| Feature 	| Beschreibung 				 |

|---------------|----------------------------------------|

| Code-Analyse  | Zeilenanzahl + Quellcode (Java/Python) |

| Draw.io       | ZIP + Compressed + Edge-Case           |

| Medien        | MIME-Type, Groesse, Audio-Dauer   	 |

| Serial-System | Automatisches Archiv 			 |

| Selbstschutz  | Ignoriert CopyCat.py 			 |



### Konsolenbefehle



python CopyCat.py                    # Standard

python CopyCat.py -i "C:\\Projekte"   # Eingabeordner

python CopyCat.py -o "docs"          # Ausgabeordner

python CopyCat.py -t code drawio     # Nur Code+Diagramme

python CopyCat.py --help             # Hilfe



### Parameter



\-i, --input     Eingabeordner (Default: Skriptordner)

\-o, --output    Ausgabeordner (Default: Eingabeordner)

\-t, --types     Typen: code web db config docs deps img audio diagram (Default: all)

\-r, --recursive Rekursive Suche in Unterordnern (Default: nur Hauptordner)



### Flach vs Rekursiv

| Modus         | Flag       | Verhalten            | Performance     |
|---------------|------------|---------------------:|-----------------|
| **Flach (Default)** | -     | Nur Hauptordner      | Schnell         |
| **Rekursiv**  | `-r`       | Alle Unterordner     | Langsamer bei 1000+ Files |



### Draw.io-Extraktion (v2.2)



\- \*\*ALLE Cells\*\*: ID, Text/HTML, Position (x,y)

\- \*\*ZIP-Fallback\*\*: drawio.zip → XML

\- \*\*Compressed\*\*: Base64+zlib+unquote (Standard)

\- \*\*Edge-Cases\*\*:

&#x20; - Leer → "\[LEERES MODELL]"

&#x20; - Corrupt → "\[XML PARSE ERROR]"

&#x20; - Binary → "\[ENCODING ERROR]"

\- \*\*Limits\*\*: <1MB, keine Bilder extrahiert

\- \*\*Statistik\*\*: Cells/Texte/Unique



#### Beispiel:



VOLLSTÄNDIGES DIAGRAMM: komplex.drawio

MODEL 1: dx=586

CELL 1 \[ID=col...] 'Start' | GEOM: x=320,y=400

STATISTIK: 152 Cells | 45 Texte | 23 Unique



#### Dateitypen:



| Kategorie | Dateien                                         | Tests	    |

|-----------|-------------------------------------------------|-------------|

| code      | \*.java, \*.py, \*.spec, \*.cpp, \*.c                | 5 Dateien   |

| web       | \*.html, \*.css, \*.js, \*.ts, \*.jsx                | 5 leere     |

| db        | \*.sql, \*.db, \*.sqlite                           | 3 Dateien   |

| config    | \*.json, \*.yaml, \*.xml, \*.properties, \*.env      | 8 Dateien   |

| docs      | \*.md, \*.txt, \*.log, \*.docx                      | 8 Dateien   |

| deps      | requirements.txt, package.json, pom.xml, go.mod | Definiert   |

| img       | \*.png, \*.jpg, \*.gif, \*.bmp, \*.webp, \*.svg       | 7 Dateien   |

| audio     | \*.mp3, \*.wav, \*.ogg, \*.m4a, \*.flac              | 5 Dateien   |

| diagram   | \*.drawio, \*.dia, \*.puml                         | 6 Edge-Cases|



47 Testdateien -> CopyCat v2.5 Serial #3



#### CLI-Beispiele:



CopyCat.py -t code diagram      # Nur Code + Diagramme

CopyCat.py -t web db config     # 3 spezifische Kategorien

CopyCat.py -t all               # Alle 9 Kategorien

CopyCat.py -i tests/            # Flach: 47 Dateien

CopyCat.py -i tests/ -r         # Rekursiv: Unterordner inkl.



### Ausgabe-Beispiel



============================================================
CopyCat v2.5 | 05.04.2026 15:05 | FLACH (Default)
c:\Projekte\Test

Gesamt: 47 Dateien
Serial #3
============================================================

CODE: 2 Dateien

IMG: 5 Dateien

AUDIO: 5 Dateien

DRAWIO: 1 Datei



CODE-Details:

code.py: 42 Zeilen [subfolder]



### Einsatzmöglichkeiten



#### 1\. IHK-Prüfung:



Ausbilder: "Zeig Code + UML!"

CopyCat.py -> 1 Textdatei statt 50+



#### 2\. Git-Backup:



git init \&\& python CopyCat.py \&\& git commit



#### 3\. Täglicher Report:



python CopyCat.py -i "C:\\Projekte" -o "Reports"



### Technik



Draw.io: 101 Cells extrahiert

WAV: Header-Analyse (struct.unpack)

Serial: combined\_copycat\_26.txt

Archiv: CopyCat\_Archive/

Recursiv: `glob()` vs `rglob()` rekursive Suche



### Fehlerbehandlung (v2.2)



\- UnicodeDecodeError: "Binary skipped"

\- ET.ParseError: "Invalid XML"

\- 0-Byte: "\[EMPTY:...]"

\- Rest: Silent Logging (kein Spam)



Beispiel: 'DIAGRAMM INVALID XML: test.drawio'



### GitHub-Setup



.gitignore:

CopyCat\_Archive/

combined\_copycat\*.txt

\_\_pycache\_\_/



Commit enthaelt:

CopyCat.py

README.md

.gitignore



### Entwickler-Guide



**Tests: 100% Core-Coverage (CLI, Serial, Draw.io)**



```bash

py -m pytest test\_copycat.py -v --cov  # Lokale Tests

\# 10/10 PASSED | Coverage: 100%

```



**Vor jedem Commit:**

1\. `pytest test\_copycat.py` ✅

2\. README.md + README\_GER.md + Code SYNCHRON 

3\. `git commit -m "feat: X | Tests: 100%"`



**CI läuft automatisch:** \[Actions](https://github.com/holger1111/CopyCat/actions)



### Demo Fachinformatiker



\- \[x] pathlib Dateisystem

\- \[x] argparse CLI

\- \[x] XML-Parsing ElementTree

\- \[x] Exception-Handling

\- \[x] Binary-Analyse struct

\- \[x] pathlib: `glob()` vs `rglob()` recursive search