# CopyCat v2.8 - Project Documenter


## Automates Code + Diagrams + Media into Text Reports

[![Tests](https://img.shields.io/badge/Tests-PASSED-brightgreen?style=flat-square&logo=github-actions)](https://github.com/holger1111/CopyCat/actions)
[![Coverage](https://img.shields.io/badge/Coverage-15:40 16.04.2026100%25-brightgreen?style=flat-square&logo=codecov)](https://codecov.io/gh/holger1111/CopyCat)


### Main Features


| Feature		| Description						|
|-----------------------|-------------------------------------------------------|
| Code Analysis		| Line count + source code (Java/Python/C++/etc.)	|
| Draw.io		| 100% extraction of all cells (ID, text, position)	|
| Media			| MIME type, size, audio duration (WAV/MP3/FLAC)	|
| Self-Protection	| Ignores CopyCat.py & old reports			|
| Serial System		| Automatic archive (CopyCat_Archive)			|
| Git Integration	| Branch + commit hash					|
| Output Formats	| TXT / JSON / Markdown (`--format`)			|
| Performance		| Recursive/flat, size filter + progress		|


### Console Commands


```bash
python CopyCat.py                    # Default (flat, all types, txt)
python CopyCat.py -i C:\Project      # Input folder
python CopyCat.py -o docs            # Output folder
python CopyCat.py -t code,diagram    # Code + diagrams only
python CopyCat.py -r -s 5            # Recursive, max 5MB
python CopyCat.py -f json            # JSON output
python CopyCat.py -f md              # Markdown output
python CopyCat.py --help             # Help
```


### Parameters


| Flag				| Beschreibung								| Default	|
|-------------------------------|-----------------------------------------------------------------------|---------------|
| -i,--input			| Input folder								| Script folder	|
| -o,--output | Output folder 	| Input folder								|		|
| -t,--types			| Types: 'ode web db config docs deps img audio diagram' oder 'all'	| 'all'		|
| -r,--recursive		| Recursive search in subfolders					| false (flat)	|
| -s,--max-size			| Max file size in MB							| Unlimited	|| -f,--format			| Output format: txt, json, md					| txt		|

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


### CLI Examples:


```bash
CopyCat.py -t code,diagram     # Code + diagrams only
CopyCat.py -t web,db,config    # 3 specific categories
CopyCat.py -t all              # All 9 categories
CopyCat.py -i tests -r         # Recursive
CopyCat.py -s 1                # Max 1MB
```


#### Output Example (v2.8)


````text
============================================================
CopyCat v2.8 | 13.04.2026 20:41 | REKURSIV
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


### Draw.io-Extraction 


- ALL Cells: ID, text/HTML, position (x,y)

- ZIP Fallback: drawio.zip → XML

- Compressed: Base64/zlib/unquote (standard)

- Edge Cases (20+ tests):

	- Empty: [EMPTY: test.drawio]

	- Corrupt: [XML PARSE ERROR]

	- Binary: [ENCODING ERROR]

- Limits: <1MB (no images extracted)

- Stats: Cells/Texts/Unique

**Example komplex.drawio:**

DIAGRAMM Test_komplex.drawio: 152 Cells, 45 Texte, 23 Unique


### Use Cases


1. **Exam Portfolio:** git init && CopyCat.py && git commit -m "Portfolio"

2. **Git Backup:** CopyCat.py -i C:\Project -o Reports

3. **Daily Report:** Cron/PS: 1 text file instead of 50+ files

**Trainer:** "Show code+UML!" → CopyCat.py -t code,diagram


### Technology


- pathlib: Glob/rglob (recursive optimized)

- argparse: CLI (comma-split, nargs="*")

- ElementTree: XML parsing

- struct.unpack: WAV duration (header)

- .gitignore: Skip rules (fnmatch)

- Serial: Regex validation + archive rotation


### Error Handling


````text
UnicodeDecodeError	→ [BINARY SKIPPED]
ET.ParseError		→ [XML PARSE ERROR]
0-Byte			→ [EMPTY]
OSError			→ Silent skip + logging
Others			→ [ERROR: file]
````
**Example:** DIAGRAMM INVALID XML: test.drawio


### Performance Tuning (v2.8)


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


CopyCat v2.8 supports three output formats via the `-f` / `--format` flag:


| Format | Flag | Output File | Description |
|--------|------|-------------|-------------|
| **TXT** | `-f txt` (default) | `combined_copycat_N.txt` | Human-readable text report |
| **JSON** | `-f json` | `combined_copycat_N.json` | Structured machine-readable data |
| **Markdown** | `-f md` | `combined_copycat_N.md` | GitHub-ready documentation |


**JSON Schema Example:**

````json
{
  "version": "2.8",
  "generated": "13.04.2026 20:41",
  "mode": "recursive",
  "input": "/projekt",
  "serial": 4,
  "git": { "branch": "main", "commit": "a1b2c3d" },
  "files": 47,
  "types": { "code": 5, "img": 3 },
  "details": {
    "code": [
      { "name": "main.py", "path": "src/main.py", "size": 1234, "lines": 42 }
    ]
  }
}
````


**Markdown output** includes `#` headers, summary tables, fenced code blocks for each source file, and file tables for binary types.


```bash
# Examples
python CopyCat.py -f json -i C:\Project    # JSON report
python CopyCat.py -f md -r                 # Recursive Markdown report
python CopyCat.py                          # Default TXT (unchanged)
```


All three formats use the same serial number system and archive rotation.


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

README.md

README_GER.md

.gitignore


### Developer Guide


**Before every commit (100% sync):**

1. pytest test_copycat.py -v --cov → 100% PASSED

2. README.md + README_GER.md + Code SYNCHRONIZED

3. git commit -m "feat: X | Tests 1000%"

**Tests:** 100% coverage (CLI, serial, gitignore, Draw.io, max-size, 1000+ edge cases)

**CI:** GitHub Actions → pytest + coverage badges

**Question:** Is CopyCat now easier to understand/maintain?

- ✓ pathlib filesystem
- ✓ argparse CLI
- ✓ ElementTree XML parsing
- ✓ Targeted exception handling
- ✓ Binary analysis (struct)
- ✓ Glob vs rglob (performance)


### IT Specialist Demo

1 text report = Code + UML + Media ✓