# CopyCat v2.9+ Entwicklungsplan  

Der Plan folgt strikt der Raumanweisung:

* Fehler zuerst,
* Doku synchron,
* CLI-Kompatibilität wahren.



**Gesamtaufwand:**

\~33-47h für 1 Person (Grundplan) + weitere ~15h für Meilensteine 37–39.



**Nach Meilenstein 3:**

Robust und produktionsreif.


**Nach Meilenstein 6:**

Vollständig dokumentiert und erweiterbar.


**Nach Meilensteine 12:**

Enterprise-Ready


**Nach Meilenstein 36:**

Produktionsreife Vollversion mit KI, Docker, Timeline und PDF.


**Nach Meilenstein 39:**

Code-Qualität auf höchstem Stand: vollständige Typisierung, ergonomische GUI, vollwertiger Data-Science-Support.



### MEILENSTEIN 1: CLI '--types' vereinheitlichen

##### ⏱️ 4h

├── **Problem**: 'types = args.types\[0]' ignoriert Multiple-Input; 't in args.types' funktioniert, aber inkonsistent mit Hilfe-Text.  

├── **Lösung**: Immer 'args.types' als Liste behandeln ('if "all" in args.types or t in args.types'). Zentrale TYPE\_FILTERS-Dict mit allen 11 Kategorien.  

├── **Tests**: 'copycat.py -t code web' → Nur diese Kategorien; '-t all' → Alle; Invalid → Fehlermeldung.  

├── **README-Änderungen**: Vollständige Liste aller 11 Typen in beiden Readmes + Beispiele erweitern.  

└── **Risiken**: Keine (reine Logik-Verbesserung).  



### MEILENSTEIN 2: Dateitypen zentral definieren + README sync

##### ⏱️ 3h

├── **Problem**: Code hat 11 Kategorien, README nur 4 (code/img/audio/drawio).  

├── **Lösung**: TYPE\_FILTERS als globales Dict mit Patterns; README-Tabelle mit allen Kategorien spiegeln.  

├── **Tests**: Jede Kategorie einzeln aufrufen → Korrekte Dateien gefunden.  

├── **README-Änderungen**: Neue Tabelle "Alle unterstützten Dateitypen" in beiden Readmes einfügen.  

└── **Risiken**: Minimale Pattern-Überlappungen (z.B. .svg in img+diagram).  



### MEILENSTEIN 3: Serial-/Archivlogik robustifizieren

##### ⏱️ 5h

├── **Problem**: 'get\_next\_serial\_number' bricht bei ungültigen Namen; Archiv nur bei serial>1.  

├── **Lösung**: Regex für Namensvalidierung; immer altes File archivieren (auch bei serial=1); Konflikt-Handling.  

├── **Tests**: Mehrere Runs → Korrekte Nummerierung/Archivierung; Edge-Cases (leere Ordner, manuelle .txt).  

├── **README-Änderungen**: Abschnitt "Serial-System + Archiv" erweitern mit Diagramm-Beispiel.  

└── **Risiken**: Dateizugriffsrechte (lösbar mit try/except).  



### MEILENSTEIN 4: Exception-Handling gezielt machen

##### ⏱️ 6h

├── **Problem**: 'except Exception' überall (drawio, binary, text).  

├── **Lösung**: Spezifische Handler: 'UnicodeDecodeError' → "Binary skipped"; 'ET.ParseError' → "Invalid XML"; Rest logging.  

├── **Tests**: Korrupte Dateien → Sinnvolle Meldungen statt Crash.  

├── **README-Änderungen**: "Fehlerbehandlung" Abschnitt mit Beispielen.  

└── **Risiken**: Neue Edge-Cases (z.B. 0-Byte XML) → Unit-Tests schreiben.  



### MEILENSTEIN 5: Draw.io-Extraktion stabilisieren

##### ⏱️ 5h

├── **Problem**: Generischer except; unvollständige Edge-Cases (leere Modelle, komprimierte Files).  

├── **Lösung**: Spezifische XML-Parser + Fallback für compressed .drawio (unzip); Statistik erweitern.  

├── **Tests**: 10 Test-Drawios (leer, komplex, corrupt) → Vollständige Ausgabe.  

├── **README-Änderungen**: "Draw.io-Feature" mit Extraktions-Details + Limits.  

└── **Risiken**: Komprimierte Files brauchen `zipfile` → Abhängigkeit prüfen.  



### MEILENSTEIN 6: Tests + Open-Source-Ready

##### ⏱️ 7-12h

├── **Problem**: Keine systematischen Tests; fehlende Contribution-Guide.  

├── **Lösung**: Pytest-Suite (CLI, Typen, Edge-Cases); CONTRIBUTING.md + LICENSE; GitHub Actions.  

├── **Tests**: 100% Coverage für Core-Funktionen; CI-Run.  

├── **README-Änderungen**: "Entwickler-Guide" + Badges (Tests, Coverage).  

└── **Risiken**: Test-Maintenance; externe Deps (pytest) → Optional halten.



