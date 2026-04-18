# CopyCat v2.1+ Entwicklungsplan  

Der Plan folgt strikt der Raumanweisung:

* Fehler zuerst,
* Doku synchron,
* CLI-Kompatibilität wahren.



**Gesamtaufwand:**

\~33-47h für 1 Person.



**Nach Meilenstein 3:**

Robust und produktionsreif.


**Nach Meilenstein 6:**

Vollständig dokumentiert und erweiterbar.


**Nach Meilensteine 12:**

Enterprise-Ready



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


