# Database step: the crawler registry

Builds the 3.0 database from the outputs of named crawlers. Rows are PKs (ZIP codes), columns are
`zipcode` plus one column per Field, and NULL simply means "no value" (a PO box ZIP has no population).

## Layout

The functionality, the crawlers and the Fields are kept apart, so that new columns only add small
files and never touch the functionality. [`test_db_structure.py`](../tests/test_db_structure.py) fails
if a module crosses these lines.

| Where | What | Rule |
|---|---|---|
| `database/*.py` | **the functionality**: [`core`](core.py), [`checks`](checks.py), [`fetch`](fetch.py), [`crawl`](crawl.py), [`build`](build.py), [`cli`](cli.py) | knows no data source and no column; only `fetch.py` opens a URL |
| [`database/crawlers/`](crawlers) | **one module per data source**; [`__init__.py`](crawlers/__init__.py) holds `CRAWLERS`, the registry | downloads and parses; cannot open a URL, does not know how a Field is read |
| [`database/fields/`](fields) | **one module per Field**; [`__init__.py`](fields/__init__.py) holds `FIELDS`, the catalog | says what the column is and how to read it from a source row; imports only `core` |
| [`database/__main__.py`](__main__.py) | joins the three | the only place that does |

| Concept | Rule |
|---|---|
| **PK** | a 5-digit ZIP as text with leading zeros |
| **PK set** | the rows of one build: `demo` (3 ZIPs), `full` (every ZIP of [`zipcode_universe`](../zipcode_universe/README.md)) or a CSV file with a `zipcode` column |
| **Field** | one column: name, dtype (`int`/`float`/`str`), description, unit, `extract` and `examples`. The catalog's order is the column order |
| **Source row** | one row of a data source under its own column names, e.g. `{"P1_001N": "32612"}` |
| **Crawler** | a name, the Fields it claims, the files it downloads and a pure `parse()` that yields `(zipcode, source row)`. Every Field is claimed by exactly one crawler |

`crawl` runs one crawler: fetch (the only network step, cached), parse (offline), each claimed Field
reads its value from the source rows, check the output contract, write. `build` left-joins every crawler
output onto the PK set; it never downloads anything, so switching PK sets is free.

A Field module is this short ([`fields/population.py`](fields/population.py)):

```python
FIELDS = (
    Field(
        name="population",
        dtype=int,
        description="Total population of the ZCTA, 2020 Census DHC table P1 (P1_001N)",
        unit="people",
        extract=column("P1_001N", parse_int),
        examples=(({"P1_001N": "32612"}, 32612), ({"P1_001N": "0"}, 0), ({"P1_001N": None}, None)),
    ),
)
```

## Run

The tasks are in [`mise.toml`](../../mise.toml) at the repository root. It pins Python 3.12; the pipeline
needs 3.11 or newer (it reads `mise.toml` with `tomllib`) and only the standard library, plus `pytest`
for the tests. Once per clone:

```
mise trust
mise install
mise run pipeline-setup
```

| Command | What it does |
|---|---|
| `mise run pipeline-check` | checks the catalog, the claims and the tasks; prints the catalog |
| `mise run crawler-<name>` | runs one crawler, e.g. `mise run crawler-census-dhc` (cached download) |
| `mise run crawler-<name> -- --refresh` | downloads that crawler's files again (at most once per 24 h; add `--force` to override) |
| `mise run crawl-all` | runs every crawler, one after another, and stops at the first failure |
| `mise run pipeline-build` | builds the database for the demo PK set |
| `mise run pipeline-build -- --pk-set full` | builds it for all 42,730 ZIPs (or `--pk-set path/to/pks.csv`) |
| `mise run pipeline-test` | runs the offline tests (no network) |

Without mise, run the same commands with `python -m data_pipeline.database check | crawl NAME | crawl --all | build`
from the repository root. Exit codes: 0 success, 2 registry / contract / PK-set problems, 1 download
and file problems. Expected errors print one message without a traceback.

Two crawlers need a free key: `census-dhc` (<https://api.census.gov/data/key_signup.html>, read from
`$CENSUS_API_KEY` or `~/.census_key`) and `zip-basics` (<https://www.huduser.gov/hudapi/public/register>,
read from `$HUD_API_TOKEN` or `~/.hud_token`). A key is added to the request in memory only: it is never
written to the cache, the manifest, the outputs or an error message.

Files:

- `data_pipeline/.cache/crawlers/<name>/`: raw downloads and `manifest.json` (url, bytes, sha256, time); ignored by git
- `data_pipeline/output/crawlers/<name>.csv` and `.json`: one row per ZIP in the source; ignored by git
- `data_pipeline/output/db_<set>.sqlite` (table `zipcode_data`), `db_<set>.csv` and `db_<set>_coverage.json`;
  only `db_demo.csv` and `db_demo_coverage.json` are committed