### MEILENSTEIN 7: Rekursive Suche implementieren

##### ⏱️ 4h

├── **Problem**: input_dir.glob(pat) (Zeile 169) scannt nur Hauptordner → ignoriert Unterordner.

├── **Lösung**: --recursive/-r Flag; rglob(pat) bei aktiv → input_dir.rglob(pat) if args.recursive.

├── **Tests**: Flach: 47 Files; -r: Unterordner inkl.; -i tests/ -r: Tests rekursiv.

├── **README-Änderungen**: Tabelle "Flach vs Rekursiv" + "Flach (Default) oder Rekursiv (-r)".

└── **Risiken**: Performance bei 1000+ Files (rglob langsamer).



### MEILENSTEIN 8: Dateigrößenlimit + Performance-Optimierung

##### ⏱️ 3h

├── **Problem**: Große Dateien (>10MB) blockieren; `rglob` bei 1000+ Files zu langsam. 

├── **Lösung**: `--max-size MB` CLI-Flag; `candidate.stat().st_size < limit`; Progress-Counter bei rekursiv.

├── **Tests**: `CopyCat.py -r --max-size 1` → Nur <1MB; Performance-Test mit 500 Files. 

├── **README-Änderungen**: "Performance-Tuning" Abschnitt mit Größen-/Tiefe-Limits.

└── **Risiken**: `stat()` bei Millionen Files (try/except umgehen).



### MEILENSTEIN 9: Git-Integration + Commit-Info

##### ⏱️ 4h

├── **Problem**: Keine Git-Branch/Commit-Info im Report; `.gitignore` ignoriert nicht. 

├── **Lösung**: `git rev-parse` für Branch/Commits; `gitignore_parser` für Skip-Listen.

├── **Tests**: Git-Repo → "Branch: main | Last Commit: abc123"; `.gitignore` Dateien skippen.

├── **README-Änderungen**: "Git-Support" Abschnitt mit Beispielen. 

└── **Risiken**: Git nicht verfügbar (Fallback: "No Git").



### MEILENSTEIN 10: JSON/Markdown Ausgabeformate

##### ⏱️ 3h

├── **Problem**: Nur `.txt`; Machine-Readable fehlt für Tools/CI.

├── **Lösung**: `--format json|md|txt` CLI; Strukturierte Ausgabe mit Datei-Metadaten. 

├── **Tests**: `CopyCat.py --format json > report.json`; jq validiert.

├── **README-Änderungen**: "Ausgabeformate" Tabelle + JSON-Schema.

└── **Risiken**: JSON bei großen Reports (>100MB). 



### MEILENSTEIN 11: Such-/Filter-Funktion

##### ⏱️ 5h

├── **Problem**: Kein Text-Suchen in Code/Docs; nur Datei-Suche.

├── **Lösung**: `--search "TODO|FIXME"` → Treffer pro Datei; Regex-Support.

├── **Tests**: `CopyCat.py --search "def " -t code` → Funktions-Definitionen.

├── **README-Änderungen**: "Inhalts-Suche" mit Regex-Beispielen.

└── **Risiken**: Performance bei 10k+ Files (indiziere erstmalig).



### MEILENSTEIN 12: Konfigurationsdatei

##### ⏱️ 4h

├── **Problem**: CLI zu lang für tägliche Nutzung; Defaults hardcodiert. 

├── **Lösung**: `copycat.conf` mit `types=all, recursive=true, max-size=5`; CLI überschreibt. 

├── **Tests**: Standard-Config → gleiches Ergebnis wie CLI; Override funktioniert.

├── **README-Änderungen**: "Konfiguration" Abschnitt + Beispiel-Config.

└── **Risiken**: Config-Syntax-Fehler (JSON/YAML).



### MEILENSTEIN 13: Logging

##### ⏱️ 3h

├── **Problem**: Keine strukturierten Laufzeit-Meldungen; stille Fehler und debug-lose Produktion.

├── **Lösung**: `logging`-Modul integriert; `--verbose` (DEBUG) und `--quiet` (nur Fehler) als CLI-Flags; GUI leitet Log-Output ins Textfenster um.

├── **Tests**: `--verbose` zeigt DEBUG-Zeilen; `--quiet` unterdrückt INFO; Logfile-Rotation auf Wunsch.

├── **README-Änderungen**: "Logging" Abschnitt mit Flag-Übersicht und Beispielausgaben.

└── **Risiken**: Zu viel Output bei `--verbose` auf großen Repos (akzeptabel).



### MEILENSTEIN 14: Config Load/Save (GUI)

##### ⏱️ 4h

├── **Problem**: GUI-Einstellungen gehen nach jedem Start verloren; CLI-Flags müssen ständig wiederholt werden.

├── **Lösung**: `copycat.conf` wird beim Start auto-geladen; CLI-Flags überschreiben Config; GUI erhält "Laden"- und "Speichern"-Buttons.

├── **Tests**: Config speichern → neu starten → Werte wiederhergestellt; CLI-Override überschreibt Config-Wert korrekt.

