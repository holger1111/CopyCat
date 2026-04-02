import argparse
import re
import xml.etree.ElementTree as ET
import shutil
from pathlib import Path
import struct
import sys

from datetime import datetime

def parse_arguments():
    parser = argparse.ArgumentParser(description="CopyCat: Kombiniert Dateien zu Textdatei")
    parser.add_argument("--input", "-i", default=None, help="Eingabeordner (default: Skriptordner)")
    parser.add_argument("--output", "-o", default=None, help="Ausgabeordner (default: Eingabeordner)")
    parser.add_argument("--types", "-t", nargs="*", default=["all"], 
                        help="Dateitypen: java, py, spec, img, audio, drawio (oder 'all')")
    return parser.parse_args()

def get_next_serial_number(base_path: Path) -> int:
    existing = list(base_path.glob("combined_copycat*.txt"))
    max_num = 0
    for p in existing:
        if "_" in p.stem:
            try:
                num = int(p.stem.split("_")[-1])
                max_num = max(max_num, num)
            except ValueError:
                pass
    return max_num + 1

def move_to_archive(base_path: Path, filename: str):
    archive_path = base_path / "CopyCat_Archive"
    archive_path.mkdir(exist_ok=True)
    old_file = base_path / filename
    if old_file.exists():
        shutil.move(old_file, archive_path / filename)