## Crawlers

| Crawler | Source | Download | Fields |
|---|---|---|---|
| `census-gazetteer` | Census [2025 Gazetteer, ZCTA file](https://www2.census.gov/geo/docs/maps-data/data/gazetteer/2025_Gazetteer/2025_Gaz_zcta_national.zip) | 1 file, 0.9 MB, no key | `lat`, `lng` (ZCTA internal point), `land_area_in_sqmi` |
| `census-dhc` | 2020 Census DHC through the [Census Data API](https://api.census.gov/data/2020/dec/dhc.html) | 1 request for all ZCTAs, 0.8 MB, key | `population` (P1_001N), `housing_units` (H1_001N) |
| `zip-basics` | [HUD-USPS crosswalk](https://www.huduser.gov/portal/datasets/usps_crosswalk.html), Census ZBP, uszipcode 2.x | 3 files, 19 MB, token for HUD | `zipcode_type` (2.x only), `major_city`, `state` (HUD, else ZBP, else 2.x) |

The Census values are ZCTA values: a ZIP without a ZCTA (PO box, unique, military) gets NULL.

## Politeness

Enforced in [`fetch.py`](fetch.py), the only module that opens a URL; crawlers cannot change it.

- A crawler declares whole files (1 to 100 per crawler), never one request per ZIP.
- A cached file is reused: no request, and the key is not even read. A crawler downloads once.
- Downloads run one at a time, 2 s apart, with a User-Agent that names this project.
- Retries only on connection errors, timeouts, 429 and 5xx: 5 attempts, waits of 5, 15, 45 and 90 s
  (`Retry-After` is honoured up to 300 s). Any other 4xx fails at once.
- The body must start with the declared magic bytes (`PK\x03\x04` for a zip, `[[` for the Census API),
  so an HTML error page is never cached. A failed download keeps the previous file.
- `--refresh` is refused if the crawler downloaded less than 24 h ago (`--force` overrides). There is
  no loop, schedule or watch mode.

## Checks

`check`, `crawl` and `build` first run every registry check and report all problems at once, each
with how to fix it:

| IDs | Checks |
|---|---|
| F1-F7 | Field names are snake_case, `zipcode` is reserved, no duplicates, dtype is `int`/`float`/`str`, a description is given, an `extract` is given, the catalog fits SQLite's 2,000 columns |
| C1-C8 | crawler names are kebab-case and unique; a crawler claims Fields and declares 1 to 100 downloads; filenames are safe and unique; URLs are `https://` and hold no key; a Secret is well formed; no URL is downloaded by two crawlers |
| K1-K3 | every claim names a Field of the catalog (with "did you mean"), no Field is claimed twice, **no Field is left unclaimed** |
| M0-M2 | `mise.toml` is valid, every crawler has its `crawler-<name>` task (the check prints the block to add), no task points to a missing crawler |
| L1 | (`check` only) every module of `fields/` and `crawlers/` is listed in its package's `MODULES` |

Before anything is written, the values read from the source rows are checked against the output contract:

| ID | Rule |
|---|---|
| D1 | no ZIP appears twice (after normalizing, e.g. `501` -> `00501`) |
| D2 | a Field can read its value: a missing source column or a value that cannot be converted is an error |
| D3 | values match the dtype (int is not bool, a float Field accepts an int) |
| D4 | a claimed Field is not NULL in every row (the source probably changed its header) |
| D5 | at least one usable row |
| D6 | no NaN or infinity |

Keys that are not ZIPs (`00000`, text) are skipped and counted. On any error nothing is written and
the previous output stays. `build` also checks that each crawler output exists and matches the
crawler's current claims, and says which `mise run crawler-<name>` to run if not.

## Result (run of 2026-11-04)

`mise run crawl-all` makes 5 requests the first time and 0 after that. `mise run pipeline-build`
then writes [`db_demo.csv`](../output/db_demo.csv): 3 rows x 9 columns.

```
zipcode,zipcode_type,major_city,state,lat,lng,land_area_in_sqmi,population,housing_units
10001,STANDARD,NEW YORK,NY,40.750649,-73.997298,0.624,32612,18926
20013,PO BOX,WASHINGTON,DC,,,,,
20037,STANDARD,WASHINGTON,DC,38.892459,-77.053811,0.732,14945,9689
```

20013 is a Washington, DC PO box ZIP: it has a city and a state, but no ZCTA, so the Census Fields are
NULL. This is expected, not an error. [`db_demo_coverage.json`](../output/db_demo_coverage.json) counts
it under `not_in_source` for those Fields.

With `--pk-set full` (42,730 ZIPs, about 1 second, no downloads):

| Fields | ZIPs with a value |
|---|---|
| `major_city`, `state` | 42,730 |
| `zipcode_type` | 42,724 (the 6 ZIPs newer than 2.x have none) |
| `lat`, `lng`, `land_area_in_sqmi` | 33,791 |
| `population`, `housing_units` | 33,774 |

The `major_city`, `state` and `zipcode_type` values were compared with `zipcode_universe.csv`, row by
row: no differences. The 17 ZCTAs in the 2025 Gazetteer but not in the 2020 DHC are in the island areas
(U.S. Virgin Islands 008xx, Guam, the Northern Mariana Islands and American Samoa), which the DHC file
does not cover.

The registry is not tied to these numbers: the tests build fake registries of 1 PK / 1 Field /
1 crawler, 3 / 5 / 2, 30 / 10 / 4, 300 / 64 / 8 and 5 / 300 / 3 and run check, crawl, build and refresh on each.

## Add a column

**From a source that already has a crawler** (for example, another DHC variable):

1. Add `fields/<name>.py` (copy [`population.py`](fields/population.py)), with examples of the source row.
2. List the module in `MODULES` in [`fields/__init__.py`](fields/__init__.py); its place there is its column position.
3. Add the name to the crawler's `fields`, and fetch the source column if the download does not include it yet.

**From a new source:**

1. Add `crawlers/<name>.py` (copy [`census_dhc.py`](crawlers/census_dhc.py)): downloads, `parse()`, `CRAWLER`.
2. List it in `MODULES` in [`crawlers/__init__.py`](crawlers/__init__.py).
3. Run `mise run pipeline-check` and add the task block it prints to `mise.toml`.
4. Add a parser test with a few real rows (see [`test_db_crawlers.py`](../tests/test_db_crawlers.py)).

**A group of columns** (one distribution): one module, named after the prefix the columns share, whose
`FIELDS` is built by a loop, one Field per number. See `test_a_module_can_generate_a_group_of_fields`.

Forgetting a step fails `mise run pipeline-check` or the tests (L1, K1, K3 or M1). As a measure of the
pattern: `zip-basics` was added with one crawler module, three Field modules, one line in each
`__init__.py` and one mise task, without touching the functionality.

## Decisions

Taken as defaults while the maintainer reviews; the maintainer's branch has the final word.

| # | Question | Decision | Status |
|---|---|---|---|
| 1 | Does `crawler-<name>` download again? | No: it reuses the cache and parses again; `-- --refresh` downloads again, at most once per 24 h | done |
| 2 | How are distributions stored? | One Field per number, generated by a loop in one module | pattern ready and tested; no distribution Field yet |
| 3 | How is history stored? | The main table holds the latest year; history goes to a separate long table `(zipcode, field, year, value)`. 256 numbers over 14 years would be 3,584 columns, and SQLite allows 2,000 | not built; comes with the first history crawler. F7 guards the limit |
| 4 | Where does the full database go? | A GitHub release asset, as in 2.x; git has only the demo | not published; waits for the Fields |
| 5 | Are city, state and ZIP type Fields? | Yes, claimed by `zip-basics`, which falls back HUD, ZBP, 2.x | done |
| 6 | Which Python? | 3.11+ for `data_pipeline/` only; `mise.toml` pins 3.12 and `pipeline-setup` installs pytest | done |
| 7 | CI? | A separate workflow, [`data_pipeline.yml`](../../.github/workflows/data_pipeline.yml), runs these tests on the `dev-jcw591*` branches; the existing workflow is unchanged | done |
| 8 | Island areas? | NULL for now. To add them later, `census-dhc` gets 4 more downloads (a Field has one crawler, so not a new crawler); the 4 island APIs list a ZCTA level, not tried yet | done (NULL) |

## Open questions for the maintainer

1. **"The whole code base."** Here the split is inside `data_pipeline/database/`, and `uszipcode/` is
   untouched. `zipcode_universe/` still has its own download code, because it builds the PK list rather than
   columns. Should it move onto `fetch.py`, and should the crawlers live inside the `uszipcode` package?
2. **`major_city` case.** It is upper case as HUD and ZBP write it; 2.x stored title case.
3. **`zipcode_type` source.** It comes only from 2.x, because no free government source has it, so new ZIPs have
   no type. Infer it from the HUD address flags instead?
4. **Census key.** `census-dhc` requires a key (free). Allow keyless calls instead (limited per IP per day)?