├── **README-Änderungen**: "Konfigurationsdatei" Abschnitt mit Beispiel-`copycat.conf` und Prioritätsregel CLI > Config > Default.

└── **Risiken**: Beschadigte Config-Datei (gelöst: `try/except` mit Fallback auf Defaults).



### MEILENSTEIN 15: Drag & Drop (tkinterdnd2)

##### ⏱️ 3h

├── **Problem**: Ordnerpfad muss manuell eingetippt werden; keine direkte Datei-/Ordner-Interaktion mit der GUI.

├── **Lösung**: `tkinterdnd2` als optionale Abhängigkeit; Drag-and-Drop auf das Eingabefeld setzt den Pfad automatisch; fehlt die Bibliothek, bleibt die GUI voll funktionsfähig.

├── **Tests**: Ordner auf GUI ziehen → Pfad gesetzt; fehlende `tkinterdnd2` → kein Crash.

├── **README-Änderungen**: GUI-Abschnitt um Drag-&-Drop-Hinweis ergänzt; optionale Abhängigkeit dokumentiert.

└── **Risiken**: `tkinterdnd2` nicht auf allen Plattformen verfügbar (gelöst: `try/except ImportError`).



### MEILENSTEIN 16: Progressbar

##### ⏱️ 2h

├── **Problem**: Bei großen Projekten wirkt die GUI eingefroren; kein Feedback während des Scans.

├── **Lösung**: `ttk.Progressbar` in der GUI zeigt den Scanfortschritt; läuft im Hintergrund-Thread, damit die GUI reaktionsfähig bleibt.

├── **Tests**: 100-Datei-Projekt → Fortschrittsbalken bewägt sich sichtbar; GUI friert nicht ein.

├── **README-Änderungen**: GUI-Screenshot-Beschreibung aktualisiert.

└── **Risiken**: Thread-Sicherheit beim GUI-Update (gelöst: `after()`-Callback).



### MEILENSTEIN 17: Notebook/CSV-Unterstützung

##### ⏱️ 4h

├── **Problem**: `.ipynb`- und `.csv`-Dateien werden nicht erkannt; Data-Science-Projekte liefern unvollständige Reports.

├── **Lösung**: `TYPE_FILTERS` um Kategorie `notebook` (`.ipynb`, `.csv`, `.tsv`, `.parquet`) erweitert; Notebooks per JSON-Parsing, CSVs als Plaintext ausgegeben.

├── **Tests**: `.ipynb` → Code-Zellen extrahiert; `.csv` → Inhalt im Report; `-t notebook` isoliert nur diese Typen.

├── **README-Änderungen**: Dateitypen-Tabelle um `notebook`-Kategorie ergänzt.

└── **Risiken**: Große Notebooks mit Base64-Blöcken (gelöst: `--max-size` greift).



### MEILENSTEIN 18: Diff-Modus

##### ⏱️ 5h

├── **Problem**: Keine Möglichkeit, zwei CopyCat-Reports zu vergleichen; Änderungen im Projekt über Zeit sind unsichtbar.

├── **Lösung**: `--diff REPORT_A REPORT_B` vergleicht zwei `.txt`/`.json`/`.md`-Reports; zeigt hinzugefügte, entfernte und geänderte Dateien; `diff_reports()` als eigene Funktion.

├── **Tests**: Zwei Reports mit bekanntem Unterschied → Delta korrekt; identische Reports → "Keine Änderungen".

├── **README-Änderungen**: "Diff-Modus" Abschnitt mit Beispielausgabe.

└── **Risiken**: Format-Inkompatibilität zwischen Reports (gelöst: Format-Check am Anfang).



### MEILENSTEIN 19: Jinja2-Templates

##### ⏱️ 4h

├── **Problem**: Nur fest kodierte Ausgabestruktur; individuelle Report-Layouts nicht möglich.

├── **Lösung**: `--template DATEI` lädt eine Jinja2-Template-Datei; `_write_template()` füllt Variablen (Dateiliste, Git-Info, Statistik); Jinja2 optionale Abhängigkeit.

├── **Tests**: Template mit Platzhaltern → korrekt gefüllter Report; fehlendes Jinja2 → sinnvolle Fehlermeldung.

├── **README-Änderungen**: "Jinja2-Templates" Abschnitt mit Minimalbeispiel.

└── **Risiken**: Jinja2 nicht installiert (gelöst: `try/except ImportError` mit Hinweis).



### MEILENSTEIN 20: Parallele Suche (ThreadPoolExecutor)

##### ⏱️ 3h

├── **Problem**: `--search` mit Regex läuft sequenziell; bei 1000+ Dateien inakzeptabel langsam.

├── **Lösung**: `concurrent.futures.ThreadPoolExecutor` parallelisiert die Regex-Suche; Ergebnisse mit Zeilennummer und Snippet werden thread-sicher gesammelt.

├── **Tests**: 500-Datei-Projekt mit `--search "TODO"` → messbar schneller als sequenziell; korrekte Treffer-Liste.

