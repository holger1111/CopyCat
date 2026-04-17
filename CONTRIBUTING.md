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

git clone https://github.com/holge-l/CopyCat.git

cd CopyCat

py -m pytest test_copycat.py -v --cov # 100% Core-Coverage

```



### Test vor Push



```bash

py -m pytest test_copycat.py -v --cov-report=term-missing

```



**Coverage: 100% Core (CLI, Serial, Draw.io)**



### Commit-Konvention



**feat**: Add neuer Typ (audio/flac)

**fix**: Serial ignoriert ungültige Namen

**docs**: README synchronisiert

**test**: 100% Coverage für extract\_drawio

**style**: PEP8 Formatierung



### Frage vor jedem Push:



**"Ist CopyCat jetzt einfacher zu verstehen/wartbar?"**

