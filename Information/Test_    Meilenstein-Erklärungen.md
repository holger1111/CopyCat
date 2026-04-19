## Meilenstein-Erklärungen: Warum sinnvoll & Was genau gemacht wird

### MEILENSTEIN 1: CLI `--types` vereinheitlichen
**Warum sinnvoll**: Aktuell ist die `--types`-Logik inkonsistent: Mehrfachauswahl wird nicht sauber als Liste behandelt, obwohl die Hilfe das suggeriert. Eine einheitliche Logik macht CopyCat für Nutzer vorhersagbarer und reduziert CLI-Fehler.
**Macht genau**: `args.types` wird immer als Liste ausgewertet, z. B. `if "all" in args.types or t in args.types`; dazu kommt eine zentrale `TYPE_FILTERS`-Definition mit allen Typen. Dadurch funktioniert `-t code web` genauso sauber wie `-t all`.

### MEILENSTEIN 2: Dateitypen zentral definieren + README sync
**Warum sinnvoll**: Wenn Code und Doku unterschiedliche Typenlisten haben, versteht niemand mehr, was CopyCat wirklich unterstützt. Eine zentrale Typenquelle verhindert Drift zwischen Implementierung und README und macht Erweiterungen deutlich wartbarer.
**Macht genau**: `TYPE_FILTERS` wird als globale Quelle für alle Kategorien genutzt, und beide Readmes bekommen eine vollständige Tabelle „Alle unterstützten Dateitypen“. So spiegeln Doku und Code exakt dieselben Kategorien wider.

### MEILENSTEIN 3: Serial-/Archivlogik robustifizieren
**Warum sinnvoll**: Das Serial-System ist ein Kernstück von CopyCat, weil es Reports versionierbar und archivierbar macht. Wenn die Nummerierung bei ungültigen Dateinamen oder Sonderfällen bricht, verliert das Tool genau dort seine Zuverlässigkeit, wo Nutzer sie erwarten.
**Macht genau**: `get_next_serial_number` wird per Regex abgesichert, alte Reports werden auch bei `serial=1` archiviert, und Konflikte werden sauber behandelt. Dadurch bleiben Nummerierung und Archiv auch bei leeren Ordnern oder manuell angelegten Dateien stabil.

### MEILENSTEIN 4: Exception-Handling gezielt machen
**Warum sinnvoll**: Generische `except Exception`-Blöcke verstecken echte Fehler und machen Debugging unnötig schwer. Spezifische Fehlerbehandlung sorgt dafür, dass CopyCat verständlich reagiert statt still oder unklar zu scheitern.
**Macht genau**: Statt pauschalem Catching werden gezielte Handler verwendet, etwa `UnicodeDecodeError` für binäre Dateien und `ET.ParseError` für kaputtes XML. So entstehen klare Meldungen wie „Binary skipped“ oder „Invalid XML“, während Restfehler weiterhin geloggt werden.

### MEILENSTEIN 5: Draw.io-Extraktion stabilisieren
**Warum sinnvoll**: Draw.io-Dateien sind oft die wichtigste visuelle Projektquelle, aber sie haben mehrere Formate und Edge-Cases. Ohne robuste Extraktion verliert CopyCat bei genau diesen Dateien an Nutzen und wirkt schnell unzuverlässig.
**Macht genau**: Die Extraktion wird auf spezifisches XML-Parsing umgestellt, inklusive Fallback für komprimierte `.drawio`-Dateien per Unzip. Zusätzlich wird die Statistik erweitert, damit leere, beschädigte oder komprimierte Diagramme sauber erkannt und dokumentiert werden.

### MEILENSTEIN 6: Tests + Open-Source-Ready
**Warum sinnvoll**: Ohne Tests bleibt jede Änderung riskant, besonders bei CLI, Serial-System und Draw.io-Parsing. Gleichzeitig braucht ein Open-Source-Projekt wie CopyCat klare Mitmachregeln, damit neue Beiträge nicht die Wartbarkeit verschlechtern.
**Macht genau**: Es entsteht eine Pytest-Suite für CLI, Typen und Edge-Cases, ergänzt durch `CONTRIBUTING.md`, Lizenz und GitHub Actions. Dazu kommen README-Erweiterungen für Entwickler-Guide, Test-Hinweise und Badges, sodass das Projekt technisch und dokumentarisch „open-source-ready“ wird.

