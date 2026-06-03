#!/usr/bin/env python3
"""Smart File Organizer - Automatically organizes files by type, date, and content patterns."""
import os
import shutil
import hashlib
from datetime import datetime
from pathlib import Path
from collections import defaultdict

EXTENSION_MAP = {
    'images': {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.webp', '.ico', '.tiff', '.heic'},
    'documents': {'.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.txt', '.md', '.csv', '.json', '.xml', '.yaml', '.yml', '.log'},
    'audio': {'.mp3', '.wav', '.flac', '.aac', '.ogg', '.wma', '.m4a'},
    'video': {'.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm'},
    'archives': {'.zip', '.rar', '.7z', '.tar', '.gz', '.bz2', '.xz'},
    'code': {'.py', '.js', '.ts', '.html', '.css', '.scss', '.cpp', '.c', '.h', '.java', '.go', '.rs', '.rb', '.php', '.sql', '.sh', '.bat', '.ps1'},
    'fonts': {'.ttf', '.otf', '.woff', '.woff2', '.eot'},
    'executables': {'.exe', '.msi', '.dmg', '.appimage', '.deb', '.rpm'},
    'spreadsheets': {'.xls', '.xlsx', '.ods', '.numbers'},
    'ebooks': {'.epub', '.mobi', '.azw3', '.djvu'},
    'cad': {'.stl', '.step', '.iges', '.dwg', '.dxf'},
}


def get_category(ext: str) -> str:
    ext = ext.lower()
    for category, extensions in EXTENSION_MAP.items():
        if ext in extensions:
            return category
    return 'other'


def file_age_days(path: Path) -> int:
    mtime = datetime.fromtimestamp(path.stat().st_mtime)
    return (datetime.now() - mtime).days


def organize_by_type(directory: str, dry_run: bool = False) -> dict:
    """Organize files into category folders based on extension."""
    path = Path(directory)
    if not path.exists():
        return {'error': f'Directory not found: {directory}'}

    moved = defaultdict(list)
    for item in path.iterdir():
        if item.is_file() and not item.name.startswith('.'):
            category = get_category(item.suffix)
            dest_dir = path / category
            dest_dir.mkdir(exist_ok=True)
            dest = dest_dir / item.name

            counter = 1
            while dest.exists():
                dest = dest_dir / f"{item.stem}_{counter}{item.suffix}"
                counter += 1

            if not dry_run:
                shutil.move(str(item), str(dest))
            moved[category].append({'from': item.name, 'to': dest.name})

    return {'categories': len(moved), 'files': sum(len(v) for v in moved.values()),
            'details': dict(moved)}


def organize_by_date(directory: str, dry_run: bool = False) -> dict:
    """Organize files into year/month folders based on modification date."""
    path = Path(directory)
    if not path.exists():
        return {'error': f'Directory not found: {directory}'}

    moved = []
    for item in path.iterdir():
        if item.is_file() and not item.name.startswith('.'):
            mtime = datetime.fromtimestamp(item.stat().st_mtime)
            dest_dir = path / str(mtime.year) / f"{mtime.month:02d}"
            dest_dir.mkdir(parents=True, exist_ok=True)
            dest = dest_dir / item.name

            counter = 1
            while dest.exists():
                dest = dest_dir / f"{item.stem}_{counter}{item.suffix}"
                counter += 1

            if not dry_run:
                shutil.move(str(item), str(dest))
            moved.append({'from': item.name, 'to': str(dest.relative_to(path))})

    return {'files_moved': len(moved), 'details': moved}


def find_duplicates(directory: str) -> dict:
    """Find duplicate files by content hash."""
    path = Path(directory)
    hashes = defaultdict(list)

    for item in path.rglob('*'):
        if item.is_file():
            try:
                with open(item, 'rb') as f:
                    file_hash = hashlib.md5(f.read()).hexdigest()
                hashes[file_hash].append(str(item.relative_to(path)))
            except (OSError, PermissionError):
                continue

    duplicates = {h: files for h, files in hashes.items() if len(files) > 1}
    return {
        'duplicate_groups': len(duplicates),
        'wasted_files': sum(len(v) - 1 for v in duplicates.values()),
        'details': duplicates
    }


def clean_empty_dirs(directory: str, dry_run: bool = False) -> dict:
    """Remove empty directories recursively."""
    path = Path(directory)
    removed = []

    for item in sorted(path.rglob('*'), key=lambda p: len(str(p)), reverse=True):
        if item.is_dir() and not any(item.iterdir()):
            if not dry_run:
                item.rmdir()
            removed.append(str(item.relative_to(path)))

    return {'removed': len(removed), 'directories': removed}


def bulk_rename(directory: str, pattern: str, start_num: int = 1,
                padding: int = 3, dry_run: bool = False) -> dict:
    """Bulk rename files with a pattern. Use {num} and {ext} as placeholders."""
    path = Path(directory)
    files = sorted([f for f in path.iterdir() if f.is_file() and not f.name.startswith('.')])
    renamed = []

    for i, file in enumerate(files, start=start_num):
        ext = file.suffix
        new_name = pattern.replace('{num}', str(i).zfill(padding)).replace('{ext}', ext)
        dest = path / new_name

        counter = 1
        while dest.exists() and dest != file:
            base = new_name.rsplit(ext, 1)[0] if ext else new_name
            dest = path / f"{base}_{counter}{ext}"
            counter += 1

        if not dry_run:
            shutil.move(str(file), str(dest))
        renamed.append({'from': file.name, 'to': new_name})

    return {'files_renamed': len(renamed), 'details': renamed}


def directory_tree(directory: str, max_depth: int = 3, exclude: list = None) -> str:
    """Generate a visual directory tree."""
    if exclude is None:
        exclude = ['.git', '__pycache__', 'node_modules', '.venv', 'venv']

    path = Path(directory)
    if not path.exists():
        return 'Directory not found.'

    lines = [f"\n{path.name}/"]

    def _walk(current: Path, prefix: str = '', depth: int = 0):
        if depth >= max_depth:
            lines.append(f"{prefix}...")
            return
        try:
            entries = sorted(current.iterdir(), key=lambda e: (e.is_file(), e.name.lower()))
            entries = [e for e in entries if e.name not in exclude and not e.name.startswith('.')]
        except PermissionError:
            return

        for i, entry in enumerate(entries):
            is_last = i == len(entries) - 1
            connector = '└── ' if is_last else '├── '
            lines.append(f"{prefix}{connector}{entry.name}")
            if entry.is_dir():
                extension = '    ' if is_last else '│   '
                _walk(entry, prefix + extension, depth + 1)

    _walk(path)
    return '\n'.join(lines)