├── **README-Änderungen**: "Inhalts-Suche" Abschnitt um Performance-Hinweis ergänzt.

└── **Risiken**: Race-Conditions beim Schreiben der Ergebnis-Liste (gelöst: `threading.Lock`).



### MEILENSTEIN 21: Pre-commit Hook

##### ⏱️ 3h

├── **Problem**: Report-Aktualisierung wird vergessen; keine automatische Integration in den Git-Workflow.

├── **Lösung**: `--install-hook DIR` schreibt ein `pre-commit`-Skript in `.git/hooks/` des Ziel-Projekts; CopyCat läuft bei jedem `git commit` automatisch.

├── **Tests**: Hook installieren → `git commit` löst CopyCat aus; bereits vorhandener Hook → Warnung statt Überschreiben.

├── **README-Änderungen**: "Pre-commit Hook" Abschnitt mit Installationsbefehl.

└── **Risiken**: Fehlende Schreibrechte auf `.git/hooks/` (gelöst: `try/except` mit Fehlermeldung).



### MEILENSTEIN 22: Watch-Modus

##### ⏱️ 4h

├── **Problem**: Report muss nach jeder Projektänderung manuell neu erstellt werden.

├── **Lösung**: `--watch` aktiviert Dateisystem-Überwachung via `watchdog`; `--cooldown SEKUNDEN` verhindert Flut bei schnellen Änderungen; neuer Lauf wird automatisch ausgelöst.

├── **Tests**: Datei ändern → Report nach Cooldown neu erstellt; `watchdog` fehlt → Fehlermeldung mit Hinweis.

├── **README-Änderungen**: "Watch-Modus" Abschnitt mit Cooldown-Erklärung.

└── **Risiken**: `watchdog` optionale Abhängigkeit (gelöst: `try/except ImportError`).



### MEILENSTEIN 23: Merge mehrerer Projekte

##### ⏱️ 4h

├── **Problem**: Multi-Repo-Projekte erfordern manuelle Zusammenführung mehrerer Reports.

├── **Lösung**: `--merge REPORT [REPORT ...]` kombiniert mehrere CopyCat-Reports in einer Ausgabedatei; `merge_reports()` als eigene Funktion; Duplikate werden erkannt.

├── **Tests**: Zwei Reports mergen → alle Dateien im Ergebnis; überlappende Einträge korrekt dedupliziert.

├── **README-Änderungen**: "Merge-Modus" Abschnitt mit Beispielbefehl.

└── **Risiken**: Inkompatible Report-Formate (gelöst: Format-Validierung vor Merge).



### MEILENSTEIN 24: Plugin-System

##### ⏱️ 6h

├── **Problem**: CopyCat ist auf fest einkompilierte Dateitypen beschränkt; neue Formate erfordern Core-Änderungen.

├── **Lösung**: `load_plugins()` lädt `.py`-Dateien dynamisch aus `plugins/`; `PLUGIN_RENDERERS`-Dict registriert eigene `render_file()`-Funktionen; `--plugin-dir` und `--list-plugins` in CLI.

├── **Tests**: Plugin laden und Typ registrieren; `render_file()` aufrufen; kaputtes Plugin überspringen; `--list-plugins`-Ausgabe prüfen; 24 neue Tests.

├── **README-Änderungen**: "Plugin-System" Abschnitt mit Minimalbeispiel + Regelwerk-Tabelle in beiden Readmes.

└── **Risiken**: Kaputte Plugins dürfen nicht crashen (gelöst: `try/except` pro Plugin-Datei).



### MEILENSTEIN 25: PyInstaller EXE als CI-Artifact

##### ⏱️ 3h

├── **Problem**: Python-Installation auf Nutzer-PCs nötig; kein fertiges Binary verfügbar; manuelle Build-Schritte fehleranfällig.

├── **Lösung**: `CopyCat.spec` + `CopyCat_Web.spec` für PyInstaller; GitHub Actions baut bei jedem Push `CopyCat.exe` und `CopyCat_Web.exe` (Windows-Runner) nach bestandenen Tests; Artifacts 30 Tage abrufbar.

├── **Tests**: CI-Jobs `build-exe` und `build-web-exe` laufen erst nach erfolgreichem `test`-Job (`needs: test`); Artifact-Upload per `actions/upload-artifact`.

├── **README-Änderungen**: "PyInstaller / EXE-Artefakte" Abschnitt mit Download-Anleitung und lokalem Build-Befehl in beiden Readmes.

└── **Risiken**: Windows-only Build; UPX-Komprimierung kann Antivirus triggern; PyInstaller erfordert alle optionalen Deps als `hiddenimports`.



### MEILENSTEIN 26: Flask Web-Interface

##### ⏱️ 8h

├── **Problem**: CLI-Kenntnisse als Einstiegshürde; kein browserbasierter Zugang zu CopyCat.

