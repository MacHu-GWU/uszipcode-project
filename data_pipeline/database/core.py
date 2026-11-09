# -*- coding: utf-8 -*-

"""
Building blocks of the crawler registry. Nothing in this module does I/O.

- :class:`Field`: one column of the final database, and how to read it from a
  row of its source. Each Field lives in its own module in ``fields/``.
- :class:`Download`: one file a crawler fetches, optionally with a :class:`Secret`.
- :class:`Crawler`: one data source: its name, the Fields it claims, its downloads
  and a pure ``parse()`` function that turns the downloaded files into source rows.
- :class:`Paths`: where caches, crawler outputs and databases live.
- the errors raised by the pipeline, each with the exit code the CLI returns.
"""

import dataclasses
import os
import typing

#: SQLite column type for each allowed Field dtype
SQL_TYPES = {int: "INTEGER", float: "REAL", str: "TEXT"}

#: one source row: {column of the source: raw value}. The source's own names, untouched.
SourceRow = typing.Mapping[str, typing.Any]


@dataclasses.dataclass(frozen=True)
class Field:
    """
    One column of the database. ``extract`` reads the value from a source row
    (None means no value). ``examples`` are ``(source row, expected value)`` pairs,
    run by the tests, so a module also shows what its source looks like.

    A derived Field names its ``inputs``: other Fields, earlier in the catalog. No
    crawler claims it; ``build`` computes it after the join, and its source row is
    ``{input: value}`` of the same PK.
    """

    name: str
    dtype: type  # int | float | str
    description: str
    unit: str = ""
    extract: typing.Optional[typing.Callable[[SourceRow], typing.Any]] = None
    examples: typing.Tuple[typing.Tuple[dict, typing.Any], ...] = ()
    inputs: typing.Tuple[str, ...] = ()


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


#: what ``Crawler.parse`` yields: (key in the source, source row)
Row = typing.Tuple[str, SourceRow]


@dataclasses.dataclass(frozen=True)
class Crawler:
    """
    One data source.

    ``parse`` receives ``{filename: local path}`` for every declared download and
    yields :data:`Row`. It never sees the PK set and never opens a URL: the
    framework downloads the files, once, before ``parse`` runs. It does not know
    the Fields either: each claimed Field reads its value from the source row.

    A history crawler (``history=True``) fills the history table, keyed by
    (zipcode, year): each source row has a ``year`` column, and it claims Fields of
    ``HISTORY_FIELDS`` instead of ``FIELDS``.
    """

    name: str  # kebab-case; the mise task is crawler-<name>
    fields: typing.Tuple[str, ...]  # the Fields this crawler claims, in output order
    downloads: typing.Tuple[Download, ...]
    parse: typing.Callable[[typing.Dict[str, str]], typing.Iterable[Row]]
    description: str = ""
    history: bool = False


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


def census_int(value) -> typing.Optional[int]:
    """Like ``parse_int``, but the Census "not available" codes (negative, e.g. -666666666) are None."""
    number = parse_int(value)
    return None if number is None or number < 0 else number


def census_float(value) -> typing.Optional[float]:
    """Like ``parse_float``, but the Census "not available" codes (negative, e.g. -666666666) are None."""
    number = parse_float(value)
    return None if number is None or number < 0 else number


def upper_text(value: str) -> str:
    return value.strip().upper()


def column(name: str, convert: typing.Optional[typing.Callable] = None):
    """An ``extract`` function: one source column. A missing column is an error: the source changed."""
    def extract(row: SourceRow):
        return convert(row[name]) if convert else row[name]
    return extract


def field_names(*modules) -> typing.Tuple[str, ...]:
    """The names of the Fields of these ``fields/`` modules: what a crawler claims."""
    return tuple(field.name for module in modules for field in module.FIELDS)


def total(*names: str, convert: typing.Callable = parse_int):
    """An ``extract`` function: the sum of several source columns; None if one of them is blank."""
    def extract(row: SourceRow):
        values = [convert(row[name]) for name in names]
        return None if any(v is None for v in values) else sum(values)
    return extract


def field_group(prefix: str, source: str, unit: str,
                buckets: typing.Sequence[typing.Tuple[str, str, typing.Sequence[str]]],
                convert: typing.Callable = parse_int) -> typing.Tuple[Field, ...]:
    """
    The Fields of one distribution, one column per bucket ``(name, label, source columns)``.
    Each Field is named ``<prefix>_<name>`` and is the sum of its source columns;
    ``source`` names the table in the descriptions.
    """
    return tuple(
        Field(
            name="%s_%s" % (prefix, name),
            dtype=int,
            description="%s; %s (%s)" % (label, source, " + ".join(columns)),
            unit=unit,
            extract=total(*columns, convert=convert),
            examples=(({c: "2" for c in columns}, 2 * len(columns)), ({c: None for c in columns}, None)),
        )
        for name, label, columns in buckets
    )


def ratio(numerator: str, denominator: str, scale: float = 1, convert: typing.Callable = parse_float,
          whole: bool = False):
    """
    An ``extract`` function: ``scale * numerator / denominator`` of two source columns; None if one
    is blank or the denominator is 0. ``whole`` rounds the result to an int.
    """
    def extract(row: SourceRow):
        top, bottom = convert(row[numerator]), convert(row[denominator])
        if top is None or not bottom:
            return None
        value = scale * top / bottom
        return int(round(value)) if whole else value
    return extract


def share_and_average_group(prefix: str, source: str, total: str, amount_scale: float,
                            buckets: typing.Sequence[typing.Tuple[str, str, str, str]]) -> typing.Tuple[Field, ...]:
    """
    Two Fields per bucket ``(name, label, count column, amount column)``, for sources that give a count
    and an amount per category: ``<prefix>_<name>_share`` = count / ``total`` and
    ``<prefix>_<name>_average`` = amount x ``amount_scale`` / count, in whole units.
    """
    fields = []
    for name, label, count, amount in buckets:
        fields.append(Field(
            name="%s_%s_share" % (prefix, name),
            dtype=float,
            description="Share with %s, 0 to 1; %s (%s / %s)" % (label, source, count, total),
            unit="share",
            extract=ratio(count, total),
            examples=(({count: "30", total: "120"}, 0.25), ({count: "0", total: "0"}, None)),
        ))
        fields.append(Field(
            name="%s_%s_average" % (prefix, name),
            dtype=int,
            description="Average %s among those with it; %s (%s x %g / %s)" % (label, source, amount, amount_scale, count),
            unit="dollars",
            extract=ratio(amount, count, scale=amount_scale, whole=True),
            examples=(({amount: "37601", count: "870"}, int(round(37601 * amount_scale / 870))),
                      ({amount: "0", count: "0"}, None)),
        ))
    return tuple(fields)


def first_value(*names: str, convert: typing.Optional[typing.Callable] = None):
    """An ``extract`` function for a fallback: the first non-blank value among these columns."""
    def extract(row: SourceRow):
        for name in names:
            value = row.get(name)
            if value is not None and not (isinstance(value, str) and not value.strip()):
                return convert(value) if convert else value
        return None
    return extract
