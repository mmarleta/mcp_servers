from __future__ import annotations

import hashlib
import threading
import time
from pathlib import Path
from typing import Callable, Iterable, List

from .indexer import Indexer
from .utils import iter_files_by_glob


class AutoIndexer:
    """
    Lightweight polling-based auto indexer. It periodically computes a digest of
    the relevant files (policy.yaml + compose files + docs) and triggers a refresh
    callback when a change is detected. No external deps required.
    """

    def __init__(self, indexer: Indexer, on_refresh: Callable[[], None], interval_sec: float = 1.0) -> None:
        self.indexer = indexer
        self.on_refresh = on_refresh
        self.interval_sec = max(0.2, float(interval_sec))
        self._thread: threading.Thread | None = None
        self._stop = threading.Event()
        self._last_digest: str = ""

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, name="auto-indexer", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)

    # --- internals ---
    def _run(self) -> None:
        # Initialize digest so we don't refresh immediately at startup if not needed
        self._last_digest = self._compute_digest()
        while not self._stop.is_set():
            try:
                cur = self._compute_digest()
                if cur != self._last_digest:
                    # Change detected: refresh and update digest
                    self.on_refresh()
                    self._last_digest = cur
            except Exception:
                # Swallow exceptions to keep the thread alive
                pass
            finally:
                self._stop.wait(self.interval_sec)

    def _compute_digest(self) -> str:
        paths = list(self._watched_files())
        h = hashlib.sha256()
        for p in sorted(paths):
            try:
                data = Path(p).read_bytes()
                h.update(len(data).to_bytes(8, "little"))
                h.update(data)
            except FileNotFoundError:
                h.update(b"<missing>")
            except IsADirectoryError:
                # Should not happen since we only pass files
                continue
        return h.hexdigest()

    def _watched_files(self) -> Iterable[str]:
        # Always include policy.yaml
        repo = self.indexer.repo_root
        policy_path = repo / "mcp_servers/optimus_project_mcp/policy.yaml"
        yield str(policy_path)

        # Compose + docs from current policy model
        pol = self.indexer.get_policy() or {}
        for spec in (pol.get("compose_files") or []):
            if any(ch in spec for ch in ["*", "?", "["]):
                for p in iter_files_by_glob(spec):
                    if p.is_file():
                        yield str(p.resolve())
            else:
                yield str((repo / spec).resolve())
        for rel in (pol.get("docs_files") or []):
            yield str((repo / rel).resolve())
            
        # 🚀 AUTO-REFRESH ENHANCEMENT: Monitor code files for search functionality
        # This ensures that search results stay up-to-date when code changes
        code_patterns = [
            "**/*.py",      # Python files
            "**/*.js",      # JavaScript files
            "**/*.ts",      # TypeScript files
            "**/*.md",      # Markdown files
            "**/*.yml",     # YAML files
            "**/*.yaml",    # YAML files
            "**/*.json",    # JSON files
        ]
        
        # Monitor key directories that users frequently search
        key_directories = [
            "ai-engine/src",
            "backend-orchestrator/src", 
            "frontend/static",
            "memory-engine/src",
            "rules-engine/src",
            "whatsapp-integration/src"
        ]
        
        for directory in key_directories:
            dir_path = repo / directory
            if dir_path.exists():
                for pattern in code_patterns:
                    try:
                        for p in dir_path.glob(pattern):
                            if p.is_file() and not self._should_ignore_file(p):
                                yield str(p.resolve())
                    except (OSError, ValueError):
                        # Skip if glob pattern fails
                        continue
    
    def _should_ignore_file(self, path: Path) -> bool:
        """Ignore files that shouldn't trigger refresh (performance optimization)"""
        ignore_patterns = [
            ".git/",
            "node_modules/", 
            "__pycache__/",
            ".pytest_cache/",
            ".mypy_cache/",
            "venv/",
            ".venv/",
            "build/",
            "dist/",
            ".log",
            ".pyc",
            ".pyo"
        ]
        
        path_str = str(path)
        return any(pattern in path_str for pattern in ignore_patterns)