### MEILENSTEIN 7: Rekursive Suche 
**Warum sinnvoll**: Aktuell verpasst CopyCat 90% echter Projekte (Code in `src/`, `tests/`, etc.). Rekursiv → vollständige Projekte.
**Macht genau**: `--recursive/-r` Flag fügt `input_dir.rglob(pat)` hinzu → scannt **alle** Unterordner, Default bleibt flach (`glob`). 

### MEILENSTEIN 8: Dateigrößenlimit + Performance 
**Warum sinnvoll**: 10MB+ Videos blockieren Reports; `rglob` bei 1000+ Files hängt. **Enterprise** braucht Kontrolle.
**Macht genau**: `--max-size 5` → skippt >5MB; Progress-Counter (`Scanned 1234/5000`); `stat().st_size` Filter vor Parsing. )

### MEILENSTEIN 9: Git-Integration + .gitignore 
**Warum sinnvoll**: 95% Projekte sind Git-Repos. Branch/Commit-Info + `.gitignore`-Skip → **kontextreiche** Reports.
**Macht genau**: `git rev-parse HEAD` → "Branch: main | abc123"; `gitignore_parser` respektiert `*.log`, `node_modules/`.

### MEILENSTEIN 10: JSON/Markdown Ausgabeformate 
**Warum sinnvoll**: Nur `.txt` → unbrauchbar für CI/CD, JSON-Parser, VSCode. **Machine-Readable** für Tools.
**Macht genau**: `--format json|md|txt` → strukturierte Ausgabe:
```json
{"files":47,"types":{"code":5},"git":{"branch":"main"}}
```

### MEILENSTEIN 11: Inhalts-Suche + Regex
**Warum sinnvoll**: "Finde alle TODOs" oder "def "-Funktionen → **10x** nützlicher als reine Dateiliste.
**Macht genau**: `--search "TODO|FIXME"` → **Zeilennummer + Snippet** pro Treffer; `re.search(pattern, content)`. 

### MEILENSTEIN 12: Konfigurationsdatei 
**Warum sinnvoll**: `CopyCat.py -i src -r -t code -o docs --max-size 2` → **zu lang** für täglich. Config = 1 Befehl.
**Macht genau**: `copycat.conf`:
```yaml
types: [code, diagram]
recursive: true
max_size_mb: 5
format: md
```

### MEILENSTEIN 13: Logging
**Warum sinnvoll**: Ohne strukturierte Laufzeit-Meldungen ist es schwer nachzuvollziehen, was CopyCat wann tut – besonders bei Fehlern in großen Projekten. Logging macht das Verhalten transparent und vereinfacht Debugging erheblich.
**Macht genau**: Das `logging`-Modul wird im gesamten Core und in der GUI integriert. `--verbose` schaltet auf DEBUG-Level, `--quiet` unterdrückt alles außer Fehlern. Die GUI leitet Log-Nachrichten ins Ausgabefenster um, sodass Nutzer den Fortschritt live sehen.

### MEILENSTEIN 14: Config Load/Save (GUI)
**Warum sinnvoll**: Wer CopyCat täglich mit denselben Einstellungen nutzt, will diese nicht bei jedem Start neu eintippen. Eine persistente Konfiguration macht das Tool deutlich angenehmer im Alltag.
**Macht genau**: `copycat.conf` wird beim Programmstart automatisch geladen und befüllt CLI-Defaults. CLI-Flags überschreiben die Config (Priorität: CLI > Config > Default). Die GUI erhält "Laden"- und "Speichern"-Buttons, über die alle aktuellen Einstellungen direkt in die Datei geschrieben werden können.

### MEILENSTEIN 15: Drag & Drop (tkinterdnd2)
**Warum sinnvoll**: Das manuelle Eintippen langer Pfade ist fehleranfällig und umständlich. Drag-and-Drop entspricht der natürlichen Erwartung an eine Desktop-GUI und senkt die Einstiegshürde sprunghaft.
**Macht genau**: Mithilfe der optionalen Bibliothek `tkinterdnd2` kann ein Ordner oder eine Datei direkt in das Eingabefeld der GUI gezogen werden – der Pfad wird automatisch übernommen. Ist `tkinterdnd2` nicht installiert, bleibt die GUI vollständig nutzbar, das Feature ist nur deaktiviert.