├── **Lösung**: `CopyCat_Web.py` mit Flask; Routen `/` (HTML-Formular), `/run` (Report erstellen), `/download` (Datei-Download mit Sicherheitscheck), `/api/run` (REST-JSON); `_run_lock` verhindert gleichzeitige Läufe; inline HTML-Template ohne externes `templates/`-Verzeichnis.

├── **Tests**: 34 neue Tests (296 gesamt, 100 % Branch-Coverage); Flask-Test-Client; `monkeypatch` für Exception-Pfade; Download-Security-Check per `re.fullmatch`.

├── **README-Änderungen**: "Web-Interface" Abschnitt mit Start-Befehl, Routen-Tabelle und JSON-API-Beispiel in beiden Readmes.

└── **Risiken**: Flask als optionale Abhängigkeit (`pip install flask`); Download-Route erlaubt ausschließlich `combined_copycat_*.{txt,json,md}` (Pfad-Traversal-Schutz).

### MEILENSTEIN 27: VS Code Extension

##### ⏱️ 8h

├── **Problem**: CopyCat nur per Terminal nutzbar; kein IDE-Integration; Entwickler müssen für Reports den Editor verlassen.

├── **Lösung**: TypeScript-Extension in `copycat-vscode/`; Befehle `Report erstellen` und `Report erstellen (rekursiv)` in Befehlspalette und Statusleiste; alle Optionen konfigurierbar über VS Code Settings (`copycat.pythonPath`, `copycat.outputFormat`, `copycat.excludePatterns` u. a.).

├── **Tests**: Extension-Aktivierung, Befehlsausführung, Settings-Lesen; Build via `npm run compile`; Paketierung als `.vsix`.

├── **README-Änderungen**: "VS Code Extension" Abschnitt mit Befehls-Tabelle, Settings-Tabelle und Build-Anleitung in beiden Readmes.

└── **Risiken**: Python-Pfad muss korrekt konfiguriert sein; `copycat-vscode/` ist optionaler Bestandteil (gelöst: auto-detect + Einstellung).



### MEILENSTEIN 28: Exclude-Patterns (`--exclude`)

##### ⏱️ 3h

├── **Problem**: Bestimmte Ordner und Dateien (z. B. `node_modules/`, `dist/`, `.venv/`) landen ungewollt im Report und blähen ihn auf.

├── **Lösung**: `-E/--exclude` akzeptiert beliebig viele Glob-Muster; `fnmatch`-basierter Abgleich beim Dateiscan überspringt passende Pfade vor der Typerkennung.

├── **Tests**: Dateien mit passendem Muster erscheinen nicht im Report; mehrere Muster kombinierbar; kein Muster = kein Ausschluss.

├── **README-Änderungen**: `-E`, `--exclude` in Parameter-Tabelle beider Readmes.

└── **Risiken**: Zu breite Muster können gewünschte Dateien ausschließen (Nutzer-Verantwortung; Dokumentation weist darauf hin).



### MEILENSTEIN 29: HTML-Report mit Syntax-Highlighting

##### ⏱️ 5h

├── **Problem**: TXT/MD-Reports sind in Browsern schwer lesbar; Syntax-Hervorhebung für Code fehlt völlig.

├── **Lösung**: `--format html` erzeugt eigenständige HTML-Datei mit klappbaren `<details>`-Sektionen pro Datei; Pygments liefert Syntax-Highlighting (optional; Fallback: einfache `<pre>`-Blöcke).

├── **Tests**: HTML-Ausgabe enthält valides Markup; Pygments vorhanden → Highlighting aktiv; Pygments fehlt → kein Crash, plain `<pre>`; alle anderen Formate unverändert.

├── **README-Änderungen**: Ausgabeformate-Tabelle um `html`-Zeile ergänzt; Pygments-Hinweis in beiden Readmes.

└── **Risiken**: Pygments optionale Abhängigkeit (`pip install pygments`); sehr große Dateien → HTML kann groß werden (gelöst: `--max-size` greift).



### MEILENSTEIN 30: Inkrementelle Reports / Cache (`--incremental`)

##### ⏱️ 4h

├── **Problem**: Bei großen Projekten werden alle Dateien bei jedem Lauf neu gelesen, auch wenn sich nichts geändert hat — unnötiger Zeitaufwand.

├── **Lösung**: `--incremental` speichert SHA-256-Hashes der Dateien in `.copycat_cache/`; beim nächsten Lauf werden nur geänderte oder neue Dateien neu gescannt.

├── **Tests**: Zweiter Lauf bei unverändertem Projekt überspringt Dateien; geänderte Datei wird neu gelesen; Cache-Verzeichnis wird automatisch angelegt.

├── **README-Änderungen**: `-I`, `--incremental` in Parameter-Tabelle + „Inkrementeller Cache" in Feature-Tabelle beider Readmes.

└── **Risiken**: Cache veraltet bei manuellen Datei-Umbenennungen (unkritisch: nächster Lauf erkennt fehlenden Hash und scannt neu).



### MEILENSTEIN 31: Code-Statistiken (`--stats`)

##### ⏱️ 4h