def list_binary_file(writer, bin_file):
    try:
        size = bin_file.stat().st_size
        if size == 0:
            writer.write(f"[EMPTY: {bin_file.name}]\n")
            return
        
        with open(bin_file, "rb") as f:
            data = f.read(1024)  # Nur Header für Metadaten
        suffix = bin_file.suffix.lower()
        mime_types = {
            '.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.gif': 'image/gif',
            '.bmp': 'image/bmp', '.webp': 'image/webp', '.wav': 'audio/wav', '.mp3': 'audio/mpeg',
            '.ogg': 'audio/ogg', '.m4a': 'audio/mp4', '.flac': 'audio/flac', '.json': 'application/json',
            '.sql': 'text/sql', '.yaml': 'text/yaml', 'xml': 'text/xml', '.html': 'text/html',
            '.css': 'text/css', '.md': 'text/markdown', '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        }
        mime = mime_types.get(suffix, 'application/octet-stream')
        duration = "N/A"
        if suffix == '.wav' and size > 44:
            frames = struct.unpack("<I", data[4:8])[0]
            rate = struct.unpack("<I", data[24:28])[0]
            duration = f"{frames / rate:.2f}s"
        
        writer.write(f"[BINARY: {bin_file.name}] [MIME: {mime}] [SIZE: {size} bytes]")
        if 'audio' in mime:
            writer.write(f" [DUR: {duration}]\n")
        else:
            writer.write("\n")
    except Exception:
        writer.write(f"[ERROR: {bin_file.name}]\n")

def extract_drawio(writer, drawio_file):
    """VOLLSTÄNDIGE Extraktion: ALLE Elemente, Attribute, Positionen, Styles"""
    try:
        tree = ET.parse(drawio_file)
        root = tree.getroot()
        
        writer.write(f"\n{'='*80}\n")
        writer.write(f"VOLLSTÄNDIGES DIAGRAMM: {drawio_file.name}\n")
        writer.write(f"Root: name='{root.get('name', 'N/A')}', id='{root.get('id', 'N/A')}'\n")
        writer.write(f"{'='*80}\n")
        
        mx_models = root.findall(".//mxGraphModel")
        for model_idx, model in enumerate(mx_models, 1):
            writer.write(f"\nMODEL {model_idx}: dx={model.get('dx')}, dy={model.get('dy')}\n")
            writer.write("-" * 50 + "\n")
            
            # ALLE Cells
            cells = model.findall(".//mxCell")
            for cell_idx, cell in enumerate(cells, 1):
                cell_id = cell.get('id', 'N/A')
                value = cell.get('value', '').strip()
                style = cell.get('style', 'N/A')[:200] + "..." if len(cell.get('style', '')) > 200 else cell.get('style', 'N/A')
                vertex = cell.get('vertex', 'N/A')
                
                # Geometrie extrahieren
                geom = cell.find(".//mxGeometry")
                geom_info = ""
                if geom is not None:
                    x, y, width, height = geom.get('x', ''), geom.get('y', ''), geom.get('width', ''), geom.get('height', '')
                    geom_info = f"x={x},y={y},w={width},h={height}"
                
                writer.write(f"  CELL {cell_idx:3d} [ID={cell_id}] vertex={vertex}\n")
                writer.write(f"    TEXT: '{value}'\n")
                writer.write(f"    STYLE: {style}\n")
                writer.write(f"    GEOM:  {geom_info}\n")
                
                # Source/Target für Verbindungen
                source = cell.get('source', 'N/A')
                target = cell.get('target', 'N/A')
                if source != 'N/A' or target != 'N/A':
                    writer.write(f"    CONN:  source={source}, target={target}\n")
                
                writer.write("\n")
        
        # Statistik
        all_texts = [cell.get("value", "") for model in mx_models 
                    for cell in model.findall(".//mxCell[@value]") if cell.get("value")]
        unique_texts = list(set(t.strip() for t in all_texts if t.strip()))
        writer.write(f"\nSTATISTIK:\n")
        writer.write(f"  Gesamt Cells: {len([c for m in mx_models for c in m.findall('.//mxCell')])}\n")
        writer.write(f"  Text-Elemente: {len(all_texts)}\n")
        writer.write(f"  Unique Texte: {len(unique_texts)}\n")
        
    except Exception as e:
        writer.write(f"DIAGRAMM ERROR: {drawio_file.name} - {str(e)}\n")

# Übersicht - Singular/Plural korrekt
def get_plural(count):
    return "Datei" if count == 1 else "Dateien"

def run_copycat(args):
    script_file = Path(__file__).resolve()
    script_dir = Path(__file__).parent
    input_dir = Path(args.input or str(script_dir))
    output_dir = Path(args.output or str(input_dir))
    output_dir.mkdir(exist_ok=True)
    
    if not input_dir.is_dir():
        print(f"Fehler: {input_dir} ist kein Ordner")
        return
    
    types = args.types[0] if args.types else "all"
    # type_filters = {
    #     'code': ['*.java', '*.py', '*.spec'],
    #     'img': ['*.png', '*.jpg', '*.jpeg', '*.gif', '*.bmp', '*.webp'],
    #     'audio': ['*.mp3', '*.wav', '*.ogg', '*.m4a', '*.flac'],
    #     'drawio': ['*.drawio', '*.drawio.png', '*.dia', '*.svg']
    # }
    type_filters = {
    'code': ['*.java', '*.py', '*.spec'],
    'web': ['*.html','*.css','*.js','*.ts'],
    'db': ['*.sql', '*.db', '*.sqlite'], 
    'config': ['*.json', '*.yaml', '*.xml', '*.properties'], # '*.xlsx',
    'docs': ['*.md', '*.txt', '*.log', '*.docx'],
    'deps': ['requirements.txt', 'package.json', 'pom.xml'],
    'img': ['*.png', '*.jpg', '*.gif', '*.bmp', '*.webp', '*.svg', '*.ico'],
    'audio': ['*.mp3', '*.wav', '*.ogg', '*.m4a', '*.flac'],
    'diagram': ['*.drawio', '*.svg', '*.dia', '*.puml']
    }
    files = {k: [] for k in type_filters}
    
    # Sammle Dateien
    for t, patterns in type_filters.items():
        if types == "all" or t in args.types:
            for pat in patterns:
                candidates = input_dir.glob(pat)
                for candidate in candidates:
                    if candidate.resolve() != script_file and "combined_copycat" not in candidate.name:
                        files[t].append(candidate)

    # Serial & Archiv
    serial = get_next_serial_number(output_dir)
    basename = "combined_copycat"
    new_file = output_dir / f"{basename}_{serial}.txt"
    if serial > 1:
        move_to_archive(output_dir, f"{basename}_{serial-1}.txt")
    
    # Übersicht
    with open(new_file, 'w', encoding='utf-8') as writer:
        writer.write("="*60 + f"\nCopyCat v2.1 | {datetime.now().strftime('%d.%m.%Y %H:%M')}\n{input_dir}\n\n")
        total_files = sum(len(files[t]) for t in files)
        writer.write(f"Gesamt: {total_files} {get_plural(total_files)}\nSerial #{serial}\n" + "="*60 + "\n")
        
        for t, flist in files.items():
            if flist:
                count = len(flist)
                writer.write(f"{t.upper()}: {count} {get_plural(count)}\n")
        
        writer.write("\n")
        
        # Codeinhalte
        if types == "all" or 'code' in args.types:
            writer.write("CODE-Details:\n")
            for code_file in files['code']:
                lines = sum(1 for line in open(code_file) if line.strip())
                writer.write(f"  {code_file.name}: {lines} Zeilen\n")
                writer.write(f"----- {code_file.name} -----\n")
                try:
                    with open(code_file, 'r', encoding='utf-8') as f:
                        writer.writelines(f.readlines())
                except UnicodeDecodeError:
                    writer.write("(Binary oder ungültiges Encoding - übersprungen)\n")
                writer.write("\n\n")
        
        # Binärdateien
        for t in ['code','web','db','config','docs','img','audio','diagram']:
            if files[t]:
                writer.write(f"\n{'='*20} {t.upper()} {'='*20}\n")
                for bfile in files[t]:
                    if t == 'diagram' and bfile.suffix.lower() in ['.drawio', '.dia']:
                        extract_drawio(writer, bfile)
                    else:
                        list_binary_file(writer, bfile)
    
    print(f"Erstellt: {new_file}")

if __name__ == "__main__":
    args = parse_arguments()
    run_copycat(args)