### MEILENSTEIN 16: Progressbar
**Warum sinnvoll**: Bei großen Projekten mit hunderten Dateien wirkt die GUI ohne Feedback eingefroren. Ein Fortschrittsbalken signalisiert, dass das Programm arbeitet, und gibt dem Nutzer Kontrolle über das Geschehen.
**Macht genau**: Ein `ttk.Progressbar`-Widget wird in die GUI eingebettet und zeigt den Scanfortschritt in Echtzeit an. Der eigentliche Scan läuft im Hintergrund-Thread, `after()`-Callbacks aktualisieren die Leiste thread-sicher, sodass die GUI jederzeit reagiert.

### MEILENSTEIN 17: Notebook/CSV-Unterstützung
**Warum sinnvoll**: Data-Science-Projekte bestehen zu großen Teilen aus Jupyter-Notebooks und CSV-Dateien. Ohne diese Kategorie liefert CopyCat bei solchen Projekten lückenhafte Reports.
**Macht genau**: `TYPE_FILTERS` erhält eine neue Kategorie `notebook` mit den Mustern `.ipynb`, `.csv`, `.tsv` und `.parquet`. Jupyter-Notebooks werden per JSON-Parsing verarbeitet, sodass Code- und Markdown-Zellen sauber extrahiert werden. CSV- und TSV-Dateien erscheinen als Plaintext im Report.

### MEILENSTEIN 18: Diff-Modus
**Warum sinnvoll**: Projekte ändern sich über Zeit – Dateien kommen hinzu, werden gelöscht oder umbenannt. Ohne Vergleichsmöglichkeit bleibt diese Entwicklung unsichtbar. Ein Diff-Modus macht Veränderungen auf einen Blick sichtbar.
**Macht genau**: `--diff REPORT_A REPORT_B` vergleicht zwei CopyCat-Reports und gibt eine strukturierte Übersicht der Unterschiede aus: hinzugefügte Dateien, entfernte Dateien und geänderte Inhalte. Die Logik steckt in der eigens dafür geschriebenen Funktion `diff_reports()`.

### MEILENSTEIN 19: Jinja2-Templates
**Warum sinnvoll**: Die fest kodierte Ausgabestruktur lässt sich nicht an individuelle Bedürfnisse anpassen. Anwender mit eigenen Report-Layouts müssten sonst den Core verändern. Templates lösen das elegant ohne jede Codeänderung.
**Macht genau**: `--template DATEI` lädt eine Jinja2-Template-Datei. `_write_template()` füllt alle verfügbaren Variablen – Dateiliste, Git-Infos, Statistiken – in das Template ein und schreibt die Ausgabe in die Report-Datei. Jinja2 ist optional; fehlt es, erscheint eine verständliche Fehlermeldung mit Installationshinweis.

### MEILENSTEIN 20: Parallele Suche (ThreadPoolExecutor)
**Warum sinnvoll**: Die sequenzielle Regex-Suche über hunderte Dateien ist bei `--search` ein spürbarer Flaschenhals. Parallelisierung nutzt moderne Mehrkern-CPUs und verkürzt die Wartezeit erheblich.
**Macht genau**: Die Dateisuche in `--search` wird auf einen `concurrent.futures.ThreadPoolExecutor` umgestellt. Jede Datei wird in einem eigenen Thread per `re.search()` durchsucht; die Treffer (Zeilennummer + Snippet) werden thread-sicher in einer gemeinsamen Liste gesammelt und am Ende sortiert ausgegeben.

### MEILENSTEIN 21: Pre-commit Hook
**Warum sinnvoll**: Der Report wird oft vergessen, wenn er manuell ausgeführt werden muss. Als Git-Hook läuft CopyCat automatisch bei jedem Commit und hält die Dokumentation so immer auf dem neuesten Stand.
**Macht genau**: `--install-hook DIR` erzeugt ein ausführbares `pre-commit`-Skript in `.git/hooks/` des angegebenen Projekts. Das Skript ruft CopyCat mit den gleichen Einstellungen auf wie zuletzt verwendet. Existiert bereits ein Hook, wird eine Warnung ausgegeben statt den vorhandenen zu überschreiben.

