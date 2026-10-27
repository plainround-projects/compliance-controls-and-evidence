"""The control matrix and its companions, read from TOML files under `controls/`."""

from __future__ import annotations

import tomllib
from datetime import date
from pathlib import Path
from typing import Any

from notes_evidence.domain.controls import FRAMEWORKS, KINDS, Control, EvidenceSpec, Gap, RecordedException
from notes_evidence.domain.review import Decision, Person, ReviewRequest


class CatalogError(ValueError):
    """A controls file is missing a field or holds an unknown value."""


def _load(path: Path) -> dict[str, Any]:
    try:
        return tomllib.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise CatalogError(f"{path} does not exist") from None
    except tomllib.TOMLDecodeError as problem:
        raise CatalogError(f"{path} is not valid TOML: {problem}") from None


def _date(raw: object) -> date | None:
    return raw if isinstance(raw, date) else None


class TomlCatalog:
    """Reads `controls.toml`, `exceptions.toml`, `gaps.toml`, `people.toml` and `access-review.toml` from one folder."""

    def __init__(self, controls_file: Path) -> None:
        self._dir = controls_file.parent
        self._controls_file = controls_file

    def controls(self) -> list[Control]:
        """The controls with their evidence specs; an unknown evidence kind is an error."""
        found: list[Control] = []
        for item in _load(self._controls_file).get("control", []):
            try:
                specs = tuple(
                    EvidenceSpec(e["file"], e["kind"], e["proves"], e["period"], int(e["refresh_days"]), e["refreshed"])
                    for e in item.get("evidence", [])
                )
                if bad := [spec.kind for spec in specs if spec.kind not in KINDS]:
                    raise CatalogError(f"{item['id']}: unknown evidence kind {bad[0]!r}")
                found.append(
                    Control(
                        item["id"],
                        item["name"],
                        item["requires"],
                        item["where"],
                        {name: tuple(item.get(name, ())) for name in FRAMEWORKS},
                        specs,
                    )
                )
            except KeyError as missing:
                raise CatalogError(f"{self._controls_file}: control is missing {missing}") from None
        return found

    def exceptions(self) -> list[RecordedException]:
        """Known deviations from `exceptions.toml`."""
        return [
            RecordedException(e["id"], e["control"], e.get("change"), e["description"], e.get("followup", ""))
            for e in _load(self._dir / "exceptions.toml").get("exception", [])
        ]

    def gaps(self) -> list[Gap]:
        """Tracked gaps from `gaps.toml`."""
        return [
            Gap(g["control"], g.get("reason", ""), g.get("ticket", ""), _date(g.get("due")))
            for g in _load(self._dir / "gaps.toml").get("gap", [])
        ]

    def people(self) -> dict[str, Person]:
        """People and the principal names they hold, from `people.toml`."""
        people: dict[str, Person] = {}
        for item in _load(self._dir / "people.toml").get("person", []):
            person = Person(item["name"], item["title"], _date(item.get("left_on")))
            for principal in item.get("principals", [item["name"]]):
                people[principal] = person
        return people

    def review_request(self) -> ReviewRequest:
        """The reviewer's decisions from `access-review.toml`."""
        data = _load(self._dir / "access-review.toml")
        review = data.get("review", {})
        try:
            return ReviewRequest(
                review["reviewer"],
                review["reviewed_on"],
                review["ticket"],
                tuple(
                    Decision(d["system"], d["principal"], bool(d["keep"]), d.get("reason", ""))
                    for d in data.get("decision", [])
                ),
            )
        except KeyError as missing:
            raise CatalogError(f"access-review.toml is missing {missing}") from None
