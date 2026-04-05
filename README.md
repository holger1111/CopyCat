# CopyCat v2.5 - Project Documenter

\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_

## Automates Code + Diagrams + Media into Text Report

\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_



[![Tests](https://github.com/holger1111/CopyCat/workflows/CI/badge.svg?branch=main)](https://github.com/holger1111/CopyCat/actions)
[![Coverage](https://codecov.io/gh/holger1111/CopyCat/branch/main/graph/badge.svg)](https://codecov.io/gh/holger1111/CopyCat)



### Main Features



| Feature 	  | Description 			   |

|-----------------|----------------------------------------|

| Code Analysis   | Line count + source code (Java/Python) |

| Draw.io         | ZIP + Compressed + Edge-Cases 	   |

| Media 	  | MIME-Type, size, audio duration        |

| Serial System   | Automatic archiving 		   |

| Self-Protection | Ignores CopyCat.py 			   |



### Console Commands



python CopyCat.py                     # Standard

python CopyCat.py -i "C:\\Projects"    # Input folder

python CopyCat.py -o "docs"           # Output folder

python CopyCat.py -t code drawio      # Code+Diagrams only

python CopyCat.py --help              # Help



### Parameters



\-i, --input     Input folder (Default: script folder)

\-o, --output    Output folder (Default: input folder)

\-t, --types     Types: code web db config docs deps img audio diagram (Default: all)

\-r, --recursive Recursive search in subfolders (Default: main folder only)



### Flat vs Recursive

| Mode          | Flag       | Behavior             | Performance      |
|---------------|------------|---------------------:|-----------------|
| **Flat (Default)** | -       | Main folder only     | Fast            |
| **Recursive** | `-r`       | All subfolders       | Slower @ 1000+ files |



### Draw.io-Extraktion (v2.2)



\- All cells: ID, Text/HTML, Position (x,y)

\- ZIP-Fallback: drawio.zip → XML

\- Compressed: Base64+zlib+unquote (Standard)

\- Edge-Cases:

&#x20; - Empty → "\[LEERES MODELL]"

&#x20; - Corrupt → "\[XML PARSE ERROR]"

&#x20; - Binary → "\[ENCODING ERROR]"

\- Limits: <1MB, keine Bilder extrahiert

\- Statistik: Cells/Texte/Unique



#### Beispiel:



VOLLSTÄNDIGES DIAGRAMM: komplex.drawio

MODEL 1: dx=586

CELL 1 \[ID=col...] 'Start' | GEOM: x=320,y=400

STATISTIK: 152 Cells | 45 Texte | 23 Unique



#### File Types:



| category  | file                                            | tests	    |

|-----------|-------------------------------------------------|-------------|

| code      | \*.java, \*.py, \*.spec, \*.cpp, \*.c                | 5 files     |

| web       | \*.html, \*.css, \*.js, \*.ts, \*.jsx                | 5 empty     |

| db        | \*.sql, \*.db, \*.sqlite                           | 3 files     |

| config    | \*.json, \*.yaml, \*.xml, \*.properties, \*.env      | 8 files     |

| docs      | \*.md, \*.txt, \*.log, \*.docx                      | 8 files     |

| deps      | requirements.txt, package.json, pom.xml, go.mod | defined     |

| img       | \*.png, \*.jpg, \*.gif, \*.bmp, \*.webp, \*.svg       | 7 files     |

| audio     | \*.mp3, \*.wav, \*.ogg, \*.m4a, \*.flac              | 5 files     |

| diagram   | \*.drawio, \*.dia, \*.puml                         | 6 Edge-cases|



47 test files -> CopyCat v2.5 Serial #3



#### CLI Example:



CopyCat.py -t code diagram      # Only code and diagrams

CopyCat.py -t web db config     # 3 specific categories

CopyCat.py -t all               # All 9 categories

CopyCat.py -i tests/            # Flat: 47 files

CopyCat.py -i tests/ -r         # Recursive: includes subfolders



### Output Example



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



### Use Cases



#### 1\. Exam Portfolio:



Trainer: "Show me code + UML!"

CopyCat.py -> 1 text file instead of 50+



#### 2\. Git Backup:



git init \&\& python CopyCat.py \&\& git commit



#### 3\. Daily Report:



python CopyCat.py -i "C:\\Projects" -o "Reports"



### Technology



Draw.io: 101 cells extracted

WAV: Header analysis (struct.unpack)

Serial: combined\_copycat\_26.txt

Archive: CopyCat\_Archive/

Recursiv: `glob()` vs `rglob()` recursive search



### Error Handling (v2.2)



\- UnicodeDecodeError: "Binary skipped"

\- ET.ParseError: "Invalid XML"

\- 0-Byte: "\[EMPTY:...]"

\- Rest: Silent Logging (no spam)



Example: 'DIAGRAMM INVALID XML: test.drawio'



### GitHub Setup



.gitignore:

CopyCat\_Archive/

combined\_copycat\*.txt

\_\_pycache\_\_/



Commit contains:

CopyCat.py

README.md

.gitignore



### Developer Guide



**Test: 100% Core-Coverage (CLI, Serial, Draw.io)**



```bash
py -m pytest test\_copycat.py -v --cov  # local tests
\\# 10/10 PASSED | Coverage: 100%
```



**Before every commit:**

1\. `pytest test\\\_copycat.py` ✅

2\. README.md + README\_GER.md + Code SYNCHRON

3\. `git commit -m "feat: X | Tests: 100%"`



**CI runs automatically:** \[Actions](https://github.com/holger1111/CopyCat/actions)



### Demo for IT Specialists



\- \[x] pathlib filesystem

\- \[x] argparse CLI

\- \[x] XML-Parsing ElementTree

\- \[x] Exception handling

\- \[x] Binary analysis struct

\- \[x] pathlib: `glob()` vs `rglob()` recursive search