### MEILENSTEIN 22: Watch-Modus
**Warum sinnvoll**: Während der aktiven Entwicklung soll der Report ständig aktuell sein, ohne dass der Entwickler manuell eingreifen muss. Der Watch-Modus macht CopyCat zum permanenten Hintergrundassistenten.
**Macht genau**: `--watch` aktiviert die Dateisystemüberwachung via `watchdog`. Sobald eine Datei im Eingabeordner geändert wird, löst CopyCat nach Ablauf des mit `--cooldown SEKUNDEN` einstellbaren Wartezeitraums automatisch einen neuen Lauf aus. `watchdog` ist optional; fehlt es, erscheint ein klarer Installationshinweis.

### MEILENSTEIN 23: Merge mehrerer Projekte
**Warum sinnvoll**: In Multi-Repo- oder Monorepo-Setups entstehen mehrere CopyCat-Reports. Diese manuell zusammenzuführen ist mühsam und fehleranfällig. Ein Merge-Befehl löst das mit einem einzigen Aufruf.
**Macht genau**: `--merge REPORT [REPORT ...]` nimmt beliebig viele CopyCat-Reports entgegen und führt sie in einer einzigen Ausgabedatei zusammen. `merge_reports()` erkennt und dedupliziert überlappende Dateieinträge. Das Zielformat (txt/json/md) wird aus dem ersten Report übernommen.

### MEILENSTEIN 24: Plugin-System
**Warum sinnvoll**: Jede neue Dateiart (`.proto`, `.avro`, benutzerdefiniert) erforderte bisher Änderungen am Core. Ein Plugin-System macht CopyCat offen erweiterbar, ohne die stabile Kern-Codebasis anzutasten – und ermöglicht Nutzern eigene Renderer ohne Fork.
**Macht genau**: `load_plugins()` durchsucht ein Plugin-Verzeichnis und importiert jede `.py`-Datei per `importlib.util`. Definiert ein Plugin `TYPE_NAME`, `PATTERNS` und optional `render_file()`, wird der Typ nahtlos in `TYPE_FILTERS` und `PLUGIN_RENDERERS` eingetragen. Fehlerhafte Plugins werden mit Warnung übersprungen. Die CLI erhält `--plugin-dir` und `--list-plugins`; `plugins/example_proto.py` liefert eine sofort kopierbare Vorlage.

### MEILENSTEIN 25: PyInstaller EXE als CI-Artifact
**Warum sinnvoll**: Nicht alle Nutzer haben Python installiert oder wollen es einrichten. Ein fertiges `.exe`-Binary senkt die Einstiegshürde drastisch und macht CopyCat direkt verwendbar – ohne Abhängigkeiten, ohne Virtualenv, per Doppelklick.
**Macht genau**: `CopyCat.spec` und `CopyCat_Web.spec` definieren One-File-Builds für PyInstaller. GitHub Actions fügt zwei Windows-Jobs (`build-exe`, `build-web-exe`) hinzu, die erst nach bestandenen Tests laufen. Die fertigen `.exe`-Dateien (`CopyCat.exe` und `CopyCat_Web.exe`) werden als Actions-Artifacts hochgeladen und sind 30 Tage abrufbar. Lokal genügt `pyinstaller CopyCat.spec`.

### MEILENSTEIN 26: Flask Web-Interface
**Warum sinnvoll**: Die CLI ist mächtig, aber nicht für alle zugänglich. Ein Browser-Interface ermöglicht CopyCat ohne Terminalkenntnisse zu nutzen – ideal für Teams, die das Tool gelegentlich einsetzen oder per REST-API in eigene Workflows einbinden wollen.
**Macht genau**: `CopyCat_Web.py` startet einen Flask-Server mit vier Routen: `/` zeigt ein HTML-Formular mit allen CopyCat-Optionen, `/run` führt den Report-Lauf durch und zeigt das Ergebnis direkt im Browser an, `/download` liefert die Report-Datei zum Herunterladen (Sicherheitscheck: nur `combined_copycat_*.{txt,json,md}` erlaubt), und `/api/run` stellt eine JSON-REST-API bereit. Ein `threading.Lock` verhindert gleichzeitige Läufe. Das gesamte HTML-Template ist inline eingebettet – kein separates `templates/`-Verzeichnis nötig. Flask ist optional (`pip install flask`); fehlt es, beendet sich die App mit einer verständlichen Fehlermeldung.

