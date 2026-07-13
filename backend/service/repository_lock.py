from __future__ import annotations

import fcntl
import threading
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator, TextIO


class RepositoryWriteLock:
    """Serialise writes across threads and backend worker processes."""

    def __init__(self, repo: Path) -> None:
        self._path = repo.resolve() / ".knowledge-write.lock"
        self._thread_lock = threading.RLock()

    @contextmanager
    def acquire(self) -> Iterator[None]:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with self._thread_lock:
            handle: TextIO
            with self._path.open("a+", encoding="utf-8") as handle:
                fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
                try:
                    yield
                finally:
                    fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
