"""The evidence folder on disk, with a manifest that records who produced each file, when, and its hash."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from notes_evidence.domain.evidence import ManifestEntry, digest

MANIFEST = "manifest.json"
_TIME = "%Y-%m-%dT%H:%M:%SZ"


class FileEvidenceStore:
    """Files under one folder. Names may not leave it."""

    def __init__(self, directory: Path) -> None:
        self._dir = directory.resolve()

    def _path(self, name: str) -> Path:
        path = (self._dir / name).resolve()
        if path.parent != self._dir:
            raise ValueError(f"evidence files live directly in {self._dir.name}: {name}")
        return path

    def write(self, name: str, text: str, control: str, produced_at: datetime, run_by: str, source: str) -> None:
        """Write the file and record it in the manifest (the index itself is recorded under control '-')."""
        self._dir.mkdir(parents=True, exist_ok=True)
        self._path(name).write_text(text, encoding="utf-8")
        entries = self._load()
        entries[name] = {
            "control": control,
            "produced_at": produced_at.astimezone(UTC).strftime(_TIME),
            "run_by": run_by,
            "source": source,
            "sha256": digest(text),
        }
        self._path(MANIFEST).write_text(json.dumps(entries, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    def read(self, name: str) -> str | None:
        """A file's text, or None when it does not exist."""
        path = self._path(name)
        return path.read_text(encoding="utf-8") if path.is_file() else None

    def read_all(self) -> dict[str, str]:
        """Every file in the folder."""
        if not self._dir.is_dir():
            return {}
        return {path.name: path.read_text(encoding="utf-8") for path in sorted(self._dir.iterdir()) if path.is_file()}

    def manifest(self) -> dict[str, ManifestEntry]:
        """The manifest entries by file name."""
        return {
            name: ManifestEntry(
                name,
                item["control"],
                datetime.strptime(item["produced_at"], _TIME).replace(tzinfo=UTC),
                item["run_by"],
                item["source"],
                item["sha256"],
            )
            for name, item in self._load().items()
        }

    def _load(self) -> dict[str, dict[str, str]]:
        path = self._path(MANIFEST)
        if not path.is_file():
            return {}
        loaded = json.loads(path.read_text(encoding="utf-8"))
        return {str(name): dict(item) for name, item in loaded.items()}