### MEILENSTEIN 27: VS Code Extension
**Warum sinnvoll**: CopyCat ist ausschließlich per Terminal nutzbar. Entwickler, die VS Code als primären Editor verwenden, müssen den Editor verlassen, um einen Report zu erstellen. Eine VS Code Extension beseitigt diese Hürde und macht CopyCat zur natürlichen Erweiterung des Editors selbst.
**Macht genau**: Eine TypeScript-Extension im Ordner `copycat-vscode/` integriert CopyCat direkt in VS Code. Zwei Befehle stehen in der Befehlspalette und in der Statusleiste bereit: `CopyCat: Report erstellen` (flach) und `CopyCat: Report erstellen (rekursiv)`. Alle wichtigen Optionen sind über VS Code Settings konfigurierbar (`copycat.pythonPath`, `copycat.scriptPath`, `copycat.outputFormat`, `copycat.maxSizeMb`, `copycat.excludePatterns`, `copycat.extraArgs`). Die Extension wird per `npm run compile` gebaut und als `.vsix` paketiert.

### MEILENSTEIN 28: Exclude-Patterns (`--exclude`)
**Warum sinnvoll**: In realen Projekten gibt es immer Ordner und Dateien, die nicht in einen Report gehören: Build-Verzeichnisse (`dist/`, `build/`), Paketmanager-Ordner (`node_modules/`, `.venv/`), generierte Dateien. Ohne Ausschluss-Mechanismus werden diese miterfasst und blähen den Report auf.
**Macht genau**: Das neue Flag `-E` / `--exclude` akzeptiert beliebig viele Glob-Muster als Argumente. Beim Dateiscan wird jeder Pfad per `fnmatch` gegen alle Muster geprüft; passende Dateien werden vor der Typerkennung übersprungen. Mehrere Muster sind kombinierbar, z. B. `--exclude "*.min.js" "dist/" "node_modules/"`. Ist kein Muster angegeben, verhält sich CopyCat unverändert.

### MEILENSTEIN 29: HTML-Report mit Syntax-Highlighting
**Warum sinnvoll**: Text- und Markdown-Berichte sind zwar portabel, aber im Browser oder bei der Weitergabe an Nicht-Entwickler schwer lesbar. Syntax-Highlighting macht Code sofort verständlich und verbessert die visuelle Qualität des Reports erheblich.
**Macht genau**: `--format html` erzeugt eine eigenständige HTML-Datei ohne externe Abhängigkeiten. Jede Datei im Report bekommt eine klappbare `<details>`-Sektion. Ist Pygments installiert (`pip install pygments`), wird der Quellcode automatisch mit dem passenden Lexer hervorgehoben; ohne Pygments erscheint der Code in einem einfachen `<pre>`-Block ohne Absturz. Das HTML-Format ergänzt die bestehenden Formate `txt`, `json` und `md`.

### MEILENSTEIN 30: Inkrementelle Reports / Cache (`--incremental`)
**Warum sinnvoll**: Bei großen Projekten mit hunderten oder tausenden Dateien nimmt das vollständige Neu-Scannen messbar Zeit in Anspruch — auch wenn sich seit dem letzten Lauf kaum etwas geändert hat. Inkrementelle Verarbeitung beschleunigt CopyCat dramatisch im Alltag.
**Macht genau**: `--incremental` / `-I` aktiviert einen dateibasierten SHA-256-Cache im Verzeichnis `.copycat_cache/`. Beim ersten Lauf werden alle Dateien gescannt und ihre Hashes gespeichert. Bei jedem weiteren Lauf werden nur Dateien verarbeitet, deren Hash sich geändert hat oder die neu sind. Das Cache-Verzeichnis wird automatisch angelegt und ist über `.gitignore` aus der Versionskontrolle ausgeschlossen.