├── **Problem**: Reports zeigen Dateiinhalte, aber keine aggregierten Metriken — Code-Qualität und -Umfang bleiben unsichtbar.

├── **Lösung**: `--stats` berechnet pro Datei LOC, Kommentaranteil, Leerzeilen und zyklomatische Komplexität (McCabe-Approximation); Zusammenfassung am Report-Ende.

├── **Tests**: Bekannte Testdateien liefern erwartete Werte; Komplexitätsberechnung korrekt; `--stats` ohne `--format`-Abhängigkeit.

├── **README-Änderungen**: `--stats`-Flag in Parameter-Tabelle + „Code-Statistiken" in Feature-Tabelle beider Readmes.

└── **Risiken**: Komplexitätsberechnung ist eine Schätzung ohne vollständiges AST-Parsing (für den Anwendungsfall ausreichend).



### MEILENSTEIN 32: Remote-Repository-Scan (`--git-url`)

##### ⏱️ 5h

├── **Problem**: Fremde Repos müssen manuell geklont, gescannt und danach gelöscht werden — mehrere fehleranfällige Schritte.

├── **Lösung**: `--git-url URL` klont das Repo per `git clone --depth 1` in ein temporäres Verzeichnis (`tempfile.TemporaryDirectory`), scannt es vollständig und räumt danach automatisch auf; URL-Validierung per Regex.

├── **Tests**: Ungültige URL → Fehlermeldung; Clone-Fehler → Fehlermeldung; Erfolg → Report erstellt; temporäres Verzeichnis nach Lauf bereinigt (15 neue Tests).

├── **README-Änderungen**: „Remote Repository" in Feature-Tabelle + `--git-url URL` in Parameter-Tabelle beider Readmes.

└── **Risiken**: Netzwerk-Timeout, große Repos (gelöst: `--depth 1` Shallow-Clone); `git` muss installiert sein.

### MEILENSTEIN 33: PDF-Export (`--format pdf`) ✅ Implementiert

##### ⏱️ 5h

├── **Problem**: Formale Übergaben (Ausbilder, Kunden, Prüfer) erfordern oft ein PDF — TXT/HTML sind dort unüblich.

├── **Lösung**: `--format pdf` erstellt via `reportlab` einen strukturierten PDF-Report mit Meta-Tabelle, Übersicht, Code-Details (max. 150 Zeilen/Datei), Stats und Suchergebnissen. `pdf` ist in `is_valid_serial_filename`, CLI-Choices und Config-Validierung registriert.

├── **Tests**: `test_write_pdf_creates_file`, `test_write_pdf_with_stats`, `test_run_copycat_pdf_format`, `test_is_valid_serial_filename_pdf`, `test_write_pdf_requires_reportlab`.

├── **README-Änderungen**: `pdf`-Zeile in Ausgabeformate-Tabelle; Installationshinweis (`pip install reportlab`) ergänzen.

└── **Risiken**: `reportlab` als optionale Abhängigkeit; ImportError wird mit klarem Hinweistext weitergegeben.



### MEILENSTEIN 34: Docker-Image ✅ Implementiert

##### ⏱️ 4h

├── **Problem**: Python-Installation und Abhängigkeiten sind auf CI-Servern oder fremden Maschinen mühsam; Setup-Fehler kosten Zeit.

├── **Lösung**: `Dockerfile` auf Basis `python:3.12-slim`; alle optionalen Abhängigkeiten (`reportlab`, `jinja2`, `watchdog`, `pygments`, `openai`) vorinstalliert; `.dockerignore` hält Image klein; `docker run --rm -v "$(pwd):/project" copycat [OPTIONEN]` schreibt Report in gemounteten Ordner.

├── **Tests**: `docker build` schlägt nicht fehl; Report erscheint nach `docker run` im gemounteten Ordner.

├── **README-Änderungen**: „Docker" Abschnitt mit `docker build`/`docker run`-Beispielen in beiden Readmes.

└── **Risiken**: Docker nicht überall verfügbar; Windows-Pfadnotation im Volume-Mount.



### MEILENSTEIN 35: AI-Zusammenfassung (`--ai-summary`) ✅ Implementiert

##### ⏱️ 6h

├── **Problem**: Ein CopyCat-Report enthält alle Rohdaten, aber keinen menschenlesbaren Projektsteckbrief.

├── **Lösung**: `--ai-summary` ruft `_generate_ai_summary()` auf; sendet nur Metadaten (Dateinamen, Counts, Git-Info) an die API — **kein Quellcode**; API-Key ausschließlich über `COPYCAT_AI_KEY`-Umgebungsvariable; `--ai-model` (Standard: `gpt-4o-mini`) und `--ai-base-url` (für Ollama) konfigurierbar; Ergebnis wird format-abhängig angehängt (TXT/MD: append, HTML: `</body>`-Injection, JSON: `ai_summary`-Feld, PDF: nur Log); bei Fehler Warnung statt Absturz.

