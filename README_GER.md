# CopyCat v2.1 - Projekt-Dokumentierer

\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_

## Automatisiert Code + Diagramme + Medien zu Text-Report

\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_



### Hauptfunktionen



| Feature | Beschreibung |

|---------|-------------|

| Code-Analyse | Zeilenanzahl + Quellcode (Java/Python) |

| Draw.io | 100% Extraktion aller Cells |

| Medien | MIME-Type, Groesse, Audio-Dauer |

| Serial-System | Automatisches Archiv |

| Selbstschutz | Ignoriert CopyCat.py |



### Konsolenbefehle



python CopyCat.py                    # Standard

python CopyCat.py -i "C:\\Projekte"   # Eingabeordner

python CopyCat.py -o "docs"          # Ausgabeordner

python CopyCat.py -t code drawio     # Nur Code+Diagramme

python CopyCat.py --help             # Hilfe



### Parameter



\-i, --input    Eingabeordner (Default: Skriptordner)

\-o, --output   Ausgabeordner (Default: Eingabeordner)

\-t, --types    Typen: code img audio drawio (Default: all)



#### Dateitypen:



| Kategorie | Dateien                                         |

| --------- | ----------------------------------------------- |

| code      | \*.java, \*.py, \*.spec, \*.cpp, \*.c                |

| web       | \*.html, \*.css, \*.js, \*.ts, \*.jsx                |

| db        | \*.sql, \*.db, \*.sqlite                           |

| config    | \*.json, \*.yaml, \*.xml, \*.properties, \*.env      |

| docs      | \*.md, \*.txt, \*.log, \*.docx                      |

| deps      | requirements.txt, package.json, pom.xml, go.mod |

| img       | \*.png, \*.jpg, \*.gif, \*.bmp, \*.webp, \*.svg       |

| audio     | \*.mp3, \*.wav, \*.ogg, \*.m4a, \*.flac              |

| diagram   | \*.drawio, \*.svg, \*.dia, \*.puml                  |



#### CLI-Beispiele:



copycat.py -t code diagram      # Nur Code + Diagramme

copycat.py -t web db config     # 3 spezifische Kategorien

copycat.py -t all               # Alle 9 Kategorien



### Ausgabe-Beispiel



============================================================

CopyCat v2.1 | 02.04.2026 14:16

c:\\Projekte\\Test



Gesamt: 13 Dateien | Serial #26

============================================================

CODE: 2 Dateien

IMG: 5 Dateien

AUDIO: 5 Dateien

DRAWIO: 1 Datei



CODE-Details:

&#x20; Code\_java.java: 28 Zeilen



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



### GitHub-Setup



.gitignore:

CopyCat\_Archive/

combined\_copycat\*.txt

\_\_pycache\_\_/



Commit enthaelt:

CopyCat.py

README.md

.gitignore



### Demo Fachinformatiker



\- \[x] pathlib Dateisystem

\- \[x] argparse CLI

\- \[x] XML-Parsing ElementTree

\- \[x] Exception-Handling

\- \[x] Binary-Analyse struct