### MEILENSTEIN 31: Code-Statistiken (`--stats`)
**Warum sinnvoll**: CopyCat liefert bisher den Inhalt von Dateien, aber keine aggregierten Kennzahlen. Für Code-Reviews, Projektabgaben oder Qualitätschecks sind schnelle Metriken wie Zeilenanzahl, Kommentaranteil und Komplexität wertvoller als der Rohtext allein.
**Macht genau**: `--stats` ergänzt den Report um eine Statistik-Sektion. Pro Code-Datei werden LOC (Lines of Code), Kommentaranteil in Prozent, Leerzeilen und die zyklomatische Komplexität (McCabe-Approximation: Anzahl der Entscheidungspunkte + 1) berechnet. Am Report-Ende erscheint eine Zusammenfassung über alle gescannten Code-Dateien. Das Flag funktioniert unabhängig vom Ausgabeformat.

### MEILENSTEIN 32: Remote-Repository-Scan (`--git-url`)
**Warum sinnvoll**: Wer ein fremdes Repository dokumentieren möchte, muss es bisher manuell klonen, den Pfad angeben, den Scan durchführen und den geklonten Ordner anschließend wieder löschen. Das sind vier Schritte, die fehleranfällig und umständlich sind. Ein einziger Befehl ist klarer und zuverlässiger.
**Macht genau**: `--git-url URL` übernimmt den gesamten Ablauf automatisch: Die URL wird per Regex auf Plausibilität geprüft. Dann klont CopyCat das Repo mit `git clone --depth 1` (Shallow-Clone für minimale Datenmenge) in ein temporäres Verzeichnis (`tempfile.TemporaryDirectory`). Nach dem Scan wird das Verzeichnis automatisch bereinigt, unabhängig davon, ob der Scan erfolgreich war oder nicht. Tritt ein Fehler auf (ungültige URL, kein Netzwerk, Clone-Fehler), erhält der Nutzer eine verständliche Fehlermeldung.

### MEILENSTEIN 33: PDF-Export (`--format pdf`)
**Warum sinnvoll**: Bei formalen Übergaben — IHK-Abschlussprojekte, Kundenpräsentationen, Prüfungsunterlagen — ist ein PDF das erwartete Format. Ein TXT- oder HTML-Report wirkt in diesem Kontext unprofessionell. Mit einem einzigen Flag kann CopyCat direkt das Endformat liefern, ohne zusätzliche Konvertierungsschritte.
**Macht genau**: `--format pdf` ergänzt die bestehenden Ausgabeformate `txt`, `json`, `md` und `html` um eine PDF-Ausgabe. Als primäre Rendering-Engine wird `weasyprint` verwendet, das HTML in PDF konvertiert und damit dieselbe strukturierte Darstellung wie der HTML-Report liefert. Ist `weasyprint` nicht verfügbar, greift `reportlab` als leichterer Fallback. Beide Bibliotheken sind optional; fehlen sie, erscheint eine klare Fehlermeldung mit Installationshinweis.

### MEILENSTEIN 34: Docker-Image
**Warum sinnvoll**: Python-Installation, virtuelle Umgebungen und optionale Abhängigkeiten sind auf CI-Servern oder fremden Rechnern eine wiederkehrende Quelle von Problemen. Ein Docker-Image kapselt CopyCat vollständig und macht es sofort verwendbar — ohne jede lokale Installation.
**Macht genau**: Ein `Dockerfile` auf Basis `python:3-slim` installiert CopyCat und alle Kernabhängigkeiten. Per Volume-Mount (`-v $(pwd):/data`) wird der zu scannende Ordner in den Container eingebunden; der fertige Report erscheint direkt im selben Verzeichnis. Das Image wird auf Docker Hub veröffentlicht. GitHub Actions baut und pusht das Image automatisch bei jedem Release-Tag. Alle Kern-Optionen (`-r`, `-f json`, `--stats`, `--git-url` etc.) funktionieren identisch wie in der lokalen Installation.

### MEILENSTEIN 35: AI-Zusammenfassung (`--ai-summary`)
**Warum sinnvoll**: Ein CopyCat-Report enthält alle relevanten Rohdaten über ein Projekt, aber keinen menschenlesbaren Überblick. Wer den Report an jemanden weitergibt, der das Projekt nicht kennt, muss den Steckbrief bisher manuell schreiben. Eine LLM-gestützte Zusammenfassung erledigt das automatisch und in konsistenter Qualität.
**Macht genau**: `--ai-summary` sendet den fertigen Report an eine OpenAI-kompatible LLM-API. Das Modell erhält einen System-Prompt, der es anweist, einen kompakten Projektsteckbrief zu erstellen: Projektzweck, erkannter Technologie-Stack, Auffälligkeiten und Empfehlungen. Der API-Key wird über die Umgebungsvariable `COPYCAT_AI_KEY` übergeben, nie über die CLI. Als lokale Alternative ohne Cloud-Kosten und ohne Datenweitergabe wird Ollama unterstützt. Die Zusammenfassung wird am Ende des Reports als eigener Abschnitt angehängt.

