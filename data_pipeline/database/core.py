# -*- coding: utf-8 -*-

"""
Building blocks of the crawler registry. Nothing in this module does I/O.

- :class:`Field`: one column of the final database.
- :class:`Download`: one file a crawler fetches, optionally with a :class:`Secret`.
- :class:`Crawler`: one data source: its name, the Fields it claims, its downloads
  and a pure ``parse()`` function that reads the downloaded files.
- :class:`Paths`: where caches, crawler outputs and databases live.
- the errors raised by the pipeline, each with the exit code the CLI returns.
"""

import dataclasses
import os
import typing

#: SQLite column type for each allowed Field dtype
SQL_TYPES = {int: "INTEGER", float: "REAL", str: "TEXT"}


@dataclasses.dataclass(frozen=True)
class Field:
    """One column of the database. ``FIELDS`` in ``fields.py`` lists all of them."""

    name: str
    dtype: type  # int | float | str
    description: str
    unit: str = ""


@dataclasses.dataclass(frozen=True)
class Secret:
    """An API key or token: read from an environment variable, else from a file in the home folder."""

    env: str  # e.g. "CENSUS_API_KEY"
    file: str  # e.g. "~/.census_key"
    signup_url: str
    query_param: str = ""  # sent as ?<query_param>=<secret>, or
    bearer: bool = False  # sent as "Authorization: Bearer <secret>"


@dataclasses.dataclass(frozen=True)
class Download:
    """One file a crawler downloads. The URL is public and never holds a secret."""

    filename: str  # cached as .cache/crawlers/<crawler>/<filename>
    url: str
    magic: bytes = b""  # required first bytes, so an HTML error page is never cached
    secret: typing.Optional[Secret] = None


#: what ``Crawler.parse`` yields: (key in the source, {field name: value or None})
Row = typing.Tuple[str, typing.Dict[str, typing.Any]]


@dataclasses.dataclass(frozen=True)
class Crawler:
    """
    One data source.

    ``parse`` receives ``{filename: local path}`` for every declared download and
    yields :data:`Row`. It never sees the PK set and never opens a URL: the
    framework downloads the files, once, before ``parse`` runs.
    """

    name: str  # kebab-case; the mise task is crawler-<name>
    fields: typing.Tuple[str, ...]  # the Fields this crawler claims, in output order
    downloads: typing.Tuple[Download, ...]
    parse: typing.Callable[[typing.Dict[str, str]], typing.Iterable[Row]]
    description: str = ""


@dataclasses.dataclass(frozen=True)
class Paths:
    cache_dir: str  # raw downloads + manifest.json, one folder per crawler
    crawler_out_dir: str  # <crawler>.csv and <crawler>.json
    db_out_dir: str  # db_<pkset>.sqlite / .csv / _coverage.json
    universe_csv: str  # the full PK set (output of zipcode_universe)
    mise_toml: str

    @classmethod
    def default(cls) -> "Paths":
        """The folders of the repository (see data_pipeline/database/README.md)."""
        pipeline = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        return cls(
            cache_dir=os.path.join(pipeline, ".cache", "crawlers"),
            crawler_out_dir=os.path.join(pipeline, "output", "crawlers"),
            db_out_dir=os.path.join(pipeline, "output"),
            universe_csv=os.path.join(pipeline, "output", "zipcode_universe.csv"),
            mise_toml=os.path.join(os.path.dirname(pipeline), "mise.toml"),
        )

    @classmethod
    def under(cls, root: str) -> "Paths":
        """Everything inside ``root`` (used by the tests)."""
        return cls(
            cache_dir=os.path.join(root, ".cache", "crawlers"),
            crawler_out_dir=os.path.join(root, "output", "crawlers"),
            db_out_dir=os.path.join(root, "output"),
            universe_csv=os.path.join(root, "output", "zipcode_universe.csv"),
            mise_toml=os.path.join(root, "mise.toml"),
        )


# ------------------------------------------------------------------------------------------- errors
class PipelineError(Exception):
    """An expected failure: the CLI prints the message (no traceback) and exits with ``exit_code``."""

    exit_code = 1


class RegistryError(PipelineError):
    exit_code = 2

    def __init__(self, problems: typing.List[str]):
        self.problems = list(problems)
        super().__init__(format_problems("registry check failed", self.problems))


class ContractError(PipelineError):
    exit_code = 2


class PkSetError(PipelineError):
    exit_code = 2


class DownloadError(PipelineError):
    exit_code = 1


def format_problems(title: str, problems: typing.List[str], limit: int = 0) -> str:
    """``title: N problem(s)`` followed by numbered lines; continuation lines are indented."""
    shown = problems if not limit else problems[:limit]
    lines = ["%s: %d problem(s)" % (title, len(problems))]
    for i, p in enumerate(shown, start=1):
        first, *rest = p.split("\n")
        lines.append("  %d. %s" % (i, first))
        lines.extend("       " + r for r in rest)
    if limit and len(problems) > limit:
        lines.append("  ... and %d more" % (len(problems) - limit))
    return "\n".join(lines)


# ------------------------------------------------------------------------------------ value parsing
def parse_int(value) -> typing.Optional[int]:
    """``None`` / blank -> None, else ``int(value)`` (sources often send numbers as text)."""
    if value is None or (isinstance(value, str) and not value.strip()):
        return None
    return int(value)


def parse_float(value) -> typing.Optional[float]:
    """``None`` / blank -> None, else ``float(value)``."""
    if value is None or (isinstance(value, str) and not value.strip()):
        return None
    return float(value)