├── **Tests**: `test_generate_ai_summary_missing_key`, `test_generate_ai_summary_missing_openai`, `test_generate_ai_summary_success`, `test_generate_ai_summary_api_error`, `test_run_copycat_ai_summary_warning_on_failure`.

├── **README-Änderungen**: „AI-Zusammenfassung" Abschnitt mit Einrichtungsanleitung und Ollama-Beispiel.

└── **Risiken**: Datenschutz-Hinweis prominent dokumentieren; lokale Ollama-Alternative empfohlen; `openai` optionale Abhängigkeit.



### MEILENSTEIN 36: Report-Timeline (`--timeline`) ✅ Implementiert

##### ⏱️ 6h

├── **Problem**: Mehrere Reports im Archiv, aber keine visuelle Übersicht über Projektentwicklung.

├── **Lösung**: `--timeline` + `--timeline-format {md,ascii,html}` liest alle `combined_copycat_N.*`-Dateien aus `CopyCat_Archive/`, extrahiert Datum/Dateianzahl/Typ-Counts; Ausgabe als Markdown-Tabelle (Standard), ASCII-Balkendiagramm (`█`) oder eigenständige HTML mit `Chart.js`-Balkendiagramm; PDF-Dateien werden übersprungen; GUI-Button „📊 Timeline" zeigt Ergebnis im Ausgabefenster.

├── **Tests**: `test_build_timeline_empty_archive`, `test_build_timeline_nonexistent_archive`, `test_build_timeline_txt_reports`, `test_build_timeline_json_reports`, `test_timeline_md_format`, `test_timeline_ascii_format`, `test_timeline_html_format`, `test_timeline_md_helper`, `test_timeline_ascii_helper`, `test_timeline_html_helper`, `test_timeline_ignores_pdf_files`.

├── **README-Änderungen**: „Report-Timeline" Abschnitt mit Beispielausgabe und `--timeline`-Erklärung.

└── **Risiken**: Archive-Reports unterschiedlicher Versionen (gelöst: robustes Parsing mit Fallback).



### MEILENSTEIN 37: Vollständige Type Annotations (mypy --strict) ✅ Implementiert

##### ⏱️ 6h

├── **Problem**: Keine Typ-Annotationen im gesamten `copycat/`-Paket; mypy-Prüfung schlug mit hunderten Fehlern fehl.

├── **Lösung**: Alle 24 Quelldateien in `copycat/` sowie `CopyCat.py` mit vollständigen Typ-Annotationen versehen; `py -m mypy copycat/ CopyCat.py --ignore-missing-imports --strict` → 0 Fehler. Schlüsselpattern: `dict[str, list[Path]]`, `dict[Path, list[tuple[int, str]]] | None`, `dict[str, Any] | None`, `IO[str]`; `spec.loader`-Guard in `plugins.py`; Callable-Narrowing via `assert renderer is not None`; `re.compile(pattern, timeout=1)  # type: ignore[call-overload]`.

├── **Tests**: Alle bestehenden 493 Tests bleiben grün; mypy-Lauf als Qualitäts-Gate.

├── **README-Änderungen**: mypy-Badge und `--strict`-Hinweis in beiden Readmes ergänzen.

└── **Risiken**: `re.compile` akzeptiert kein `timeout`-Keyword laut mypy-Stubs (gelöst mit `# type: ignore[call-overload]`).



### MEILENSTEIN 38: GUI-Reorganisation mit ttk.Notebook ✅ Implementiert

##### ⏱️ 5h

├── **Problem**: `CopyCat_GUI.py` war ein flaches Formular; mit wachsender Feature-Zahl wurde die Oberfläche unübersichtlich.

├── **Lösung**: `ttk.Notebook` mit 4 Tabs (**Basic**, **Erweitert**, **Plugins**, **Tools**); Run-Leiste und Ausgabefenster bleiben immer sichtbar unterhalb der Tabs. Tab-Inhalte: Basic (Ordner, Dateitypen, Rekursiv/Format/Max-Größe, Regex-Suche), Erweitert (Git-URL, Ausschließen, Inkrementell/Stats, Template, Watch-Cooldown), Plugins (Plugin-Verzeichnis + Browse + Refresh + geladene-Plugins-Anzeige), Tools (Config laden/speichern, Diff, Merge, Timeline, Git-Hook). Neue Members: `_plugin_dir_var`, `_browse_plugin_dir()`, `_refresh_plugins()`; `_build_args()` übergibt `plugin_dir`.

├── **Tests**: Headless-Fixture um `_plugin_dir_var` ergänzt; alle 493 Tests weiterhin grün; Commit `b130166`.

├── **README-Änderungen**: GUI-Beschreibung mit Tab-Struktur und Screenshot-Hinweis aktualisieren.

└── **Risiken**: Bestehende Headless-Test-Fixtures fehlten das neue Member (gelöst: `instance._plugin_dir_var = _make_var("")`).



### MEILENSTEIN 39: CSV-Support Komplettierung ✅ Implementiert

##### ⏱️ 5h