### MEILENSTEIN 36: Report-Timeline (`--timeline`)
**Warum sinnvoll**: CopyCat archiviert automatisch alle Reports im `CopyCat_Archive/`-Ordner. Dieses Archiv enthält wertvolle historische Informationen — Dateianzahl, Typverteilung, Codevolumen über Zeit —, die bisher ungenutzt bleiben. Eine Timeline macht die Projektentwicklung auf einen Blick sichtbar und liefert objektive Kennzahlen für Fortschrittsberichte oder Retrospektiven.
**Macht genau**: `--timeline` liest alle Reports im `CopyCat_Archive/`-Ordner, parst ihre Header (Serial-Nummer, Datum, Dateianzahl, Typ-Aufschlüsselung) und baut daraus eine Zeitreihe. Die Standard-Ausgabe ist eine Markdown-Tabelle mit einer Zeile pro Report. Optional erzeugt `--timeline --format html` eine eigenständige HTML-Datei mit einem eingebetteten Chart (Chart.js via CDN), das Dateianzahl und Codevolumen über die Zeit visualisiert. Ein ASCII-Chart steht für rein terminale Nutzung bereit.

### MEILENSTEIN 37: Vollständige Type Annotations (mypy --strict)
**Warum sinnvoll**: Ohne Typ-Annotationen ist jede Refactoring-Maßnahme riskant – Parametertypen, Rückgabewerte und komplexe Datenstrukturen bleiben implizit und fehleranfällig. `mypy --strict` als hartes Qualitäts-Gate schließt eine ganze Klasse von Bugs bereits vor der Laufzeit aus und macht das Projekt für externe Beitragende wesentlich einstiegsfreundlicher.
**Macht genau**: Alle 24 Quelldateien im `copycat/`-Paket sowie `CopyCat.py` erhalten vollständige Typ-Annotationen. Komplexe Schnittstellen-Muster wie `dict[str, list[Path]]`, `dict[Path, list[tuple[int, str]]] | None` und `IO[str]` werden konsequent durchgezogen. In `plugins.py` wird ein expliziter `if spec is None or spec.loader is None`-Guard eingeführt, statt `# type: ignore` zu verwenden. Plugin-Callables werden via `assert renderer is not None` vor dem Aufruf narrowed. `re.compile` erhält ein `# type: ignore[call-overload]` für das `timeout`-Keyword, das mypy-Stubs nicht kennen. Ergebnis: `py -m mypy copycat/ CopyCat.py --ignore-missing-imports --strict` meldet **0 Fehler** in 24 Quelldateien.

### MEILENSTEIN 38: GUI-Reorganisation mit ttk.Notebook
**Warum sinnvoll**: Mit über 35 implementierten Features wurde das flache `CopyCat_GUI.py`-Formular unüberschaubar. Nutzer mussten für jede Einstellung durch eine endlose Spalte von Widgets scrollen, ohne visuelle Orientierung. Eine Tab-basierte Oberfläche macht die GUI intuitiver, reduziert kognitive Last und skaliert für weitere Features, ohne die Oberfläche erneut überladen zu müssen.
**Macht genau**: `CopyCat_GUI.py` wird auf ein `ttk.Notebook` mit vier thematisch gruppierten Tabs umgestellt. Run-Leiste (Fortschrittsbalken + Starten-Knopf) und das Ausgabefenster bleiben immer sichtbar unterhalb der Tabs. Tab **Basic** enthält Ordner (Eingabe/Ausgabe mit Drag-&-Drop), Dateitypen-Checkboxen, Rekursiv/Format/Max-Größe und Regex-Suche. Tab **Erweitert** gruppiert Git-URL, Ausschluss-Muster, Inkrementell/Stats, Jinja2-Template und Watch-Cooldown. Tab **Plugins** bietet Plugin-Verzeichnis-Browser (`_browse_plugin_dir()`), ein Widget für geladene Plugins und einen Refresh-Button (`_refresh_plugins()`). Tab **Tools** fasst Config laden/speichern, Diff, Merge, Timeline und Git-Hook zusammen. Die GUI-Klasse erhält `_plugin_dir_var` als neues Member; `_build_args()` übergibt `plugin_dir` an die Core-Engine. Headless-Test-Fixtures werden um `_plugin_dir_var` ergänzt.

