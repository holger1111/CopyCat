# CopyCat v2.2 - Project Documenter

\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_

## Automates Code + Diagrams + Media into Text Report

\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_



### Main Features



| Feature 	  | Description 			   |

|-----------------|----------------------------------------|

| Code Analysis   | Line count + source code (Java/Python) |

| Draw.io         | 100% extraction of all cells 	   |

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



\-i, --input    Input folder (Default: script folder)

\-o, --output   Output folder (Default: input folder)

\-t, --types    Types: code web db config docs deps img audio diagram (Default: all)



#### File Types:



| category  | file                                            |

| --------- | ------------------------------------------------|

| code      | \*.java, \*.py, \*.spec, \*.cpp, \*.c                |

| web       | \*.html, \*.css, \*.js, \*.ts, \*.jsx                |

| db        | \*.sql, \*.db, \*.sqlite                           |

| config    | \*.json, \*.yaml, \*.xml, \*.properties, \*.env      |

| docs      | \*.md, \*.txt, \*.log, \*.docx                      |

| deps      | requirements.txt, package.json, pom.xml, go.mod |

| img       | \*.png, \*.jpg, \*.gif, \*.bmp, \*.webp, \*.svg       |

| audio     | \*.mp3, \*.wav, \*.ogg, \*.m4a, \*.flac              |

| diagram   | \*.drawio, \*.dia, \*.puml                         |



#### CLI Example:



CopyCat.py -t code diagram      # Only code and diagrams

CopyCat.py -t web db config     # 3 specific categories

CopyCat.py -t all               # All 9 categories



### Output Example



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



### Demo for IT Specialists



\- \[x] pathlib filesystem

\- \[x] argparse CLI

\- \[x] XML-Parsing ElementTree

\- \[x] Exception handling

\- \[x] Binary analysis struct