├── **Problem**: `.csv`-Dateien wurden im `db`-Typ als Binary behandelt (`list_binary_file`); kein strukturierter Report-Inhalt für Data-Science-Projekte.

├── **Lösung**: Neuer Extraktor `copycat/extractors/csv_extractor.py` mit `extract_csv()`, `_detect_delimiter()` (csv.Sniffer, Fallback `,`), `_col_stats()` (numeric/text, min/max/mean, unique, leer); Vorschau-Tabelle (erste 10 Zeilen); Encoding-Fallback (utf-8-sig → utf-8 → latin-1). `*.csv` von `db`-Typ nach `notebook`-Typ verschoben. Alle 4 Exporter (txt, md, html, json_export) dispatchen `.csv` via `extract_csv()` und `.ipynb` via `extract_notebook()`. JSON-Exporter ergänzt `"csv"`-Objekt mit `rows`, `columns`, `headers`, `delimiter`.

├── **Tests**: 34 neue Tests (527 gesamt, 99 % Branch-Coverage); Unit-Tests für `_detect_delimiter`, `_col_stats`, `extract_csv` (leer, latin-1, Tab-Delimiter, fehlende Zellen, OSError); Integration-Tests für txt/md/json-Exporter und Typ-Routing; Commit `5f75703`.

├── **README-Änderungen**: `notebook`-Zeile in Dateitypen-Tabelle um `*.csv` ergänzen; CSV-Extraktion unter Spezial-Renderer dokumentieren.

└── **Risiken**: Sniffer versagt bei Single-Column-CSVs (gelöst: `csv.Error`-Fallback); sehr große CSVs (gelöst: `--max-size` greift vor Extraktion).


---

## Meilenstein 40 – Python Packaging (pyproject.toml, `copycat` CLI Entry Point, PyPI-ready)

**Ziel:** CopyCat als installierbares Python-Paket veröffentlichen (PyPI-Name `copycat-tool`), mit `copycat`-CLI-Befehl statt `python CopyCat.py`, versionierter JSON-Ausgabe und GitHub-Actions-Publish-Pipeline.

├── **Problem**: CopyCat war nur als direktes Skript (`python CopyCat.py`) nutzbar; kein `pip install`, kein CLI-Einstiegspunkt, keine PyPI-Veröffentlichung, keine dynamische Versionsverwaltung.

├── **Lösung**:
│   ├── `copycat/__init__.py`: `__version__ = "2.9.0"` als zentrale Versionsquelle; `"__version__"` in `__all__`.
│   ├── `copycat/cli.py`: Neuer CLI-Einstiegspunkt `main()` – lädt Argumente via `parse_arguments()`, setzt Log-Level, delegiert an `list_plugins`, `install_hook`, `merge_reports`, `diff_reports`, `watch_and_run`, `build_timeline` oder `run_copycat`.
│   ├── `copycat/core.py`: `--version` Flag in `parse_arguments()` via `action="version"` und `__version__`.
│   ├── `copycat/exporters/json_export.py`: `"version"` im JSON-Output jetzt dynamisch aus `__version__` statt hartkodiert `"2.9"`.
│   ├── `CopyCat.py`: Legacy-Wrapper; `__main__`-Block delegiert an `copycat.cli:main`.
│   ├── `pyproject.toml`: PEP 621/517-konform mit `hatchling`; optionale Extras (`template`, `watch`, `html`, `pdf`, `ai`, `web`, `gui`, `all`); `[project.scripts] copycat = "copycat.cli:main"`.
│   ├── `.github/workflows/ci.yml`: Neuer `publish`-Job (tag-getriggert, Trusted Publishing via `pypa/gh-action-pypi-publish`).
│   ├── `Dockerfile`: Label-Version auf `2.9.0`, `pyproject.toml` eingebunden, `pip install -e .`, `ENTRYPOINT ["copycat", ...]`.
│   └── `copycat-vscode/`: Extension und `package.json` aktualisiert – CLI-Fallback wenn kein `CopyCat.py` gefunden.

├── **Tests**: 14 neue Tests (543 gesamt, 100 % Branch-Coverage); `test_version_exported`, `test_version_in_json_export`, `test_cli_main_version`, `test_cli_main_runs_run_copycat`, `test_cli_main_list_plugins`, `test_cli_main_list_plugins_with_results`, `test_cli_main_install_hook`, `test_cli_main_diff`, `test_cli_main_merge`, `test_cli_main_timeline`, `test_cli_main_watch`, `test_cli_main_verbose_log_level`, `test_cli_main_quiet_log_level`.

├── **README-Änderungen**: Installationsblock (`pip install copycat-tool[all]`), Konsolenbefehle auf `copycat`-CLI umgestellt, Testanzahl 530 → 543, mypy-Quelldateien 24 → 25.

└── **Risiken**: Zirkulärer Import `json_export.py → copycat → json_export` gelöst durch Top-Level-`__version__`-Definition in `__init__.py` vor allen Importen; verifiziert via pytest + mypy --strict (0 Fehler, 25 Quelldateien).
