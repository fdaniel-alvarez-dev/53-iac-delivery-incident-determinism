from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class TextFile:
    path: Path
    relpath: str
    text: str


def load_text_files(root: Path, *, extensions: set[str]) -> list[TextFile]:
    root = root.resolve()
    files: list[TextFile] = []
    for p in sorted(root.rglob("*")):
        if not p.is_file():
            continue
        if p.suffix.lower() not in extensions and p.name not in extensions:
            continue
        try:
            text = p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        rel = str(p.relative_to(root))
        files.append(TextFile(path=p, relpath=rel, text=text))
    return files


def file_exists(root: Path, relative: str) -> bool:
    try:
        return (root / relative).is_file()
    except OSError:
        return False