### MEILENSTEIN 39: CSV-Support Komplettierung
**Warum sinnvoll**: `.csv`-Dateien wurden bisher im `db`-Typ als Binary behandelt und lieferten keinerlei Strukturinformation im Report. Für Data-Science-Projekte – die zu großen Teilen aus CSV-Daten bestehen – war der CopyCat-Report dadurch praktisch wertlos. Eine vollwertige CSV-Extraktion schließt diese Lücke und macht CopyCat zu einem vollständigen Dokumentationswerkzeug für Data-Science- und Analytics-Projekte.
**Macht genau**: Ein neuer Extraktor `copycat/extractors/csv_extractor.py` implementiert `extract_csv()` als zentralen Einstiegspunkt. `_detect_delimiter()` erkennt das Trennzeichen automatisch per `csv.Sniffer` mit Fallback auf `,` (unterstützt Komma, Semikolon, Tab, Pipe). `_col_stats()` berechnet pro Spalte, ob der Inhalt numerisch oder textuell ist, und liefert entsprechend min/max/mean oder Längenbereiche, Unique-Count und Leer-Zählung. Das Encoding wird automatisch erkannt (utf-8-sig → utf-8 → latin-1, schlägt nie fehl). Eine formatierte Vorschau-Tabelle zeigt die ersten 10 Datenzeilen. `*.csv` wird aus dem `db`-Typ in den `notebook`-Typ verschoben. In allen vier Exportern (txt, md, html, json_export) wird innerhalb des `notebook`-Zweigs nach Suffix unterschieden: `.csv` → `extract_csv()`, `.ipynb` → `extract_notebook()`. Der JSON-Exporter ergänzt pro CSV-Eintrag ein `"csv"`-Metadaten-Objekt mit `rows`, `columns`, `headers` und `delimiter`.

### MEILENSTEIN 40: Python Packaging (pyproject.toml, `copycat` CLI, PyPI-ready)
**Warum sinnvoll**: CopyCat war bislang nur als direktes Skript nutzbar (`python CopyCat.py`). Für eine breite Nutzerbasis, Integrierbarkeit in Build-Pipelines und Community-Beiträge ist ein installierbares Paket mit `pip install copycat-tool` und einem dedizierten `copycat`-Befehl essenziell. Der PyPI-Standard (PEP 517/621) stellt sicher, dass CopyCat in jedem Python-Ökosystem (venv, conda, Docker, CI) ohne Pfad-Hacks funktioniert.
**Macht genau**: `copycat/__init__.py` erhält `__version__ = "2.9.0"` als zentrale Versionsquelle. `copycat/cli.py` implementiert `main()` als offiziellen CLI-Einstiegspunkt – er lädt Argumente, setzt den Log-Level und delegiert an die passende Funktion (`run_copycat`, `list_plugins`, `install_hook`, `merge_reports`, `diff_reports`, `watch_and_run`, `build_timeline`). `parse_arguments()` in `core.py` bekommt `--version` (gibt `CopyCat 2.9.0` aus). `json_export.py` liest die Version jetzt dynamisch aus `__version__` statt hartkodiert `"2.9"`. `pyproject.toml` (hatchling, PEP 621) definiert den PyPI-Namen `copycat-tool`, optionale Extras (`template`, `watch`, `html`, `pdf`, `ai`, `web`, `gui`, `all`) und den `[project.scripts]`-Eintrag `copycat = "copycat.cli:main"`. `CopyCat.py` wird zum reinen Legacy-Wrapper (`__main__` delegiert an `copycat.cli:main`). In `.github/workflows/ci.yml` übernimmt ein neuer `publish`-Job (tag-getriggert, Trusted Publishing) das automatische PyPI-Release. `Dockerfile` und die VS Code Extension werden ebenfalls auf die neue CLI umgestellt.
