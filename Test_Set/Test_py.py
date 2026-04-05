from pathlib import Path

CATEGORIES = {
    "code": ["*.java", "*.py", "*.spec", "*.cpp", "*.c"],
    "web": ["*.html", "*.css", "*.js", "*.ts", "*.jsx"],
    "db": ["*.sql", "*.db", "*.sqlite"],
    "config": ["*.json", "*.yaml", "*.xml", "*.properties", "*env"],
    "docs": ["*.md", "*.txt", "*.log", "*.docx"],
    "deps": ["requirements.txt", "package.json", "pom.xml", "go.mod"],
    "img": ["*.png", "*.jpg", "*.gif", "*.bmp", "*.webp", "*.svg", "*.ico"],
    "audio": ["*.mp3", "*.wav", "*.ogg", "*.m4a", "*.flac"],
    "diagram": ["*.drawio", "*.svg", "*.dia", "*.puml"],
}


def pattern_to_filename(pattern: str) -> str:
    pattern = pattern.strip()
    if not pattern:
        raise ValueError("Leeres Muster ist nicht erlaubt.")

    if pattern.startswith("*."):
        ext = pattern[2:]
        return f"Test_{ext}.{ext}"

    if pattern.startswith("*"):
        suffix = pattern[1:]
        return f"Test_{suffix}{suffix}" if suffix.startswith(".") else f"Test_{suffix}.{suffix.lstrip('.')}"

    if "." in pattern:
        base, ext = pattern.rsplit(".", 1)
        return f"Test_{base}.{ext}"

    return f"Test_{pattern}.{pattern}"


def create_empty_files(patterns: list[str], count: int = 1) -> None:
    folder = Path.cwd()
    for pattern in patterns:
        filename = pattern_to_filename(pattern)
        stem = Path(filename).stem
        suffix = Path(filename).suffix
        for i in range(count):
            path = folder / (filename if count == 1 else f"{stem}_{i+1}{suffix}")
            path.touch(exist_ok=False)
            print(f"Erstellt: {path.name}")


if __name__ == "__main__":
    print("Verfügbare Gruppen:")
    for name in CATEGORIES:
        print("-", name)

    group = input("Gruppe eingeben: ").strip()
    if group not in CATEGORIES:
        raise ValueError(f"Unbekannte Gruppe: {group}")

    qty = input("Wie viele Dateien pro Muster erstellen? [1]: ").strip()
    count = int(qty) if qty else 1
    create_empty_files(CATEGORIES[group], count)