from __future__ import annotations

import os
from pathlib import Path


def writable_target(path: Path) -> bool:
    if path.exists():
        return (path.is_file() or path.is_dir()) and os.access(path, os.W_OK)
    candidate = path.parent
    while not candidate.exists() and candidate != candidate.parent:
        candidate = candidate.parent
    return candidate.is_dir() and os.access(candidate, os.W_OK)
