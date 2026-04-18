# Mitmachen bei CopyCat



**Ziel:** Robustes, wartbares Projekt-Dokumentierer-Tool.



### Regeln (für jeden Commit)


- **Code + README.md + README_GER.md SYNCHRON** halten

- **Fehler vor Features** (CLI-Types, Serial, Encoding)

- Dateitypen **zentral** in `TYPE_FILTERS` definieren

- Jede Änderung: **eindeutiger, robuster, besser dokumentiert**

- CLI-Optionen **rückwärtskompatibel**



### Entwicklung



```bash

git clone https://github.com/holger1111/CopyCat.git

cd CopyCat

pip install jinja2 watchdog tkinterdnd2   # optionale Abhängigkeiten

py -m pytest test_copycat.py --cov=. --cov-config=.coveragerc --cov-report=term-missing

```


### Test vor Push



```bash

py -m pytest test_copycat.py --cov=. --cov-config=.coveragerc --cov-report=term-missing

```



**Coverage: 100 % (238 Tests, Branch-Coverage aktiv)**



### Commit-Konvention



**feat**: Neue Funktion (z.B. Watch-Modus, Jinja2-Templates)

**fix**: Fehlerkorrektur (z.B. Serial ignoriert ungültige Namen)

**docs**: README synchronisiert

**test**: Coverage verbessert / neue Tests

**ci**: CI-Pipeline angepasst

**style**: PEP8-Formatierung / Bereinigung



### Frage vor jedem Push:



**"Ist CopyCat jetzt einfacher zu verstehen/wartbar?"**

